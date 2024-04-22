from src.indexing.nonparametric import GammaCode, DeltaCode, OmegaCode, Simple9, VByte
from src.indexing.parametric import GolombRiceCode
from src.indexing.contextual import InterpolativeCode
from src.indexing.huffman import HuffmanCode, LLRUN, HuffmanTree


def test_postings():
    g = GammaCode()
    print(g.encode(5))
    print(g.decode(g.encode(5)))

    d = DeltaCode()
    print(int("10111", 2))  # 23 in binary has length 5, and hence its delta code should start with the above result.
    print(d.encode(23))
    print(d.decode(d.encode(23)))

    o = OmegaCode()
    print(o.encode(69))  # Omega code should have the exact number you want to encode as the last bits, plus a 0.
    print(o.decode(o.encode(69)))

    postings = [69, 58, 1, 421, 1]
    print(o.encodeMany(postings))
    print(list(o.decodeMany(o.encodeMany(postings))))

    s = Simple9()
    print(s.encodeMany(postings))
    print(list(s.decodeMany(s.encodeMany(postings))))

    v = VByte()
    print(v.encodeMany(postings))
    print(list(v.decodeMany(v.encodeMany(postings))))

    g = GolombRiceCode(64)
    print(g.encodeMany(postings))
    print(list(g.decodeMany(g.encodeMany(postings))))

    ordered_postings = [2,9,12,14,19,21,31,32,33]  # Example from lecture 8, slide 68 (2022). Encoded, it should be "0001001 010 000011111 01101 1000 0110 001 1010 0001 "
    i = InterpolativeCode()
    print(i.encodeMany(ordered_postings))
    print(list(i.decodeMany(i.encodeMany(ordered_postings))))


def test_huffman():
    h = HuffmanCode()
    h.trainFromCounts({"c": 12, "d": 13, "a": 5, "b": 9, "e": 16, "f": 45})  # https://www.geeksforgeeks.org/huffman-coding-greedy-algo-3/
    print(h.tree.getCodebookCanonical())
    print(sorted(h.tree.getCodebook().items()))  # Note: Geeks4Geeks implements it such that the lower-probability child leans left and hence receives a 0. I give a 0 to the highest-probability child, so all my bits are flipped.

    h2 = HuffmanTree.fromCodebook(h.tree.getCodebook())
    print(sorted(h2.getCodebook().items()))

    # Note: in a canonical Huffman tree, ordering isn't done based on probability, but on codeword length (which is not
    #       known when constructing the tree otherwise), meaning that it's now not the heaviest child that receives a 0,
    #       but rather the shortest child. The shortest subword hence consists entirely of 0.
    h3 = HuffmanTree.fromCanonicalCodebook(h.tree.getCodebookCanonical())
    print(sorted(h3.getCodebook().items()))

    words = ["a", "f", "b", "e", "d"]
    print(h.encodeMany(words))
    print(list(h.decodeMany(h.encodeMany(words))))

    postings = [69, 58, 1, 421, 1]
    l = LLRUN()
    l.train([1,2,3,54,50,10,20,40,50,60,40,4,5,7,545,7,54,754,8,4,54,2,45,755,57,154])
    print(l.tree.getCodebook())
    print(l.encodeMany(postings))
    print(list(l.decodeMany(l.encodeMany(postings))))


if __name__ == "__main__":
    test_huffman()
    # test_postings()
