from typing import Iterable, Dict, Tuple, List
from collections import Counter
from dataclasses import dataclass
import numpy as np

from src.indexing.nonparametric import Code, Encoding, Decoding, ONE, ZERO, toBinary


CanonicalCodebook = Tuple[List[str], List[int]]


@dataclass
class HuffmanTree:

    weight: int
    name: str
    left: "HuffmanTree" =None
    right: "HuffmanTree" =None

    def __lt__(self, other: "HuffmanTree"):
        return self.weight < other.weight

    def __add__(self, other: "HuffmanTree") -> "HuffmanTree":
        return HuffmanTree(
            weight=self.weight + other.weight,
            name=self.name + other.name,
            left=self,
            right=other
        )

    def isLeaf(self):
        return self.left is None and self.right is None

    def getCodebook(self) -> Dict[str,str]:
        if self.isLeaf():  # You are a lone node.
            return {self.name: ""}
        else:
            return {k: ZERO + v for k,v in self.left.getCodebook().items()} \
                 | {k: ONE  + v for k,v in self.right.getCodebook().items()}

    def getCodebookCanonical(self) -> CanonicalCodebook:
        codebook = self.getCodebook()
        return tuple(zip(*sorted([(k, len(v)) for k,v in codebook.items()])))

    @staticmethod
    def fromCodebook(codebook: Dict[str,str]) -> "HuffmanTree":
        if len(codebook) == 1:
            assert all(len(v) == 0 for v in codebook.values())

            key, codeword = codebook.popitem()
            codebook[key] = codeword  # Don't want to alter the codebook.
            return HuffmanTree(
                weight=0,
                name=key
            )
        else:
            assert all(len(v) > 0 for v in codebook.values())

            left_codewords  = {k: v[1:] for k,v in codebook.items() if v[0] == ZERO}
            right_codewords = {k: v[1:] for k,v in codebook.items() if v[0] == ONE}

            return HuffmanTree.fromCodebook(left_codewords) + HuffmanTree.fromCodebook(right_codewords)

    @staticmethod
    def fromCanonicalCodebook(codebook: CanonicalCodebook) -> "HuffmanTree":
        lengths = list(zip(codebook[1], codebook[0]))
        lengths.sort()

        reverse_codebook = dict()
        while lengths:
            length, key = lengths.pop(0)

            codeword = ""
            while len(codeword) < length:
                if codeword + ZERO not in reverse_codebook:
                    codeword += ZERO
                elif codeword + ONE not in reverse_codebook:
                    codeword += ONE
                else:  # This is possible: if you have 3 codewords with length 3, you could have 000 and 001, and it should backtrack to flip the first 0 that doesn't create a prefix.
                    while True:
                        last_zero = codeword.rfind(ZERO)
                        codeword = codeword[:last_zero]
                        if codeword + ONE not in reverse_codebook:
                            break
                    codeword += ONE

            reverse_codebook[codeword] = key

        return HuffmanTree.fromCodebook({v:k for k,v in reverse_codebook.items()})


class HuffmanCode(Code):

    def __init__(self):
        self.tree: HuffmanTree = None

    def train(self, corpus: Iterable[str]):
        self.trainFromCounts(Counter(corpus))

    def trainFromCounts(self, counts: Counter):
        nodes = [HuffmanTree(weight=count, name=str(key)) for key, count in counts.items()]
        nodes.sort(reverse=True)  # Lowest-probability keys are now at the end.

        while len(nodes) > 1:
            # Pop worst nodes and combine them
            worst_node        = nodes.pop()
            second_worst_node = nodes.pop()
            combination = second_worst_node + worst_node

            # Insert
            i = 0
            while i < len(nodes) and combination < nodes[i]:
                i += 1
            nodes.insert(i, combination)

        self.tree = nodes[0]

    def encode(self, source: str) -> Encoding:
        return self.tree.getCodebook().get(source)

    def decode(self, target: Encoding) -> Decoding:
        current_node = self.tree
        head = 0
        while True:
            if current_node.isLeaf():
                return current_node.name, head
            if head >= len(target):  # Consumed the full thing but didn't get anywhere.
                return "", head

            if target[head] == ZERO:
                current_node = current_node.left
            elif target[head] == ONE:
                current_node = current_node.right
            else:
                raise ValueError("Found weird character in encoding:", target[head])
            head += 1


class LLRUN(HuffmanCode):

    def train(self, corpus: Iterable[int]):
        buckets = Counter()
        for number in corpus:
            buckets[int(np.log2(number))] += 1  # [2^i ... 2^{i+1}-1] all have the same result for int(log2), namely i, and there are 2^i such numbers, codable with i bits of offset.

        # Make sure there are no gaps in the bucket numbers. We expect numbers anywhere in the maximum bucket range (but nothing beyond that).
        for bucket in range(max(buckets.keys())):
            if bucket not in buckets:
                buckets[bucket] = 0

        self.trainFromCounts(buckets)

    def encode(self, source: int) -> Encoding:
        bucket = int(np.log2(source))
        return self.tree.getCodebook()[str(bucket)] + (toBinary(source - 2**bucket).zfill(bucket) if bucket != 0 else "")  # No length indications needed. Huffman will go down the tree and stop at the boundary, and then we will also know how many bits the rest took to encode.

    def decode(self, target: Encoding) -> Decoding:
        bucket, head = super().decode(target)
        if not bucket:
            return 0, head

        bucket = int(bucket)
        return 2**bucket + (int(target[head:head+bucket], 2) if bucket != 0 else 0), head+bucket
