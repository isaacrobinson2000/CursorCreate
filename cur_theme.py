import copy
import plistlib
from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Type, Any, Tuple

import numpy as np
from PIL import Image

from cursor import AnimatedCursor
from xcur_format import XCursorFormat
from cur_format import CurFormat
from ani_format import AniFormat


class CursorThemeBuilder(ABC):
    """
    Abstract class for representing theme builders for different platforms. Also includes a list of cursors which
    a cursor theme can provide, in a class variable call DEFAULT_CURSORS.
    """
    # List of cursors need to be supported for full theme support on all platforms...(Most for linux)
    DEFAULT_CURSORS = {
        'alias',
        'all-scroll',
        'bottom_left_corner',
        'bottom_right_corner',
        'bottom_side',
        'cell',
        'center_ptr',
        'col-resize',
        'color-picker',
        'context-menu',
        'copy',
        'crosshair',
        'default',
        'dnd-move',
        'dnd-no-drop',
        'down-arrow',
        'draft',
        'fleur',
        'help',
        'left-arrow',
        'left_side',
        'no-drop',
        'not-allowed',
        'openhand',
        'pencil',
        'pirate',
        'pointer',
        'progress',
        'right-arrow',
        'right_ptr',
        'right_side',
        'row-resize',
        'size_bdiag',
        'size_fdiag',
        'size_hor',
        'size_ver',
        'text',
        'top_left_corner',
        'top_right_corner',
        'top_side',
        'up-arrow',
        'vertical-text',
        'wait',
        'wayland-cursor',
        'x-cursor',
        'zoom-in',
        'zoom-out'
    }

    __ERROR_MSG = "Subclass doesn't implement this method!!!"

    @classmethod
    @abstractmethod
    def build_theme(cls, theme_name: str, metadata: Dict[str, Any], cursor_dict: Dict[str, AnimatedCursor], directory: Path):
        """
        Build the passed cursor theme for this platform...

        :param theme_name: The name of the Theme to build...
        :param metadata: A dictionary of string to any(mostly string) stores "author", "licence", and "licence_name".
        :param cursor_dict: A dictionary of cursor name to AnimatedCursor, specifying cursors and the types they
                            are suppose to be. Look at the 'DEFAULT_CURSORS' class variable in the CursorThemeBuilder
                            class to see all valid types which a theme builder will accept...
        :param directory: The directory to build the theme for this platform in.
        """
        raise NotImplementedError(cls.__ERROR_MSG)

    @classmethod
    @abstractmethod
    def get_name(cls):
        """
        Get the name of this theme builder. Usually specifies the platform this theme builder applies to.

        :return: A string, the name of this theme builder's platform.
        """
        raise NotImplementedError(cls.__ERROR_MSG)


