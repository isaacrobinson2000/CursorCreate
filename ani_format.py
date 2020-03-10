from io import BytesIO
from typing import BinaryIO, Iterator, Tuple, Set, Dict, Any
from format_core import AnimatedCursorStorageFormat, to_int, to_bytes, to_signed_bytes
from PIL import BmpImagePlugin, Image
from cur_format import CurFormat
from cursor import CursorIcon, Cursor, AnimatedCursor
import copy
import numpy as np

# The default dpi for BMP images written by this encoder...
DEF_BMP_DPI = (96, 96)

# UTILITY METHODS:
def read_chunks(buffer: BinaryIO, skip_chunks: Set[bytes]=None, list_chunks: Set[bytes]=None, byteorder="little") -> Iterator[Tuple[bytes, int, bytes]]:
    if(skip_chunks is None):
        skip_chunks = set()
    if(list_chunks is None):
        list_chunks = set()

    while(True):
        next_id = buffer.read(4)
        if(next_id == b''):
            return
        if(next_id in skip_chunks):
            continue

        size = to_int(buffer.read(4), byteorder=byteorder)

        if(next_id in list_chunks):
            print(f"(entering {next_id} chunk) -> [")
            yield from read_chunks(BytesIO(buffer.read(size)), skip_chunks, list_chunks, byteorder)
            print(f"](exiting {next_id} chunk)")
            continue

        print(f"emit chunk {next_id} of size {size}")
        yield (next_id, size, buffer.read(size))


def write_chunk(buffer: BinaryIO, chunk_id: bytes, chunk_data: bytes, byteorder="little"):
    buffer.write(chunk_id[:4])
    buffer.write(to_bytes(len(chunk_data), 4, byteorder=byteorder))
    buffer.write(chunk_data)


def _header_chunk(header: None, data: bytes, data_out: Dict[str, Any]):
    if(header is not None):
        raise SyntaxError("This ani has 2 headers!")

    if(len(data) == 36):
        data = data[4:]

    h_data = {
        "num_frames": to_int(data[0:4]),
        "num_steps": to_int(data[4:8]),
        "width": to_int(data[8:12]),
        "height": to_int(data[12:16]),
        "bit_count": to_int(data[16:20]),
        "num_planes": 1,
        "display_rate": to_int(data[24:28]),
        "contains_seq": bool((to_int(data[28:32]) >> 1) & 1),
        "is_in_ico": bool(to_int(data[28:32]) & 1)
    }

    data_out["header"] = h_data
    data_out["seq"] = [i % h_data["num_frames"] for i in range(h_data["num_steps"])]
    data_out["rate"] = [h_data["display_rate"]] * h_data["num_steps"]


