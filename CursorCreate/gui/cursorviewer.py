from PySide2 import QtWidgets, QtGui, QtCore
from CursorCreate.lib.cursor import AnimatedCursor
from PIL.ImageQt import ImageQt

class CursorDisplayWidget(QtWidgets.QWidget):

    DEF_SIZE = 64

    def __init__(self, parent = None, cursor: AnimatedCursor = None, size=None, *args, **kwargs):
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
        self._size = self.DEF_SIZE if(size is None) else int(size)

        self.current_cursor = cursor

        self.setMinimumSize(self._imgs[self._current_frame].size())
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.resize(self._imgs[self._current_frame].size())

    def paintEvent(self, event: QtGui.QPaintEvent):
        self.__painter.begin(self)
        self.__painter.drawPixmap(0, 0, self._imgs[self._current_frame])
        self.__painter.end()

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
            self._cur.normalize([(self._size, self._size)])
            self._imgs = [QtGui.QPixmap(ImageQt(cur[(self._size, self._size)].image)) for cur, delay in cursor]
            self._delays = [delay for cur, delay in cursor]

            if(len(cursor) > 1):
                self._is_ani = True
        else:
            self._imgs = [QtGui.QPixmap(QtGui.QImage(bytes(4 * self._size ** 2), self._size, self._size, 4,
                                                     QtGui.QImage.Format_ARGB32))]
            self._delays = [0]

        self.moveStep()

    def stop_and_destroy(self):
        """ Forcefully destroys the cursor viewers animation timer by stopping it and deleting it. """
        if((self.__animation_timer is not None) and (self.__animation_timer.isActive())):
            self.__animation_timer.stop()

        del self.__animation_timer
        self.__animation_timer = None

    def __del__(self):
        self.stop_and_destroy()