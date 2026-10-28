"""HID adapter (hidraw on Linux, hidapi elsewhere) and conservative, non-probing collection discovery.

HIDAPI's Python binding supplies usage metadata but usually no report lengths.
Linux sysfs descriptors provide the shared-hidraw collection fallback. On Windows
the known FF02/2 and FF01/0 usages are used when lengths are not provided.
"""
import hashlib
import importlib
import os
from pathlib import Path
import re
import sys

from .domain import DeviceError, DeviceInfo, integer


def descriptor_collections(descriptor):
    """Return (usage_page, usage, direction, report_id, byte_length) entries.

    Parse HID short items with bounded stacks and accumulated report bit sizes.
    Long items and malformed descriptors fail closed rather than guessing.
    """
    data = bytes(descriptor)
    if not data or len(data) > 4096:
        raise DeviceError('Invalid HID report descriptor length.')
    state = dict(page=0, size=0, count=0, report=0)
    globals_stack, collections = [], []
    usage = 0
    totals = {}
    offset = 0
    while offset < len(data):
        prefix = data[offset]
        offset += 1
        if prefix == 0xfe:
            raise DeviceError('Unsupported long HID descriptor item.')
        length = (0, 1, 2, 4)[prefix & 3]
        if offset + length > len(data):
            raise DeviceError('Truncated HID report descriptor.')
        value = int.from_bytes(data[offset:offset + length], 'little')
        offset += length
        category, tag = (prefix >> 2) & 3, prefix >> 4
        if category == 1:
            if tag in (0, 7, 8, 9):
                state[{0: 'page', 7: 'size', 8: 'report', 9: 'count'}[tag]] = value
            elif tag == 10:
                globals_stack.append(state.copy())
            elif tag == 11:
                if not globals_stack:
                    raise DeviceError('Unbalanced HID global state.')
                state = globals_stack.pop()
        elif category == 2 and tag == 0:
            usage = value
        elif category == 0:
            if tag == 10:
                collections.append(collections[0] if collections else (state['page'], usage))
            elif tag == 12:
                if not collections:
                    raise DeviceError('Unbalanced HID collection.')
                collections.pop()
            elif tag in (8, 9, 11):
                if not collections:
                    raise DeviceError('HID report has no collection.')
                if state['report'] > 255 or state['size'] > 65535 or state['count'] > 65535:
                    raise DeviceError('Oversized HID report.')
                key = (*collections[0], {8: 'input', 9: 'output', 11: 'feature'}[tag], state['report'])
                totals[key] = totals.get(key, 0) + state['size'] * state['count']
            usage = 0
        if len(collections) > 32 or len(globals_stack) > 32:
            raise DeviceError('HID descriptor nesting is too deep.')
    if collections or globals_stack:
        raise DeviceError('Truncated HID descriptor state.')
    return {(*key, (bits + 7) // 8 + bool(key[3])) for key, bits in totals.items()}


def linux_descriptor(path):
    path = os.fsdecode(path)
    if not re.fullmatch(r'/dev/hidraw\d+', path):
        return None
    descriptor = Path('/sys/class/hidraw') / Path(path).name / 'device/report_descriptor'
    try:
        with descriptor.open('rb') as stream:
            return stream.read(4097)
    except OSError:
        return None


def _parent_key(row):
    serial = row.get('serial_number') or ''
    if serial:
        return ('serial', row['product_id'], serial)
    # Windows collection suffixes vary; retain the physical instance token.
    path = os.fsdecode(row['path']).lower()
    path = re.sub(r'&col[0-9a-f]+', '', path)
    return ('path', row['product_id'], path)


class HidTransport:
    def __init__(self, hid_module=None, descriptor_reader=None):
        self._hid = hid_module
        self._descriptor_reader = descriptor_reader or linux_descriptor
        self._command = None
        self._input = None

    def _api(self):
        if self._hid is None:
            if sys.platform == 'linux':
                # Standard library only; libusb paths would lack the hidraw descriptors and uaccess permissions.
                from .hidraw import Hidraw
                self._hid = Hidraw()
            else:
                try:
                    self._hid = importlib.import_module('hid')
                except (ImportError, OSError) as exc:
                    raise DeviceError('Install the hidapi Python package and the system HIDAPI library.') from exc
        return self._hid

    def scan(self):
        try:
            rows = self._api().enumerate(0x25a7, 0)
        except (OSError, ValueError) as exc:
            raise DeviceError(f'Cannot enumerate HID devices: {exc}') from exc
        groups = {}
        by_path = {}
        for row in rows:
            if row.get('vendor_id') != 0x25a7 or row.get('product_id') not in (0xfa7b, 0xfa7c):
                continue
            path = row.get('path')
            if not path:
                continue
            item = by_path.setdefault(path, {'row': row, 'command': False, 'input': False})
            page, usage = row.get('usage_page'), row.get('usage')
            if (page, usage) == (0xff02, 2) and row.get('feature_report_length', 17) == 17:
                item['command'] = True
            if (page, usage) == (0xff01, 0) and row.get('input_report_length', 17) == 17:
                item['input'] = True
        for path, item in by_path.items():
            descriptor = self._descriptor_reader(path)
            if descriptor is not None:
                try:
                    caps = descriptor_collections(descriptor)
                except DeviceError:
                    continue
                item['command'] = (0xff02, 2, 'feature', 8, 17) in caps
                item['input'] = (0xff01, 0, 'input', 9, 17) in caps
            if item['command'] and item['input']:
                # Linux collections often refer to a single hidraw node.
                groups[('shared', path)] = [item]
            else:
                groups.setdefault(_parent_key(item['row']), []).append(item)
        devices = []
        for items in groups.values():
            commands = [item for item in items if item['command']]
            inputs = [item for item in items if item['input']]
            if len(commands) != 1 or len(inputs) != 1:
                continue  # no cross-device probes or guessed pairing
            row = commands[0]['row']
            command_path, input_path = row['path'], inputs[0]['row']['path']
            identity = hashlib.sha256(os.fsencode(command_path)).hexdigest()[:16]
            name = 'AJ199 · USB cable' if row['product_id'] == 0xfa7b else 'AJ199 · Wireless receiver'
            devices.append(DeviceInfo(identity, name, 0x25a7, row['product_id'], command_path,
                                      input_path, row.get('serial_number') or ''))
        return sorted(devices, key=lambda device: (device.pid, device.id))

    def open(self, device):
        self.close()
        if device.vid != 0x25a7 or device.pid not in (0xfa7b, 0xfa7c) or device.notification_path is None:
            raise DeviceError('Unsupported device or missing configuration input collection.')
        try:
            self._input = self._api().device()
            self._input.open_path(os.fsencode(device.notification_path))
            # Binding read(size,0) uses hid_read, so this MUST be nonblocking.
            self._input.set_nonblocking(1)
            if device.command_path == device.notification_path:
                self._command = self._input
            else:
                self._command = self._api().device()
                self._command.open_path(os.fsencode(device.command_path))
        except (OSError, ValueError, RuntimeError) as exc:
            self.close()
            raise DeviceError(f'Cannot open mouse; check permissions/udev rules and reconnect: {exc}') from exc

    def send(self, data):
        if self._command is None:
            raise DeviceError('Mouse is disconnected.')
        if len(data) != 17 or data[0] != 8:
            raise DeviceError('Configuration requires Feature report 8 with 17 bytes.')
        try:
            return self._command.send_feature_report(bytes(data))
        except (OSError, ValueError, RuntimeError) as exc:
            self.close()
            raise DeviceError(f'Cannot send to mouse: {exc}') from exc

    def receive(self, timeout_ms):
        integer(timeout_ms, 0, 10000, 'Read timeout')
        if self._input is None:
            raise DeviceError('Mouse is disconnected.')
        try:
            return bytes(self._input.read(17, timeout_ms))
        except (OSError, ValueError, RuntimeError) as exc:
            self.close()
            raise DeviceError(f'Cannot read mouse: {exc}') from exc

    def close(self):
        handles = [self._command, self._input]
        self._command = self._input = None
        closed = set()
        for handle in handles:
            if handle is not None and id(handle) not in closed:
                closed.add(id(handle))
                try:
                    handle.close()
                except (OSError, ValueError):
                    pass
