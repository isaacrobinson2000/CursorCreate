from io import BytesIO
from typing import BinaryIO

from CursorCreate.lib.cursor import AnimatedCursor, Cursor, CursorIcon
import cairosvg
from PIL import Image, ImageOps
from CursorCreate.lib import format_core
from xml.etree import ElementTree
from PIL import ImageSequence

# Some versions of pillow don't actually have this error, so just set this exception to the general case in this case.
try:
    from PIL import UnidentifiedImageError
except ImportError as e:
    UnidentifiedImageError = Exception


# Default sizes which all cursors loaded with this module are normalized with...
DEFAULT_SIZES = [(32, 32), (48, 48), (64, 64), (128, 128)]
MAX_DEFAULT_SIZE = DEFAULT_SIZES[-1]

def load_cursor_from_image(file: BinaryIO) -> AnimatedCursor:
    """
    Load a cursor from an image. Image is expected to be square. If it is not square, this method will slide
    horizontally across the image using a height * height square, loading each following square as next frame of the
    cursor with a delay of 100 and hotspots of (0, 0). Note this method supports all formats supported by the
    PIL or pillow Image library. If the image passed is an animated image format like .gif or .apng, this method
    will avoid loading in horizontal square tiles and will rather load in each frame of the image as each frame of
    the cursor.

    :param file: The file handler pointing to the image data.
    :return: An AnimatedCursor object, representing an animated cursor. Static cursors will only have 1 frame.
    """
    image: Image.Image = Image.open(file)

    if(hasattr(image, "is_animated") and (image.is_animated)):
        # If this is an animated file, load in each frame as the frames of the cursor (Ex, ".gif")
        min_dim = min(image.size) # We fit the image to a square...
        images_durations = [(ImageOps.fit(image, (min_dim, min_dim)), frame.info.get("duration", 100))
                            for frame in ImageSequence.Iterator(image)]
    else:
        # Separate all frames (Assumed to be stored horizontally)
        height = image.size[1]
        num_frames = image.size[0] // height

        if(num_frames == 0):
            raise ValueError("Image width is smaller then height so this will load as a 0 frame cursor!!!")

        images_durations = [(image.crop((i * height, 0, i * height + height, height)), 100) for i in range(num_frames)]

    # Now convert images into the cursors, resizing them to match all the default sizes...
    final_cursor = AnimatedCursor()

    for img, delay in images_durations:
        frame = Cursor()

        for size in DEFAULT_SIZES:
            frame.add(CursorIcon(img.resize(size, Image.LANCZOS), 0, 0))

        final_cursor.append((frame, delay))

    return final_cursor


def load_cursor_from_svg(file: BinaryIO) -> AnimatedCursor:
    """
    Load a cursor from an SVG. SVG is expected to be square. If it is not square, this method will slide
    horizontally across the SVG using a height * height square, loading each following square as next frame of the
    cursor with a delay of 100 and hotspots of (0, 0). Note this method uses CairoSVG library to load and render
    SVGs of various sizes to bitmaps. For info on supported SVG features, look at the docs for the CairoSVG library.

    :param file: The file handler pointing to the SVG data.
    :return: An AnimatedCursor object, representing an animated cursor. Static cursors will only have 1 frame.
    """
    # Convert SVG in memory to PNG, and read that in with PIL to get the default size of the SVG...
    mem_png = BytesIO()
    cairosvg.svg2png(file_obj=file, write_to=mem_png)
    file.seek(0)
    size_ref_img = Image.open(mem_png)

    # Compute height to width ratio an the number of frame(Assumes they are stored horizontally)...
    h_to_w_multiplier = size_ref_img.size[0] / size_ref_img.size[1]
    num_frames = int(h_to_w_multiplier)

    if (num_frames == 0):
        raise ValueError("Image width is smaller then height so this will load as a 0 frame cursor!!!")

    # Build empty animated cursor to start stashing frames in...
    ani_cur = AnimatedCursor([Cursor() for __ in range(num_frames)], [100] * num_frames)

    for sizes in DEFAULT_SIZES:
        # For each default size, resize svg to it and add all frames to the AnimatedCursor object...
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
    """
    Loads a cursor from one of the supported cursor formats implemented in this library. Normalizes sizes and
    removes non-square versions of the cursor...

    :param file: The file handler pointing to the SVG data.
    :return: An AnimatedCursor object, representing an animated cursor. Static cursors will only have 1 frame.
    """
    # Currently supported cursor formats...
    ani_cur_readers = format_core.AnimatedCursorStorageFormat.__subclasses__()
    cur_readers = format_core.CursorStorageFormat.__subclasses__()

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
    """
    Loads a cursor from any array of formats, including cursor formats (cur, ani, xcur), Images, and SVGs.

    :param file: The file handler pointing to a format which is convertible to a cursor.
    :return: A AnimatedCursor object, will contain a single frame if representing a static cursor...

    :raises: A ValueError if format is unknown (not a .svg, image, or cursor format) or if the width of the image is
             smaller than the height of the image, meaning it would be loaded as a 0-frame cursor (only applies to
             non-cursor formats)...
    """
    try:
        return load_cursor_from_cursor(file)
    except ValueError:
        file.seek(0)
        try:
            return load_cursor_from_image(file)
        except (UnidentifiedImageError):
            file.seek(0)
            try:
                return load_cursor_from_svg(file)
            except ElementTree.ParseError:
                raise ValueError("Unable to open file by any specified methods...")