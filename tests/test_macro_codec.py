import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from vela.domain import Binding, Macro, MacroEvent, MouseSettings, ValidationError
from vela.protocol import encode_macro, decode_macro, encode_combination, decode_combination
from vela.service import MouseService
from vela.domain import default_workspace, DeviceError
from vela.storage import ProfileStore


class MacroCodecTests(unittest.TestCase):
    def test_hardware_vector_checksum_delay_and_name(self):
        value = Macro(7, 'A', [MacroEvent('down', 4, 0x1234)])
        raw = encode_macro(value)
        self.assertEqual(len(raw), 41)
        self.assertEqual(raw[:4], b'\x02A\0\0')
        self.assertEqual(raw[31:], bytes.fromhex('01 81 04 00 12 34 89 00 00 00'))
        self.assertEqual(decode_macro(raw, 7), value)

    def test_70_boundary_and_surrogate_safe_name(self):
        for count, length in ((69, 381), (70, 383)):
            value = Macro(1, 'a' * 14 + '\U0001f680', [MacroEvent('up', 4)] * count)
            raw = encode_macro(value)
            self.assertEqual(len(raw), length)
            self.assertEqual(raw[0], 28)
            self.assertEqual(decode_macro(raw, 1).name, 'a' * 14)
        with self.assertRaises(ValidationError):
            encode_macro(Macro(1, 'x', [MacroEvent('up', 4)] * 71))

    def test_unsupported_events_and_lossy_fields_rejected(self):
        for event in (MacroEvent('wheel'), MacroEvent('down', 0xf5), MacroEvent('move', dx=128), MacroEvent('down', 4, dx=1)):
            with self.subTest(event=event), self.assertRaises(ValidationError):
                encode_macro(Macro(1, 'x', [event]))
        with self.assertRaises(ValidationError):
            encode_macro(Macro(1, 'x', [MacroEvent('down', 0xe7)]))

    def test_combination_vector_order_and_slot_bound(self):
        value = Binding('keyboard', [4, 5], 3)
        raw = encode_combination(value)
        self.assertEqual(raw[:-1], bytes.fromhex('08 80 01 00 80 02 00 81 04 00 81 05 00 40 01 00 40 02 00 41 05 00 41 04 00'))
        self.assertEqual(sum(raw) & 255, 0x55)
        self.assertEqual(decode_combination(raw), value)
        self.assertEqual(len(encode_combination(Binding('keyboard', [4], 15))), 32)
        for value in (Binding('keyboard', [4, 5], 15), Binding('keyboard', [4, 5, 6, 7]), Binding('keyboard')):
            with self.assertRaises(ValidationError):
                encode_combination(value)

    def test_consumer_usage_vector(self):
        raw = encode_combination(Binding('consumer:00e9'))
        self.assertEqual(raw, bytes.fromhex('02 82 e9 00 42 e9 00 bd'))
        self.assertEqual(decode_combination(raw), Binding('consumer:00e9'))

    def test_unmapped_keyboard_usages_rejected(self):
        for usage in (0x32, 0x64):
            with self.subTest(usage=usage), self.assertRaises(ValidationError):
                encode_macro(Macro(1, 'x', [MacroEvent('down', usage)]))

    def test_unchanged_existing_macro_survives_apply_without_library(self):
        service = MouseService(demo=True)
        settings = service.connect(service.scan()[0]).settings
        settings.bindings[0] = Binding('macro', macro_id=1)
        macro = Macro(1, 'x', [MacroEvent('down', 4)])
        service.apply(settings, [macro])
        service.disconnect()
        settings = service.connect(service.scan()[0]).settings
        settings.debounce_ms = 12
        snapshot = service.apply(settings)
        self.assertEqual(snapshot.settings.bindings, settings.bindings)
        service.disconnect()

    def test_no_unchanged_auxiliary_writes(self):
        service = MouseService(demo=True)
        settings = service.connect(service.scan()[0]).settings
        settings.bindings[0] = Binding('keyboard', [4])
        service.apply(settings)
        count = service.transport.write_count
        service.apply(settings)
        self.assertEqual(service.transport.write_count, count)
        service.disconnect()

    def test_connected_macro_library_matches_bindings_and_can_save_workspace(self):
        service = MouseService(demo=True)
        settings = service.connect(service.scan()[0]).settings
        settings.bindings[2] = Binding('macro', macro_id=7)
        service.apply(settings, [Macro(7, 'x', [MacroEvent('down', 4)], 'held')])
        service.disconnect()
        count = service.transport.write_count
        settings = service.connect(service.scan()[0]).settings
        self.assertEqual(service.transport.write_count, count)
        macros = service.macros
        self.assertEqual(macros[0].id, settings.bindings[2].macro_id)
        self.assertEqual(macros[0].loop_mode, 'held')
        self.assertEqual(macros[0].events, [MacroEvent('down', 4)])
        macros[0].name = 'changed externally'
        self.assertEqual(service.macros[0].name, 'x')
        workspace = default_workspace()
        workspace.profiles[0].settings = settings
        workspace.macros = service.macros
        with tempfile.TemporaryDirectory() as root:
            store = ProfileStore(Path(root))
            store.save(workspace)
            self.assertEqual(store.load(), workspace)
        service.disconnect()

    def test_unsupported_macro_slot_becomes_preservable_unknown_binding(self):
        service = MouseService(demo=True)
        settings = service.connect(service.scan()[0]).settings
        settings.bindings[0] = Binding('macro', macro_id=7)
        service.apply(settings, [Macro(7, 'x', [MacroEvent('down', 4)])])
        service.transport.memory[0x320] = 0xff
        settings = service.refresh().settings
        self.assertTrue(settings.bindings[0].action.startswith('unknown:'))
        self.assertEqual(service.macros, [])
        settings.debounce_ms = 12
        self.assertEqual(service.apply(settings).settings.bindings, settings.bindings)
        service.disconnect()

    def test_shared_macro_is_one_library_entry_with_matching_binding_ids(self):
        service = MouseService(demo=True)
        settings = service.connect(service.scan()[0]).settings
        settings.bindings[0] = Binding('macro', macro_id=7)
        settings.bindings[1] = Binding('macro', macro_id=7)
        service.apply(settings, [Macro(7, 'x', [MacroEvent('down', 4)])])
        self.assertEqual(len(service.macros), 1)
        self.assertEqual(service.macros[0].id, 7)
        service.disconnect()

    def test_service_applies_auxiliary_before_matrix_and_reads_back(self):
        service = MouseService(demo=True)
        old = service.connect(service.scan()[0])
        draft = copy.deepcopy(old.settings)
        draft.bindings[3] = Binding('macro', macro_id=7)
        draft.bindings[4] = Binding('keyboard', [4], 1)
        macro = Macro(7, 'Test', [MacroEvent('down', 4, 12), MacroEvent('up', 4)])
        snapshot = service.apply(draft, [macro])
        self.assertEqual(snapshot.settings.bindings, draft.bindings)
        memory = service.transport.memory
        self.assertEqual(memory[0x900:0x900 + 46], encode_macro(macro))
        writes = [int.from_bytes(p[3:5], 'big') for p in service.transport.sent if p[1] == 7]
        self.assertLess(writes.index(0x900), writes.index(0x70))
        self.assertEqual(service.refresh().settings.bindings, draft.bindings)
        service.disconnect()
