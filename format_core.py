from abc import ABC, abstractmethod
from typing import BinaryIO
from cursor import AnimatedCursor, Cursor


def to_bytes(num, length, byteorder="little"):
    return int.to_bytes(num, length, byteorder)

def to_int(b, byteorder="little"):
    return int.from_bytes(b, byteorder)

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