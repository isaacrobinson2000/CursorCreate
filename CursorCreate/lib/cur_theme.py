import plistlib
from abc import ABC, abstractmethod
from io import BytesIO, StringIO
from pathlib import Path
from typing import Dict, List, Type, Any, Tuple, Union

import numpy as np
from PIL import Image, ImageDraw
# For building archives dynamically in-place...
import tarfile
import zipfile

from CursorCreate.lib.cursor import AnimatedCursor
from CursorCreate.lib.xcur_format import XCursorFormat
from CursorCreate.lib.cur_format import CurFormat
from CursorCreate.lib.ani_format import AniFormat


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


class ArchivePath:
    """
    For creating archive paths in .zip and .tar file. Provides basic path string manipulations...
    """
    def __init__(self, *path_seg):
        self._paths_segments = path_seg

    def __truediv__(self, other):
        return self._new_path(*self._paths_segments, other)

    def parent(self):
        return self._new_path(*self._paths_segments[:-1])

    def __str__(self):
        return "/".join(self._paths_segments)

    @classmethod
    def _new_path(cls, *path_seg):
        return cls(*path_seg)


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
    # Legal export sizes...
    LEGAL_EXPORT_SIZES = {(32, 32), (48, 48), (64, 64), (128, 128)}

    @classmethod
    def _tarinfo(cls, name: ArchivePath, tar_type: bytes, data: Union[StringIO, BytesIO] = None, **other_args) -> tarfile.TarInfo:
        new_tarinfo = tarfile.TarInfo(str(name))

        if(tar_type == tarfile.DIRTYPE):
            new_tarinfo.mode = 0o777
        else:
            new_tarinfo.mode = 0o666

        new_tarinfo.type = tar_type
        if(data is not None):
            new_tarinfo.size = len(data.getvalue())

        for key, value in other_args.items():
            setattr(new_tarinfo, key, value)

        return new_tarinfo


    @classmethod
    def build_theme(cls, theme_name: str, metadata: Dict[str, Any], cursor_dict: Dict[str, AnimatedCursor], directory: Path):
        with tarfile.open(str(directory / (theme_name + ".tar.gz")), "w|gz") as tar:
            # Write the theme directory...
            theme_dir = ArchivePath(theme_name)
            tar.addfile(cls._tarinfo(theme_dir, tarfile.DIRTYPE))

            # Write the theme config file...
            theme_f = BytesIO()
            author = metadata.get("author", None)
            if(author is not None):
                theme_f.write(f"# {theme_name} cursor theme created by {author}.\n".encode())
            theme_f.write(f"[Icon Theme]\nName={theme_name}\n".encode())
            theme_f.seek(0)

            tar.addfile(cls._tarinfo(theme_dir / cls.THEME_FILE_NAME, tarfile.REGTYPE, theme_f), theme_f)

            # If the license actually exists, write it to a file...
            licence_text = metadata.get("licence", None)
            if(licence_text is not None):
                license_file = BytesIO(licence_text.encode())
                tar.addfile(cls._tarinfo(theme_dir / cls.LICENCE_FILE_NAME, tarfile.REGTYPE, license_file), license_file)

            cursor_dir = (theme_dir / "cursors")
            tar.addfile(cls._tarinfo(cursor_dir, tarfile.DIRTYPE))

            # Write all of the cursors...
            for name, cursor in cursor_dict.items():
                cursor = cursor.copy()
                cursor.restrict_to_sizes(cls.LEGAL_EXPORT_SIZES)

                cur_out = BytesIO()
                XCursorFormat.write(cursor, cur_out)
                cur_out.seek(0)
                tar.addfile(cls._tarinfo(cursor_dir / name, tarfile.REGTYPE, cur_out), cur_out)

            # If default is in the cursor dictionary, create a preview file for this theme...
            if("default" in cursor_dict):
                d_cur = cursor_dict["default"]
                preview_out = BytesIO()
                d_cur[0][0][d_cur[0][0].max_size()].image.save(preview_out, "png")
                preview_out.seek(0)
                tar.addfile(cls._tarinfo(cursor_dir / cls.PREVIEW_FILE, tarfile.REGTYPE, preview_out), preview_out)

            # Create all required symlinks for linux theme to work fully....
            for link, link_to in cls.SYM_LINKS_TO_CUR.items():
                if(link_to in cursor_dict):
                    tar.addfile(cls._tarinfo(cursor_dir / link, tarfile.SYMTYPE, linkname=link_to))

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

    # Legal export sizes...
    LEGAL_EXPORT_SIZES = {(32, 32), (48, 48), (64, 64)}

    # Name of file storing licence...
    LICENCE_FILE_NAME = "LICENSE.txt"

    @classmethod
    def build_theme(cls, theme_name: str, metadata: Dict[str, Any], cursor_dict: Dict[str, AnimatedCursor], directory: Path):
        with zipfile.ZipFile(str(directory / (theme_name + ".zip")), 'w') as zip_f:
            theme_dir = ArchivePath(theme_name)

            win_cursors = {name: cursor for name, cursor in cursor_dict.items() if(name in cls.LINUX_TO_WIN_CURSOR)}
            reg_used = {cls.LINUX_TO_WIN_CURSOR[name][0] for name in win_cursors}

            reg_list = []
            for name in cls.REGISTRY_ORDER:
                reg_list.append(f"%10%\%CUR_DIR%\%{name}%" if(name in reg_used) else "")
            reg_list = ",".join(reg_list)

            cursor_names = {}
            for name, cursor in win_cursors.items():
                cursor = cursor.copy()
                cursor.restrict_to_sizes(cls.LEGAL_EXPORT_SIZES)
                reg_name, file_name = cls.LINUX_TO_WIN_CURSOR[name]

                if(len(cursor) == 0):
                    continue
                elif(len(cursor) == 1):
                    file_name += ".cur"
                    out_f = BytesIO()
                    CurFormat.write(cursor[0][0], out_f)
                    zip_f.writestr(str(theme_dir / file_name), out_f.getvalue())
                else:
                    file_name += ".ani"
                    out_f = BytesIO()
                    AniFormat.write(cursor, out_f)
                    zip_f.writestr(str(theme_dir / file_name), out_f.getvalue())

                cursor_names[reg_name] = file_name

            cursor_list = "\n".join([f'"{file_name}"' for file_name in cursor_names.values()])
            cursor_reg_list = "\n".join([f'{name} = "{file_name}"' for name, file_name in cursor_names.items()])

            licence_text = metadata.get("licence")
            if(licence_text is not None):
                zip_f.writestr(str(theme_dir / cls.LICENCE_FILE_NAME), licence_text)
                licence_info = f"[Scheme.Txt]\n{cls.LICENCE_FILE_NAME}"
            else:
                licence_info = ""

            author = metadata.get("author", None)
            author = "" if(author is None) else f" by {author}"

            inf_file = WINDOWS_INF_FILE.format(name=theme_name, author=author, reg_list=reg_list, cursor_list=cursor_list,
                                               licence_txt=licence_info, cursor_reg_list=cursor_reg_list)

            zip_f.writestr(str(theme_dir / "install.inf"), inf_file)

            # Set windows as the os it was created on such that permissions are not copied...
            for z_info in zip_f.filelist:
                z_info:  zipfile.ZipInfo = z_info
                z_info.create_system = 0

    @classmethod
    def get_name(cls):
        return "windows"


