from typing import Any, List

_QT_Implementations = ["PySide6", "PySide2", "PyQt6", "PyQt5"]
_QT_IMPL = None

for impl_name in _QT_Implementations:
    try:
        _QT_IMPL = __import__(impl_name, globals(), locals(), [], 0)
        __name__ = impl_name
        break
    except ImportError:
        pass

if(_QT_IMPL is None):
    raise ImportError("Unable to find a Qt toolkit for the UI!")

def __getattr__(attr: str) -> Any:
    return getattr(_QT_IMPL, attr)

def __dir__() -> List[str]:
    return dir(_QT_IMPL)