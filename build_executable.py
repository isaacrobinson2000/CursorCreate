import subprocess
import os
import sys

env = os.environ.copy()
# Import QtKit to figure out what Qt library is being used...
import CursorCreate.gui.QtKit as QtKit
env["PYTHON_QT_LIB"] = QtKit.__name__

if(sys.platform.startswith("win")):
    command = "python -m nuitka --standalone --onefile --windows-disable-console --windows-icon-from-ico=icon_windows.ico --enable-plugin=pyside6 --enable-plugin=numpy CursorCreate/cursorcreate.py"
elif(sys.platform.startswith("linux")):
    command = "python -m nuitka --standalone --onefile --linux-onefile-icon=icon_linux.xpm --enable-plugin=pyside6 --enable-plugin=numpy CursorCreate/cursorcreate.py"
elif(sys.platform.startswith("darwin")):
    command = "python -m nuitka --standalone --onefile --macos-create-app-bundle --macos-disable-console --macos-onefile-icon=icon_mac.icns --enable-plugin=pyside6 --enable-plugin=numpy CursorCreate/cursorcreate.py"
else:
    raise EnvironmentError(f"Unsupported Platform: {sys.platform}")

# Run the command...
print("Building an executable...")
process = subprocess.run(command, env=env)
