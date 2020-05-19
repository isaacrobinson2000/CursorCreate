from pathlib import Path
from typing import Dict, Tuple, Union, Any
from CursorCreate.lib import cursor_util
from CursorCreate.lib.cur_theme import get_theme_builders
from CursorCreate.lib.cursor import AnimatedCursor
from PIL import Image
import shutil
import json
import traceback

CURRENT_FORMAT_VERSION = 1
CURRENT_FORMAT_NAME = "cursor_build_file"

def build_theme(theme_name: str, directory: Path, metadata: Dict[str, Any], cursor_dict: Dict[str, AnimatedCursor]):
    """
    Build the specified theme using all currently loaded theme builders, building it for all platforms...

    :param theme_name: The name of the theme.
    :param directory: The directory to build the new theme in.
    :param metadata: A dictionary of string to any(mostly string) stores "author", and "licence".
    :param cursor_dict: A dictionary of cursor name(string) to AnimatedCursor, specifying cursors and the types they
                        are suppose to be. Look at the 'DEFAULT_CURSORS' class variable in the CursorThemeBuilder
                        class to see all valid types which a theme builder will accept...
    """
    build_theme_in = directory / theme_name
    build_theme_in.mkdir(exist_ok=True)
    theme_builders = get_theme_builders()

    for theme_builder in theme_builders:
        try:
            ext_dir = build_theme_in / theme_builder.get_name()
            ext_dir.mkdir(exist_ok=True)
            theme_builder.build_theme(theme_name, metadata, cursor_dict, ext_dir)
        except Exception:
            traceback.print_exc()


def _make_image(cursor: AnimatedCursor) -> Image:
    """
    PRIVATE METHOD:
    Make an image from a cursor, representing all of it's frames. Used by save_project to make project art files
    when original files can't be found and copied over, as the cursor was loaded from the clip board as an image
    or dragged and dropped from the internet...

    :param cursor: The cursor to convert to a tiled horizontal image.
    :return: An picture with frames stored horizontally...
    """
    cursor.normalize([(128, 128)])
    im = Image.new("RGBA", (128 * len(cursor), 128), (0, 0, 0, 0))

    for i, (cursor, delay) in enumerate(cursor):
        im.paste(cursor[(128, 128)].image, (128 * i, 0))

    return im


def _disable_newlines(json_data: str, num_lines_in: int) -> str:
    """
    PRIVATE METHOD:
    Strip new lines in a json made by python's json parser a certain amount of blocks in. Used by save_project
    to write a cleaner json file.

    :param json_data: The json data to strip of new lines.
    :param num_lines_in: Number of json "blocks" in (blocks are defined by {} and [])
    :return: A cleaner json string with some new line characters stripped...
    """
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


def save_project(theme_name: str, directory: Path, metadata: Dict[str, Any], file_dict: Dict[str, Tuple[Path, AnimatedCursor]]):
    """
    Save the cursor project to the cursor project format, which includes all source images and a build.json which
    specifies how to build the platform dependent cursor themes from the source images.

    :param theme_name: The name of this new project.
    :param directory: The directory to save the new project in.
    :param metadata: A dictionary of string to any(mostly string) stores "author", and "licence".
    :param file_dict: A dictionary of cursor name(string) to a tuple of source file and AnimatedCursor, specifying
                      cursors, there source files and the types they are suppose to be. Look at the 'DEFAULT_CURSORS'
                      class variable in the CursorThemeBuilder class to see all valid types which a theme builder
                      will accept... The source files will be copied into the project's main directory if available,
                      otherwise a tiled png will be made from the animated cursor object included...
    """
    build_theme_in = directory / theme_name
    build_theme_in.mkdir(exist_ok=True)

    json_obj = {
        "format": CURRENT_FORMAT_NAME,
        "version": CURRENT_FORMAT_VERSION,
        "metadata": metadata,
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


def load_project(theme_build_file: Path) -> Union[None, Tuple[Dict[str, Any], Dict[str, Tuple[Path, AnimatedCursor]]]]:
    """
    Load a cursor theme project from it's build.json file, and return it's (source file, cursor) dictionary...

    :param theme_build_file: The path to the build.json of this cursor theme project.
    :return: A tuple, containing 2 items in order:
                - dictionary of string -> any. Contains metadata, including the licence, author, and etc.
                - dictionary of name(string) -> (source file path, cursor). This specifies all data needed to build the
                  cursor project.
    """
    theme_build_dir = theme_build_file.resolve().parent

    with theme_build_file.open("r") as f:
        json_build_data = json.load(f)

        is_format = ("format" in json_build_data) and (json_build_data["format"] == CURRENT_FORMAT_NAME)
        is_version = ("version" in json_build_data) and (json_build_data["version"] == CURRENT_FORMAT_VERSION)

        file_cur_dict = {}

        if("metadata" in json_build_data):
            metadata_info = json_build_data["metadata"]
        else:
            metadata_info = {
                "author": None,
                "licence": None,
            }

        if((not is_format) or (not is_version)):
            return None

        for cursor_info in json_build_data["data"]:
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

        return (metadata_info, file_cur_dict)
