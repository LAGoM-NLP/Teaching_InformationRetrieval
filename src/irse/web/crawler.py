from pathlib import Path
from typing import List, Dict, Optional, Tuple, Iterable

from irse.general import PATH_DATA_OUT

import json
import requests
import bs4
import lxml
import time
from urllib.parse import urlparse


class JACK:
    """
    Just Another Crawler Klass.

    Probably the dumbest crawler you could write.
    No URL buffer memory limit. No duplicate page checking. No resuming. No robots.txt check.

    The only intelligent feature is that you can disqualify any links with <nav> or <footer> as ancestor, e.g. if you want
    to crawl Wikipedia without the sidebar (although that's much more difficult in their new layout, smh).
    """

    def __init__(self, get_href_from_sides: bool=False, truncate_outlinks: bool=True):
        self.do_surroundings = get_href_from_sides
        self.do_truncate = truncate_outlinks

    def crawl(self, starting_url: str, max_crawls: int) -> Path:
        known  = {starting_url: 0}
        buffer = [starting_url]

        extracted_data = dict()

        i = 0
        while buffer and i < max_crawls:
            current_url = buffer.pop(0)

            # Get page
            print(f"Crawling URL {i+1}:", current_url)
            soup = self._getSoup(current_url)
            if soup is None:
                continue

            # Get anchors with hrefs, then add them to the buffer if not already seen.
            outlinks = self._getUniqueHrefs(current_url, soup)
            out_ids = []
            for href in outlinks:
                if href not in known:
                    buffer.append(href)
                    known[href] = len(known)
                    # print("\t> New link:", href)
                out_ids.append(known.get(href))
            out_ids = sorted(out_ids)

            # Get payload
            title, body = self._getContent(soup)
            extracted_data[i] = {
                "url": current_url,
                "title": title,
                "body": body,
                "outlinks": out_ids if not self.do_truncate else list(filter(lambda i: i < max_crawls, out_ids))
            }

            # Wait a bit before your next request.
            time.sleep(1)
            i += 1

        if i < max_crawls:
            print("Stopped crawling prematurely because the link buffer was emptied.")

        print("Saving results...")
        output = PATH_DATA_OUT / time.strftime("crawl-%H%M%S.json")
        with open(output, "w", encoding="utf-8") as handle:
            json.dump(extracted_data, handle, indent=4)
        return output

    def _getSoup(self, url: str) -> Optional[bs4.BeautifulSoup]:
        parsed_url = urlparse(url)
        if "wikipedia." in parsed_url.netloc:  # New Wikipedia layout no longer puts the translation pages in a <nav> and that causes messy crawling.
            url += "?useskin=vector"

        try:
            response = requests.get(url)
        except:
            print("\tURL couldn't be requested.")
            return None

        if response.status_code == 200 and response.headers.get("Content-Type", "").startswith("text/html"):
            try:
                return bs4.BeautifulSoup(response.text, features="lxml")
            except:
                print("\tFailed to make soup :(")
                return None
        else:
            print(f"\tURL either isn't HTML or has bad status code ({response.status_code}).")
            return None

    def _getUniqueHrefs(self, url: str, soup: bs4.BeautifulSoup) -> List[str]:
        parsed_url = urlparse(url)
        outlinks = []
        for a in soup.find_all("a", href=True):
            if not self.do_surroundings and len(a.find_parents(["nav", "footer"])) > 0:
                continue

            # Sanitise href
            href = a["href"]
            parsed_href = urlparse(href)
            if not parsed_href.netloc:
                href = parsed_url.scheme + "://" + parsed_url.netloc + parsed_href.path
                parsed_href = urlparse(href)
            if not parsed_href.scheme:
                href = "https://" + parsed_href.netloc + parsed_href.path

            # Add if not already on the page (we're not using a set, because we want to keep the order).
            if href not in outlinks:
                outlinks.append(href)

        return outlinks

    def _getContent(self, soup: bs4.BeautifulSoup) -> Tuple[str, str]:
        tag = soup.find("title")
        if tag is not None:
            title = tag.text
        else:
            title = ""

        for tag in soup.find_all("p"):
            if len(tag.text.split()) > 20:
                body = tag.text
                break
        else:
            body = ""

        return title, body

    @staticmethod
    def graphFromCrawl(crawler_output: Path) -> Dict[int,List[int]]:
        with open(crawler_output, "r", encoding="utf-8") as handle:
            data = json.load(handle)

        graph = dict()
        for i,id_data in data.items():
            graph[int(i)] = id_data["outlinks"]

        return graph

    @staticmethod
    def corpusFromCrawl(crawler_output: Path) -> Iterable[str]:
        with open(crawler_output, "r", encoding="utf-8") as handle:
            data = json.load(handle)

        for i,id_data in data.items():
            yield id_data["title"] + "\n" + id_data["body"]
