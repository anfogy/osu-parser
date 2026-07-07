class BufferReader(bytearray):
    __slots__ = ("__pointer",)

    def __init__(self, source=None) -> None:
        super().__init__(source)
        self.__pointer = 0

    def read(self, n: int) -> bytes:
        chunk = self[self.__pointer:self.__pointer + n]
        self.__pointer += len(chunk)
        return bytes(chunk)


class ULEB128(object):
    def __init__(self, value: int | bytes | bytearray):
        if isinstance(value, int):
            self.value = value
            self.bytes = self.__encode_int()
        elif isinstance(value, (bytes, bytearray)):
            self.bytes = bytes(value)
            self.value = self.__decode_bytes()
        else:
            raise TypeError("Value must be an int, bytes, or bytearray")

    def __encode_int(self) -> bytes:
        if self.value < 0:
            raise ValueError("ULEB128 value cannot be negative")

        buffer = []
        while True:
            byte = self.value & 0x7F
            self.value >>= 7
            if self.value != 0:
                byte |= 0x80
            buffer.append(byte)
            if self.value == 0:
                break
        return bytes(buffer)

    def __decode_bytes(self) -> int:
        result = 0
        shift = 0
        for byte in self.bytes:
            result |= (byte & 0x7F) << shift
            if not (byte & 0x80):
                break
            shift += 7
        return result

    def __repr__(self):
        return f"ULEB128(int={self.value}, bytes={self.bytes!r})"
