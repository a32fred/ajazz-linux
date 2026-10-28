# Dependency license references

Vela's MIT license does not relicense its dependencies. Installations obtain dependencies separately through pip. Redistributors must review the licenses of the exact versions they bundle, include their required notices, and satisfy applicable source/relinking requirements.

- **PySide6 / shiboken6 / Qt for Python:** LGPLv3/GPLv3/commercial terms as applicable. Qt runtime modules have their own license and third-party notices. Official references: <https://doc.qt.io/qtforpython-6/licenses.html> and <https://doc.qt.io/qt-6/licensing.html>. Installed PySide6 distributions include license files and module notices. Vela uses QtCore, QtGui, QtWidgets and QtSvgWidgets from PySide6-Essentials; it does not ship a modified Qt build.
- **Python HIDAPI bindings (`hidapi`):** BSD-style binding license and bundled HIDAPI library licenses. Repository/license reference: <https://github.com/trezor/cython-hidapi>. Underlying HIDAPI offers GPLv3, BSD-style or HIDAPI-specific license alternatives; review <https://github.com/libusb/hidapi/blob/master/LICENSE.txt> and files referenced there. Linux backend dependencies may carry additional notices.
- **CPython:** Python Software Foundation license and bundled component notices: <https://docs.python.org/3/license.html>.
- **Build tools (setuptools, build, pip):** build/development dependencies, not Vela application assets. Their installed distributions contain their licenses.

No vendor application, binary, skin, image, font or SDK is included. Protocol notes in `docs/reference` were derived from analysis of the vendor driver for interoperability and contain no copied code. The packaged sail logo is Vela's original local SVG, copied exactly from the approved brand asset.
