try:
    from PySide6 import *
except ImportError:
    try:
        from PySide2 import *
    except ImportError:
        try:
            from PyOt6 import *
        except ImportError:
            try:
                from PyQt5 import *
            except ImportError:
                raise ImportError("Unable to find a Qt toolkit for the UI!")

