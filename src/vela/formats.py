"""Bounded adapters for the documented legacy layouts, never host pointers.

Only evidenced profile action encodings can be newly exported. Imported opaque
records/bytes remain data and are retained on subsequent legacy exports.
"""
import copy
import struct

from .domain import (Binding, DpiStage, FileFormatError, LightingSettings, Macro,
                     MacroEvent, MouseSettings, Profile, ValidationError)
from .protocol import PHYSICAL_MATRIX
from .storage import atomic_write, bounded_read

JMM_SIZE = 834
PROFILE_SIZE = 2116
JMA_SIZE = 10456
_ACTIONS = {
    'left': 0x01000011, 'left_double_click': 0x01000016,
    'left_triple_click': 0x01000017, 'dpi_up': 0x080000a8,
    'dpi_down': 0x080000a9, 'dpi_cycle': 0x080000aa,
    'light_toggle': 0x080000a7, 'polling_cycle': 0x080000ac,
    'profile_cycle': 0x080000b0,
}
# This adapter alone translates the spec's Windows VK column to HID usages.
_HID_VK = {**{4 + i: 0x41 + i for i in range(26)},
           **{0x3a + i: 0x70 + i for i in range(12)},
           **{0x1e + i: 0x31 + i for i in range(9)},
           **{0x59 + i: 0x61 + i for i in range(9)},
           0x29: 0x1b, 0x27: 0x30, 0x2b: 9, 0x39: 0x14,
           0x28: 0x0d, 0x2a: 8, 0x2c: 0x20, 0x2f: 0xdb,
           0x30: 0xdd, 0x31: 0xdc, 0x33: 0xba, 0x34: 0xde,
           0x36: 0xbc, 0x37: 0xbe, 0x38: 0xbf, 0x35: 0xc0,
           0x2e: 0xbb, 0x2d: 0xbd, 0x46: 0x2c, 0x47: 0x91,
           0x48: 0x13, 0x49: 0x2d, 0x4a: 0x24, 0x4b: 0x21,
           0x4c: 0x2e, 0x4d: 0x23, 0x4e: 0x22, 0x52: 0x26,
           0x51: 0x28, 0x50: 0x25, 0x4f: 0x27, 0x62: 0x60,
           0x57: 0x6b, 0x56: 0x6d, 0x55: 0x6a, 0x54: 0x6f,
           0x53: 0x90, 0x58: 0x0d, 0x63: 0x6e, 0x65: 0x5d,
           **{0xe0 + i: vk for i, vk in enumerate((0xa2, 0xa0, 0xa4, 0x5b, 0xa3, 0xa1, 0xa5, 0x5c))}}
_VK_HID = {vk: hid for hid, vk in _HID_VK.items()}
_VK_HID[0x0d] = 0x28  # VK_RETURN cannot distinguish keypad Enter.


def _u32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def _put(data, offset, value):
    struct.pack_into('<I', data, offset, value)


def _text(data, maximum):
    units = [data[i:i + 2] for i in range(0, len(data), 2)]
    try:
        end = units.index(b'\0\0')
        if end > maximum:
            raise ValueError('Name exceeds limit.')
        return b''.join(units[:end]).decode('utf-16-le')
    except (ValueError, UnicodeError) as exc:
        raise FileFormatError('Invalid bounded UTF-16 name.') from exc


def _remember(value, raw, kind):
    setattr(value, '_legacy_' + kind, (bytes(raw), copy.deepcopy(value)))
    return value


