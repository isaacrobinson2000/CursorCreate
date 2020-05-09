from typing import BinaryIO, Tuple

import numpy as np
from PIL import Image

from CursorCreate.lib.cursor import AnimatedCursor, CursorIcon, Cursor
from CursorCreate.lib.format_core import AnimatedCursorStorageFormat, to_int, to_bytes


class XCursorFormat(AnimatedCursorStorageFormat):
    """
    The linux for X-Org format for storing cursor, both animated and static. Contains "XCur" magic followed by the
    number of entries in the file. Each entry is 16 bytes and contains the type, subtype, offset, and length. Out
    in memory at the offset is another header which gives the type and subtype again and then gives the
    width, height, x hotspot, y hotspot, and the delay, followed by BGRA image data. Note all attributes in this format
    are stored as 4 byte or 32 bit little endian unsigned integers except image data described above.
    """
    MAGIC = b"Xcur"
    VERSION = 65536
    CURSOR_TYPE = 0xfffd0002
    HEADER_SIZE = 16
    IMG_CHUNK_H_SIZE = 36
    # The downscaling factor of the nominal size...
    SIZE_SCALING_FACTOR = 3 / 4

    @classmethod
    def check(cls, first_bytes):
        """
        Check if the first bytes of this file are a valid x-org cursor file

        :param first_bytes: The first 12 bytes of the file being tested.
        :return: True if a valid x-org cursor file, otherwise False.
        """
        return first_bytes[:4] == cls.MAGIC

    @classmethod
    def _assert(cls, boolean, msg="Something is wrong!!!"):
        """ Private, used for throwing exceptions when assertions don't hold while reading the format. """
        if(not boolean):
            raise SyntaxError(msg)

    @classmethod
    def read(cls, cur_file: BinaryIO) -> AnimatedCursor:
        """
        Read an xcur or X-Org cursor file from the specified file buffer.

        :param cur_file: The file buffer with xcursor data.
        :return: An AnimatedCursor object, non-animated cursors will contain only 1 frame.
        """
        magic_data = cur_file.read(4)

        cls._assert(cls.check(magic_data), "Not a XCursor File!!!")

        header_size = to_int(cur_file.read(4))
        cls._assert(header_size == cls.HEADER_SIZE, f"Header size is not {cls.HEADER_SIZE}!")
        version = to_int(cur_file.read(4))

        # Number of cursors...
        num_toc = to_int(cur_file.read(4))
        # Used to store cursor offsets per size...
        nominal_sizes = {}

        for i in range(num_toc):
            main_type = to_int(cur_file.read(4))

            if(main_type == cls.CURSOR_TYPE):
                nominal_size = to_int(cur_file.read(4))
                offset = to_int(cur_file.read(4))

                if(nominal_size not in nominal_sizes):
                    nominal_sizes[nominal_size] = [offset]
                else:
                    nominal_sizes[nominal_size].append(offset)

        max_len = max(len(nominal_sizes[size]) for size in nominal_sizes)
        cursors = []
        delays = []

        for i in range(max_len):
            cursor = Cursor()
            sub_delays = []

            for size, offsets in nominal_sizes.items():
                if(i < len(offsets)):
                    img, x_hot, y_hot, delay = cls._read_chunk(offsets[i], cur_file, size)
                    cursor.add(CursorIcon(img, x_hot, y_hot))
                    sub_delays.append(delay)

            cursors.append(cursor)
            delays.append(max(sub_delays))

        return AnimatedCursor(cursors, delays)


    @classmethod
    def _read_chunk(cls, offset: int, buffer: BinaryIO, nominal_size: int) -> Tuple[Image.Image, int, int, int]:
        buffer.seek(offset)
        # Begin to check if this is valid...
        chunk_size = to_int(buffer.read(4))
        cls._assert(chunk_size == cls.IMG_CHUNK_H_SIZE, f"Image chunks must be {cls.IMG_CHUNK_H_SIZE} bytes!")
        cls._assert(to_int(buffer.read(4)) == cls.CURSOR_TYPE, f"Type does not match type in TOC!")
        cls._assert(to_int(buffer.read(4)) == nominal_size, f"Nominal sizes in TOC and image header don't match!")
        cls._assert(to_int(buffer.read(4)) == 1, f"Unsupported version of image header...")
        # Checks are done, load the rest of the header as we are good from here...
        rest_of_chunk = buffer.read(20)
        width, height, x_hot, y_hot, delay = [to_int(rest_of_chunk[i:i+4]) for i in range(0, len(rest_of_chunk), 4)]

        cls._assert(width <= 0x7fff, "Invalid width!")
        cls._assert(height <= 0x7fff, "Invalid height!")

        x_hot, y_hot = x_hot if(0 <= x_hot < width) else 0, y_hot if(0 <= y_hot < height) else 0

        img_data = np.frombuffer(buffer.read(width * height * 4), dtype=np.uint8).reshape(width, height, 4)

        # ARGB packed in little endian format, therefore its actually BGRA when read sequentially....
        image = Image.fromarray(img_data[:, :, (2, 1, 0, 3)], "RGBA")

        return (image, x_hot, y_hot, delay)


    @classmethod
    def write(cls, cursor: AnimatedCursor, out: BinaryIO):
        """
        Write an AnimatedCursor to the specified file in the X-Org cursor format.

        :param cursor: The AnimatedCursor object to write.
        :param out: The file buffer to write the new X-Org Cursor data to.
        """
        cursor = cursor.copy()
        cursor.normalize()

        if(len(cursor) == 0):
            return

        num_curs = sum(len(l) for l, delay in cursor)

        out.write(cls.MAGIC)
        out.write(to_bytes(cls.HEADER_SIZE, 4))
        out.write(to_bytes(cls.VERSION, 4))

        out.write(to_bytes(num_curs, 4))
        # The initial offset...
        offset = (num_curs * 12 + cls.HEADER_SIZE)

        sorted_sizes = sorted(cursor[0][0])

        # Write the Table of contents [type, subtype(size), offset]
        for size in sorted_sizes:
            for sub_cur, delay in cursor:
                out.write(to_bytes(cls.CURSOR_TYPE, 4))
                out.write(to_bytes(int(size[0] * cls.SIZE_SCALING_FACTOR), 4))
                out.write(to_bytes(offset, 4))
                offset += cls.IMG_CHUNK_H_SIZE + (size[0] * size[1] * 4)

        # Write the actual images...
        for size in sorted_sizes:
            for sub_cur, delay in cursor:
                cls._write_chunk(out, sub_cur[size], delay)


    @classmethod
    def _write_chunk(cls, out_file: BinaryIO, img: CursorIcon, delay: int):
        out_file.write(to_bytes(cls.IMG_CHUNK_H_SIZE, 4))
        out_file.write(to_bytes(cls.CURSOR_TYPE, 4))
        out_file.write(to_bytes(int(img.image.size[0] * cls.SIZE_SCALING_FACTOR), 4))
        out_file.write(to_bytes(1, 4))

        # The width and height...
        width, height = img.image.size
        x_hot, y_hot = img.hotspot
        cls._assert(width <= 0x7fff, "Invalid width!")
        cls._assert(height <= 0x7fff, "Invalid height!")
        out_file.write(to_bytes(width, 4))
        out_file.write(to_bytes(width, 4))
        x_hot, y_hot = x_hot if(0 <= x_hot < width) else 0, y_hot if(0 <= y_hot < height) else 0

        # Hotspot and delay...
        out_file.write(to_bytes(x_hot, 4))
        out_file.write(to_bytes(y_hot, 4))
        out_file.write(to_bytes(delay, 4))

        # Now the image, ARGB packed in little endian integers...(So really BGRA)(ARGB -> BGRA)
        im_bytes = (np.asarray(img.image.convert("RGBA"))[:, :, (2, 1, 0, 3)]).tobytes()
        out_file.write(im_bytes)

    @classmethod
    def get_identifier(cls) -> str:
        return "xcur"