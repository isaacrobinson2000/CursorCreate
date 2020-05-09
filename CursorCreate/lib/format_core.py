from abc import ABC, abstractmethod
from typing import BinaryIO
from CursorCreate.lib.cursor import AnimatedCursor, Cursor


def to_bytes(num: int, length: int, byteorder: str="little") -> bytes:
    """
    Encode a python integer object as a unsigned n-bit length integer, stored in a bytes object

    :param num: The number to encode.
    :param length: The length of the unsigned integer to output, measured in bytes.
    :param byteorder: The byteorder. Valid options are "little" and "big"...
    :return: A bytes object encoding the unsigned integer of length bits...
    """
    return int.to_bytes(num, length, byteorder)

def to_int(b: bytes, byteorder: str="little") -> int:
    """
    Read in bytes as an unsigned integer...

    :param b: The bytes to decode to an unsigned integer...
    :param byteorder: The byteorder. Valid options are "little" and "big"...
    :return: An integer, represented by the bytes...
    """
    return int.from_bytes(b, byteorder)

def to_signed_int(b, byteorder="little"):
    """
    Read in bytes as an signed integer...

    :param b: The bytes to decode to an signed integer...
    :param byteorder: The byteorder. Valid options are "little" and "big"...
    :return: A signed integer, represented by the bytes...
    """
    new_int = to_int(b, byteorder)
    power = (2 ** (len(b) * 8))
    signed_limit = (power // 2) - 1
    print(new_int, power, signed_limit)

    if(new_int > signed_limit):
        new_int = -(power - new_int)

    return new_int

def to_signed_bytes(num, length, byteorder="little"):
    """
    Encode a python integer object as a signed n-bit length integer, stored in a bytes object.

    :param num: The number to encode.
    :param length: The length of the signed integer to output, measured in bytes.
    :param byteorder: The byteorder. Valid options are "little" and "big"...
    :return: A bytes object encoding the signed integer of length bits...
    """
    power = 2 ** int(length * 8)
    limit = power // 2
    num = int(num)

    if(not (-limit <= num < limit)):
        raise ValueError(f"Integer {num} must be between {-limit} and {limit - 1}")

    return to_bytes((power + num) % power, length, byteorder)

class CursorStorageFormat(ABC):
    """
    Abstract class for representing static cursor formats. It allows programs to read and write cursors to a specific
    file format. An example of a static cursor format is '.cur', the windows format for storing OS cursors.
    """

    __ERROR_MSG = "Subclass doesn't implement this method!!!"

    @classmethod
    @abstractmethod
    def check(cls, first_bytes):
        """
        Check and see if the specified file is of this format. Checks if the first bytes of this file match the
        expected 'magic' bytes for this format.

        :param first_bytes: The first 12 bytes of the file.
        :return: True if this file is of this format, otherwise False.
        """
        raise NotImplementedError(cls.__ERROR_MSG)

    @classmethod
    @abstractmethod
    def read(cls, cur_file: BinaryIO) -> AnimatedCursor:
        """
        Read in a file of this format as a static cursor.

        :param cur_file: A binary file handler pointing to the data which is desired to be open.
        :return: A Cursor object, representing a static cursor.
        """
        raise NotImplementedError(cls.__ERROR_MSG)

    @classmethod
    @abstractmethod
    def write(cls, cursor: Cursor, out: BinaryIO):
        """
        Write a static cursor in this format out to the specified file...

        :param cursor: A Cursor object, the static cursor to write to the file...
        :param out: The file which to write the cursor to in this format...
        """
        raise NotImplementedError(cls.__ERROR_MSG)

    @classmethod
    @abstractmethod
    def get_identifier(cls) -> str:
        """
        Get the identifier for this format. Is usually a 3-4 character string.

        :return: A string, representing this file format. Usually is the same as this files most common extension.
        """
        raise NotImplementedError(cls.__ERROR_MSG)


class AnimatedCursorStorageFormat(ABC):

    __ERROR_MSG = "Subclass doesn't implement this method!!!"

    @classmethod
    @abstractmethod
    def check(cls, first_bytes):
        """
        Check and see if the specified file is of this format. Checks if the first bytes of this file match the
        expected 'magic' bytes for this format.

        :param first_bytes: The first 12 bytes of the file.
        :return: True if this file is of this format, otherwise False.
        """
        raise NotImplementedError(cls.__ERROR_MSG)

    @classmethod
    @abstractmethod
    def read(cls, cur_file: BinaryIO) -> AnimatedCursor:
        """
        Read in a file of this format as an animated cursor.

        :param cur_file: A binary file handler pointing to the data which is desired to be open.
        :return: A AnimatedCursor object, representing an animated cursor.
        """
        raise NotImplementedError(cls.__ERROR_MSG)

    @classmethod
    @abstractmethod
    def write(cls, cursor: AnimatedCursor, out: BinaryIO):
        """
        Write an animated cursor in this format out to the specified file...

        :param cursor: An AnimatedCursor object, the animated cursor to write to the file...
        :param out: The file which to write the cursor to in this format...
        """
        raise NotImplementedError(cls.__ERROR_MSG)

    @classmethod
    @abstractmethod
    def get_identifier(cls) -> str:
        """
        Get the identifier for this format. Is usually a 3-4 character string.

        :return: A string, representing this file format. Usually is the same as this files most common extension.
        """
        raise NotImplementedError(cls.__ERROR_MSG)
