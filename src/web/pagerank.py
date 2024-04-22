"""
Code based on https://github.com/bhaveshgawri/PageRank.
except I took out all the bugs and simplified bad practices.
"""
from enum import Enum
from typing import Dict, List
from collections import defaultdict
from pathlib import Path

import numpy as np
from tqdm.auto import tqdm

from fiject import LineGraph


def readEdges(edge_file_tsv: Path):
    edges = defaultdict(list)

    with open(edge_file_tsv, "r", encoding="utf-8") as handle:
        for line in tqdm(handle, desc="Reading edge file"):
            if line.startswith("//") or line.startswith("#"):
                continue
            from_, to_ = line.strip().split('\t')
            from_, to_ = int(from_), int(to_)
            edges[from_].append(to_)

    return edges


class PageRank:

    def __init__(self, teleportation_probability: float, max_iterations: int=20, norm: int=2, epsilon: float=1e-6):
        self.gamma = 1 - teleportation_probability
        self.norm = norm
        self.epsilon = epsilon
        self.maximum_iterations = max_iterations

    def getPageRankVector(self, edges: Dict[int,List[int]], nodes: int=None, filter_sink_tail: bool=False,
                          plot: LineGraph=None):
        if not edges:
            return np.array([])

        # Find maximum node known to the graph.
        min_src_node_id = +np.inf
        max_src_node_id = -np.inf
        min_dst_node_id = +np.inf
        max_dst_node_id = -np.inf
        for source, destinations in edges.items():
            min_src_node_id = min(min_src_node_id,source)
            max_src_node_id = max(max_src_node_id,source)
            min_dst_node_id = min(min_dst_node_id,min(destinations))
            max_dst_node_id = max(max_dst_node_id,max(destinations))

        # Min node is just used for a warning.
        min_node_id = min(min_src_node_id, min_dst_node_id)
        if min_node_id > 1:
            print(f"Beware that the given graph starts at node {min_node_id} rather than 0 or 1, so a lot of dummy pages will be in the vector.")

        # Max node is used to have the correct PageRank vector size.
        if filter_sink_tail:
            max_node_id = max_src_node_id
            for source, destinations in edges.items():
                edges[source] = list(filter(lambda d: d <= max_node_id, destinations))
            print(edges)
        else:
            max_node_id = max(max_src_node_id, max_dst_node_id)

        N = max_node_id+1 if nodes is None else max(nodes, max_node_id+1)
        UNIFORM_PROBABILITY = np.ones(N)/N

        # Iterative computation (summation form; no matrices)
        prev_PR_vector = UNIFORM_PROBABILITY
        absolute_deviation = np.inf
        for i in tqdm(range(self.maximum_iterations), desc="PageRank"):
            if absolute_deviation < self.epsilon:
                break

            current_PR_vector = np.zeros(N)
            for source in edges:
                for destination in edges[source]:
                    current_PR_vector[destination] += prev_PR_vector[source] / len(edges[source])  # Probability of being at the source times probability of jumping to the destination from there.

            # Renormalise
            current_PR_vector /= np.sum(current_PR_vector)

            # Add teleportation
            current_PR_vector = self.gamma*current_PR_vector + (1-self.gamma)*UNIFORM_PROBABILITY

            absolute_deviation = np.linalg.norm(current_PR_vector - prev_PR_vector, ord=self.norm)
            prev_PR_vector = current_PR_vector

            if plot is not None:
                plot.add(f"PageRank ($N={N}$, $\gamma = {self.gamma}$) $||\cdot||_{self.norm}$", i, absolute_deviation)

        return prev_PR_vector


if __name__ == "__main__":
    from src.general import PATH_DATA_IN
    # test = ROOT / "data" / "web" / "test1.tsv"
    test = PATH_DATA_IN / "web" / "wikitalk.tsv"

    pr = PageRank(teleportation_probability=0.15, max_iterations=50, norm=1)

    g = LineGraph("PR-convergence")

    ###
    # edges = readEdges(test)

    from src.web.crawler import PATH_DATA_OUT, JACK
    crawler = JACK()
    edges = crawler.graphFromCrawl(PATH_DATA_OUT / "crawl-180417.json")
    ###

    print(pr.getPageRankVector(edges, filter_sink_tail=True, plot=g))
    g.commitWithArgs(
        LineGraph.ArgsGlobal(x_label="Iteration", y_label="Absolute change", legend_position="upper right"),
        LineGraph.ArgsPerLine(show_points=False)
    )