def _macro_from_raw(raw):
    if len(raw) != JMM_SIZE or _u32(raw, 0) != 0xfacb99a0 or not _u32(raw, 4):
        raise FileFormatError('Invalid legacy macro header or zero ID.')
    try:
        automatic = _u32(raw, 12)
        if automatic not in (0, 1):
            raise FileFormatError('Invalid automatic delay flag.')
        mode = {0: 'count', 2: 'held', 1: 'toggle'}[_u32(raw, 16)]
        events = []
        for offset in range(106, JMM_SIZE, 8):
            code, flags, delay = struct.unpack_from('<HHI', raw, offset)
            if code == 0 and delay == 0:
                break
            if len(events) >= 70 or flags not in (0, 1, 2) or delay > 65535:
                raise FileFormatError('Unsupported macro event count/flags/delay.')
            if flags == 2:
                x, y = code & 255, code >> 8
                event = MacroEvent('move', delay_ms=delay, dx=x - 256 if x > 127 else x, dy=y - 256 if y > 127 else y)
            else:
                if code in range(0xf0, 0xf5):
                    hid = code
                elif code > 255 or code in (0xf5, 0xf6) or code not in _VK_HID:
                    raise FileFormatError('Unsupported legacy macro key or wheel event.')
                else:
                    hid = _VK_HID[code]
                event = MacroEvent('down' if flags else 'up', hid, delay)
            events.append(event)
        macro = Macro(_u32(raw, 4), _text(raw[20:100], 39), events, mode,
                      struct.unpack_from('<H', raw, 104)[0], bool(automatic))
        macro.validate()
        return _remember(macro, raw, 'macro')
    except (ValidationError, KeyError) as exc:
        raise FileFormatError(f'Unsupported legacy macro: {exc}') from exc


def _macro_to_raw(macro):
    macro.validate()
    if not macro.id:
        raise ValidationError('Legacy macro export requires a nonzero ID.')
    previous = getattr(macro, '_legacy_macro', None)
    if previous and macro == previous[1]:
        return previous[0]
    raw = bytearray(JMM_SIZE)
    if previous:
        raw[:] = previous[0]
    _put(raw, 0, 0xfacb99a0)
    _put(raw, 4, macro.id)
    _put(raw, 12, int(macro.auto_delay))
    _put(raw, 16, {'count': 0, 'held': 2, 'toggle': 1}[macro.loop_mode])
    raw[20:100] = macro.name.encode('utf-16-le').ljust(80, b'\0')
    struct.pack_into('<H', raw, 104, macro.repeat)
    raw[106:] = bytes(JMM_SIZE - 106)
    for index, event in enumerate(macro.events):
        if event.kind == 'move':
            if event.code or not -128 <= event.dx <= 127 or not -128 <= event.dy <= 127:
                raise ValidationError('Legacy movement requires signed byte components and no key code.')
            code, flags = (event.dx & 255) | ((event.dy & 255) << 8), 2
            if code == 0 and event.delay_ms == 0:
                raise ValidationError('Zero movement without delay is a legacy terminator.')
        else:
            if event.dx or event.dy:
                raise ValidationError('Keyboard event cannot contain movement.')
            if event.code in range(0xf0, 0xf5):
                code = event.code
            elif event.code not in _HID_VK or event.code == 0x58:
                raise ValidationError('Unsupported or ambiguous legacy keyboard usage.')
            else:
                code = _HID_VK[event.code]
            flags = int(event.kind == 'down')
        struct.pack_into('<HHI', raw, 106 + 8 * index, code, flags, event.delay_ms)
    return bytes(raw)


def load_macro(path):
    data = bounded_read(path, JMM_SIZE)
    if len(data) != JMM_SIZE:
        raise FileFormatError('JMM files must contain exactly 834 bytes.')
    return _macro_from_raw(bytes(((value << 2) & 255) | (value >> 6) for value in data))


def save_macro(path, macro):
    raw = _macro_to_raw(macro)
    atomic_write(path, bytes((value >> 2) | ((value << 6) & 255) for value in raw))


def _rgb(value):
    if value > 0xffffff:
        raise FileFormatError('Unsupported legacy COLORREF high byte.')
    return '#' + value.to_bytes(3, 'little').hex()


def _boolean(raw, offset):
    value = _u32(raw, offset)
    if value not in (0, 1):
        raise FileFormatError('Invalid legacy boolean value.')
    return bool(value)


def _profile_macro_ids(raw):
    return {_u32(raw, offset + 8) for offset in range(0x23c, 0x6bc, 24)
            if _u32(raw, offset) >> 24 == 5}


