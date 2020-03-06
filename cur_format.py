from typing import BinaryIO
from io import BytesIO
from PIL.IcoImagePlugin import IcoFile
from PIL import Image
from cursor import Cursor, CursorIcon
from format_core import CursorStorageFormat, to_bytes


class CurFormat(CursorStorageFormat):

    MAGIC = b"\0\0\2\0"
    ICO_MAGIC = b"\0\0\1\0"

    @classmethod
    def check(cls, first_bytes) -> bool:
        return first_bytes[:4] == cls.MAGIC or first_bytes[:4] == cls.ICO_MAGIC

    @classmethod
    def read(cls, cur_file: BinaryIO) -> Cursor:
        """
        Read a cursor file in the windows .cur format.

        :param cur_file: The file or file-like object to read from.
        :return: A Cursor
        """
        magic_header = cur_file.read(4)

        if(not cls.check(magic_header)):
            raise SyntaxError("Not a Cur Type File!!!")

        is_ico = (magic_header == cls.ICO_MAGIC)

        # Dump the file with the ico header to allow to be read by Pillow Ico reader...
        data = BytesIO()
        data.write(cls.ICO_MAGIC)
        data.write(cur_file.read())
        data.seek(0)

        ico_img = IcoFile(data)
        cursor = Cursor()

        for head in ico_img.entry:
            width = head["width"]
            height = head["height"]
            x_hot = 0 if(is_ico) else head["planes"]
            y_hot = 0 if(is_ico) else head["bpp"]

            # Check that hotspots are valid...
            if(not (0 <= x_hot < width)):
                x_hot = 0
            if(not (0 <= y_hot < height)):
                y_hot = 0

            image = ico_img.getimage((width, height))

            cursor.add(CursorIcon(image, x_hot, y_hot))

        return cursor


    @classmethod
    def _to_png(cls, image: Image.Image, size) -> bytes:
        temp = image.copy()
        temp.thumbnail(size, Image.LANCZOS)
        byte_io = BytesIO()
        temp.save(byte_io, "png")
        return byte_io.getvalue()

    @classmethod
    def write(cls, cursor: Cursor, out: BinaryIO):
        """
        Writes cursor to a file in the form of the windows .cur format...

        :param cursor: The cursor object to save.
        :param out: The file handle to output the cursor to.
        """
        out.write(cls.MAGIC)
        out.write(to_bytes(len(cursor), 2))

        offset = out.tell() + len(cursor) * 16
        imgs = []

        for size in cursor:
            width, height = size

            hot_x, hot_y = cursor[size].hotspot
            hot_x, hot_y = hot_x if (0 <= hot_x < width) else 0, hot_y if(0 <= hot_y < height) else 0

            image_data = cls._to_png(cursor[size].image, (width, height))

            width, height = width if(width < 256) else 0, height if(height < 256) else 0

            out.write(to_bytes(width, 1))
            out.write(to_bytes(height, 1))
            out.write(b"\0\0")
            out.write(to_bytes(hot_x, 2))
            out.write(to_bytes(hot_y, 2))
            out.write(to_bytes(len(image_data), 4))
            out.write(to_bytes(offset, 4))

            offset += len(image_data)
            imgs.append(image_data)

        for image_data in imgs:
            out.write(image_data)
