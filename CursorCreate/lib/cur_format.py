from typing import BinaryIO
from io import BytesIO
from PIL.IcoImagePlugin import IcoFile
from PIL import Image
from CursorCreate.lib.cursor import Cursor, CursorIcon
from CursorCreate.lib.format_core import CursorStorageFormat, to_bytes, to_signed_bytes
import numpy as np

# The default dpi for BMP images written by this encoder...
DEF_BMP_DPI = (96, 96)

def _write_bmp(img: Image.Image, out_file: BinaryIO):
    # Grab the dpi for calculations later...
    dpi = img.info.get("dpi", DEF_BMP_DPI)
    ppm = tuple(int(dpi_val * 39.3701 + 0.5) for dpi_val in dpi)

    # BMP HEADER:
    out_file.write(to_bytes(40, 4)) # BMP Header size
    out_file.write(to_signed_bytes(img.size[0], 4)) # Image Width
    out_file.write(to_signed_bytes(img.size[1] * 2, 4)) # Image Height
    out_file.write(to_bytes(1, 2)) # Number of planes
    out_file.write(to_bytes(32, 2)) # The bits per pixel...
    out_file.write(to_bytes(0, 4)) # The compression method, we set it to raw or no compression...
    out_file.write(to_bytes(4 * img.size[0] * (img.size[1] * 2), 4)) # The size of the image data...
    out_file.write(to_signed_bytes(ppm[0], 4)) # The resolution of the width in pixels per meter...
    out_file.write(to_signed_bytes(ppm[1], 4)) # The resolution of the height in pixels per meter...
    out_file.write(to_bytes(0, 4)) # The number of colors in the color table, in this case none...
    out_file.write(to_bytes(0, 4)) # Number of important colors in the color table, again none...

    img = img.convert("RGBA")
    data = np.array(img)
    # Create the alpha channel...
    alpha_channel = data[:, :, 3]
    alpha_channel = np.packbits(alpha_channel == 0, axis=1)[::-1]
    # Create the main image with transparency...
    bgrx_data: np.ndarray = (data[::-1, :, (2, 1, 0, 3)])
    # Dump the main image...
    out_file.write(bgrx_data.tobytes())

    # We now dump the mask and some zeros to finish filling the space...
    mask_data = alpha_channel.tobytes()
    leftover_space = (img.size[0] * img.size[1] * 4) - len(mask_data)
    out_file.write(mask_data)
    out_file.write(bytes(leftover_space))


class CurFormat(CursorStorageFormat):
    """
    The windows .cur format, which is used for storing static cursors. It is a subset of the windows .ico format.
    Although windows supports placing png's in the cur rather then bmp images, it is poorly supported in the
    .ani decoder on windows so this encoder uses the older more well support nested bmp format.
    """

    MAGIC = b"\0\0\2\0"
    ICO_MAGIC = b"\0\0\1\0"

    @classmethod
    def check(cls, first_bytes) -> bool:
        """
        Check if the first bytes of this file match the windows .cur magic bytes.

        :param first_bytes: First 12 bytes of the file, this format actually only needs the first 4.
        :return: True if valid .cur, otherwise false...
        """
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
        if(image.size != size):
            raise ValueError("Size of image stored in image and cursor object don't match!!!")
        byte_io = BytesIO()
        image.save(byte_io, "png")
        return byte_io.getvalue()

    @classmethod
    def _to_bmp(cls, image: Image.Image, size) -> bytes:
        if (image.size != size):
            raise ValueError("Size of image stored in image and cursor object don't match!!!")
        byte_io = BytesIO()
        _write_bmp(image, byte_io)
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

        for size in sorted(cursor):
            width, height = size

            if(width > 256 or height > 256):
                continue

            hot_x, hot_y = cursor[size].hotspot
            hot_x, hot_y = hot_x if (0 <= hot_x < width) else 0, hot_y if(0 <= hot_y < height) else 0

            image_data = cls._to_bmp(cursor[size].image, (width, height))

            width, height = width if(width < 256) else 0, height if(height < 256) else 0

            out.write(to_bytes(width, 1)) # Width, 1 byte.
            out.write(to_bytes(height, 1)) # Height, 1 byte.
            out.write(b"\0\0")
            out.write(to_bytes(hot_x, 2))
            out.write(to_bytes(hot_y, 2))
            out.write(to_bytes(len(image_data), 4))
            out.write(to_bytes(offset, 4))

            offset += len(image_data)
            imgs.append(image_data)

        for image_data in imgs:
            out.write(image_data)

    @classmethod
    def get_identifier(cls) -> str:
        return "cur"
