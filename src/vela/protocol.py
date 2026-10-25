"""AJ199 report and EEPROM codecs, independently implemented from the spec.

No retries are performed after writes: missing acknowledgements leave write state
uncertain. A bounded drain prevents already queued replies satisfying a new call.
"""
from dataclasses import dataclass
import threading
import time

from .domain import (ProtocolError, DeviceError, ValidationError, integer, dpi, Macro, MacroEvent,
                     Binding, DpiStage, LightingSettings, MouseSettings)

PHYSICAL_MATRIX = (0, 1, 2, 4, 3, 5)
DIRECT_ACTIONS = {
    'disabled': 0, 'left': 0x101, 'right': 0x201, 'middle': 0x401,
    'back': 0x801, 'forward': 0x1001,
    'left_double_click': 0x023204, 'left_triple_click': 0x033204,
    'dpi_up': 0x202, 'dpi_down': 0x302, 'dpi_cycle': 0x102,
    'polling_cycle': 7, 'light_toggle': 8, 'profile_cycle': 9,
}
POLLING_TO_WIRE = {1000: 1, 500: 2, 250: 4, 125: 8}
LIGHT_MODES = {0: 4, 1: 2, 2: 1, 4: 3, 6: 7}
LIGHT_SPEED = (0, 255, 230, 210, 190, 170, 150, 130, 110, 70, 40)
LIGHT_BRIGHTNESS = (0, 45, 50, 75, 100, 125, 150, 175, 200, 225, 255)
CONSUMER_USAGES = {
    'Media player': 0x183, 'Play/pause': 0xcd, 'Stop media': 0xb7,
    'Previous track': 0xb6, 'Next track': 0xb5, 'Volume up': 0xe9,
    'Volume down': 0xea, 'Mute': 0xe2, 'Email': 0x18a,
    'Calculator': 0x192, 'File explorer': 0x194, 'Search': 0x221,
    'Home page': 0x223, 'Browser back': 0x224, 'Browser forward': 0x225,
    'Browser stop': 0x226, 'Browser refresh': 0x227, 'Favorites': 0x22a,
}
KEYBOARD_USAGES = frozenset(range(4, 0x66)) - {0x32, 0x64}
_MODIFIERS = {0xe0: 1, 0xe1: 2, 0xe2: 4, 0xe3: 8,
              0xe4: 16, 0xe5: 32, 0xe6: 64}
_MOUSE = {0xf0: 1, 0xf1: 2, 0xf2: 4, 0xf3: 16, 0xf4: 8}


def encode_macro(macro):
    """Hardware body; options/repeats belong to the matrix, not this body."""
    macro.validate()
    raw = bytearray(32)
    raw[31] = len(macro.events)
    for event in macro.events:
        if event.kind == 'move':
            if event.code or not -128 <= event.dx <= 127 or not -128 <= event.dy <= 127:
                raise ValidationError('Hardware movement requires signed byte components and no key code.')
            kind, low, high = 5, event.dx & 255, event.dy & 255
        else:
            if event.dx or event.dy:
                raise ValidationError('Keyboard events cannot contain movement.')
            if event.code in _MODIFIERS:
                family, low = 0, _MODIFIERS[event.code]
            elif event.code in _MOUSE:
                family, low = 4, _MOUSE[event.code]
            elif event.code in KEYBOARD_USAGES:
                family, low = 1, event.code
            else:
                raise ValidationError('Unsupported hardware macro key or mouse event.')
            kind, high = (0x80 if event.kind == 'down' else 0x40) | family, 0
        raw.extend((kind, low, high, event.delay_ms >> 8, event.delay_ms & 255))
    raw.append((0x55 - sum(raw[31:])) & 255)
    if len(macro.events) <= 69:
        raw.extend(b'\0\0\0')
    name = macro.name.encode('utf-16-le')[:30]
    if name and 0xd800 <= int.from_bytes(name[-2:], 'little') <= 0xdbff:
        name = name[:-2]
    raw[0] = len(name)
    raw[1:1 + len(name)] = name
    return bytes(raw)