def _profile_from_raw(raw, macros):
    if len(raw) != PROFILE_SIZE or _u32(raw, 0) != 0xfcaa1234 or not _u32(raw, 4):
        raise FileFormatError('Invalid legacy profile header.')
    try:
        count, bank = _u32(raw, 0x760), _u32(raw, 0x238)
        if not 1 <= count <= 6 or bank > 2:
            raise FileFormatError('Unsupported legacy DPI stage count or binding bank.')
        stages = []
        for i in range(count):
            offset = 0x6d8 + i * 16
            if _u32(raw, offset + 12) != 0:
                raise FileFormatError('Unsupported legacy per-stage flags.')
            stages.append(DpiStage(_u32(raw, offset), _u32(raw, offset + 4), _rgb(_u32(raw, offset + 8))))
        by_id = {macro.id: macro for macro in macros}
        if not _profile_macro_ids(raw) <= by_id.keys():
            raise FileFormatError('Legacy profile references a missing macro in a binding bank.')
        bindings = []
        action_names = {code: name for name, code in _ACTIONS.items()}
        for matrix in PHYSICAL_MATRIX:
            offset = 0x23c + bank * 0x180 + matrix * 24
            code = _u32(raw, offset)
            if code in action_names:
                binding = Binding(action_names[code])
            elif code >> 24 == 5:
                macro_id = _u32(raw, offset + 8)
                if macro_id not in by_id:
                    raise FileFormatError('Legacy profile references a missing macro.')
                binding = Binding('macro', macro_id=macro_id)
            else:
                binding = Binding('legacy:' + bytes(raw[offset:offset + 24]).hex())
            bindings.append(binding)
        settings = MouseSettings(stages, _u32(raw, 0x758),
            {0x125: 125, 0x250: 250, 0x500: 500, 0x1000: 1000}[_u32(raw, 0x6bc)],
            _u32(raw, 0x774), _u32(raw, 0x764), _boolean(raw, 0x76c), _boolean(raw, 0x768),
            _boolean(raw, 0x77c), _boolean(raw, 0x778), _u32(raw, 0x770),
            LightingSettings(_u32(raw, 0x7c0), _u32(raw, 0x7c8), _u32(raw, 0x7c4), _rgb(_u32(raw, 0x7cc))), bindings)
        settings.validate()
        return _remember(settings, raw, 'profile')
    except (ValidationError, KeyError) as exc:
        raise FileFormatError(f'Unsupported legacy profile settings: {exc}') from exc


def _profile_to_raw(settings, macros):
    settings.validate()
    previous = getattr(settings, '_legacy_profile', None)
    if previous and settings == previous[1]:
        return previous[0]
    raw = bytearray(previous[0] if previous else bytes(PROFILE_SIZE))
    _put(raw, 0, 0xfcaa1234)
    if not previous:
        _put(raw, 4, 1)  # valid nonzero state token, never a process address
        raw[0x210:0x238] = 'Vela'.encode('utf-16-le').ljust(40, b'\0')
    bank = _u32(raw, 0x238)
    by_id = {macro.id: macro for macro in macros}
    for position, (matrix, binding) in enumerate(zip(PHYSICAL_MATRIX, settings.bindings)):
        offset = 0x23c + bank * 0x180 + matrix * 24
        if previous and binding == previous[1].bindings[position]:
            continue
        if binding.keys or binding.modifiers:
            raise ValidationError('Legacy keyboard/combination layout is unavailable; save native JSON instead.')
        if binding.action == 'macro' and binding.macro_id in by_id:
            code = 0x05000000
        elif binding.action in _ACTIONS and binding.macro_id is None:
            code = _ACTIONS[binding.action]
        else:
            raise ValidationError(f'Legacy export cannot represent {binding.action!r}; save native JSON instead.')
        raw[offset:offset + 24] = bytes(24)
        _put(raw, offset, code)
        _put(raw, offset + 4, matrix + 1)
        if binding.action == 'macro':
            _put(raw, offset + 8, binding.macro_id)
    _put(raw, 0x6bc, {125: 0x125, 250: 0x250, 500: 0x500, 1000: 0x1000}[settings.polling_hz])
    for i, stage in enumerate(settings.stages):
        for j, value in enumerate((stage.x, stage.y, int.from_bytes(bytes.fromhex(stage.color[1:]), 'little'), 0)):
            _put(raw, 0x6d8 + i * 16 + j * 4, value)
    for offset, value in ((0x758, settings.active_stage), (0x760, len(settings.stages)),
                          (0x764, settings.lod_mm), (0x768, settings.ripple),
                          (0x76c, settings.angle_snapping), (0x770, settings.idle_seconds),
                          (0x774, settings.debounce_ms), (0x778, settings.light_off_while_moving),
                          (0x77c, settings.light_on), (0x7c0, settings.lighting.mode),
                          (0x7c4, settings.lighting.speed), (0x7c8, settings.lighting.brightness),
                          (0x7cc, int.from_bytes(bytes.fromhex(settings.lighting.color[1:]), 'little'))):
        _put(raw, offset, int(value))
    return bytes(raw)


