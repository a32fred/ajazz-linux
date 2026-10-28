"""Synchronous, serialized application service; GUI callers use a worker thread."""
import copy
import json
import threading
import time
from pathlib import Path

from .domain import (ApplyError, Binding, DeviceError, DeviceSnapshot, ProtocolError,
                     ValidationError, VelaError, integer)
from .protocol import (PHYSICAL_MATRIX, ProtocolClient, decode_notification, decode_settings,
                       encode_binding, settings_records, checked, encode_macro,
                       encode_combination, decode_combination, decode_macro, verify_record)
from .simulator import SimulatedTransport
from .transport import HidTransport


# EEPROM regions this application knows: settings block, key combinations, macro bodies.
WRITABLE = ((0x0000, 0x00b9), (0x0100, 0x01c0), (0x0300, 0x0b00))
POLL_FAILURES_BEFORE_DISCONNECT = 3
BACKUPS_KEPT = 20


class MouseService:
    def __init__(self, demo=False, transport=None, backup_dir=None):
        self.transport = transport if transport is not None else (SimulatedTransport() if demo else HidTransport())
        self._client = ProtocolClient(self.transport)
        self._device = None
        self._snapshot = None
        self._raw = None
        self._macros = []
        self._lock = threading.RLock()
        self.backup_dir = None if backup_dir is None else Path(backup_dir)
        self._poll_failures = 0

    @property
    def connected(self):
        return self._device is not None

    @property
    def device(self):
        return self._device

    @property
    def macros(self):
        """Decoded active device slots; IDs match bindings, values never alias."""
        with self._lock:
            return copy.deepcopy(self._macros)

    def scan(self):
        with self._lock:
            return self.transport.scan()

    def connect_first(self, devices):
        failures = []
        with self._lock:
            for device in devices:
                try:
                    return self.connect(device)
                except (VelaError, OSError) as exc:
                    failures.append(f'{device.name}: {exc}')
        raise DeviceError('No active mouse connection responded. ' + ' '.join(failures))

    def connect(self, device):
        with self._lock:
            self.disconnect()
            try:
                self.transport.open(device)
                self._device = device
                connection = self._client.query(3)
                if connection.size != 1 or connection.data != b'\x01':
                    raise ProtocolError('Mouse connection response is unsupported.')
                return self.refresh()
            except (VelaError, OSError):
                self.disconnect()
                raise

    def refresh(self):
        with self._lock:
            if not self.connected:
                raise DeviceError('Connect a mouse first.')
            try:
                profile = self._client.query(14)
                if profile.size != 1:
                    raise ProtocolError('Malformed current profile response.')
                raw = self._client.read_eeprom(0, 0xb9)
                settings = decode_settings(raw)
                macros = []
                for position, matrix in enumerate(PHYSICAL_MATRIX):
                    action = int.from_bytes(verify_record(raw[0x60 + matrix * 4:0x64 + matrix * 4]), 'little')
                    if action == 5:
                        auxiliary = self._client.read_eeprom(0x100 + matrix * 32, 32)
                        settings.bindings[position] = decode_combination(auxiliary)
                    elif action & 255 == 6 and (action >> 8) & 255 == matrix:
                        auxiliary = self._client.read_eeprom(0x300 + matrix * 0x180, 384)
                        mode = action >> 16
                        if mode not in (*range(1, 251), 0xfe, 0xff):
                            continue
                        macro_id = 0x80000000 + matrix
                        cached = self._applied_macro_ids.get(matrix)
                        if cached and auxiliary[:len(cached[1])] == cached[1] and cached[2] == mode:
                            macro_id = cached[0]
                        try:
                            macro = decode_macro(auxiliary, macro_id,
                                loop_mode='held' if mode == 0xfe else 'toggle' if mode == 0xff else 'count',
                                repeat=mode if mode <= 250 else 1)
                        except ProtocolError:
                            continue  # retain original opaque binding for unsupported bodies
                        matching = next((item for item in macros if item.id == macro.id), None)
                        if matching is not None and matching != macro:
                            macro.id = next(value for value in range(0x80000000, 0x80000010)
                                            if all(item.id != value for item in macros))
                        if matching is None or matching != macro:
                            macros.append(macro)
                        settings.bindings[position] = Binding('macro', macro_id=macro.id)
                battery = self._client.query(4)
                if battery.size != 2:
                    raise ProtocolError('Malformed battery response.')
                # Undocumented battery scales/flags remain unavailable.
                percent = battery.data[0] if battery.data[0] <= 100 else None
                charging = bool(battery.data[1]) if battery.data[1] in (0, 1) else None
                snapshot = DeviceSnapshot(self._device, settings, percent, profile.data[0], None, charging)
                self._raw, self._snapshot, self._macros = raw, copy.deepcopy(snapshot), macros
                return snapshot
            except (VelaError, OSError):
                self.disconnect()
                raise

    def _binding_records(self, settings, macros):
        """Prepare validated auxiliary slots and matrix records before any writes."""
        records = {}
        by_id = {}
        for macro in macros:
            macro.validate()
            if macro.id in by_id:
                raise ValidationError('Macro IDs must be unique.')
            by_id[macro.id] = macro
        self._pending_macro_ids = dict(getattr(self, '_applied_macro_ids', {}))
        for position, (matrix, binding) in enumerate(zip(PHYSICAL_MATRIX, settings.bindings)):
            if binding.action == 'macro':
                if binding == self._snapshot.settings.bindings[position] and binding.macro_id not in by_id:
                    continue
                if binding.keys or binding.modifiers or binding.macro_id not in by_id:
                    raise ValidationError('Select an available macro without keyboard parameters.')
                macro = by_id[binding.macro_id]
                records[0x300 + matrix * 0x180] = encode_macro(macro)
                mode = {'count': macro.repeat, 'held': 0xfe, 'toggle': 0xff}[macro.loop_mode]
                records[0x60 + matrix * 4] = checked(bytes([6, matrix, mode]))
                self._pending_macro_ids[matrix] = (macro.id, records[0x300 + matrix * 0x180], mode)
                continue
            if binding.action == 'keyboard' or binding.action.startswith('consumer:'):
                records[0x100 + matrix * 32] = encode_combination(binding)
                records[0x60 + matrix * 4] = checked(b'\x05\0\0')
                continue
            if binding == self._snapshot.settings.bindings[position]:
                continue  # preserve unknown action bytes exactly when unchanged
            records[0x60 + matrix * 4] = encode_binding(binding)
        return records

    def apply(self, settings, macros=()):
        with self._lock:
            settings = copy.deepcopy(settings)
            settings.validate()
            if not self.connected:
                raise DeviceError('Connect a mouse first.')
            self.refresh()
            records = settings_records(settings, self._raw, include_bindings=False)
            # Validate every requested operation before making the first write.
            records.update(self._binding_records(settings, macros))
            had_left = any(binding.action == 'left' for binding in self._snapshot.settings.bindings)
            if had_left and not any(binding.action == 'left' for binding in settings.bindings):
                raise ValidationError('Keep at least one button assigned to Left click, or the mouse cannot be used to undo this change.')
            # The base snapshot ends at B9; compare auxiliary slots against their
            # actual device bytes rather than treating every apply as a change.
            try:
                records = {address: record for address, record in records.items()
                           if address < 0x100 or self._client.read_eeprom(address, len(record)) != record}
            except (DeviceError, ProtocolError, OSError):
                self.disconnect()
                raise
            records = {address: record for address, record in records.items()
                       if self._raw[address:address + len(record)] != record}
            for address, record in records.items():
                if not any(start <= address and address + len(record) <= end for start, end in WRITABLE):
                    raise ValidationError(f'Refusing to write outside known EEPROM regions (0x{address:04x}).')
            self._backup(records)
            shrinking = len(settings.stages) < len(self._snapshot.settings.stages)
            order = []
            if shrinking and 4 in records:
                order.append(4)
            # Initialize added DPI/color records before increasing the stage count.
            order.extend(sorted(address for address in records if 12 <= address < 0x4c))
            if 2 in records:
                order.append(2)
            if 4 in records and 4 not in order:
                order.append(4)
            # Auxiliary data must be confirmed before a matrix entry enables it.
            order.extend(sorted(address for address in records if address >= 0x100))
            order.extend(sorted(address for address in records if address not in order))
            completed = 0
            attempted = False
            try:
                for address in order:
                    attempted = True
                    self._client.write_eeprom(address, records[address])
                    completed += 1
                self._applied_macro_ids = self._pending_macro_ids
                return self.refresh()
            except (VelaError, OSError) as exc:
                self.disconnect()
                raise ApplyError(f'Application stopped after {completed} confirmed writes. '
                                 f'The mouse may contain some changes; reconnect to read its state. {exc}',
                                 completed_writes=completed, partial=attempted) from exc

    def _backup(self, records):
        """Save the bytes about to be overwritten; no backup means no write."""
        if self.backup_dir is None or not records:
            return
        try:
            regions = {0: self._raw}
            for address, record in records.items():
                if address >= 0x100:
                    regions[address] = self._client.read_eeprom(address, len(record))
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            stamp = time.strftime('%Y%m%d-%H%M%S')
            path = self.backup_dir / f'eeprom-{stamp}.json'
            path.write_text(json.dumps({'device': self._device.name, 'time': stamp,
                                        'regions': {f'0x{a:04x}': bytes(v).hex() for a, v in regions.items()}}, indent=1))
            for old in sorted(self.backup_dir.glob('eeprom-*.json'))[:-BACKUPS_KEPT]:
                old.unlink()
        except (OSError, DeviceError, ProtocolError) as exc:
            raise DeviceError(f'Could not save a backup before writing, so nothing was written: {exc}') from exc

    def poll(self):
        """Cheap status check: profile, battery and the header holding stage count and active stage.

        A changed header or profile triggers a full read. One failed check does not end the session.
        """
        with self._lock:
            if not self.connected:
                raise DeviceError('Connect a mouse first.')
            try:
                profile = self._client.query(14)
                battery = self._client.query(4)
                header = self._client.read_eeprom(0, 12)
                if profile.size != 1 or battery.size != 2:
                    raise ProtocolError('Malformed status response.')
            except (VelaError, OSError):
                self._poll_failures += 1
                if self._poll_failures >= POLL_FAILURES_BEFORE_DISCONNECT:
                    self.disconnect()
                raise
            self._poll_failures = 0
            if profile.data[0] != self._snapshot.current_profile or header != self._raw[:12]:
                return self.refresh()
            snapshot = copy.deepcopy(self._snapshot)
            snapshot.battery_percent = battery.data[0] if battery.data[0] <= 100 else None
            snapshot.charging = bool(battery.data[1]) if battery.data[1] in (0, 1) else None
            self._snapshot.battery_percent, self._snapshot.charging = snapshot.battery_percent, snapshot.charging
            return snapshot

    def dump(self, length=0x1000):
        """Read-only copy of the first `length` EEPROM bytes."""
        integer(length, 1, 0x10000, 'Dump length')
        with self._lock:
            if not self.connected:
                raise DeviceError('Connect a mouse first.')
            try:
                return self._client.read_eeprom(0, length)
            except (VelaError, OSError):
                self.disconnect()
                raise

    def listen(self, seconds):
        """Collect unsolicited reports for a while as (seconds, events, raw hex); sends nothing."""
        integer(seconds, 1, 600, 'Listen time')
        found = []
        with self._lock:
            if not self.connected:
                raise DeviceError('Connect a mouse first.')
            start = time.monotonic()
            while time.monotonic() - start < seconds:
                raw = self.transport.receive(200)
                if raw:
                    found.append((round(time.monotonic() - start, 2), decode_notification(raw), bytes(raw).hex(' ')))
        return found

    def switch_profile(self, index):
        integer(index, 0, 255, 'Device profile index')
        with self._lock:
            if not self.connected:
                raise DeviceError('Connect a mouse first.')
            try:
                self._client.query(16, size=1, data=bytes([index]))
                snapshot = self.refresh()
                if snapshot.current_profile != index:
                    raise ProtocolError('Device profile selection was not confirmed by readback.')
                return snapshot
            except (VelaError, OSError):
                self.disconnect()
                raise

    def disconnect(self):
        with self._lock:
            self._device = self._snapshot = self._raw = None
            self._macros = []
            self._applied_macro_ids = {}
            self._poll_failures = 0
            self.transport.close()