def decode_macro(data, macro_id=0, *, loop_mode='count', repeat=1):
    raw = bytes(data)
    if len(raw) < 33 or raw[0] > 30 or raw[0] % 2 or raw[31] > 70:
        raise ProtocolError('Invalid hardware macro header.')
    length = 32 + 5 * raw[31]
    if len(raw) < length + 1 or sum(raw[31:length + 1]) & 255 != 0x55:
        raise ProtocolError('Invalid hardware macro length or checksum.')
    try:
        name = raw[1:1 + raw[0]].decode('utf-16-le')
        events = []
        for offset in range(32, length, 5):
            kind, low, high, delay_hi, delay_lo = raw[offset:offset + 5]
            delay = (delay_hi << 8) | delay_lo
            if kind == 5:
                events.append(MacroEvent('move', delay_ms=delay, dx=low - 256 if low > 127 else low,
                                         dy=high - 256 if high > 127 else high))
                continue
            if kind & 0xc0 not in (0x40, 0x80) or high:
                raise ProtocolError('Unsupported hardware macro event.')
            family = kind & 0x3f
            if family == 0:
                code = {value: key for key, value in _MODIFIERS.items()}[low]
            elif family == 4:
                code = {value: key for key, value in _MOUSE.items()}[low]
            elif family == 1 and low in KEYBOARD_USAGES:
                code = low
            else:
                raise ProtocolError('Unsupported hardware macro family.')
            events.append(MacroEvent('down' if kind & 0x80 else 'up', code, delay))
        result = Macro(macro_id, name, events, loop_mode, repeat)
        result.validate()
        return result
    except (UnicodeError, KeyError, ValidationError) as exc:
        raise ProtocolError('Unsupported hardware macro contents.') from exc


def encode_combination(binding):
    binding.validate()
    if binding.macro_id is not None:
        raise ValidationError('Combination cannot reference a macro.')
    events = []
    if binding.action == 'keyboard':
        modifiers = [1 << bit for bit in range(4) if binding.modifiers & (1 << bit)]
        if not binding.keys and not modifiers or len(binding.keys) + len(modifiers) > 5:
            raise ValidationError('Combination requires one to five total keys/modifiers.')
        if any(key not in KEYBOARD_USAGES for key in binding.keys) or len(set(binding.keys)) != len(binding.keys):
            raise ValidationError('Unsupported or duplicate keyboard usage.')
        events = [(0x80, value, 0) for value in modifiers]
        events += [(0x81, key, 0) for key in binding.keys]
        events += [(0x40, value, 0) for value in modifiers]
        events += [(0x41, key, 0) for key in reversed(binding.keys)]
    elif binding.action.startswith('consumer:') and not binding.keys and not binding.modifiers:
        try:
            usage = int(binding.action[9:], 16)
        except ValueError as exc:
            raise ValidationError('Invalid consumer usage.') from exc
        if usage not in CONSUMER_USAGES.values():
            raise ValidationError('Unsupported consumer usage.')
        events = [(0x82, usage & 255, usage >> 8), (0x42, usage & 255, usage >> 8)]
    else:
        raise ValidationError('Unsupported combination action.')
    return checked(bytes([len(events)]) + bytes(value for event in events for value in event))


def decode_combination(data):
    raw = bytes(data)
    if not raw or raw[0] > 10 or len(raw) < 2 + raw[0] * 3:
        raise ProtocolError('Invalid combination length.')
    raw = raw[:2 + raw[0] * 3]
    verify_record(raw)
    presses = [tuple(raw[i:i + 3]) for i in range(1, 1 + raw[0] * 3, 3)]
    if len(presses) == 2 and presses[0][0] == 0x82:
        result = Binding(f'consumer:{presses[0][1] | presses[0][2] << 8:04x}')
    else:
        modifiers, keys = 0, []
        for kind, low, high in presses:
            if kind & 0x40:
                break
            if kind == 0x80 and low in (1, 2, 4, 8) and high == 0:
                modifiers |= low
            elif kind == 0x81 and high == 0:
                keys.append(low)
            else:
                raise ProtocolError('Unsupported combination event.')
        result = Binding('keyboard', keys, modifiers)
    try:
        if encode_combination(result) != raw:
            raise ProtocolError('Noncanonical or unsupported combination.')
    except ValidationError as exc:
        raise ProtocolError('Unsupported combination contents.') from exc
    return result


def checked(data):
    raw = bytes(data)
    return raw + bytes([(0x55 - sum(raw)) & 255])


def verify_record(data):
    if not data or sum(data) & 255 != 0x55:
        raise ProtocolError('Invalid EEPROM register checksum.')
    return data[:-1]


def build_frame(command, *, status=0, address=0, size=None, data=b'', report_id=8):
    integer(command, 0, 255, 'Command')
    integer(status, 0, 255, 'Status')
    integer(address, 0, 65535, 'EEPROM address')
    integer(report_id, 8, 9, 'Report ID')
    data = bytes(data)
    size = len(data) if size is None else size
    integer(size, 0, 10, 'Payload size')
    if len(data) > 10 or len(data) > size:
        raise ValidationError('Report data exceeds payload size.')
    return checked(bytes([report_id, command, status, address >> 8, address & 255, size]) + data + bytes(10 - len(data)))


