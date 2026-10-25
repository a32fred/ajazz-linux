from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from vela.domain import Binding, DpiStage, FileFormatError, LightingSettings, Macro, MacroEvent, MouseSettings, ValidationError
from vela.formats import load_macro, save_macro, load_profile, save_profile, load_dct, select_profile_macros


def fixture_macro():
    data = bytearray(834)
    struct.pack_into('<IIII', data, 0, 0xfacb99a0, 123, 0, 1)
    data[20:26] = b'T\0e\0s\0'
    struct.pack_into('<H', data, 104, 1)
    struct.pack_into('<HHI', data, 106, 0x41, 1, 0x1234)
    struct.pack_into('<HHI', data, 114, 0x41, 0, 0)
    return data


def rotated(data):
    return bytes((value >> 2) | ((value << 6) & 255) for value in data)


def fixture_profile(macro_reference=False):
    """Pack documented offsets directly; never use production file codecs.

    CLONE_SPEC profile layout: selected bank+238, bank1+3BC, six matrix
    positions, DWORD polling+6BC, X/Y/COLORREF/flag records+6D8, and controls
    +758..77C/+7C0..7CC. Distinct values expose wrong offsets/byte order.
    """
    data = bytearray(2116)
    struct.pack_into('<II', data, 0, 0xfcaa1234, 0xdeadbeef)
    data[0x210:0x228] = 'Spec fixture'.encode('utf-16-le')
    struct.pack_into('<I', data, 0x238, 1)
    # Bank0 differs deliberately: a decoder ignoring selected bank must fail.
    for matrix in range(6):
        struct.pack_into('<II', data, 0x23c + matrix * 24, 0x080000aa, matrix + 1)
    for matrix, action in enumerate((0x01000011, 0x01000016, 0x080000a9,
                                     0x080000b0, 0x080000a8, 0x080000ac)):
        struct.pack_into('<II', data, 0x3bc + matrix * 24, action, matrix + 1)
    if macro_reference:
        struct.pack_into('<III', data, 0x41c, 0x05000000, 5, 123)
    for offset, value in ((0x6bc, 0x250), (0x758, 1), (0x760, 2),
                          (0x764, 2), (0x768, 1), (0x76c, 1), (0x770, 300),
                          (0x774, 17), (0x778, 0), (0x77c, 0),
                          (0x7c0, 4), (0x7c4, 3), (0x7c8, 9), (0x7cc, 0x3c2b1a)):
        struct.pack_into('<I', data, offset, value)
    struct.pack_into('<IIII', data, 0x6d8, 1200, 2450, 0xac6824, 0)
    struct.pack_into('<IIII', data, 0x6e8, 26000, 50, 0xbadcfe, 0)
    return data


def expected_profile(macro_reference=False):
    # Literal domain values, independent of the fixture packing/conversion.
    return MouseSettings(
        stages=[DpiStage(1200, 2450, '#2468ac'), DpiStage(26000, 50, '#fedcba')],
        active_stage=1, polling_hz=250, debounce_ms=17, lod_mm=2,
        angle_snapping=True, ripple=True, light_on=False,
        light_off_while_moving=False, idle_seconds=300,
        lighting=LightingSettings(4, 9, 3, '#1a2b3c'),
        bindings=[Binding('left'), Binding('left_double_click'), Binding('dpi_down'),
                  Binding('macro', macro_id=123) if macro_reference else Binding('dpi_up'),
                  Binding('profile_cycle'), Binding('polling_cycle')])


def fixture_jma():
    macro = fixture_macro()
    struct.pack_into('<II', macro, 12, 0, 2)  # manual delay, held mode
    macro[20:100] = '编辑 🚀'.encode('utf-16-le').ljust(80, b'\0')
    struct.pack_into('<H', macro, 104, 12)
    struct.pack_into('<HHI', macro, 114, 0x07fd, 2, 3)  # signed X=-3,Y=7
    # Ten decoded macro slots; the referenced macro is deliberately in slot3.
    return bytes(fixture_profile(True)) + bytes(3 * 834) + bytes(macro) + bytes(6 * 834)


