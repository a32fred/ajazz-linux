"""Deterministic in-memory device using the same numbered reports as hardware."""
from collections import deque

from .domain import DeviceError, DeviceInfo, MouseSettings, ProtocolError
from .protocol import build_frame, settings_records


class SimulatedTransport:
    """Local demo transport. Fault controls affect real framing/readback paths.

    EEPROM remains global when switching the profile selector: the specification
    does not establish independent EEPROM banks. Demo is not a firmware emulator.
    """
    def __init__(self):
        self.device = DeviceInfo('vela-demo', 'Vela Demo Mouse', 0x25a7, 0xfa7b,
                                 'simulator:command', 'simulator:input', 'DEMO')
        self.memory = bytearray(b'\xff' * 65536)
        for address, record in settings_records(MouseSettings()).items():
            self.memory[address:address + len(record)] = record
        self.is_open = False
        self.current_profile = 0
        self.sent = []
        self._queue = deque()
        self.fail_after_writes = None
        self.ignore_writes = False
        self.write_count = 0

    def scan(self):
        return [self.device]

    def open(self, device):
        if device != self.device:
            raise DeviceError('Unknown simulated device.')
        self._queue.clear()
        self.is_open = True

    def send(self, data):
        if not self.is_open:
            raise DeviceError('Demo mouse is disconnected.')
        raw = bytes(data)
        if len(raw) != 17 or raw[0] != 8 or sum(raw) & 255 != 0x55 or raw[5] > 10:
            raise ProtocolError('Invalid simulated command report.')
        self.sent.append(raw)
        command, size = raw[1], raw[5]
        address = int.from_bytes(raw[3:5], 'big')
        payload = raw[6:6 + size]
        status = 0
        if command in (7, 8):
            if not 1 <= size <= 10 or address + size > len(self.memory):
                status = 1
                payload = b''
            elif command == 7:
                if self.fail_after_writes is not None and self.write_count >= self.fail_after_writes:
                    raise DeviceError('Demo device disconnected during application.')
                if not self.ignore_writes:
                    self.memory[address:address + size] = payload
                self.write_count += 1
            else:
                payload = bytes(self.memory[address:address + size])
        elif command == 3:
            payload = b'\x01'
        elif command == 4:
            payload = b'\x57\x00'
        elif command == 14:
            payload = bytes([self.current_profile])
        elif command == 16 and size == 1:
            self.current_profile = payload[0]
        else:
            status, payload = 1, b''
        self._queue.append(build_frame(command, report_id=9, status=status, address=address,
                                       size=size if command in (7, 8) else len(payload), data=payload))
        return 17

    def receive(self, timeout_ms):
        if not self.is_open:
            raise DeviceError('Demo mouse is disconnected.')
        return self._queue.popleft() if self._queue else b''

    def close(self):
        self.is_open = False
        self._queue.clear()