def eeprom_frame(command, address, size, data=b''):
    integer(size, 1, 10, 'EEPROM chunk length')
    integer(address, 0, 65536 - size, 'EEPROM address')
    if command not in (7, 8) or (command == 7 and len(data) != size) or (command == 8 and data):
        raise ValidationError('Invalid EEPROM request.')
    return build_frame(command, address=address, size=size, data=data)


@dataclass(frozen=True)
class Reply:
    command: int
    status: int
    address: int
    size: int
    data: bytes


def parse_frame(data):
    raw = bytes(data)
    if len(raw) != 17 or raw[0] != 9 or sum(raw) & 255 != 0x55:
        raise ProtocolError('Malformed input report or invalid checksum.')
    if raw[5] > 10:
        raise ProtocolError('Input report payload exceeds ten bytes.')
    return Reply(raw[1], raw[2], int.from_bytes(raw[3:5], 'big'), raw[5], raw[6:6 + raw[5]])


def encode_dpi(x, y):
    cx, cy = dpi(x) // 50 - 1, dpi(y) // 50 - 1
    return checked(bytes([cx & 255, cy & 255, ((cx >> 8) << 2) | ((cy >> 8) << 6)]))


def decode_dpi(data):
    if len(data) != 4:
        raise ProtocolError('Invalid DPI register length.')
    x, y, control = verify_record(data)
    x |= (control & 0x0c) << 6
    y |= (control & 0xc0) << 2
    if control & 0x22:
        raise ProtocolError('Unsupported DPI multiplier bits.')
    return (x + 1) * (100 if control & 1 else 50), (y + 1) * (100 if control & 0x10 else 50)


def encode_binding(binding):
    binding.validate()
    if binding.action not in DIRECT_ACTIONS or binding.keys or binding.modifiers or binding.macro_id is not None:
        raise ValidationError(f'Button action {binding.action!r} is unavailable in this backend.')
    return checked(DIRECT_ACTIONS[binding.action].to_bytes(3, 'little'))


def decode_binding(data):
    if len(data) != 4:
        raise ProtocolError('Invalid binding register length.')
    action = int.from_bytes(verify_record(data), 'little')
    actions = {value: key for key, value in DIRECT_ACTIONS.items()}
    return Binding(actions.get(action, f'unknown:{action:06x}'))


def encode_lighting(settings, existing=None):
    settings.validate()
    if settings.mode == 0 and existing is not None:
        if len(existing) != 7:
            raise ProtocolError('Invalid lighting register length.')
        raw = bytearray(verify_record(existing))
        raw[0] = 4
        return checked(raw)
    return checked(bytes([LIGHT_MODES[settings.mode]]) + bytes.fromhex(settings.color[1:]) +
                   bytes([LIGHT_SPEED[settings.speed], LIGHT_BRIGHTNESS[settings.brightness]]))


def decode_lighting(data):
    if len(data) != 7:
        raise ProtocolError('Invalid lighting register length.')
    raw = verify_record(data)
    try:
        mode = {value: key for key, value in LIGHT_MODES.items()}[raw[0]]
        speed = LIGHT_SPEED.index(raw[4], 1)
        brightness = LIGHT_BRIGHTNESS.index(raw[5], 1)
    except (KeyError, ValueError) as exc:
        raise ProtocolError('Unsupported lighting register value.') from exc
    return LightingSettings(mode, brightness, speed, '#' + raw[1:4].hex())