class FormatTests(unittest.TestCase):
    def test_independent_jmm_fixture_rotation_and_vk_adapter(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'a.jmm'
            path.write_bytes(rotated(fixture_macro()))
            macro = load_macro(path)
            self.assertEqual(macro, Macro(123, 'Tes', [MacroEvent('down', 4, 0x1234), MacroEvent('up', 4)]))
            save_macro(path, macro)
            self.assertEqual(path.read_bytes()[:4], bytes.fromhex('28 66 f2 be'))
            self.assertEqual(len(path.read_bytes()), 834)
            self.assertEqual(load_macro(path), macro)

    def test_jmm_rejects_length_magic_wheel_and_excess_events(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'bad.jmm'
            variants = [b'', bytes(833), bytes(835), bytes(834)]
            for code, flags, delay in ((0xf5, 1, 0), (0xf6, 0, 1), (0x41, 4, 0), (0x41, 1, 65536)):
                raw = fixture_macro()
                struct.pack_into('<HHI', raw, 106, code, flags, delay)
                variants.append(rotated(raw))
            raw = fixture_macro()
            for index in range(71):
                struct.pack_into('<HHI', raw, 106 + index * 8, 0x41, 1, 0)
            variants.append(rotated(raw))
            for data in variants:
                path.write_bytes(data)
                with self.subTest(size=len(data)), self.assertRaises(FileFormatError):
                    load_macro(path)

    def test_jmm_preserves_unknown_bytes_when_unchanged(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'x.jmm'
            data = fixture_macro()
            data[100:104] = b'\x12\x34\x56\x78'
            path.write_bytes(rotated(data))
            value = load_macro(path)
            save_macro(path, value)
            self.assertEqual(path.read_bytes(), rotated(data))

    def test_independent_jma_fixture_settings_bindings_and_macro_reference(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'x.jma'
            data = fixture_jma()
            path.write_bytes(data)
            settings = expected_profile(True)
            macro = Macro(123, '编辑 🚀', [MacroEvent('down', 4, 0x1234),
                          MacroEvent('move', delay_ms=3, dx=-3, dy=7)], 'held', 12, False)
            self.assertEqual(load_profile(path), (settings, [macro]))
            save_profile(path, settings, [macro])
            self.assertEqual(load_profile(path), (settings, [macro]))
            for bad in (data[:-1], data + b'\0', bytes(10456)):
                path.write_bytes(bad)
                with self.assertRaises(FileFormatError):
                    load_profile(path)

    def test_jma_export_rejects_unsupported_or_missing_references_without_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'x.jma'
            path.write_bytes(b'previous')
            settings = MouseSettings(bindings=[Binding('dpi_cycle') for _ in range(6)])
            settings.bindings[0] = Binding('keyboard', [4])
            with self.assertRaises(ValidationError):
                save_profile(path, settings, [])
            settings.bindings[0] = Binding('macro', macro_id=999)
            with self.assertRaises(ValidationError):
                save_profile(path, settings, [])
            settings.bindings[0] = Binding('dpi_cycle')
            with self.assertRaises(ValidationError):
                save_profile(path, settings, [Macro(i, 'x', []) for i in range(1, 12)])
            self.assertEqual(path.read_bytes(), b'previous')

    def test_dct_prefix_and_four_block_bound(self):
        with tempfile.TemporaryDirectory() as root:
            block = bytes(fixture_profile())
            dct = Path(root) / 'x.dct'
            dct.write_bytes(b'\xef\xbe\xad\xde' + block * 4)
            profiles = load_dct(dct)
            self.assertEqual(len(profiles), 4)
            self.assertEqual([profile.name for profile in profiles], ['Spec fixture'] * 4)
            for profile in profiles:
                self.assertEqual(profile.settings, expected_profile())
            for bad in (b'', b'\0' * 4 + block[:-1], b'\0' * 4 + block * 5):
                dct.write_bytes(bad)
                with self.assertRaises(FileFormatError):
                    load_dct(dct)

    def test_jma_preserves_opaque_bytes_and_macro_slot_positions(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'x.jma'
            data = bytearray(fixture_jma())
            data[0x100:0x104] = b'\x12\x34\x56\x78'
            path.write_bytes(data)
            settings, macros = load_profile(path)
            save_profile(path, settings, macros)
            self.assertEqual(path.read_bytes(), data)
            settings.debounce_ms = 19
            save_profile(path, settings, macros)
            self.assertEqual(path.read_bytes()[0x100:0x104], b'\x12\x34\x56\x78')

    def test_missing_macro_reference_in_inactive_bank_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'x.jma'
            data = bytearray(fixture_jma())
            struct.pack_into('<I', data, 0x23c, 0x05000000)
            struct.pack_into('<I', data, 0x244, 999)
            path.write_bytes(data)
            with self.assertRaises(FileFormatError):
                load_profile(path)

    def test_unchanged_legacy_fast_path_still_validates_numeric_types(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'x.jma'
            path.write_bytes(fixture_jma())
            settings, macros = load_profile(path)
            settings.active_stage = True
            with self.assertRaises(ValidationError):
                save_profile(path, settings, macros)

    def test_dct_rejects_invalid_profile_name(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'x.jma'
            block = fixture_profile()
            block[0x210:0x238] = bytes(40)
            path.write_bytes(bytes(4) + block)
            with self.assertRaises(FileFormatError):
                load_dct(path)

    def test_explicit_jma_export_keeps_unreferenced_macro_and_original_slots(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'x.jma'
            raw = bytearray(fixture_jma())
            unused = fixture_macro()
            struct.pack_into('<I', unused, 4, 321)
            raw[2116:2116 + 834] = unused
            path.write_bytes(raw)
            settings, macros = load_profile(path)
            self.assertEqual([m.id for m in macros], [321, 123])
            save_profile(path, settings, macros)
            self.assertEqual(path.read_bytes(), raw)
            settings.debounce_ms = 19
            save_profile(path, settings, macros)
            self.assertEqual([m.id for m in load_profile(path)[1]], [321, 123])

    def test_profile_selection_drops_replaced_active_reference_but_keeps_other_records(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'x.jma'
            raw = bytearray(fixture_jma())
            # Last record in bank2 is opaque to the six visible button controls.
            struct.pack_into('<III', raw, 0x6a4, 0x05000000, 16, 123)
            path.write_bytes(raw)
            settings, macros = load_profile(path)
            settings.bindings[3] = Binding('left')
            self.assertEqual([m.id for m in select_profile_macros(settings, macros)], [123])
            with self.assertRaises(ValidationError):
                select_profile_macros(settings, [])
            path.write_bytes(fixture_jma())
            settings, macros = load_profile(path)
            settings.bindings[3] = Binding('left')
            self.assertEqual(select_profile_macros(settings, macros), [])

    def test_profile_selection_enforces_slot_limit_after_all_bank_selection(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'x.jma'
            raw = fixture_profile()
            slots = []
            for index in range(10):
                struct.pack_into('<III', raw, 0x23c + index * 24, 0x05000000, index + 1, index + 1)
                macro = fixture_macro()
                struct.pack_into('<I', macro, 4, index + 1)
                slots.append(bytes(macro))
            original_file = bytes(raw) + b''.join(slots)
            path.write_bytes(original_file)
            settings, macros = load_profile(path)
            # Ten retained bank0 entries plus a newly assigned active entry.
            settings.bindings[3] = Binding('macro', macro_id=11)
            macros.append(Macro(11, 'New assignment', []))
            selection = select_profile_macros(settings, macros)
            self.assertEqual(len(selection), 11)
            with self.assertRaises(ValidationError):
                save_profile(path, settings, selection)
            self.assertEqual(path.read_bytes(), original_file)
