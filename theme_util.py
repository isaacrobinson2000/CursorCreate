from pathlib import Path
from typing import Dict, Tuple, Union
import cursor_util
from cur_theme import get_theme_builders
from cursor import AnimatedCursor
from PIL import Image
import shutil
import json


CURRENT_FORMAT_VERSION = 1
CURRENT_FORMAT_NAME = "cursor_build_file"

def build_theme(theme_name: str, directory: Path, cursor_dict: Dict[str, AnimatedCursor]):
    """
    Build the specified theme using all currently loaded theme builders, building it for all platforms...

    :param theme_name: The name of the theme.
    :param directory: The directory to build the new theme in.
    :param cursor_dict: A dictionary of cursor name(string) to AnimatedCursor, specifying cursors and the types they
                        are suppose to be. Look at the 'DEFAULT_CURSORS' class variable in the CursorThemeBuilder
                        class to see all valid types which a theme builder will accept...
    """
    build_theme_in = directory / theme_name
    build_theme_in.mkdir(exist_ok=True)
    theme_builders = get_theme_builders()

    for theme_builder in theme_builders:
        ext_dir = build_theme_in / theme_builder.get_name()
        ext_dir.mkdir(exist_ok=True)
        theme_builder.build_theme(theme_name, cursor_dict, ext_dir)


def _make_image(cursor: AnimatedCursor) -> Image:
    """
    PRIVATE METHOD:
    Make an image from a cursor, representing all of it's frames. Used by save_project to make project art files
    when original files can't be found and copied over, as the cursor was loaded from the clip board as an image...

    :param cursor:
    :return:
    """
    cursor.normalize([(128, 128)])
    im = Image.new("RGBA", (128 * len(cursor), 128), (0, 0, 0, 0))

    for i, (cursor, delay) in enumerate(cursor):
        im.paste(cursor[(128, 128)].image, (128 * i, 0))

    return im


def _disable_newlines(json_data: str, num_lines_in: int) -> str:
    json_data = list(json_data)
    blocks = {"{": "}", "[": "]"}
    block_stack = []
    last_enter = None

    for i, value in enumerate(json_data):
        if (value in blocks):
            block_stack.append(blocks[value])
            if (len(block_stack) >= num_lines_in and json_data[i + 1] == "\n"):
                json_data[i + 1] = ""
        elif ((len(block_stack) > 0) and (block_stack[-1] == value)):
            if (len(block_stack) >= num_lines_in and last_enter is not None):
                json_data[last_enter] = ""
            block_stack.pop()
        elif ((len(block_stack) >= num_lines_in) and (value == "\n")):
            json_data[i] = " "
            last_enter = i
        elif ((len(block_stack) >= num_lines_in) and (value.isspace())):
            json_data[i] = ""

    return "".join(json_data)


def save_project(theme_name: str, directory: Path, file_dict: Dict[str, Tuple[Path, AnimatedCursor]]):
    build_theme_in = directory / theme_name
    build_theme_in.mkdir(exist_ok=True)

    json_obj = {
        "format": CURRENT_FORMAT_NAME,
        "version": CURRENT_FORMAT_VERSION,
        "data": []
    }

    for name, (file, cursor) in file_dict.items():
        cursor.normalize([(64, 64)])

        if(file is not None):
            new_file = build_theme_in / (name + file.suffix)
            if(Path(file) != Path(new_file)):
                shutil.copy(str(file), str(new_file))
        else:
            new_file = build_theme_in / (name + ".png")
            _make_image(cursor).save(str(new_file), "PNG")

        json_obj["data"].append({
            "cursor_name": name,
            "cursor_file": new_file.name,
            "hotspots_64": [sub_cursor[(64, 64)].hotspot for sub_cursor, delay in cursor],
            "delays": [delay for sub_cursor, delay in cursor],
        })

    with (build_theme_in / "build.json").open("w") as fp:
        fp.write(_disable_newlines(json.dumps(json_obj, indent=4), 4))


def load_project(theme_build_file: Path) -> Union[None, Dict[str, Tuple[Path, AnimatedCursor]]]:
    theme_build_dir = theme_build_file.parent

    with theme_build_file.open("r") as f:
        json_build_data = json.load(f)

        is_format = ("format" in json_build_data) and (json_build_data["format"] == CURRENT_FORMAT_NAME)
        is_version = ("version" in json_build_data) and (json_build_data["version"] == CURRENT_FORMAT_VERSION)

        file_cur_dict = {}

        if((not is_format) or (not is_version)):
            return None

        for cursor_info in json_build_data["data"]:
            cursor = None
            cursor_path = theme_build_dir / cursor_info["cursor_file"]

            with cursor_path.open("rb") as cur_file:
                cursor = cursor_util.load_cursor(cur_file)

            for i, delay in enumerate(cursor_info["delays"]):
                cursor[i] = (cursor[i][0], delay)

            for hotspot, (sub_cursor, delay) in zip(cursor_info["hotspots_64"], cursor):
                for size in sub_cursor:
                    x_hot, y_hot = int((size[0] / 64) * hotspot[0]), int((size[1] / 64) * hotspot[1])
                    sub_cursor[size].hotspot = (x_hot, y_hot)

            file_cur_dict[cursor_info["cursor_name"]] = (cursor_path, cursor)

        return file_cur_dict
