from irse.indexing.nonparametric import Code, UnaryCode, toBinary, Encoding, Decoding


class GolombRiceCode(Code):

    def __init__(self, bucket_size: int):
        self.M = bucket_size
        self.unary = UnaryCode()
        self.offset_length = len(toBinary(bucket_size-1))  # Biggest offset possible needs this many bits

    def encode(self, source: int) -> Encoding:
        source -= 1  # Now it is >= 0. Saves us some bits.
        return self.unary.encode(source // self.M + 1) + toBinary(source % self.M).zfill(self.offset_length)  # + 1 to the quotient because it can be 0, and there is no unary for 0.

    def decode(self, target: Encoding) -> Decoding:
        q_plus_one, head = self.unary.decode(target)
        r = int(target[head:head+self.offset_length], 2)
        return ((q_plus_one-1)*self.M + r) + 1, head+self.offset_length