class LinuxThemeBuilder(CursorThemeBuilder):
    """
    The theme builder for the linux platform. Technically works for any platform which uses X-Org or Wayland
    (FreeBSD, etc.), but is called Linux as this is the most common platform known for using X-Org Cursor Theme
    Format for loading cursors. Generates a valid X-Org Cursor Theme which when placed in the ~/.icons or
    /usr/share/icons folder on linux becomes visible in the system settings and can be selected.
    """

    # All symlinks required by x-org cursor themes to be fully compatible with all software...
    SYM_LINKS_TO_CUR = {
         'e29285e634086352946a0e7090d73106': 'pointer',
         '9d800788f1b08800ae810202380a0822': 'pointer',
         'xterm': 'text',
         'crossed_circle': 'not-allowed',
         '1081e37283d90000800003c07f3ef6bf': 'copy',
         'closedhand': 'dnd-move',
         'hand2': 'pointer',
         'hand1': 'pointer',
         'sb_h_double_arrow': 'size_hor',
         'a2a266d0498c3104214a47bd64ab0fc8': 'alias',
         'split_h': 'col-resize',
         'dnd-none': 'dnd-move',
         'split_v': 'row-resize',
         '3085a0e285430894940527032f8b26df': 'alias',
         '5c6cd98b3f3ebcb1f9c7f1c204630408': 'help',
         'fcf21c00b30f7e3f83fe0dfd12e71cff': 'dnd-move',
         'left_ptr': 'default',
         'circle': 'not-allowed',
         'd9ce0ab605698f320427677b458ad60b': 'help',
         '03b6e0fcb3499374a867c041f52298f0': 'not-allowed',
         'size-hor': 'default',
         '00008160000006810000408080010102': 'size_ver',
         'size-ver': 'default',
         'forbidden': 'no-drop',
         '08e8e1c95fe2fc01f976f1e063a24ccd': 'progress',
         'ibeam': 'text',
         '4498f0e0c1937ffe01fd06f973665830': 'dnd-move',
         'left_ptr_watch': 'progress',
         'cross': 'crosshair',
         'watch': 'wait',
         '3ecb610c1bf2410f44200f48c40d3599': 'progress',
         'link': 'alias',
         '9081237383d90e509aa00f00170e968f': 'dnd-move',
         'h_double_arrow': 'size_hor',
         '640fb0e74195791501fd1ed57b41487f': 'alias',
         'plus': 'cell',
         'b66166c04f8c3109214a4fbd64a50fc8': 'copy',
         'pointing_hand': 'pointer',
         'size-bdiag': 'default',
         'w-resize': 'size_hor',
         'n-resize': 'size_ver',
         's-resize': 'size_ver',
         'question_arrow': 'help',
         'sb_v_double_arrow': 'size_ver',
         'dnd-copy': 'copy',
         'half-busy': 'progress',
         'e-resize': 'size_hor',
         '00000000000000020006000e7e9ffc3f': 'progress',
         'top_left_arrow': 'default',
         'whats_this': 'help',
         'size-fdiag': 'default',
         'move': 'dnd-move',
         'v_double_arrow': 'size_ver',
         'left_ptr_help': 'help',
         'size_all': 'fleur',
         '6407b0e94181790501fd1e167b474872': 'copy'
    }
    # The file name which gives the preview in system settings...
    PREVIEW_FILE = "thumbnail.png"
    # The x-org index theme file name...
    THEME_FILE_NAME = "index.theme"
    # Name of file storing licence...
    LICENCE_FILE_NAME = "LICENSE.txt"

    @classmethod
    def build_theme(cls, theme_name: str, metadata: Dict[str, Any], cursor_dict: Dict[str, AnimatedCursor], directory: Path):
        new_theme = directory / theme_name
        new_theme.mkdir(exist_ok=True)

        with (new_theme / cls.THEME_FILE_NAME).open("w") as theme_f:
            author = metadata.get("author", None)
            if(author is not None):
                theme_f.write(f"# {theme_name} cursor theme created by {author}.\n")
            theme_f.write(f"[Icon Theme]\nName={theme_name}\n")

        licence_text = metadata["licence"]
        if(licence_text is not None):
            with (new_theme / cls.LICENCE_FILE_NAME).open("w") as f:
                f.write(licence_text)

        cursor_path = (new_theme / "cursors")
        cursor_path.mkdir(exist_ok=True)

        for name, cursor in cursor_dict.items():
            with (cursor_path / name).open("wb") as cur_out:
                XCursorFormat.write(cursor, cur_out)

        if("default" in cursor_dict):
            dcur = cursor_dict["default"]
            dcur[0][0][dcur[0][0].max_size()].image.save(str(cursor_path / cls.PREVIEW_FILE))

        for link, link_to in cls.SYM_LINKS_TO_CUR.items():
            if(link_to in cursor_dict):
                if((cursor_path / link).exists()):
                    (cursor_path / link).unlink()
                (cursor_path / link).symlink_to((cursor_path / link_to), False)

    @classmethod
    def get_name(cls):
        return "linux"


