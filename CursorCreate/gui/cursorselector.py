from PySide2 import QtWidgets, QtGui, QtCore
from CursorCreate.lib.cursor_util import load_cursor
from CursorCreate.gui.cursorviewedit import CursorViewEditWidget
from urllib.request import urlopen
from urllib.error import URLError
from io import BytesIO
import pathlib


class CursorSelectWidget(QtWidgets.QFrame):

    FILE_DIALOG_TYPES = "Image, Cursor, or SVG (*)"

    def __init__(self, parent=None, label_text="Label", def_cursor=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Raised)

        self._main_layout = QtWidgets.QVBoxLayout()
        self._label = QtWidgets.QLabel(label_text)
        self._label.setAlignment(QtCore.Qt.AlignCenter)
        self._viewer = CursorViewEditWidget(cursor=def_cursor)
        self._file_sel_btn = QtWidgets.QPushButton("Select File")
        self._current_file = None

        # Make a frame to wrap around the hotspot picker and add a border...
        self._frame = QtWidgets.QFrame()
        self._f_lay = QtWidgets.QVBoxLayout()
        self._f_lay.setMargin(0)
        self._f_lay.addWidget(self._viewer)
        self._frame.setLayout(self._f_lay)
        self._frame.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        self._frame.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self._main_layout.addWidget(self._label)
        self._main_layout.addWidget(self._frame)
        self._main_layout.addWidget(self._file_sel_btn)

        self._main_layout.setAlignment(self._frame, QtCore.Qt.AlignHCenter)

        self.setLayout(self._main_layout)
        self.setAcceptDrops(True)

        # Events...
        self._file_sel_btn.clicked.connect(self.openFile)


    def openFile(self):
        path, __ = QtWidgets.QFileDialog.getOpenFileName(self, "Select a Cursor", filter=self.FILE_DIALOG_TYPES)
        if(path != ""):
            with open(path, "rb") as f:
                try:
                    self.current_cursor = load_cursor(f)
                    self._current_file = path
                except ValueError as e:
                    print(e)
                    return

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if(event.mimeData().hasImage() or event.mimeData().hasUrls()):
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent):
        self.dragEnterEvent(event)

    def dropEvent(self, event: QtGui.QDropEvent):
        if(event.mimeData().hasUrls()):
            cursor = None
            working_path = None

            for cur_path in event.mimeData().urls():
                if(cur_path.isLocalFile()):
                    path = cur_path.path(options=QtCore.QUrl.FullyDecoded)

                    if(isinstance(pathlib.PurePath(), pathlib.PureWindowsPath) and path.startswith("/")):
                        path = path[1:]

                    with open(path, "rb") as f:
                        try:
                            cursor = load_cursor(f)
                            working_path = path
                        except ValueError as e:
                            print(e)
                else:
                    try:
                        req = urlopen(cur_path.url())
                        data = BytesIO(req.read())
                        data.seek(0)
                        cursor = load_cursor(data)
                        working_path = None
                    except (URLError, ValueError) as e:
                        print(e)

            if(cursor is not None):
                self.current_cursor = cursor
                self._current_file = working_path
                event.acceptProposedAction()
                return

        if(event.mimeData().hasImage()):
            mem_img = BytesIO()
            buffer = QtCore.QBuffer()
            image = QtGui.QImage(event.mimeData().imageData())
            image.save(buffer, "PNG")

            mem_img.write(buffer)
            mem_img.seek(0)

            self.current_cursor = load_cursor(mem_img)
            self._current_file = None
            event.acceptProposedAction()
            return


    @property
    def current_cursor(self):
        return self._viewer.current_cursor

    @current_cursor.setter
    def current_cursor(self, value):
        self._viewer.current_cursor = value

    @property
    def label_text(self):
        return self._label.text()

    @label_text.setter
    def label_text(self, value):
        self._label.setText(value)

    @property
    def current_file(self):
        return self._current_file

    @current_file.setter
    def current_file(self, value):
        if((not isinstance(value, str)) and (value is not None)):
            raise ValueError("The file path must be a string!!!")

        self._current_file = value


if(__name__ == "__main__"):
    app = QtWidgets.QApplication([])
    window = CursorSelectWidget(label_text="wait")
    window.show()
    app.exec_()
    print(window.current_cursor, window.current_file)