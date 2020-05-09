from typing import Tuple
import numpy as np
from PIL import Image, ImageQt
from PySide2 import QtWidgets, QtGui, QtCore
from CursorCreate.lib.cursor import AnimatedCursor, Cursor, CursorIcon
from CursorCreate.gui.layouts import FlowLayout
from CursorCreate.gui.cursorpreviewdialog import CursorPreviewDialog


class CursorHotspotWidget(QtWidgets.QWidget):

    VIEW_SIZE = (64, 64)

    userHotspotChange = QtCore.Signal((int, int))

    def __init__(self, parent=None, cursor: AnimatedCursor=None, frame=0, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._frame = 0
        self._frame_img = None
        self._pressed = False

        if((cursor is None) or (len(cursor) == 0)):
            self._cursor = AnimatedCursor(
                [Cursor([CursorIcon(Image.fromarray(np.zeros(self.VIEW_SIZE + (4,), dtype=np.uint8)), 0, 0)])],
                [100]
            )
        else:
            self._cursor = cursor
            self._cursor.normalize([self.VIEW_SIZE])

        self.__painter = QtGui.QPainter()
        self.frame = frame
        self.setCursor(QtGui.Qt.CrossCursor)

        self.setMinimumSize(QtCore.QSize(*self.VIEW_SIZE))
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.resize(self.minimumSize())

    def paintEvent(self, event: QtGui.QPaintEvent):
        self.__painter.begin(self)

        self.__painter.setPen(QtGui.QColor("black"))
        self.__painter.setBrush(QtGui.QColor("red"))

        self.__painter.drawPixmap(0, 0, self._frame_img)

        hotspot = QtCore.QPoint(*self.hotspot)

        self.__painter.setPen(QtGui.QColor(0, 0, 0, 150))
        self.__painter.setBrush(QtGui.QColor(255, 0, 0, 100))
        self.__painter.drawEllipse(hotspot, 4, 4)

        self.__painter.setPen(QtGui.QColor(0, 0, 255, 255))
        self.__painter.setBrush(QtGui.QColor(0, 0, 255, 255))
        self.__painter.drawEllipse(hotspot, 1, 1)

        self.__painter.end()


    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(*self.VIEW_SIZE)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        self._pressed = True

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if(self._pressed):
            x, y = event.x(), event.y()
            self.hotspot = x, y
            self.userHotspotChange.emit(x, y)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if(self._pressed):
            self.mouseMoveEvent(event)
            self._pressed = False

    @property
    def frame(self) -> int:
        return self._frame

    @frame.setter
    def frame(self, value: int):
        if(0 <= value < len(self._cursor)):
            self._frame = value
            self._frame_img = QtGui.QPixmap(ImageQt.ImageQt(self._cursor[self._frame][0][self.VIEW_SIZE].image))
            self.update()
        else:
            raise ValueError(f"The frame must land within length of the animated cursor!")

    @property
    def hotspot(self) -> Tuple[int, int]:
        return self._cursor[self._frame][0][self.VIEW_SIZE].hotspot

    @hotspot.setter
    def hotspot(self, value: Tuple[int, int]):
        if(not (isinstance(value, Tuple) and len(value) == 2)):
            raise ValueError("Not a coordinate pair!")

        value = min(max(0, value[0]), self.VIEW_SIZE[0] - 1), min(max(0, value[1]), self.VIEW_SIZE[1] - 1)

        for size in self._cursor[self._frame][0]:
            x_rat, y_rat = size[0] / self.VIEW_SIZE[0], size[1] / self.VIEW_SIZE[1]
            x_hot, y_hot = int(value[0] * x_rat), int(value[1] * y_rat)

            self._cursor[self._frame][0][size].hotspot = x_hot, y_hot

        self.update()

    @property
    def current_cursor(self) -> AnimatedCursor:
        return self._cursor


class CursorEditWidget(QtWidgets.QFrame):

    userDelayChange = QtCore.Signal((int,))
    userHotspotChange = QtCore.Signal((int, int))

    def __init__(self, parent=None, cursor: AnimatedCursor=None, frame=0, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self._main_layout = QtWidgets.QVBoxLayout(self)
        self._hotspot_picker = CursorHotspotWidget(cursor=cursor, frame=frame)
        self._delay_adjuster = QtWidgets.QSpinBox()
        self._delay_adjuster.setRange(0, 0xFFFF)
        self._delay_adjuster.setSingleStep(1)

        self._frame = QtWidgets.QFrame()
        self._f_lay = QtWidgets.QVBoxLayout()
        self._f_lay.setMargin(0)
        self._f_lay.addWidget(self._hotspot_picker)
        self._frame.setLayout(self._f_lay)
        self._frame.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        self._frame.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self._main_layout.addWidget(self._frame)
        self._main_layout.setAlignment(self._frame, QtCore.Qt.AlignHCenter)
        self._main_layout.addWidget(self._delay_adjuster)

        self.setLayout(self._main_layout)
        self.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Raised)

        # Copy properties from the hotspot picking widget...
        self._hotspot_picker.userHotspotChange.connect(lambda x, y: self.userHotspotChange.emit(x, y))

        # Update the delay value...
        self.delay = self.delay
        self._delay_adjuster.setValue(self.delay)

        # Connect spin box to delay value
        self._delay_adjuster.valueChanged.connect(self._change_delay)

    def _change_delay(self, value: int):
        self.delay = value
        self.userDelayChange.emit(self.delay)

    @property
    def current_cursor(self) -> AnimatedCursor:
        return self._hotspot_picker.current_cursor

    @property
    def hotspot(self) -> Tuple[int, int]:
        return self._hotspot_picker.hotspot

    @hotspot.setter
    def hotspot(self, value: Tuple[int, int]):
        self._hotspot_picker.hotspot = value

    @property
    def frame(self):
        return self._hotspot_picker.frame

    @frame.setter
    def frame(self, value: int):
        self._hotspot_picker.frame = value
        self.delay = self.delay

    @property
    def delay(self) -> int:
        return self.current_cursor[self.frame][1]

    @delay.setter
    def delay(self, value: int):
        if(not (0 <= value < 0xFFFF and isinstance(value, int))):
            return

        self._delay_adjuster.setValue(value)
        self.current_cursor[self.frame] = (self.current_cursor[self.frame][0], value)


class HotspotEditDialog(QtWidgets.QDialog):

    CURS_PER_LINE = 5

    def __init__(self, parent=None, cursor: AnimatedCursor=None):
        super().__init__(parent)
        super().setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowCloseButtonHint)

        self._outer_layout = QtWidgets.QVBoxLayout(self)
        self._inner_layout = FlowLayout()
        self._in_scroll_wid = QtWidgets.QWidget()
        self._scroll_area = QtWidgets.QScrollArea()
        self._scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)


        self._info_text = "Modify cursor hotspots below: "
        self._info_label = QtWidgets.QLabel(self._info_text)

        if((cursor is None) or (len(cursor) == 0)):
            self._hotspot_picker_lst = [CursorEditWidget()]
            self._cursor = self._hotspot_picker_lst[0].current_cursor
        else:
            self._hotspot_picker_lst = [CursorEditWidget(None, cursor, i) for i in range(len(cursor))]
            self._cursor = cursor

        for i, cur_picker in enumerate(self._hotspot_picker_lst):
            self._inner_layout.addWidget(cur_picker)
        self._scroll_area.setWidgetResizable(True)
        self._in_scroll_wid.setLayout(self._inner_layout)
        self._scroll_area.setWidget(self._in_scroll_wid)

        self._share_hotspots = QtWidgets.QCheckBox("Share Hotspots Between Frames")
        self._share_hotspots.setTristate(False)

        self._share_delays = QtWidgets.QCheckBox("Share Delays Between Frames")
        self._share_delays.setTristate(False)

        self._preview = QtWidgets.QPushButton("Preview")

        self._outer_layout.addWidget(self._info_label)
        self._outer_layout.addWidget(self._scroll_area)
        self._outer_layout.addWidget(self._share_hotspots)
        self._outer_layout.addWidget(self._share_delays)
        self._outer_layout.addWidget(self._preview)

        self.setLayout(self._outer_layout)
        self.resize(self.sizeHint())

        # Event connections...
        self._share_hotspots.stateChanged.connect(self._share_hotspot_chg)
        self._share_delays.stateChanged.connect(self._share_delays_chg)
        self._preview.clicked.connect(self._on_preview)
        for cur_picker in self._hotspot_picker_lst:
            cur_picker.userHotspotChange.connect(self._on_hotspot_changed)
            cur_picker.userDelayChange.connect(self._on_delay_changed)
        # Set to delete this dialog on close...
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)


    def _share_hotspot_chg(self, state: int):
        if(state == QtCore.Qt.Checked):
            # Trigger an update...
            self._on_hotspot_changed(*self._hotspot_picker_lst[0].hotspot)

    def _share_delays_chg(self, state: int):
        if(state == QtCore.Qt.Checked):
            # Trigger update to all delays...
            self._on_delay_changed(self._hotspot_picker_lst[0].delay)

    def _on_hotspot_changed(self, x: int, y: int):
        if(self._share_hotspots.isChecked()):
            for cur_picker in self._hotspot_picker_lst:
                cur_picker.hotspot = x, y

    def _on_delay_changed(self, value: int):
        if(self._share_delays.isChecked()):
            for cur_picker in self._hotspot_picker_lst:
                cur_picker.delay = value

    def _on_preview(self):
        dialog = CursorPreviewDialog(self, self.current_cursor)
        dialog.exec_()

    def closeEvent(self, evt: QtGui.QCloseEvent):
        super().closeEvent(evt)
        self.accept()

    @property
    def current_cursor(self) -> AnimatedCursor:
        return self._cursor

