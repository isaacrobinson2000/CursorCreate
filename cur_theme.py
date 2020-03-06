from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Type
from cursor import AnimatedCursor
from xcur_format import XCursorFormat
from cur_format import CurFormat
from ani_format import AniFormat


class CursorThemeBuilder(ABC):
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


    @classmethod
    @abstractmethod
    def build_theme(cls, theme_name: str, cursor_dict: Dict[str, AnimatedCursor], directory: Path):
        pass

    @classmethod
    @abstractmethod
    def get_name(cls):
        pass


class LinuxThemeBuilder(CursorThemeBuilder):

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
    PREVIEW_FILE = "thumbnail.png"
    THEME_FILE_NAME = "index.theme"

    @classmethod
    def build_theme(cls, theme_name: str, cursor_dict: Dict[str, AnimatedCursor], directory: Path):
        new_theme = directory / theme_name
        new_theme.mkdir(exist_ok=True)

        with (new_theme / cls.THEME_FILE_NAME).open("w") as theme_f:
            theme_f.write(f"[Icon Theme]\nName={theme_name}\n")

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

#
WINDOWS_INF_FILE = """\
; Windows installer for {name} cursor theme.
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

[Strings]
CUR_DIR = "Cursors\{name}"
SCHEME_NAME = "{name}"
{cursor_reg_list}
"""

class WindowsThemeBuilder(CursorThemeBuilder):

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

    REGISTRY_ORDER = [
        "pointer", "help", "work", "busy", "cross", "text", "hand", "unavailable",
        "vert", "horz", "dgn1", "dgn2", "move", "alternate", "link"
    ]

    @classmethod
    def build_theme(cls, theme_name: str, cursor_dict: Dict[str, AnimatedCursor], directory: Path):
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

        inf_file = WINDOWS_INF_FILE.format(name=theme_name, reg_list=reg_list, cursor_list=cursor_list,
                                           cursor_reg_list=cursor_reg_list)

        with (theme_dir / "install.inf").open("w") as f:
            f.write(inf_file)

    @classmethod
    def get_name(cls):
        return "windows"


def get_theme_builders() -> List[Type[CursorThemeBuilder]]:
    return CursorThemeBuilder.__subclasses__()