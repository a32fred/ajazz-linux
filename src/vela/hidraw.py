"""Linux hidraw backend using only the standard library: the part of the hidapi API the transport
uses. Reads wait with select(), so they never hang."""
import fcntl
import os
from pathlib import Path
import select

_IOC_WRITE, _IOC_READ = 1, 2


def hidiocsfeature(length):
    """HIDIOCSFEATURE(length) from linux/hidraw.h: _IOC(_IOC_WRITE | _IOC_READ, 'H', 0x06, length)."""
    return ((_IOC_WRITE | _IOC_READ) << 30) | (length << 16) | (ord('H') << 8) | 0x06


class HidrawDevice:
    def __init__(self, ioctl=fcntl.ioctl):
        self._ioctl = ioctl
        self._fd = None

    def open_path(self, path):
        self._fd = os.open(os.fsdecode(path), os.O_RDWR | os.O_NONBLOCK | os.O_CLOEXEC)

    def set_nonblocking(self, _flag):
        """Always non-blocking; kept so the transport can treat this like the hidapi binding."""

    def send_feature_report(self, data):
        buffer = bytearray(data)
        return self._ioctl(self._fd, hidiocsfeature(len(buffer)), buffer)

    def read(self, size, timeout_ms):
        ready, _, _ = select.select([self._fd], [], [], timeout_ms / 1000)
        if not ready:
            return b''
        try:
            return os.read(self._fd, size)
        except BlockingIOError:
            return b''

    def close(self):
        fd, self._fd = self._fd, None
        if fd is not None:
            os.close(fd)


class Hidraw:
    def __init__(self, sysfs='/sys/class/hidraw', dev='/dev', ioctl=fcntl.ioctl):
        self._sysfs, self._dev, self._ioctl = Path(sysfs), dev, ioctl

    def enumerate(self, vendor_id=0, product_id=0):
        rows = []
        nodes = [node for node in self._sysfs.glob('hidraw[0-9]*') if node.name[6:].isdigit()]
        for node in sorted(nodes, key=lambda item: int(item.name[6:])):
            try:
                text = (node / 'device' / 'uevent').read_text(errors='replace')
                info = dict(line.split('=', 1) for line in text.splitlines() if '=' in line)
                _bus, vid, pid = (int(part, 16) for part in info['HID_ID'].split(':'))
            except (OSError, KeyError, ValueError):
                continue
            if (vendor_id and vid != vendor_id) or (product_id and pid != product_id):
                continue
            rows.append({'path': os.fsencode(f'{self._dev}/{node.name}'), 'vendor_id': vid, 'product_id': pid,
                         'serial_number': info.get('HID_UNIQ', ''), 'product_string': info.get('HID_NAME', ''),
                         'usage_page': 0, 'usage': 0})
        return rows

    def device(self):
        return HidrawDevice(self._ioctl)
