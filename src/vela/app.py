"""Desktop and CLI entry points. Backend work begins only after explicit choice."""
import argparse
from pathlib import Path
import sys


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if '--cli' in argv:
        from .cli import run
        argv.remove('--cli')
        return run(argv)
    parser = argparse.ArgumentParser(prog='vela', description='Ajazz Linux — native AJ199 settings')
    parser.add_argument('--demo', action='store_true', help='Auto-connect the labeled local simulator')
    parser.add_argument('--workspace', type=Path, help='Directory for native workspace storage')
    parser.add_argument('--screenshot', type=Path, help='Save a demo preview PNG then exit (requires --demo)')
    args = parser.parse_args(argv)
    if args.screenshot and not args.demo:
        parser.error('--screenshot requires --demo; preview never opens a physical mouse')
    from PySide6.QtCore import QCoreApplication, QElapsedTimer, QEvent, QTimer
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication
    from .storage import ProfileStore
    from .ui.window import MainWindow
    app = QApplication.instance() or QApplication([sys.argv[0]])
    app.setApplicationName('Ajazz Linux')
    app.setOrganizationName('Vela')
    app.setWindowIcon(QIcon(str(Path(__file__).parent / 'assets' / 'vela.svg')))
    window = MainWindow(demo=args.demo, store=ProfileStore(args.workspace))
    window.show()
    preview_result = 0
    if args.screenshot:
        timer = QTimer(window)
        elapsed = QElapsedTimer()
        elapsed.start()
        def capture():
            nonlocal preview_result
            if window.busy and elapsed.elapsed() < 10000:
                return
            timer.stop()
            try:
                if window.busy:
                    raise RuntimeError('Demo startup exceeded 10 seconds.')
                if window.snapshot is None:
                    raise RuntimeError(f'Demo could not connect. {window.status.text()}')
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                if not window.grab().save(str(args.screenshot)):
                    raise OSError('Could not save preview image.')
            except Exception as exc:
                preview_result = 1
                print(f'Vela preview failed: {exc}', file=sys.stderr)
            window.close()
        timer.timeout.connect(capture)
        timer.start(100)
    result = app.exec()
    # Destroy the window and its I/O thread now, while the QApplication still exists; leaving it to
    # interpreter shutdown can free Qt objects after the application and corrupt memory.
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    return preview_result or result
