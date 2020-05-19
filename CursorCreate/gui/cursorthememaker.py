from io import BytesIO
from pathlib import Path
from typing import Union, Dict, Any
from PySide2 import QtWidgets, QtCore, QtGui
from CursorCreate.lib import theme_util
from CursorCreate.gui.cursorselector import CursorSelectWidget
from CursorCreate.gui.layouts import FlowLayout
from CursorCreate.lib.cur_theme import CursorThemeBuilder
from PIL.ImageQt import ImageQt
from PIL import Image
import copy
import base64
import re
import sys


ICON = """
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
"""

class CursorThemeMaker(QtWidgets.QWidget):

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        mem_icon = BytesIO(base64.b64decode(ICON))

        self.setWindowTitle("Cursor Theme Builder")
        self.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(ImageQt(Image.open(mem_icon)))))

        self._open_build_project = None

        self._metadata = {"author": None, "licence": None}

        self._main_layout = QtWidgets.QVBoxLayout(self)

        self._scroll_pane = QtWidgets.QScrollArea()
        self._scroll_pane.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self._scroll_pane.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._scroll_pane.setWidgetResizable(True)

        self._inner_pane_area = QtWidgets.QWidget()
        self._flow_layout = FlowLayout()

        self._cursor_selectors = {}

        for cursor_name in sorted(CursorThemeBuilder.DEFAULT_CURSORS):
            self._cursor_selectors[cursor_name] = CursorSelectWidget(label_text=cursor_name)
            self._flow_layout.addWidget(self._cursor_selectors[cursor_name])

        self._edit_metadata = QtWidgets.QPushButton("Edit Artist Info")
        self._main_layout.addWidget(self._edit_metadata)

        self._inner_pane_area.setLayout(self._flow_layout)
        self._scroll_pane.setWidget(self._inner_pane_area)

        self._button_layout = QtWidgets.QHBoxLayout()
        self._main_layout.addWidget(self._scroll_pane)

        self._build_button = QtWidgets.QPushButton("Build Project")
        self._create_proj_btn = QtWidgets.QPushButton("Save Project")
        self._load_proj_btn = QtWidgets.QPushButton("Load Project")
        self._update_proj_btn = QtWidgets.QPushButton("Update Project")
        self._build_in_place = QtWidgets.QPushButton("Build in Place")
        self._clear_btn = QtWidgets.QPushButton("New Project")
        self._update_proj_btn.setEnabled(False)
        self._build_in_place.setEnabled(False)
        self._button_layout.addWidget(self._build_button)
        self._button_layout.addWidget(self._create_proj_btn)
        self._button_layout.addWidget(self._load_proj_btn)
        self._button_layout.addWidget(self._update_proj_btn)
        self._button_layout.addWidget(self._build_in_place)
        self._button_layout.addWidget(self._clear_btn)

        self._main_layout.addLayout(self._button_layout)

        self.setLayout(self._main_layout)
        # self.setMinimumSize(self.sizeHint())

        self._build_button.clicked.connect(self.build_project)
        self._create_proj_btn.clicked.connect(self.create_project)
        self._load_proj_btn.clicked.connect(self.load_project)
        self._update_proj_btn.clicked.connect(self.update_project)
        self._build_in_place.clicked.connect(self.build_in_place)
        self._clear_btn.clicked.connect(self.clear_ui)
        self._edit_metadata.clicked.connect(self._chg_metadata)

    def create_project(self):
        dir_picker = DirectoryPicker(self, "Select Directory to Create Project In")
        dir_picker.exec_()
        directory_info = dir_picker.get_results()

        if(directory_info is not None):
            theme_name, theme_dir = directory_info
            files_and_cursors = {}

            for cursor_name, selector in self._cursor_selectors.items():
                if(selector.current_cursor is not None):
                    c_f_path = Path(selector.current_file) if(selector.current_file is not None) else None
                    files_and_cursors[cursor_name] = (c_f_path, selector.current_cursor)

            theme_util.save_project(theme_name, theme_dir, self._metadata, files_and_cursors)
            self._open_build_project = str((Path(theme_dir) / theme_name) / "build.json")
            self._update_proj_btn.setEnabled(True)
            self._build_in_place.setEnabled(True)

    def build_project(self):
        dir_picker = DirectoryPicker(self, "Select Directory to Build Project In")
        dir_picker.exec_()
        directory_info = dir_picker.get_results()

        if(directory_info is not None):
            theme_name, theme_dir = directory_info
            cursors = {}

            for cursor_name, selector in self._cursor_selectors.items():
                if(selector.current_cursor is not None):
                    cursors[cursor_name] = selector.current_cursor

            theme_util.build_theme(theme_name, theme_dir, self._metadata, cursors)

    def build_in_place(self):
        if(self._open_build_project is None):
            return

        project_folder = Path(self._open_build_project).parent
        theme_name, dir_path = project_folder.name, project_folder.parent

        cursors = {}

        for cursor_name, selector in self._cursor_selectors.items():
            if (selector.current_cursor is not None):
                cursors[cursor_name] = selector.current_cursor

        theme_util.build_theme(theme_name, dir_path, self._metadata, cursors)

        QtWidgets.QMessageBox.information(self, "Cursor Theme Maker", f"Project '{self._open_build_project}' Built!!!")

    def update_project(self):
        if(self._open_build_project is None):
            return

        path_total = Path(self._open_build_project).parent
        theme_name, dir_path = path_total.name, path_total.parent

        files_and_cursors = {}

        for cursor_name, selector in self._cursor_selectors.items():
            if (selector.current_cursor is not None):
                c_f_path = Path(selector.current_file) if (selector.current_file is not None) else None
                files_and_cursors[cursor_name] = (c_f_path, selector.current_cursor)

        theme_util.save_project(theme_name, dir_path, self._metadata, files_and_cursors)

        QtWidgets.QMessageBox.information(self, "Cursor Theme Maker",
                                          f"Project '{self._open_build_project}' Updated!!!")

    def load_project(self):
        file_name, __ = QtWidgets.QFileDialog.getOpenFileName(self, "Select the build file for the project.",
                                                              filter="JSON Build File (*.json)")

        self.load_from_path(file_name)


    def load_from_path(self, file_name: str):
        if(file_name != ""):
            try:
                metadata, data = theme_util.load_project(Path(file_name))

                for name, (path, cursor) in data.items():
                    if(name in self._cursor_selectors):
                        self._cursor_selectors[name].current_cursor = cursor
                        self._cursor_selectors[name].current_file = str(path)

                self._open_build_project = file_name
                self._metadata = metadata
                self._update_proj_btn.setEnabled(True)
                self._build_in_place.setEnabled(True)
            except Exception as e:
                print(e)

    def _chg_metadata(self):
        dialog = MetaDataEdit(self, self._metadata)
        dialog.exec_()
        self._metadata = dialog.get_metadata()

    def clear_ui(self):
        for name, cursor_selector in self._cursor_selectors.items():
            cursor_selector.current_cursor = None
            cursor_selector.current_file = None
        self._metadata = {"author": None, "licence": None}
        self._open_build_project = None
        self._update_proj_btn.setEnabled(False)
        self._build_in_place.setEnabled(False)


