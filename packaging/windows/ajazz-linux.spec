# PyInstaller spec: a one-folder build (starts faster than one-file, which unpacks on every launch).
# Run from the repository root: pyinstaller packaging/windows/ajazz-linux.spec
import os
import sys

root = os.path.abspath(os.path.join(SPECPATH, '..', '..'))  # paths below are relative to the spec file otherwise

windows = sys.platform == 'win32'
a = Analysis(
    [os.path.join(root, 'packaging', 'windows', 'entry.py')],
    pathex=[os.path.join(root, 'src')],
    datas=[(os.path.join(root, 'src', 'vela', 'assets', '*'), 'vela/assets')],
    # hidapi is imported by name at run time on Windows.
    hiddenimports=['hid'] if windows else [],
    excludes=['tkinter', 'unittest', 'pydoc', 'PySide6.QtNetwork', 'PySide6.QtQml', 'PySide6.QtQuick',
              'PySide6.QtPdf', 'PySide6.QtOpenGL', 'PySide6.QtDBus', 'PySide6.QtSql', 'PySide6.QtTest'],
)
pyz = PYZ(a.pure)
# Two programs share one folder: the window (no console) and the command line tool (console).
gui = EXE(pyz, a.scripts, [], exclude_binaries=True, name='ajazz-linux', console=False)
cli = EXE(pyz, a.scripts, [], exclude_binaries=True, name='ajazz-linux-cli', console=True)
coll = COLLECT(gui, cli, a.binaries, a.datas, strip=False, upx=False, name='ajazz-linux')
