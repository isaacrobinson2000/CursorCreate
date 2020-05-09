from CursorCreate.gui.cursorviewer import CursorDisplayWidget
from CursorCreate.lib.cursor import AnimatedCursor
from PySide2 import QtWidgets, QtCore, QtGui
from PIL import ImageQt
from CursorCreate.lib import cursor_util


class CursorPreviewDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, cursor: AnimatedCursor=None):
        super().__init__(parent)
        super().setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowCloseButtonHint)

        self._colors = ["white", "black"]

        self._main_layout = QtWidgets.QVBoxLayout()

        self._preview_panel = PreviewArea(None, cursor)
        self._frame = QtWidgets.QFrame()
        self._frame.setFrameStyle(QtWidgets.QFrame.Box | QtWidgets.QFrame.Plain)
        self._box = QtWidgets.QVBoxLayout()
        self._box.addWidget(self._preview_panel)
        self._frame.setLayout(self._box)
        self._box.setMargin(0)

        self._viewers = []

        for color in self._colors:
            widget = QtWidgets.QWidget()
            widget.setStyleSheet(f"background-color: {color};")
            hbox = QtWidgets.QHBoxLayout()

            for size in cursor_util.DEFAULT_SIZES:
                c_view = CursorDisplayWidget(cursor=cursor, size=size[0])
                self._viewers.append(c_view)
                hbox.addWidget(c_view)

            widget.setLayout(hbox)
            self._main_layout.addWidget(widget)

        self._main_layout.addWidget(self._frame)

        self.setLayout(self._main_layout)
        self.setMinimumSize(self.sizeHint())

        # Set to delete this dialog on close...
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

    def closeEvent(self, evt: QtGui.QCloseEvent):
        super().closeEvent(evt)
        self.accept()


class PreviewArea(QtWidgets.QWidget):

    CURSOR_SIZE = (32, 32)

    def __init__(self, parent, cursor: AnimatedCursor):
        super().__init__(parent)
        self._core_painter = QtGui.QPainter()
        self._pixmaps = [QtGui.QPixmap(ImageQt.ImageQt(sub_cur[self.CURSOR_SIZE].image)) for sub_cur, delay in cursor]
        self._hotspots = [sub_cur[self.CURSOR_SIZE].hotspot for sub_cur, delay in cursor]
        self._delays = [delay for sub_cur, delay in cursor]

        self._animation_timer = QtCore.QTimer()
        self._animation_timer.setSingleShot(True)
        self._animation_timer.timeout.connect(self.moveStep)
        self._current_frame = -1

        self._main_layout = QtWidgets.QVBoxLayout()
        self._example_label = QtWidgets.QLabel("Hover over me to see the cursor! Click to see the hotspot.")
        self._main_layout.addWidget(self._example_label)
        self.setLayout(self._main_layout)

        self._hotspot_preview_loc = None
        self._pressed = False

        self.moveStep()

    def moveStep(self):
        self._current_frame = (self._current_frame + 1) % len(self._delays)
        if(len(self._pixmaps) > 0):
            self.setCursor(QtGui.QCursor(self._pixmaps[self._current_frame], *self._hotspots[self._current_frame]))
        if(len(self._pixmaps) > 1):
            self._animation_timer.setInterval(self._delays[self._current_frame])
            self._animation_timer.start()

    def paintEvent(self, event: QtGui.QPaintEvent):
        self._core_painter.begin(self)

        if(self._hotspot_preview_loc is not None):
            self._core_painter.setPen(QtGui.QColor(0, 0, 0, 0))
            colors = [(0, 0, 255, 100), (0, 255, 0, 200), (255, 0, 0, 255)]
            widths = [20, 8, 3]
            for color, width in zip(colors, widths):
                self._core_painter.setBrush(QtGui.QBrush(QtGui.QColor(*color)))
                self._core_painter.drawEllipse(QtCore.QPoint(*self._hotspot_preview_loc), width, width)

        self._core_painter.end()


    def mousePressEvent(self, event: QtGui.QMouseEvent):
        self._pressed = True
        self._hotspot_preview_loc = (event.x(), event.y())
        self.update()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if(self._pressed):
            self._hotspot_preview_loc = (event.x(), event.y())
            self.update()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if(self._pressed):
            self.mouseMoveEvent(event)
            self._pressed = False

    def __del__(self):
        del self._animation_timer
