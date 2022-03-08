from CursorCreate.gui.QtKit import QtGui, QtCore
from CursorCreate.gui.cursorhotspotedit import HotspotEditDialog
from CursorCreate.gui.cursorviewer import CursorDisplayWidget


class CursorViewEditWidget(CursorDisplayWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        self._pressed = True

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if self._pressed:
            self._pressed = False
            if self.current_cursor is not None:
                mod_hotspot = HotspotEditDialog(self.window(), self.current_cursor)
                mod_hotspot.exec_()
                self.current_cursor = self.current_cursor
                del mod_hotspot