def settings_records(settings, existing=None, include_bindings=True):
    """Return independent writable registers; never include unknown B5/B7."""
    settings.validate()
    records = {0: checked([POLLING_TO_WIRE[settings.polling_hz]]),
               2: checked([len(settings.stages)]), 4: checked([settings.active_stage]),
               10: checked([settings.lod_mm]), 0xa9: checked([settings.debounce_ms]),
               0xab: checked([int(settings.light_on)]), 0xad: checked([settings.idle_seconds // 10]),
               0xaf: checked([int(settings.angle_snapping)]), 0xb1: checked([int(settings.ripple)]),
               0xb3: checked([int(settings.light_off_while_moving)])}
    for index, stage in enumerate(settings.stages):
        records[12 + 4 * index] = encode_dpi(stage.x, stage.y)
        records[44 + 4 * index] = checked(bytes.fromhex(stage.color[1:]))
    records[0xa0] = encode_lighting(settings.lighting, None if existing is None else existing[0xa0:0xa7])
    if include_bindings:
        for matrix, binding in zip(PHYSICAL_MATRIX, settings.bindings):
            records[0x60 + matrix * 4] = encode_binding(binding)
    return records


def decode_settings(memory):
    if len(memory) < 0xb9:
        raise ProtocolError('Device settings readback is truncated.')

    def scalar(address):
        return verify_record(memory[address:address + 2])[0]

    def boolean(address):
        value = scalar(address)
        if value not in (0, 1):
            raise ProtocolError('Unsupported device boolean value.')
        return bool(value)

    try:
        count = scalar(2)
        if not 1 <= count <= 6:
            raise ProtocolError('Device returned an unsupported DPI stage count.')
        stages = []
        for index in range(count):
            x, y = decode_dpi(memory[12 + 4 * index:16 + 4 * index])
            rgb = verify_record(memory[44 + 4 * index:48 + 4 * index])
            stages.append(DpiStage(x, y, '#' + rgb.hex()))
        polling = {value: key for key, value in POLLING_TO_WIRE.items()}[scalar(0)]
        settings = MouseSettings(stages=stages, active_stage=scalar(4), polling_hz=polling,
                                 debounce_ms=scalar(0xa9), lod_mm=scalar(10),
                                 angle_snapping=boolean(0xaf), ripple=boolean(0xb1),
                                 light_on=boolean(0xab), light_off_while_moving=boolean(0xb3),
                                 idle_seconds=scalar(0xad) * 10, lighting=decode_lighting(memory[0xa0:0xa7]),
                                 bindings=[decode_binding(memory[0x60 + i * 4:0x64 + i * 4]) for i in PHYSICAL_MATRIX])
        settings.validate()
        return settings
    except (ValidationError, KeyError) as exc:
        raise ProtocolError(f'Device returned unsupported settings: {exc}') from exc


class ProtocolClient:
    def __init__(self, transport, timeout_ms=1000, max_reports=64):
        self.transport = transport
        self.timeout_ms = integer(timeout_ms, 1, 10000, 'Timeout')
        self.max_reports = integer(max_reports, 1, 1024, 'Report limit')
        self._lock = threading.RLock()

    def query(self, command, *, address=0, size=None, data=b'', match_eeprom=False):
        request = build_frame(command, address=address, size=size, data=data)
        with self._lock:
            # Non-blocking and bounded: an unsolicited flood cannot stall a call.
            for _ in range(self.max_reports):
                if not self.transport.receive(0):
                    break
            else:
                raise DeviceError('Too many pending input reports; reconnect the mouse.')
            if self.transport.send(request) != 17:
                raise DeviceError('The feature report was only partially sent.')
            deadline = time.monotonic() + self.timeout_ms / 1000
            for _ in range(self.max_reports):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                raw = self.transport.receive(max(1, int(remaining * 1000)))
                if not raw:
                    break
                try:
                    reply = parse_frame(raw)
                except ProtocolError:
                    continue
                if reply.command == 10 or reply.command != command:
                    continue
                if match_eeprom and (reply.address != address or reply.size != size):
                    continue
                if reply.status:
                    raise ProtocolError(f'Mouse rejected command 0x{command:02x} (status {reply.status}).')
                return reply
            raise DeviceError(f'Timed out waiting for command 0x{command:02x}.')

    def read_eeprom(self, address, size):
        integer(size, 1, 65536, 'EEPROM length')
        integer(address, 0, 65536 - size, 'EEPROM address')
        with self._lock:
            result = bytearray()
            while len(result) < size:
                length = min(10, size - len(result))
                result.extend(self.query(8, address=address + len(result), size=length, match_eeprom=True).data)
            return bytes(result)

    def write_eeprom(self, address, data):
        data = bytes(data)
        integer(len(data), 1, 65536, 'EEPROM length')
        integer(address, 0, 65536 - len(data), 'EEPROM address')
        with self._lock:
            for offset in range(0, len(data), 10):
                chunk = data[offset:offset + 10]
                # Only command/status are established for write ACKs. Address and
                # length are required on the subsequent readback, not invented
                # requirements on an uncaptured write response.
                self.query(7, address=address + offset, size=len(chunk), data=chunk)
                if self.read_eeprom(address + offset, len(chunk)) != chunk:
                    raise ProtocolError(f'EEPROM readback differs at 0x{address + offset:04x}.')