# Window inf file template...
WINDOWS_INF_FILE = """\
; Windows installer for {name} cursor theme{author}.
; Right click on this file ("install.inf"), and click "Install" to install the cursor theme.
; After installing, change the cursors via windows mouse pointer settings dialog.

[Version]
signature="$CHICAGO$"

[DefaultInstall]
CopyFiles = Scheme.Cur, Scheme.Txt
AddReg = Scheme.Reg

[DestinationDirs]
Scheme.Cur = 10,"%CUR_DIR%"
Scheme.Txt = 10,"%CUR_DIR%"

[Scheme.Reg]
HKCU,"Control Panel\Cursors\Schemes","%SCHEME_NAME%",,"{reg_list}"

[Scheme.Cur]
"install.inf"
{cursor_list}

{licence_txt}

[Strings]
CUR_DIR = "Cursors\{name}"
SCHEME_NAME = "{name}"
{cursor_reg_list}
"""

class WindowsThemeBuilder(CursorThemeBuilder):
    """
    The theme builder for the windows platform. Takes a subset of the cursors which actually apply to the windows
    platform, converts them to windows formats, and then packages them in a folder with a install.inf file which
    will automatically move the cursors into the right system paths and add them to Registry as a cursor theme
    the user can set in the control panel.
    """
    # Converts cursor names specified in DEFAULT_CURSORS to the cursors for windows...
    LINUX_TO_WIN_CURSOR = {
        "default": ("pointer", "normal-select"),
        "help": ("help", "help-select"),
        "progress": ("work", "working-in-background"),
        "wait": ("busy", "busy"),
        "text": ("text", "text-select"),
        "no-drop": ("unavailable", "unavailable"),
        "size_ver": ("vert", "vertical-resize"),
        "size_hor": ("horz", "horizontal-resize"),
        "size_fdiag": ("dgn1", "diagonal-resize-1"),
        "size_bdiag": ("dgn2", "diagonal-resize-2"),
        "fleur": ("move", "move"),
        "pointer": ("link", "link-select"),
        "crosshair": ("cross", "precision-select"),
        "pencil": ("hand", "handwriting"),
        "up-arrow": ("alternate", "alt-select")
    }

    # Order of cursor pseudo-names in the registry...
    REGISTRY_ORDER = [
        "pointer", "help", "work", "busy", "cross", "text", "hand", "unavailable",
        "vert", "horz", "dgn1", "dgn2", "move", "alternate", "link"
    ]

    # Name of file storing licence...
    LICENCE_FILE_NAME = "LICENSE.txt"

    @classmethod
    def build_theme(cls, theme_name: str, metadata: Dict[str, Any], cursor_dict: Dict[str, AnimatedCursor], directory: Path):
        theme_dir = directory / theme_name
        theme_dir.mkdir(exist_ok=True)

        win_cursors = {name: cursor for name, cursor in cursor_dict.items() if(name in cls.LINUX_TO_WIN_CURSOR)}
        reg_used = {cls.LINUX_TO_WIN_CURSOR[name][0] for name in win_cursors}

        reg_list = []
        for name in cls.REGISTRY_ORDER:
            reg_list.append(f"%10%\%CUR_DIR%\%{name}%" if(name in reg_used) else "")
        reg_list = ",".join(reg_list)

        cursor_names = {}
        for name, cursor in win_cursors.items():
            reg_name, file_name = cls.LINUX_TO_WIN_CURSOR[name]

            if(len(cursor) == 0):
                continue
            elif(len(cursor) == 1):
                file_name += ".cur"
                with (theme_dir / file_name).open("wb") as f:
                    CurFormat.write(cursor[0][0], f)
            else:
                file_name += ".ani"
                with (theme_dir / file_name).open("wb") as f:
                    AniFormat.write(cursor, f)

            cursor_names[reg_name] = file_name

        cursor_list = "\n".join([f'"{file_name}"' for file_name in cursor_names.values()])
        cursor_reg_list = "\n".join([f'{name} = "{file_name}"' for name, file_name in cursor_names.items()])

        licence_text = metadata.get("licence")
        if(licence_text is not None):
            with (theme_dir / cls.LICENCE_FILE_NAME).open("w") as f:
                f.write(licence_text)
            licence_info = f"[Scheme.Txt]\n{cls.LICENCE_FILE_NAME}"
        else:
            licence_info = ""

        author = metadata.get("author", None)
        author = "" if(author is None) else f" by {author}"

        inf_file = WINDOWS_INF_FILE.format(name=theme_name, author=author, reg_list=reg_list, cursor_list=cursor_list,
                                           licence_txt=licence_info, cursor_reg_list=cursor_reg_list)

        with (theme_dir / "install.inf").open("w") as f:
            f.write(inf_file)

    @classmethod
    def get_name(cls):
        return "windows"


