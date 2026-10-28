"""One queued owner for the synchronous service and its transport lifetime."""
import copy
from PySide6.QtCore import QObject, Signal, Slot


class HardwareWorker(QObject):
    completed = Signal(str, object, object)
    stopped = Signal()

    def __init__(self, service):
        super().__init__()
        self.service = service

    @Slot(str, object)
    def execute(self, operation, arguments):
        try:
            result = getattr(self.service, operation)(*arguments)
            if operation in ('connect', 'connect_first', 'refresh', 'apply', 'poll'):
                result = (result, self.service.macros)
            self.completed.emit(operation, copy.deepcopy(result), None)
        except Exception as exc:
            # Keep the event loop alive, including on unexpected backend errors.
            self.completed.emit(operation, None, exc)

    @Slot()
    def shutdown(self):
        try:
            self.service.disconnect()
        finally:
            self.stopped.emit()
