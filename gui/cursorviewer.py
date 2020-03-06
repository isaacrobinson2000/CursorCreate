from PySide2 import QtWidgets, QtGui, QtCore
from cursor import AnimatedCursor
from gui.cursorhotspotedit import HotspotEditDialog
from PIL.ImageQt import ImageQt

class CursorDisplayWidget(QtWidgets.QWidget):

    DEF_SIZE = 64

    def __init__(self, parent = None, cursor: AnimatedCursor = None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self._cur = None
        self._current_frame = None
        self._is_ani = None
        self.__painter = QtGui.QPainter()
        self.__animation_timer = QtCore.QTimer()
        self.__animation_timer.setSingleShot(True)
        self.__animation_timer.timeout.connect(self.moveStep)
        self._imgs = None
        self._delays = None
        self._pressed = False

        self.current_cursor = cursor

        self.setCursor(QtGui.Qt.PointingHandCursor)

        self.setMinimumSize(self._imgs[self._current_frame].size())
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.resize(self._imgs[self._current_frame].size())

    def paintEvent(self, event: QtGui.QPaintEvent):
        self.__painter.begin(self)
        self.__painter.drawPixmap(0, 0, self._imgs[self._current_frame])
        self.__painter.end()

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        self._pressed = True

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if(self._pressed):
            self._pressed = False
            if(self.current_cursor is not None):
                mod_hotspot = HotspotEditDialog(self.window(), self.current_cursor)
                mod_hotspot.exec()
                self.current_cursor = self.current_cursor

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(self.DEF_SIZE, self.DEF_SIZE)

    def moveStep(self):
        self._current_frame = (self._current_frame + 1) % len(self._imgs)
        self.update()
        if(self._is_ani):
            self.__animation_timer.setInterval(self._delays[self._current_frame])
            self.__animation_timer.start()


    @property
    def current_cursor(self) -> AnimatedCursor:
        return self._cur

    @current_cursor.setter
    def current_cursor(self, cursor: AnimatedCursor):
        self._cur = cursor
        self._current_frame = -1
        self._is_ani = False
        self.__animation_timer.stop()

        if(cursor is not None and (len(cursor) > 0)):
            self._cur.normalize([(self.DEF_SIZE, self.DEF_SIZE)])
            self._imgs = [QtGui.QPixmap(ImageQt(cur[(self.DEF_SIZE, self.DEF_SIZE)].image)) for cur, delay in cursor]
            self._delays = [delay for cur, delay in cursor]

            if(len(cursor) > 1):
                self._is_ani = True
        else:
            self._imgs = [QtGui.QPixmap(QtGui.QImage(bytes(4 * self.DEF_SIZE ** 2), self.DEF_SIZE, self.DEF_SIZE, 4,
                                                     QtGui.QImage.Format_ARGB32))]
            self._delays = [0]

        self.moveStep()
