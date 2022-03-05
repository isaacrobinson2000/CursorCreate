# Eventually, if we could get this working... :(
# python -m nuitka --standalone --onefile --macos-create-app-bundle --macos-disable-console --macos-onefile-icon=icon_mac.icns --enable-plugin=pyside6 --enable-plugin=numpy CursorCreate/cursorcreate.py

# For now, fall back to pyinstaller
pyinstaller CursorCreate.spec