from io import BytesIO
from typing import BinaryIO
from cursor import AnimatedCursor, Cursor, CursorIcon
import cairosvg
from PIL import Image, UnidentifiedImageError
import ani_format
import cur_format
import xcur_format
from xml.etree import ElementTree

DEFAULT_SIZES = [(24, 24), (32, 32), (48, 48), (64, 64), (128, 128)]
MAX_DEFAULT_SIZE = DEFAULT_SIZES[-1]

def load_cursor_from_image(file: BinaryIO) -> AnimatedCursor:
    image: Image.Image = Image.open(file)

    height = image.size[1]
    num_frames = image.size[0] // height

    images = [image.crop((i * height, 0, i * height + height, height)) for i in range(num_frames)]

    final_cursor = AnimatedCursor()

    for img in images:
        frame = Cursor()

        for size in DEFAULT_SIZES:
            frame.add(CursorIcon(img.resize(size, Image.LANCZOS), 0, 0))

        final_cursor.append((frame, 100))

    return final_cursor


def load_cursor_from_svg(file: BinaryIO) -> AnimatedCursor:
    mem_png = BytesIO()
    cairosvg.svg2png(file_obj=file, write_to=mem_png)
    file.seek(0)
    size_ref_img = Image.open(mem_png)

    h_to_w_multiplier = size_ref_img.size[0] / size_ref_img.size[1]
    num_frames = int(h_to_w_multiplier)

    ani_cur = AnimatedCursor([Cursor() for i in range(num_frames)], [100] * num_frames)

    for sizes in DEFAULT_SIZES:
        image = BytesIO()
        cairosvg.svg2png(file_obj=file, write_to=image, output_height=sizes[1],
                         output_width=int(sizes[1] * h_to_w_multiplier))
        file.seek(0)
        image = Image.open(image)

        height = image.size[1]
        for i in range(num_frames):
            ani_cur[i][0].add(CursorIcon(image.crop((i * height, 0, i * height + height, height)), 0, 0))

    return ani_cur


def load_cursor_from_cursor(file: BinaryIO) -> AnimatedCursor:
    ani_cur_readers = [ani_format.AniFormat, xcur_format.XCursorFormat]
    cur_readers = [cur_format.CurFormat]

    file.seek(0)
    magic = file.read(12)
    file.seek(0)

    for reader in ani_cur_readers:
        if(reader.check(magic)):
            ani_cur = reader.read(file)
            ani_cur.normalize(DEFAULT_SIZES)
            ani_cur.remove_non_square_sizes()
            return ani_cur

    for reader in cur_readers:
        if(reader.check(magic)):
            ani_cur = AnimatedCursor([reader.read(file)], [100])
            ani_cur.normalize(DEFAULT_SIZES)
            ani_cur.remove_non_square_sizes()
            return ani_cur

    raise ValueError("Unsupported cursor format.")


def load_cursor(file: BinaryIO):
    try:
        return load_cursor_from_cursor(file)
    except ValueError:
        file.seek(0)
        try:
            return load_cursor_from_image(file)
        except UnidentifiedImageError:
            file.seek(0)
            try:
                return load_cursor_from_svg(file)
            except ElementTree.ParseError:
                raise ValueError("Unable to open file by any specified methods...")

