from abc import ABC, abstractmethod
from typing import BinaryIO
from cursor import AnimatedCursor, Cursor


def to_bytes(num, length, byteorder="little"):
    return int.to_bytes(num, length, byteorder)

def to_int(b, byteorder="little"):
    return int.from_bytes(b, byteorder)

def to_signed_int(b, byteorder="little"):
    new_int = to_int(b, byteorder)
    power = (2 ** (len(b) * 8))
    signed_limit = (power // 2) - 1
    print(new_int, power, signed_limit)

    if(new_int > signed_limit):
        new_int = -(power - new_int)

    return new_int

def to_signed_bytes(num, length, byteorder="little"):
    power = 2 ** int(length * 8)
    limit = power // 2
    num = int(num)

    if(not (-limit <= num < limit)):
        raise ValueError(f"Integer {num} must be between {-limit} and {limit - 1}")

    return to_bytes((power + num) % power, length, byteorder)

class CursorStorageFormat(ABC):
    @classmethod
    @abstractmethod
    def check(cls, first_bytes):
        pass

    @classmethod
    @abstractmethod
    def read(cls, cur_file: BinaryIO) -> AnimatedCursor:
        pass

    @classmethod
    @abstractmethod
    def write(cls, cursor: Cursor, out: BinaryIO):
        pass


class AnimatedCursorStorageFormat(ABC):
    @classmethod
    @abstractmethod
    def check(cls, first_bytes):
        pass

    @classmethod
    @abstractmethod
    def read(cls, cur_file: BinaryIO) -> AnimatedCursor:
        pass

    @classmethod
    @abstractmethod
    def write(cls, cursor: AnimatedCursor, out: BinaryIO):
        pass