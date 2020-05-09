from io import BytesIO
from typing import BinaryIO, Iterator, Tuple, Set, Dict, Any
from CursorCreate.lib.format_core import AnimatedCursorStorageFormat, to_int, to_bytes
from PIL import BmpImagePlugin
from CursorCreate.lib.cur_format import CurFormat
from CursorCreate.lib.cursor import CursorIcon, Cursor, AnimatedCursor


# UTILITY METHODS:
def read_chunks(buffer: BinaryIO, skip_chunks: Set[bytes]=None, list_chunks: Set[bytes]=None, byteorder="little") -> Iterator[Tuple[bytes, int, bytes]]:
    """
    Reads a valid RIFF file, reading all the chunks in the file...

    :param buffer: The file buffer with valid RIFF data.
    :param skip_chunks: A set of length 4 bytes specifying chunks which are not actual chunks but are identifiers
                        followed by valid chunks.
    :param list_chunks: A set of length 4 bytes specifying chunks which containing sub-chunks, meaning there data
                        should be sub-iterated.
    :param byteorder: The byteorder of the integers in the file, "big" or "little". Default is "little".
    :return: A generator which yields each chunks identifier, size, and data as bytes.
    """
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
            # print(f"(entering {next_id} chunk) -> [")
            yield from read_chunks(BytesIO(buffer.read(size)), skip_chunks, list_chunks, byteorder)
            # print(f"](exiting {next_id} chunk)")
            continue

        # print(f"emit chunk {next_id} of size {size}")
        yield (next_id, size, buffer.read(size))


def write_chunk(buffer: BinaryIO, chunk_id: bytes, chunk_data: bytes, byteorder="little"):
    """
    Writes a chunk to file.

    :param buffer: The file buffer to write to.
    :param chunk_id: The 4 byte chunk identifier.
    :param chunk_data: The chunk's data as a bytes object.
    :param byteorder: The byteorder to use when writing the byte's size, defaults to "little"
    """
    buffer.write(chunk_id[:4])
    buffer.write(to_bytes(len(chunk_data), 4, byteorder=byteorder))
    buffer.write(chunk_data)


def _header_chunk(header: None, data: bytes, data_out: Dict[str, Any]):
    """
    Represents .ani's header chunk, which has an identifier of "anih".
    """
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
    """
    Represents .ani icon chunk, which has an identifier of "icon".
    """
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
    """
    Represents .ani's sequence chunk, which has an identifier of "seq ".
    """
    if(header is None):
        raise SyntaxError("seq chunk came before header!")

    if((len(data) // 4) != header["num_steps"]):
        raise SyntaxError("Length of sequence chunk does not match the number of steps!")

    data_out["seq"] = [to_int(data[i:i+4]) for i in range(0, len(data), 4)]


def _rate_chunk(header: Dict[str, Any], data: bytes, data_out: Dict[str, Any]):
    """
    Represents .ani's rate chunk, which has an identifier of "rate".
    """
    if(header is None):
        raise SyntaxError("rate chunk became before header!")

    if((len(data) // 4) != header["num_steps"]):
        raise SyntaxError("Length of rate chunk does not match the number of steps!")

    data_out["rate"] = [to_int(data[i:i+4]) for i in range(0, len(data), 4)]

class AniFormat(AnimatedCursorStorageFormat):
    """
    Represents the windows .ani format, used on windows for storing animated cursors. The file is a type of RIFF file
    with an identifier of "ACON" and contains a list of .cur files internally in "icon" chunks. The "seq " chunk stores
    the order to play the icons in and and "rate" chunk specifies the rate each frame should last on screen, measured
    in 1/60ths of a second.
    """

    # Magic for general RIFF format and ANI format.
    RIFF_MAGIC = b"RIFF"
    ACON_MAGIC = b"ACON"

    # All important .ani RIFF chunks which are vital to reading the file.
    CHUNKS = {
        b"anih": _header_chunk,
        b"icon": _icon_chunk,
        b"rate": _rate_chunk,
        b"seq ": _seq_chunk
    }

    @classmethod
    def check(cls, first_bytes) -> bool:
        """
        Check if the first bytes of this file are a valid windows .ani file

        :param first_bytes: The first 12 bytes of the file being tested.
        :return: True if a valid windows .ani file, otherwise False.
        """
        return ((first_bytes[:4] == cls.RIFF_MAGIC) and (first_bytes[8:12] == cls.ACON_MAGIC))

    @classmethod
    def read(cls, cur_file: BinaryIO) -> AnimatedCursor:
        """
        Read a windows .ani file from disk to an AnimatedCursor.

        :param cur_file: The file buffer pointer to the windows .ani data.
        :return: An AnimatedCursor object storing all cursor info.
        """
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


    @classmethod
    def write(cls, cursor: AnimatedCursor, out: BinaryIO):
        """
        Write an AnimatedCursor to the specified file in the windows .ani format.

        :param cursor: The AnimatedCursor object to write.
        :param out: The file buffer to write the new .ani data to.
        """
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

    @classmethod
    def get_identifier(cls) -> str:
        return "ani"