class DirectoryPicker(QtWidgets.QDialog):

    IS_VALID_THEME_NAME = re.compile("[-.\w ]+")

    def __init__(self, parent=None, name=""):
        super().__init__(parent)
        super().setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowCloseButtonHint)
        self.setWindowTitle(name)
        self._result = None

        self._form_layout = QtWidgets.QFormLayout(self)
        self._hbox_layout = QtWidgets.QHBoxLayout()

        self._button = QtWidgets.QPushButton("Select")
        self._text = QtWidgets.QLineEdit("")
        self._text.setReadOnly(True)
        self._hbox_layout.addWidget(self._button)
        self._hbox_layout.addWidget(self._text)

        self._theme_text = QtWidgets.QLineEdit()

        self._form_layout.addRow("Theme Name:", self._theme_text)
        self._form_layout.addRow("Theme Directory:", self._hbox_layout)

        self._submit_btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Cancel |
                                                       QtWidgets.QDialogButtonBox.Ok)
        self._submit_btns.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self._form_layout.addRow(self._submit_btns)

        self.setLayout(self._form_layout)

        self._button.clicked.connect(self.openDir)

        self._submit_btns.rejected.connect(self.reject)
        self._submit_btns.accepted.connect(self.accept)
        self._theme_text.textChanged.connect(lambda a: self.validate())

        self.accepted.connect(self.on_submit_stuff)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

    def openDir(self):
        sel_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select a Directory")
        self._text.setText(sel_dir)
        self.validate()

    def validate(self):
        folder_name = self._theme_text.text().strip()
        dir_name = self._text.text().strip()

        path_exists = (Path(dir_name) / folder_name).exists()

        if(self.IS_VALID_THEME_NAME.fullmatch(folder_name) and (dir_name != "") and (not path_exists)):
            self._submit_btns.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
        else:
            self._submit_btns.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

    def on_submit_stuff(self):
        self._result = self._theme_text.text().strip(), Path(self._text.text().strip()).resolve()

    def get_results(self):
        return self._result


class MetaDataEdit(QtWidgets.QDialog):

    FILE_PICKER_FILTER = "Text Files (*.txt)"
    TITLE = "CursorCreate Metadata"

    def __init__(self, parent=None, metadata: Dict[str, Any]=None):
        super().__init__(parent)
        super().setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowCloseButtonHint)
        self.setWindowTitle(self.TITLE)

        if(metadata is None):
            self._metadata = {"author": None, "licence": None}
        else:
            self._metadata = copy.deepcopy(metadata)

        self._main_layout = QtWidgets.QFormLayout(self)
        self._author = QtWidgets.QLineEdit()
        self._author.setText("" if(self._metadata.get("author", None) is None) else self._metadata["author"])

        self._licence_text = QtWidgets.QTextEdit()
        self._licence_text.setText("" if(self._metadata.get("licence", None) is None) else self._metadata["licence"])

        self._licence_btn = QtWidgets.QPushButton("From File")

        self._submit_btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Cancel |
                                                       QtWidgets.QDialogButtonBox.Ok)

        self._main_layout.addRow("Author:", self._author)
        self._main_layout.addRow("Licence:", self._licence_btn)
        self._main_layout.addRow(self._licence_text)
        self._main_layout.addRow(self._submit_btns)

        self._licence_btn.clicked.connect(self._on_file_req)
        self._submit_btns.accepted.connect(self._on_accept)
        self._submit_btns.rejected.connect(self.reject)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

    def _on_file_req(self):
        path, __ = QtWidgets.QFileDialog.getOpenFileName(self, "Select a Licence File", filter=self.FILE_PICKER_FILTER)

        if(path != ""):
            try:
                with open(path) as f:
                    self._licence_text.setText(f.read())
            except IOError as e:
                print(e)

    def _on_accept(self):
        self._metadata["author"] = None if(self._author.text() == "") else self._author.text()
        self._metadata["licence"] = None if(self._licence_text.toPlainText() == "") else self._licence_text.toPlainText()
        self.accept()

    def get_metadata(self):
        return self._metadata


def launch_gui(def_project: Union[str, None]):
    app = QtWidgets.QApplication(sys.argv)
    window = CursorThemeMaker()
    window.show()

    if(def_project is not None):
        window.load_from_path(def_project)

    app.exec_()
