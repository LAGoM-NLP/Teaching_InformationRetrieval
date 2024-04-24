from typing import Iterable, List
from irse.indexing.nonparametric import Code, Encoding, Decoding, GammaCode, toBinary


class InterpolativeCode(Code):

    def __init__(self):
        self.initial_code = GammaCode()

    def encode(self, source: int) -> Encoding:
        raise RuntimeError("Interpolative code doesn't exist for individual numbers.")

    def decode(self, target: Encoding) -> Decoding:
        raise RuntimeError("Interpolative code doesn't exist for individual numbers.")

    def encodeMany(self, source: Iterable[int]) -> Encoding:
        L = list(source)
        return self.initial_code.encode(len(L)) \
               + self.initial_code.encode(L[0]) \
               + self.initial_code.encode(L[-1] - L[0]) \
               + self._encodeInternals(L)

    def _encodeInternals(self, source: List[int]) -> Encoding:
        """
        Encodes everything except the first and last element, which are assumed to have been encoded already.
        """
        if len(source) < 3:
            return ""

        mid_index = len(source) // 2

        minimum_possible = source[0]  + mid_index                    # If you're at [1], you have to be at least L[0] + 1.
        maximum_possible = source[-1] - (len(source)-1 - mid_index)  # If you're at [len(L)-2], you can be at most L[len(L)-1] - 1.
        possible_values = maximum_possible - minimum_possible + 1

        mid_value = source[mid_index]
        shifted_mid_value = mid_value - minimum_possible  # The result ranges from 0 up to (not including) possible_values.

        # print(f"{mid_value} in [{minimum_possible},{maximum_possible}] is offset by {shifted_mid_value} ({toBinary(shifted_mid_value).zfill(len(toBinary(possible_values-1)))}) inside the {possible_values} values.")
        # Note: 16 possible values can be encoded with 4 bits, 8 with 3 bits, 4 with 2 bits, 2 with 1 bit, so 1 should be encoded with 0 bits.
        #       This number can still be recovered because the decoder can always compute the length of the next value and will hence find that it should look for a 0-width number.
        return (toBinary(shifted_mid_value).zfill(len(toBinary(possible_values-1))) if possible_values > 1 else "") \
            + self._encodeInternals(source[:mid_index+1]) \
            + self._encodeInternals(source[mid_index:])

    def decodeMany(self, target: Encoding) -> Iterable[int]:
        while target:
            # Decode preamble
            head = 0
            n, extra_head = self.initial_code.decode(target[head:])
            head += extra_head
            L1, extra_head = self.initial_code.decode(target[head:])
            head += extra_head
            diff, extra_head = self.initial_code.decode(target[head:])
            head += extra_head
            Ln = L1 + diff

            # Decode recursively
            inner_values, extra_head = self._decodeInternals(target[head:], n, L1, Ln)
            head += extra_head
            target = target[head:]

            values = [L1] + inner_values + [Ln]
            for value in values:
                yield value

    def _decodeInternals(self, target: Encoding, n, L1, Ln):
        if n < 3:
            return [], 0

        # We know that we padded the result of the first recursive call by an amount of zeroes that was independent of
        # the value we encoded, using only the value of the boundaries and the index of the value in the list (n//2).
        mid_index = n//2

        minimum_possible = L1 + mid_index
        maximum_possible = Ln - (n-1 - mid_index)
        possible_values = maximum_possible - minimum_possible + 1

        # mid_value = source[mid_index]
        # shifted_mid_value = mid_value - minimum_possible  # The result ranges from 0 up to (not including) possible_values.

        if possible_values > 1:
            head      = len(toBinary(possible_values - 1))
            mid_value = int(target[:head], 2)
        else:
            head      = 0
            mid_value = 0

        mid_value += minimum_possible

        decoded_left_half, extra_head = self._decodeInternals(target[head:], mid_index+1, L1, mid_value)
        head += extra_head
        decoded_right_half, extra_head = self._decodeInternals(target[head:], n-1 - mid_index + 1, mid_value, Ln)
        head += extra_head
        return decoded_left_half + [mid_value] + decoded_right_half, head