def load_profile(path):
    raw = bounded_read(path, JMA_SIZE)
    return _jma_from_raw(raw)


def _jma_from_raw(raw):
    if len(raw) != JMA_SIZE:
        raise FileFormatError('JMA files must contain exactly 10456 bytes.')
    macros = []
    ids = set()
    for offset in range(PROFILE_SIZE, JMA_SIZE, JMM_SIZE):
        slot = raw[offset:offset + JMM_SIZE]
        if not any(slot):
            continue
        macro = _macro_from_raw(slot)
        if macro.id in ids:
            raise FileFormatError('Duplicate legacy macro ID.')
        ids.add(macro.id)
        macros.append(macro)
    settings = _profile_from_raw(raw[:PROFILE_SIZE], macros)
    settings._legacy_jma = (raw, copy.deepcopy(settings), copy.deepcopy(macros))
    return settings, macros


def select_profile_macros(settings, macros):
    """Select library entries needed by the exported profile, including opaque banks.

    Selection uses the same serialized binding records as save_profile, so edited
    active bindings replace their old references. The caller's library is intact;
    save_profile still exports all explicitly supplied macros and enforces limits.
    """
    macros = list(macros)
    required = _profile_macro_ids(_profile_to_raw(settings, macros))
    if not required <= {macro.id for macro in macros}:
        raise ValidationError('Profile references a missing macro in a binding bank.')
    return [macro for macro in macros if macro.id in required]


def save_profile(path, settings, macros):
    settings.validate()
    macros = list(macros)
    if len(macros) > 10 or len({macro.id for macro in macros}) != len(macros):
        raise ValidationError('JMA supports at most ten macros with distinct IDs.')
    macro_data = [_macro_to_raw(macro) for macro in macros]
    ids = {macro.id for macro in macros}
    if any(binding.action == 'macro' and binding.macro_id not in ids for binding in settings.bindings):
        raise ValidationError('Profile references a missing macro.')
    previous = getattr(settings, '_legacy_jma', None)
    if previous and settings == previous[1] and macros == previous[2]:
        atomic_write(path, previous[0])
        return
    raw = _profile_to_raw(settings, macros)
    if not _profile_macro_ids(raw) <= ids:
        raise ValidationError('An inactive binding bank references a missing macro.')
    atomic_write(path, raw + b''.join(macro_data) + bytes((10 - len(macros)) * JMM_SIZE))


def load_dct(path):
    raw = bounded_read(path, 4 + 4 * PROFILE_SIZE)
    if len(raw) < 4 + PROFILE_SIZE or (len(raw) - 4) % PROFILE_SIZE:
        raise FileFormatError('DCT requires a four-byte prefix and one to four profile blocks.')
    result = []
    for offset in range(4, len(raw), PROFILE_SIZE):
        block = raw[offset:offset + PROFILE_SIZE]
        settings = _profile_from_raw(block, [])
        profile = Profile(_text(block[0x210:0x238], 19), settings)
        try:
            profile.validate()
        except ValidationError as exc:
            raise FileFormatError(f'Invalid DCT profile: {exc}') from exc
        result.append(profile)
    return result
