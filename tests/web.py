import numpy.random as npr

from src.web.crawler import *
from src.web.pagerank import PageRank
from src.retrieval.bm25 import OkapiRetrieval


def exampleCrawl():
    crawler = JACK(get_href_from_sides=False, truncate_outlinks=True)
    # crawler.crawl("https://en.wikipedia.org/wiki/Integral", max_crawls=50)
    return crawler.crawl("https://en.wikipedia.org/wiki/Language", max_crawls=100)


def exampleRanking(path: Path, use_pagerank=True, use_filterrank=False):
    # Filter
    corpus = list(JACK.corpusFromCrawl(path))   # Brace yourselves, this may be a lot.
    ir = OkapiRetrieval(corpus)

    # Ranker
    pr = PageRank(teleportation_probability=0.15)
    ranks = pr.getPageRankVector(JACK.graphFromCrawl(path))

    while True:
        print("="*79)
        query = ""
        while not query:
            query = input("Query: ")

        ids_and_scores = ir.filter(query, truncate_at=50)
        filter_set = [i for i, _ in ids_and_scores]

        # Re-rank
        if not use_filterrank:
            npr.shuffle(filter_set)
        if use_pagerank:
            filter_set.sort(key=lambda i: ranks[i], reverse=True)  # Highest-PR first.

        # Output 5 most relevant.
        for n,i in enumerate(filter_set[:5]):
            print("="*35, "MATCH", n+1, "="*35)
            print(corpus[i])


if __name__ == "__main__":
    # exampleCrawl()
    exampleRanking(PATH_DATA_OUT / "crawl-190326.json",
                   use_pagerank=True)