class MacOSMousecapeThemeBuilder(CursorThemeBuilder):
    """

    """

    # Converts cursor names to correct mac cursors
    LINUX_TO_MAC_CUR = {
        "default": ("com.apple.coregraphics.Arrow", "com.apple.coregraphics.ArrowCtx", "com.apple.coregraphics.Move"),
        "alias": ("com.apple.coregraphics.Alias", "com.apple.cursor.2"),
        "wait": ("com.apple.coregraphics.Wait",),
        "text": ("com.apple.coregraphics.IBeam", "com.apple.coregraphics.IBeamXOR"),
        "no-drop": ("com.apple.cursor.3",),
        "progress": ("com.apple.cursor.4",),
        "copy": ("com.apple.cursor.5",),
        "crosshair": ("com.apple.cursor.7", "com.apple.cursor.8"),
        "dnd-move": ("com.apple.cursor.11",),
        "openhand": ("com.apple.cursor.12",),
        "pointer": ("com.apple.cursor.13",),
        "left_side": ("com.apple.cursor.17",),
        "right_side": ("com.apple.cursor.18",),
        "col-resize": ("com.apple.cursor.19",),
        "top_side": ("com.apple.cursor.21",),
        "bottom_side": ("com.apple.cursor.22",),
        "row-resize": ("com.apple.cursor.23",),
        "context-menu": ("com.apple.cursor.24",),
        "pirate": ("com.apple.cursor.25",),
        "vertical-text": ("com.apple.cursor.26",),
        "right-arrow": ("com.apple.cursor.27",),
        "size_hor": ("com.apple.cursor.28",),
        "size_bdiag": ("com.apple.cursor.30",),
        "up-arrow": ("com.apple.cursor.31",),
        "size_ver": ("com.apple.cursor.32",),
        "size_fdiag": ("com.apple.cursor.34",),
        "down-arrow": ("com.apple.cursor.36",),
        "left-arrow": ("com.apple.cursor.38",),
        "all-scroll": ("com.apple.cursor.39",),
        "help": ("com.apple.cursor.40",),
        "cell": ("com.apple.cursor.41", "com.apple.cursor.20"),
        "zoom-in": ("com.apple.cursor.42",),
        "zoom-out": ("com.apple.cursor.43",)
    }

    CURSOR_EXPORT_SIZES = [(32, 32), (64, 64), (160, 160)]
    HOTSPOT_ADJUSTMENT_FACTOR = (0.5, 0.5)

    Vec2D = Tuple[int, int]

    @classmethod
    def __unify_frames(cls, cur: AnimatedCursor) -> Tuple[int, float, Vec2D, Vec2D, List[Image.Image]]:
        cur = copy.deepcopy(cur)
        delays = np.array([delay for sub_cur, delay in cur])
        cumulative_delay = np.cumsum(delays)
        half_avg = int(np.mean(delays) / 4)
        gcd_of_em = np.gcd.reduce(delays)

        unified_delay = max(gcd_of_em, half_avg)
        num_frames = cumulative_delay[-1] // unified_delay

        cur.normalize(cls.CURSOR_EXPORT_SIZES)
        new_images = [Image.new("RGBA", ((size[0] * 2) - 1, ((size[1] * 2) - 1) * num_frames), (0,0,0,0)) for size in
                      cls.CURSOR_EXPORT_SIZES]

        next_ani_frame = 1
        for current_out_frame in range(num_frames):
            time_in = current_out_frame * unified_delay
            while((next_ani_frame < len(cumulative_delay)) and (time_in >= cumulative_delay[next_ani_frame])):
                next_ani_frame += 1

            for i, img in enumerate(new_images):
                current_size = cls.CURSOR_EXPORT_SIZES[i]
                current_cur = cur[next_ani_frame - 1][0][current_size]
                x_off = current_size[0] - (current_cur.hotspot[0] + 1)
                y_off = ((current_size[0] * 2 - 1) * current_out_frame) + (current_size[0] - (current_cur.hotspot[1] + 1))
                img.paste(current_cur.image, (x_off, y_off))

        final_hotspot = (cls.CURSOR_EXPORT_SIZES[0][0] - 1, cls.CURSOR_EXPORT_SIZES[0][1] - 1)
        final_dims = (cls.CURSOR_EXPORT_SIZES[0][0] * 2 - 1, cls.CURSOR_EXPORT_SIZES[0][1] * 2 - 1)

        return (int(num_frames), float(unified_delay) / 1000, final_hotspot, final_dims, new_images)


    @classmethod
    def build_theme(cls, theme_name: str, metadata: Dict[str, Any], cursor_dict: Dict[str, AnimatedCursor], directory: Path):
        author = metadata.get("author", None)

        auth_str = "unknown" if(author is None) else "".join(author.lower().split())
        theme_str = "".join(theme_name.lower().split())

        plist_data = {
            "Author": author if(author is not None) else "",
            "CapeName": theme_name,
            "CapeVersion": 1.0,
            "Cloud": True,
            "Cursors": {},
            "HiDPI": True,
            "Identifier": ".".join(["com", auth_str, theme_str]),
            "MinimumVersion": 2.0,
            "Version": 2.0
        }

        for name, cur in cursor_dict.items():
            if(name in cls.LINUX_TO_MAC_CUR):
                mac_names = cls.LINUX_TO_MAC_CUR[name]
                num_frames, delay_secs, hotspot, size, images = cls.__unify_frames(cur)
                representations = []

                for img in images:
                    b = BytesIO()
                    img.save(b, "png")
                    representations.append(b.getvalue())

                for mac_name in mac_names:
                    plist_data["Cursors"][mac_name] = {
                        "FrameCount": num_frames,
                        "FrameDuration": delay_secs,
                        "HotSpotX": float(hotspot[0]),
                        "HotSpotY": float(hotspot[1]),
                        "PointsWide": float(size[0]),
                        "PointsHigh": float(size[1]),
                        "Representations": representations
                    }

        licence = metadata.get("licence", None)

        if(licence is not None):
            with (directory / "LICENSE.txt").open("w") as l:
                l.write(licence)

        with (directory / (theme_name + ".cape")).open("wb") as cape:
            plistlib.dump(plist_data, cape, fmt=plistlib.FMT_XML, sort_keys=True)


    @classmethod
    def get_name(cls):
        return "mousecape_macos"


def get_theme_builders() -> List[Type[CursorThemeBuilder]]:
    """
    Returns all subclasses of CursorThemeBuilder or all cursor builders loaded into python currently.

    :return: A list of theme builders currently visible to the python interpreter...
    """
    # We have to do this as it doesn't think types match...
    # noinspection PyTypeChecker
    return CursorThemeBuilder.__subclasses__()