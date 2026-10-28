"""Desktop toasts through notify-send; a missing tool or a refusal just means no toast."""
from PySide6.QtCore import QProcess
from PySide6.QtGui import QGuiApplication


class Notifier:
    def __init__(self):
        self.enabled = True

    def show(self, title, body='', key='vela', timeout_ms=2500):
        """Return True if a toast was handed to the desktop. Same key replaces the previous toast."""
        if not self.enabled or QGuiApplication.platformName() == 'offscreen':
            return False
        return bool(QProcess.startDetached('notify-send', [
            '--app-name', 'Vela Mouse Studio', '--icon', 'input-mouse', '--expire-time', str(timeout_ms),
            f'--hint=string:x-canonical-private-synchronous:{key}', title, body]))
