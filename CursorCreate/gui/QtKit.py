import sys
import os
from typing import Any

# Change Qt Implementation here...
if("PYTHON_QT_LIB" in os.environ):
    val = os.environ["PYTHON_QT_LIB"]
    # We have to hard code imports for nuitka...
    # this forces nuitka to look for Qt and include it.
    if(val == "PySide2"):
        from PySide2 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets, QtWebEngineCore
    elif(val == "PyQt6"):
        from PyQt6 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets, QtWebEngineCore
    elif(val == "PyQt5"):
        from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets, QtWebEngineCore
    else:
        from PySide6 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets, QtWebEngineCore
else:
    # Load the Qt Implementation dynamically in all other cases...
    _QT_IMPLEMENTATIONS = ["PySide6", "PySide2", "PyQt6", "PyQt5"]
    _SELECTED_QT_IMPL = None

    for impl_name in _QT_IMPLEMENTATIONS:
        try:
            _SELECTED_QT_IMPL = __import__(impl_name, globals(), locals(), [], 0)
            break
        except ImportError:
            continue

    if(_SELECTED_QT_IMPL is None):
        raise ImportError("Unable to find a Python Qt library to use!")

    __name__ = _SELECTED_QT_IMPL.__name__

    def __dir__() -> list:
        return dir(_SELECTED_QT_IMPL)

    def __getattr__(name: str) -> Any:
        return getattr(_SELECTED_QT_IMPL, name)


# Keep qt from freezing on MacOS...
if(sys.platform.startswith("darwin")):
    os.environ["QT_MAC_WANTS_LAYER"] = "1"