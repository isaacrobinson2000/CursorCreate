from io import BytesIO
from typing import BinaryIO, Tuple

from PIL import Image, ImageOps, ImageSequence
from CursorCreate.lib import format_core
from CursorCreate.lib.cursor import AnimatedCursor, Cursor, CursorIcon

# New SVG Support...
from CursorCreate.gui.QtKit import QtWidgets, QtWebEngineWidgets, QtWebEngineCore, QtCore
# Qt5 Fix...
if(not hasattr(QtWebEngineCore, "QWebEnginePage")):
    QtWebEngineCore.QWebEnginePage = QtWebEngineWidgets.QWebEnginePage
import base64

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

    if hasattr(image, "is_animated") and (image.is_animated):
        # If this is an animated file, load in each frame as the frames of the cursor (Ex, ".gif")
        min_dim = min(image.size)  # We fit the image to a square...
        images_durations = [
            (ImageOps.fit(image, (min_dim, min_dim)), frame.info.get("duration", 100))
            for frame in ImageSequence.Iterator(image)
        ]
    else:
        # Separate all frames (Assumed to be stored horizontally)
        height = image.size[1]
        num_frames = image.size[0] // height

        if num_frames == 0:
            raise ValueError(
                "Image width is smaller then height so this will load as a 0 frame cursor!!!"
            )

        images_durations = [
            (image.crop((i * height, 0, i * height + height, height)), 100)
            for i in range(num_frames)
        ]

    # Now convert images into the cursors, resizing them to match all the default sizes...
    final_cursor = AnimatedCursor()

    for img, delay in images_durations:
        frame = Cursor()

        for size in DEFAULT_SIZES:
            frame.add(CursorIcon(img.resize(size, Image.LANCZOS), 0, 0))

        final_cursor.append((frame, delay))

    return final_cursor


class _ChromiumSVGRenderer:
    SVG_SIZE_SCRIPT = """
    function get_svg_size() {{
        let img_text = '{svg_text}';
        let img = new Image();

        img.onload = () => console.log([img.naturalWidth, img.naturalHeight]);
        img.onerror = () => {{
            throw "Invalid svg image!";
        }};
        img.src = 'data:image/svg+xml;base64,' + img_text;
    }};

    get_svg_size();
    """.replace(
        "\n    ", "\n"
    )

    SVG_RENDER_SCRIPT = """
    function render_svg() {{
        let img_text = '{svg_text}';
        let img = new Image();

        img.onload = () => {{
            let c = document.createElement("canvas");
            c.width = {width};
            c.height = {height};
            let painter = c.getContext('2d');
            painter.drawImage(img, 0, 0, {width}, {height});
            console.log(c.toDataURL().split(',')[1]);
        }};
        img.onerror = () => {{
            throw "Invalid svg image!";
        }};
        img.src = 'data:image/svg+xml;base64,' + img_text;
    }};
    
    render_svg();
    """.replace(
        "\n    ", "\n"
    )

    class DumpPage(QtWebEngineCore.QWebEnginePage):
        JSMessageLevel = QtWebEngineCore.QWebEnginePage.JavaScriptConsoleMessageLevel

        def __init__(self, parent=None):
            super().__init__(parent)
            self.on_dump = None

        def javaScriptConsoleMessage(
            self, level: JSMessageLevel, message: str, line_number: int, source_id: str
        ) -> None:
            no_error = level == self.JSMessageLevel.InfoMessageLevel
            if self.on_dump is not None:
                self.on_dump(no_error, message)

    def __init__(self, parent=None):
        self._app = QtWidgets.QApplication.instance()
        if self._app is None:
            self._app = QtWidgets.QApplication([])

        self._web_engine = QtWebEngineWidgets.QWebEngineView(parent)
        self._page = self.DumpPage(self._web_engine)
        self._web_engine.setPage(self._page)

    @classmethod
    def _load_file_b64(cls, file: BinaryIO) -> str:
        file.seek(0)
        return base64.b64encode(file.read()).decode()

    def _run_script(self, script: str, **kwargs) -> str:
        loop = QtCore.QEventLoop()
        message = (False, "Could not load browser...")

        def on_dump(no_error, msg):
            nonlocal message
            message = (no_error, msg)
            loop.quit()

        self._page.on_dump = on_dump
        self._page.runJavaScript(script.format(**kwargs), 0)
        loop.exec_()

        if not message[0]:
            raise ValueError(f"Error while running script: {message[1]}")

        return str(message[1])

    def get_svg_size(self, file: BinaryIO) -> Tuple[int, int]:
        res = self._run_script(self.SVG_SIZE_SCRIPT, svg_text=self._load_file_b64(file))
        w, h = [int(v) for v in res.split(",")]
        return (w, h)

    def render_svg(self, file: BinaryIO, width: int, height: int) -> BinaryIO:
        res = self._run_script(
            self.SVG_RENDER_SCRIPT,
            svg_text=self._load_file_b64(file),
            width=width,
            height=height,
        )

        return BytesIO(base64.b64decode(res.encode()))

    def __del__(self):
        self._web_engine.destroy()
        del self._page
        del self._web_engine


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
    svg_renderer = _ChromiumSVGRenderer()
    w, h = svg_renderer.get_svg_size(file)

    # Compute height to width ratio an the number of frame(Assumes they are stored horizontally)...
    h_to_w_multiplier = w / h
    num_frames = int(h_to_w_multiplier)

    if num_frames == 0:
        raise ValueError(
            "Image width is smaller then height so this will load as a 0 frame cursor!!!"
        )

    # Build empty animated cursor to start stashing frames in...
    ani_cur = AnimatedCursor([Cursor() for __ in range(num_frames)], [100] * num_frames)

    for sizes in DEFAULT_SIZES:
        # For each default size, resize svg to it and add all frames to the AnimatedCursor object...
        image = svg_renderer.render_svg(
            file, int(sizes[1] * h_to_w_multiplier), sizes[1]
        )
        image = Image.open(image)

        height = image.size[1]
        for i in range(num_frames):
            ani_cur[i][0].add(
                CursorIcon(
                    image.crop((i * height, 0, i * height + height, height)), 0, 0
                )
            )

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
        if reader.check(magic):
            ani_cur = reader.read(file)
            ani_cur.normalize(DEFAULT_SIZES)
            ani_cur.remove_non_square_sizes()
            return ani_cur

    for reader in cur_readers:
        if reader.check(magic):
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
        except UnidentifiedImageError:
            file.seek(0)
            try:
                return load_cursor_from_svg(file)
            except ValueError:
                raise ValueError("Unable to open file by any specified methods...")
