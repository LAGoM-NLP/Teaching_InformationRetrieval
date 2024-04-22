from pathlib import Path
from typing import List, Dict

from src.general import PATH_DATA_OUT

import json
import requests
import bs4
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

    def __init__(self, do_surroundings: bool=False):
        self.do_surroundings = do_surroundings

    def crawl(self, starting_url: str, max_crawls: int):
        """
        Creates the following tables:
            ID -> URL
            ID -> linked-to-IDs
            ID -> <title>
        """
        known  = {starting_url: 0}
        buffer = [starting_url]

        extracted_data = dict()

        i = 0
        while buffer and i < max_crawls:
            current_url = buffer.pop(0)
            parsed_url  = urlparse(current_url)

            # Get page
            print("Crawling", current_url)
            url_to_get = current_url
            if "wikipedia." in parsed_url.netloc:  # New Wikipedia layout no longer puts the translation pages in a <nav> and that causes messy crawling.
                url_to_get += "?useskin=vector"

            response = requests.get(url_to_get)
            if response.status_code == 200 and response.headers.get("Content-Type").startswith("text/html"):
                soup = bs4.BeautifulSoup(response.text, features="lxml")
            else:
                continue

            # Get anchors with hrefs, then add them to the buffer if not already seen.
            outlinks = set()
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

                if href not in known:
                    buffer.append(href)
                    known[href] = len(known)
                    # print("\t> New link:", href)
                outlinks.add(known[href])

            outlinks = sorted(outlinks)

            # Get payload
            extracted_data[i] = {
                "url": current_url,
                "title": soup.find("title").text,
                "outlinks": outlinks
            }

            # Wait a bit before your next request.
            time.sleep(1)
            i += 1

        with open(PATH_DATA_OUT / time.strftime("crawl-%H%M%S.json"), "w", encoding="utf-8") as handle:
            json.dump(extracted_data, handle, indent=4)

    def graphFromCrawl(self, crawler_output: Path) -> Dict[int,List[int]]:
        with open(crawler_output, "r", encoding="utf-8") as handle:
            data = json.load(handle)

        graph = dict()
        for i,id_data in data.items():
            graph[int(i)] = id_data["outlinks"]

        return graph


if __name__ == "__main__":
    crawler = JACK(do_surroundings=False)
    # crawler.crawl("https://en.wikipedia.org/wiki/Integral", max_crawls=50)
    crawler.crawl("https://en.wikipedia.org/wiki/Language", max_crawls=100)