def _icon_chunk(header: Dict[str, Any], data: bytes, data_out: Dict[str, Any]):
    if(header is None):
        raise SyntaxError("icon chunk became before header!")

    if(header["is_in_ico"]):
        # Cursors are stored as either .cur or .ico, use CurFormat to read them...
        cursor = CurFormat.read(BytesIO(data))
    else:
        # BMP format, load in and then correct the height...
        c_icon = CursorIcon(BmpImagePlugin.DibImageFile(BytesIO(data)), 0, 0)
        c_icon.image._size = (c_icon.image.size[0], c_icon.image.size[1] // 2)
        d, e, o, a = c_icon.image.tile[0]
        c_icon.image.tile[0] = d, (0, 0) + c_icon.image.size, o, a
        # Add the image to the cursor list...
        cursor = Cursor([c_icon])

    if("list" not in data_out):
        data_out["list"] = []

    data_out["list"].append(cursor)


def _seq_chunk(header: Dict[str, Any], data: bytes, data_out: Dict[str, Any]):
    if(header is None):
        raise SyntaxError("seq chunk came before header!")

    if((len(data) // 4) != header["num_steps"]):
        raise SyntaxError("Length of sequence chunk does not match the number of steps!")

    data_out["seq"] = [to_int(data[i:i+4]) for i in range(0, len(data), 4)]


def _rate_chunk(header: Dict[str, Any], data: bytes, data_out: Dict[str, Any]):
    if(header is None):
        raise SyntaxError("rate chunk became before header!")

    if((len(data) // 4) != header["num_steps"]):
        raise SyntaxError("Length of rate chunk does not match the number of steps!")

    data_out["rate"] = [to_int(data[i:i+4]) for i in range(0, len(data), 4)]


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
    out_file.write(to_bytes(4 * img.size[0] * img.size[1], 4)) # The size of the image data...
    out_file.write(to_signed_bytes(ppm[0], 4)) # The resolution of the width in pixels per meter...
    out_file.write(to_signed_bytes(ppm[1], 4)) # The resolution of the height in pixels per meter...
    out_file.write(to_bytes(0, 4)) # The number of colors in the color table, in this case none...
    out_file.write(to_bytes(0, 4)) # Number of important colors in the color table, again none...

    img = img.convert("RGBA")
    data = np.array(img)
    # Create the alpha channel...
    alpha_channel = data[:, :, 3]
    alpha_channel = alpha_channel == 0
    # Create the main image with transparency...
    bgrx_data = data[:, :, (2, 1, 0, 3)]



class AniFormat(AnimatedCursorStorageFormat):
    RIFF_MAGIC = b"RIFF"
    ACON_MAGIC = b"ACON"

    CHUNKS = {
        b"anih": _header_chunk,
        b"icon": _icon_chunk,
        b"rate": _rate_chunk,
        b"seq ": _seq_chunk
    }

    @classmethod
    def check(cls, first_bytes) -> bool:
        return ((first_bytes[:4] == cls.RIFF_MAGIC) and (first_bytes[8:12] == cls.ACON_MAGIC))

    @classmethod
    def read(cls, cur_file: BinaryIO) -> AnimatedCursor:
        magic_header = cur_file.read(12)

        if(not cls.check(magic_header)):
            raise SyntaxError("Not a .ani file!")

        ani_data: Dict[str, Any] = {"header": None}

        for chunk_id, chunk_len, chunk_data in read_chunks(cur_file, {b"fram"}, {b"LIST"}):
            if(chunk_id in cls.CHUNKS):
                cls.CHUNKS[chunk_id](ani_data["header"], chunk_data, ani_data)

        ani_cur = AnimatedCursor()

        for idx, rate in zip(ani_data["seq"], ani_data["rate"]):
            # We have to convert the rate to milliseconds. Normally stored in jiffies(1/60ths of a second)
            ani_cur.append((ani_data["list"][idx], int((rate * 1000) / 60)))

        return ani_cur


    DEF_CURSOR_SIZE = (32, 32)

    @classmethod
    def write(cls, cursor: AnimatedCursor, out: BinaryIO):
        # Normalize the cursor sizes...
        cursor = copy.deepcopy(cursor)
        cursor.normalize([cls.DEF_CURSOR_SIZE])
        cursor.remove_non_square_sizes()

        # Write the magic...
        out.write(cls.RIFF_MAGIC)
        # We will deal with writing the length of the entire file later...
        out.write(b"\0\0\0\0")
        out.write(cls.ACON_MAGIC)

        # Write the header...
        header = bytearray(36)
        # We write the header length twice for some dumb reason...
        header[0:4] = to_bytes(36, 4)  # Header length...
        header[4:8] = to_bytes(len(cursor), 4)  # Number of frames
        header[8:12] = to_bytes(len(cursor), 4)  # Number of steps
        # Ignore width, height, and bits per pixel...
        # The number of planes should always be 1....
        header[24:28] = to_bytes(1, 4)
        header[28:32] = to_bytes(10, 4)  # We just pass 10 as the default delay...
        header[32:36] = to_bytes(1, 4)  # The flags, last flag is flipped which specifies data is stored in .cur

        write_chunk(out, b"anih", header)

        # Write the LIST of icons...
        list_data = bytearray(b"fram")
        delay_data = bytearray()

        for sub_cursor, delay in cursor:
            # Writing a single cursor to the list...
            mem_stream = BytesIO()
            CurFormat.write(sub_cursor, mem_stream)
            # We write these chunks manually to avoid wasting a ton of lines of code, as using "write_chunks" ends up
            # being just as complicated...
            cur_data = mem_stream.getvalue()
            list_data.extend(b"icon")
            list_data.extend(to_bytes(len(cur_data), 4))
            list_data.extend(cur_data)
            # Writing the delay to the rate chunk
            delay_data.extend(to_bytes(round((delay * 60) / 1000), 4))

        # Now that we have gathered the data actually write the chunks...
        write_chunk(out, b"LIST", list_data)
        write_chunk(out, b"rate", delay_data)

        # Now we are to the end, get the length of the file and write it as the RIFF chunk length...
        entire_file_len = out.tell() - 8
        out.seek(4)
        out.write(to_bytes(entire_file_len, 4))