class MacOSMousecapeThemeBuilder(CursorThemeBuilder):
    """
    Cursor theme builder for the MacOS platform. MacOS doesn't natively support themes, so we actually build a .cape
    file for the Mousecape software on Mac, which allows the user to change cursors. A cape file is a mac plist
    format(xml) containing each cursor as a dictionary. Animated images are stored vertically, in tiles.
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
        "fleur": ("com.apple.cursor.39",),
        "help": ("com.apple.cursor.40",),
        "cell": ("com.apple.cursor.41", "com.apple.cursor.20"),
        "zoom-in": ("com.apple.cursor.42",),
        "zoom-out": ("com.apple.cursor.43",)
    }

    CURSOR_EXPORT_SIZES = [(32, 32), (64, 64), (160, 160)]

    Vec2D = Tuple[int, int]

    @classmethod
    def __unify_frames(cls, cur: AnimatedCursor) -> Tuple[int, float, Vec2D, Vec2D, List[Image.Image]]:
        """
        Private method, takes a cursor and converts it into a vertically tiled image with a single delay and single
        hotspot. Uses some hacky shenanigans to do this. :)......

        :param cur: An AnimatedCursor
        :return: A tuple with:
                    - Integer: Number of frames
                    - Float: Delay in seconds for each frame.
                    - Vec2D: Hotspot location.
                    - Vec2D: Size of image
                    - List[PIL.Image]: Image representations, at 1x, 2x, and 5x...
        """
        cur = cur.copy()

        delays = np.array([delay for sub_cur, delay in cur])
        cumulative_delay = np.cumsum(delays)
        half_avg = int(np.mean(delays) / 4)
        gcd_of_em = np.gcd.reduce(delays)

        unified_delay = max(gcd_of_em, half_avg)
        num_frames = cumulative_delay[-1] // unified_delay

        cur.restrict_to_sizes(cls.CURSOR_EXPORT_SIZES)
        new_images = [Image.new("RGBA", (size[0] * 2, (size[1] * 2) * num_frames), (0,0,0,0)) for size in
                      cls.CURSOR_EXPORT_SIZES]

        next_ani_frame = 1
        for current_out_frame in range(num_frames):
            time_in = current_out_frame * unified_delay
            while((next_ani_frame < len(cumulative_delay)) and (time_in >= cumulative_delay[next_ani_frame])):
                next_ani_frame += 1

            for i, img in enumerate(new_images):
                current_size = cls.CURSOR_EXPORT_SIZES[i]
                current_cur = cur[next_ani_frame - 1][0][current_size]
                x_off = current_size[0] - current_cur.hotspot[0]
                y_off = ((current_size[1] * 2) * current_out_frame) + (current_size[1] - current_cur.hotspot[1])
                img.paste(current_cur.image, (x_off, y_off))

        final_hotspot = (cls.CURSOR_EXPORT_SIZES[0][0], cls.CURSOR_EXPORT_SIZES[0][1])
        final_dims = (cls.CURSOR_EXPORT_SIZES[0][0] * 2, cls.CURSOR_EXPORT_SIZES[0][1] * 2)

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


class PreviewPictureBuilder(CursorThemeBuilder):
    """
    Not really a theme builder, but constructs a transparent png image with all of the cursors arranged in a grid.
    This image is meant to be pasted on top of a background to provide a preview of your cursor theme if you plan
    on posting it on the internet or giving it to others...
    """

    SIZE_PER_CURSOR = 64

    CURSOR_ORDER = [
        'default',
        'alias',
        'copy',
        'context-menu',
        'help',
        'no-drop',
        'center_ptr',
        'right_ptr',
        'text',
        'vertical-text',
        'progress',
        'wait',
        'pointer',
        'openhand',
        'dnd-move',
        'dnd-no-drop',
        'not-allowed',
        'pirate',
        'draft',
        'pencil',
        'color-picker',
        'zoom-in',
        'zoom-out',
        'crosshair',
        'cell',
        'fleur',
        'all-scroll',
        'up-arrow',
        'right-arrow',
        'down-arrow',
        'left-arrow',
        'top_side',
        'right_side',
        'bottom_side',
        'left_side',
        'top_left_corner',
        'top_right_corner',
        'bottom_right_corner',
        'bottom_left_corner',
        'col-resize',
        'row-resize',
        'size_ver',
        'size_bdiag',
        'size_hor',
        'size_fdiag',
        'wayland-cursor',
        'x-cursor',
    ]

    @classmethod
    def build_theme(cls, theme_name: str, metadata: Dict[str, Any], cursor_dict: Dict[str, AnimatedCursor], directory: Path):
        cur_center = cls.SIZE_PER_CURSOR
        w_in_curs = int(np.ceil(np.sqrt(len(cursor_dict))))
        cur_w = cls.SIZE_PER_CURSOR * 2

        new_image = Image.new("RGBA", (w_in_curs * cur_w, w_in_curs * cur_w), (0, 0, 0, 0))
        drawer = ImageDraw.Draw(new_image)

        cursor_order_dict = {name: i for i, name in enumerate(cls.CURSOR_ORDER)}

        for i, name in enumerate(sorted(cursor_dict, key=cursor_order_dict.get)):
            lookup_s = (cls.SIZE_PER_CURSOR,) * 2
            cur = cursor_dict[name].copy()
            cur.restrict_to_sizes([lookup_s])

            x_center = (((i % w_in_curs) * cur_w) + cur_center)
            y_center = (((i // w_in_curs) * cur_w) + cur_center)
            x_img_off = x_center - cur[0][0][lookup_s].hotspot[0]
            y_img_off = y_center - cur[0][0][lookup_s].hotspot[1]

            for x_mult, y_mult in zip([0, 0, 1, -1], [1, -1, 0, 0]):
                    x_cross_end = x_center + int(x_mult * cur_center * 0.25)
                    y_cross_end = y_center + int(y_mult * cur_center * 0.25)
                    drawer.line((x_center, y_center, x_cross_end, y_cross_end), fill=(50, 50, 50, 150), width=3)
                    drawer.line((x_center, y_center, x_cross_end, y_cross_end), fill=(205, 205, 205, 150), width=1)

            cur_img = cur[0][0][lookup_s].image
            new_image.paste(cur_img, (x_img_off, y_img_off), cur_img)

        new_image.save(str(directory / f"{theme_name}_preview.png"), "png")

    @classmethod
    def get_name(cls):
        return "preview_picture"


def get_theme_builders() -> List[Type[CursorThemeBuilder]]:
    """
    Returns all subclasses of CursorThemeBuilder or all cursor builders loaded into python currently.

    :return: A list of theme builders currently visible to the python interpreter...
    """
    # We have to do this as it doesn't think types match...
    # noinspection PyTypeChecker
    return CursorThemeBuilder.__subclasses__()