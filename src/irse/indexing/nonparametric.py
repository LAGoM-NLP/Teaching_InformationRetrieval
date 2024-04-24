from typing import Tuple, Iterable
from abc import abstractmethod, ABC


Encoding = str
Decoding = Tuple[int,int]  # Result and how much you moved in the input.

ONE = "1"
ZERO = "0"

def toBinary(i: int) -> Encoding:
    return bin(i)[2:]


class Code(ABC):

    @abstractmethod
    def encode(self, source: int) -> Encoding:
        pass

    @abstractmethod
    def decode(self, target: Encoding) -> Decoding:
        pass

    def encodeMany(self, source: Iterable[int]) -> Encoding:
        return "".join(map(self.encode, source))

    def decodeMany(self, target: Encoding) -> Iterable[int]:
        while target:
            result, cursor = self.decode(target)
            target = target[cursor:]
            yield result


class UnaryCode(Code):

    def encode(self, source: int) -> Encoding:  # 1 is 1, 2 is 01, 3 is 001, ...
        return ZERO*(source-1) + ONE

    def decode(self, target: Encoding) -> Decoding:
        i = 0
        while target[i] == ZERO:
            i += 1
        return i+1, i+1


class GammaCode(Code):

    def __init__(self):
        self.unary = UnaryCode()

    def encode(self, source: int) -> Encoding:
        b = toBinary(source)
        return self.unary.encode(len(b)) + b[1:]

    def decode(self, target: Encoding) -> Decoding:
        length, head = self.unary.decode(target)
        return int(ONE + target[head:head+length-1], base=2), head+length-1  # length-1 because the first 1 is truncated.


class DeltaCode(Code):

    def __init__(self):
        self.gamma = GammaCode()

    def encode(self, source: int) -> Encoding:
        b = toBinary(source)
        return self.gamma.encode(len(b)) + b[1:]

    def decode(self, target: Encoding) -> Decoding:
        length, head = self.gamma.decode(target)
        return int(ONE + target[head:head+length-1], base=2), head+length-1  # length-1 because the first 1 is truncated.


class OmegaCode(Code):

    def encode(self, source: int) -> Encoding:
        result = ZERO
        while source != 1:
            b = toBinary(source)  # Length at least 2 since source is >= 2, i.e. "10".
            result = b + result
            source = len(b)-1  # >= 1 as a result
        return result

    def decode(self, target: Encoding) -> Decoding:
        head = 0
        next_length = 2
        while target[head] != ZERO:
            next_chunk = target[head:head+next_length]
            head       += next_length
            next_length = int(next_chunk, 2) + 1
        return next_length-1, head+1


class VByte(Code):

    def encode(self, source: int) -> Encoding:
        bits = toBinary(source)
        result = ""
        n_bytes = (len(bits)-1)//7+1  # There are as many bytes as ceil(len/7), i.e. 1 at 1,2,3,4,5,6,7 bits, 2 at 8,9,10,11,12,13,14, 3 at 15, ...
        bits = bits.zfill(n_bytes*7)  # Make sure we can chunk it nicely starting in the front rather than the back.
        for i in range(n_bytes):
            result += (ZERO if i != n_bytes-1 else ONE) + bits[7*i:7*(i+1)]
        return result

    def decode(self, target: Encoding) -> Decoding:
        bits = ""
        head = 0
        stop = False
        while not stop:
            stop = target[head] == ONE
            bits += target[head+1:head+8]
            head += 8
        return int(bits, 2), head


class Simple9(Code):

    def __init__(self):
        self.possible_amounts = [1, 2, 3, 4, 5, 7, 9, 14, 28]

    def encode(self, source: int) -> Encoding:
        raise RuntimeError("Simple-9 has no individual encoding.")

    def decode(self, target: Encoding) -> Decoding:
        raise RuntimeError("Simple-9 has no individual decoding.")

    def encodeMany(self, source: Iterable[int]) -> Encoding:
        """
        Go through the list, and accumulate numbers. Then, you can do two things:
          1. switch preferred mode, or
          2. commit to the word.
        The first happens when an integer has a bigger length than the current stride. Possibly, you then have to commit
        what was already in the buffer using the old stride.
        The second happens when your accumulated numbers can fill up the current mode, i.e. there are  >= amount  integers.
        """
        result = ""
        buffer = []

        amount_index = len(self.possible_amounts) - 1
        amount       = self.possible_amounts[amount_index]
        for number in source:
            bits = toBinary(number)
            buffer.append(bits)

            if len(bits) > 28 // amount:  # Current stride can't support this length.
                new_index  = amount_index
                new_amount = amount
                while len(bits) > 28 // new_amount:
                    new_index -= 1
                    new_amount = self.possible_amounts[new_index]

                # Now here's the thing: this new number may need a new mode that has so few slots that the buffer would
                # fill the slots before getting to this new number. If that's the case, don't use this new stride yet, but
                # commit using the old stride. If the buffer does fit, no "emergency commit" has to be done yet.
                if len(buffer) > new_amount:  # The buffer stretches past the new amount, and the last element is that new integer.
                    new_bits = (toBinary(amount) if amount != 28 else ZERO).zfill(4) + "".join(map(lambda bits: bits.zfill(28 // amount), buffer[:-1]))  # Note the :-1 instead of :amount because we're not sure if we can even fill all the old slots. We only know we have too much for the new slots.
                    result += new_bits + ZERO*(32-len(new_bits))
                    buffer = [buffer[-1]]

                amount_index = new_index
                amount       = new_amount

            # Normal commit
            if len(buffer) >= amount:
                new_bits = (toBinary(amount) if amount != 28 else ZERO).zfill(4) + "".join(map(lambda bits: bits.zfill(28//amount), buffer[:amount]))
                result += new_bits + ZERO*(32-len(new_bits))
                buffer = buffer[amount:]

                # Reset stride
                amount_index = len(self.possible_amounts) - 1
                amount       = self.possible_amounts[amount_index]

        if buffer:  # Use the current stride, which we know is valid, to commit the rest.
            new_bits = (toBinary(amount) if amount != 28 else ZERO).zfill(4) + "".join(map(lambda bits: bits.zfill(28 // amount), buffer[:amount]))
            result += new_bits + ZERO * (32 - len(new_bits))

        return result

    def decodeMany(self, target: Encoding) -> Iterable[int]:
        while target:
            amount = int(target[:4], 2) or 28
            stride = 28 // amount
            for i in range(amount):
                number = int(target[4 + i*stride:4 + (i+1)*stride], 2)
                if number == 0:
                    break
                yield number

            target = target[32:] # Will trim off an extra '28 % amount' versus what the loop saw.
