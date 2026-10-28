import copy
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from vela.domain import Binding, DpiStage, LightingSettings, MouseSettings, ApplyError, DeviceError, ProtocolError, ValidationError
from vela.protocol import ProtocolClient
from vela.simulator import SimulatedTransport
from vela.service import MouseService


class ServiceTests(unittest.TestCase):
    def test_auto_connect_skips_unavailable_connection_without_writes(self):
        from dataclasses import replace
        unavailable = replace(self.transport.device, id='inactive', command_path='inactive')
        self.transport.sent.clear()
        result = self.service.connect_first([unavailable, self.transport.device])
        self.assertEqual(result.device, self.transport.device)
        self.assertEqual(self.writes(), [])

    def setUp(self):
        self.transport = SimulatedTransport()
        self.service = MouseService(transport=self.transport)
        self.snapshot = self.service.connect(self.service.scan()[0])

    def tearDown(self):
        self.service.disconnect()

    def draft(self):
        return copy.deepcopy(self.snapshot.settings)

    def writes(self):
        return [report for report in self.transport.sent if report[1] == 7]

    def test_demo_readback_and_defaults_are_not_written_on_connect(self):
        self.assertTrue(self.service.connected)
        self.assertEqual(self.snapshot.settings.polling_hz, 1000)
        self.assertEqual(self.snapshot.battery_percent, 87)
        self.assertIsNone(self.snapshot.firmware)
        self.assertEqual(self.writes(), [])
        self.snapshot.settings.stages[0].x = 50
        self.assertEqual(self.service.refresh().settings.stages[0].x, 800)

    def test_differential_apply_and_exact_dpi_record(self):
        draft = self.draft()
        draft.stages[0].x = draft.stages[0].y = 26000
        result = self.service.apply(draft)
        self.assertEqual(result.settings.stages[0].x, 26000)
        self.assertEqual(bytes(self.transport.memory[12:16]), bytes.fromhex('07 07 88 bf'))
        self.assertEqual(len(self.writes()), 1)
        self.service.apply(result.settings)
        self.assertEqual(len(self.writes()), 1)

    def test_expand_stages_before_count_then_active(self):
        draft = self.draft()
        draft.stages.append(DpiStage(5000, 5000, '#ffffff'))
        draft.active_stage = 3
        self.service.apply(draft)
        addresses = [int.from_bytes(report[3:5], 'big') for report in self.writes()]
        self.assertLess(addresses.index(24), addresses.index(2))
        self.assertLess(addresses.index(2), addresses.index(4))

    def test_shrink_reduces_active_index_before_count(self):
        draft = self.draft()
        draft.active_stage = 2
        self.service.apply(draft)
        self.transport.sent.clear()
        draft.stages = draft.stages[:1]
        draft.active_stage = 0
        self.service.apply(draft)
        addresses = [int.from_bytes(report[3:5], 'big') for report in self.writes()]
        self.assertLess(addresses.index(4), addresses.index(2))

    def test_polling_behavior_and_lighting_edits(self):
        draft = self.draft()
        draft.polling_hz = 125
        draft.debounce_ms = 30
        draft.lod_mm = 2
        draft.angle_snapping = True
        draft.ripple = True
        draft.light_on = False
        draft.light_off_while_moving = False
        draft.idle_seconds = 300
        draft.lighting = LightingSettings(mode=2, brightness=10, speed=1, color='#123456')
        result = self.service.apply(draft)
        self.assertEqual(result.settings, draft)
        self.assertEqual(bytes(self.transport.memory[0:2]), bytes.fromhex('08 4d'))
        self.assertEqual(bytes(self.transport.memory[0xa0:0xa7]), bytes.fromhex('01 12 34 56 ff ff ba'))
        self.assertEqual(bytes(self.transport.memory[0xb5:0xb9]), b'\xff' * 4)

    def test_lighting_off_preserves_existing_color_tables(self):
        before = bytes(self.transport.memory[0xa1:0xa6])
        draft = self.draft()
        draft.lighting = LightingSettings(mode=0, color='#000000', speed=10, brightness=1)
        result = self.service.apply(draft)
        self.assertEqual(bytes(self.transport.memory[0xa1:0xa6]), before)
        self.assertEqual(result.settings.lighting.mode, 0)
        self.assertEqual(result.settings.lighting.color, '#ff00ff')

    def test_physical_forward_back_masks(self):
        draft = self.draft()
        draft.bindings[3] = Binding('forward')
        draft.bindings[4] = Binding('back')
        result = self.service.apply(draft)
        self.assertEqual(result.settings.bindings, draft.bindings)
        self.assertEqual(bytes(self.transport.memory[0x70:0x74]), bytes.fromhex('01 08 00 4c'))
        self.assertEqual(bytes(self.transport.memory[0x6c:0x70]), bytes.fromhex('01 10 00 44'))

    def test_unsupported_binding_fails_before_writes(self):
        draft = self.draft()
        draft.polling_hz = 125
        draft.bindings[0] = Binding('right_double_click')
        with self.assertRaisesRegex(ValidationError, 'unavailable'):
            self.service.apply(draft)
        self.assertEqual(self.writes(), [])
        self.assertTrue(self.service.connected)

    def test_dpi_light_brightness_writes_only_its_record_and_is_read_back(self):
        from vela.protocol import encode_dpi_effect
        from vela.domain import DpiEffect
        self.transport.memory[0x4c:0x54] = encode_dpi_effect(DpiEffect(1, 1, 3))
        snapshot = self.service.refresh()
        self.assertEqual(snapshot.settings.dpi_effect, DpiEffect(1, 1, 3))
        draft = copy.deepcopy(snapshot.settings)
        draft.dpi_effect.brightness = 10
        self.transport.sent.clear()
        result = self.service.apply(draft)
        self.assertEqual(result.settings.dpi_effect.brightness, 10)
        self.assertEqual(bytes(self.transport.memory[0x4c:0x54]), bytes.fromhex('01 54 ff 56 03 52 00 55'))
        self.assertEqual(len(self.writes()), 1)

    def test_apply_without_a_reported_dpi_light_leaves_that_record_alone(self):
        self.assertIsNone(self.snapshot.settings.dpi_effect)
        before = bytes(self.transport.memory[0x4c:0x54])
        draft = self.draft()
        draft.polling_hz = 500
        self.service.apply(draft)
        self.assertEqual(bytes(self.transport.memory[0x4c:0x54]), before)

    def test_removing_the_last_left_click_is_refused_before_writes(self):
        draft = self.draft()
        draft.bindings[0] = Binding('right')
        with self.assertRaisesRegex(ValidationError, 'Left click'):
            self.service.apply(draft)
        self.assertEqual(self.writes(), [])

    def test_write_outside_known_regions_is_refused_before_writes(self):
        draft = self.draft()
        draft.polling_hz = 125
        self.service._binding_records = lambda settings, macros: {0x00f0: bytes(4)}
        with self.assertRaisesRegex(ValidationError, 'outside known EEPROM'):
            self.service.apply(draft)
        self.assertEqual(self.writes(), [])

    def test_backup_is_saved_before_writing_and_missing_backup_blocks_the_write(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as root:
            self.service.backup_dir = Path(root) / 'backups'
            before = bytes(self.transport.memory[0:0xb9])
            draft = self.draft()
            draft.stages[0].x = draft.stages[0].y = 1600
            self.service.apply(draft)
            files = list((Path(root) / 'backups').glob('eeprom-*.json'))
            self.assertEqual(len(files), 1)
            self.assertEqual(bytes.fromhex(json.loads(files[0].read_text())['regions']['0x0000']), before)
            blocker = Path(root) / 'not-a-folder'
            blocker.write_text('x')
            self.service.backup_dir = blocker / 'backups'
            writes = len(self.writes())
            draft.stages[0].x = draft.stages[0].y = 3200
            with self.assertRaisesRegex(DeviceError, 'nothing was written'):
                self.service.apply(draft)
            self.assertEqual(len(self.writes()), writes)

    def test_poll_is_light_and_one_failure_keeps_the_session(self):
        self.transport.sent.clear()
        snapshot = self.service.poll()
        self.assertEqual(snapshot.settings, self.snapshot.settings)
        self.assertEqual(snapshot.battery_percent, 87)
        self.assertEqual(len(self.transport.sent), 4)  # profile, battery, two header chunks
        self.transport.ignore_writes = False
        original = self.service._client.query
        def broken(*args, **kwargs):
            raise DeviceError('timeout')
        self.service._client.query = broken
        for _ in range(2):
            with self.assertRaises(DeviceError):
                self.service.poll()
            self.assertTrue(self.service.connected)
        with self.assertRaises(DeviceError):
            self.service.poll()
        self.assertFalse(self.service.connected)
        self.service._client.query = original

    def test_poll_reads_everything_again_when_the_header_changes(self):
        from vela.protocol import settings_records
        draft = self.draft()
        draft.active_stage = 1
        record = settings_records(draft)[4]
        self.transport.memory[4:4 + len(record)] = record  # active stage changed on the mouse
        snapshot = self.service.poll()
        self.assertEqual(snapshot.settings.active_stage, 1)

    def test_partial_failure_is_reported_and_handle_closed(self):
        draft = self.draft()
        draft.polling_hz = 500
        draft.debounce_ms = 10
        self.transport.fail_after_writes = 1
        with self.assertRaises(ApplyError) as caught:
            self.service.apply(draft)
        self.assertTrue(caught.exception.partial)
        self.assertEqual(caught.exception.completed_writes, 1)
        self.assertFalse(self.service.connected)
        self.assertFalse(self.transport.is_open)
        self.transport.fail_after_writes = None
        actual = self.service.connect(self.service.scan()[0])
        self.assertEqual(actual.settings.polling_hz, 500)
        self.assertEqual(actual.settings.debounce_ms, 8)

    def test_readback_mismatch_does_not_claim_success(self):
        self.transport.ignore_writes = True
        draft = self.draft()
        draft.polling_hz = 500
        with self.assertRaises(ApplyError):
            self.service.apply(draft)
        self.assertFalse(self.service.connected)

    def test_lost_first_ack_is_partial_even_with_zero_confirmed_writes(self):
        original_send = self.transport.send
        def lose_ack(data):
            result = original_send(data)
            if data[1] == 7:
                self.transport._queue.clear()
            return result
        self.transport.send = lose_ack
        draft = self.draft()
        draft.polling_hz = 500
        draft.debounce_ms = 12
        with self.assertRaises(ApplyError) as caught:
            self.service.apply(draft)
        self.assertEqual(caught.exception.completed_writes, 0)
        self.assertTrue(caught.exception.partial)
        self.assertEqual(self.transport.memory[0], 2)
        self.assertEqual(self.transport.memory[0xa9], 8)

    def test_unknown_binding_is_preserved_when_unchanged(self):
        self.transport.memory[0x60:0x64] = bytes.fromhex('aa bb cc 24')
        snapshot = self.service.refresh()
        self.assertEqual(snapshot.settings.bindings[0].action, 'unknown:ccbbaa')
        snapshot.settings.debounce_ms = 2
        self.service.apply(snapshot.settings)
        self.assertEqual(bytes(self.transport.memory[0x60:0x64]), bytes.fromhex('aa bb cc 24'))

    def test_failed_connect_closes_transport(self):
        self.service.disconnect()
        original_send = self.transport.send
        def lose_reply(data):
            result = original_send(data)
            self.transport._queue.clear()
            return result
        self.transport.send = lose_reply
        with self.assertRaises(DeviceError):
            self.service.connect(self.service.scan()[0])
        self.assertFalse(self.transport.is_open)
        self.assertFalse(self.service.connected)

    def test_eeprom_chunks_and_corrupt_register(self):
        client = ProtocolClient(self.transport)
        payload = bytes(range(23))
        client.write_eeprom(0x1234, payload)
        self.assertEqual(client.read_eeprom(0x1234, 23), payload)
        sizes = [report[5] for report in self.writes()]
        self.assertEqual(sizes, [10, 10, 3])
        self.transport.memory[1] = 0
        with self.assertRaises(ProtocolError):
            self.service.refresh()
        self.assertFalse(self.transport.is_open)

    def test_profile_switch_is_explicit_command_and_readback(self):
        result = self.service.switch_profile(2)
        self.assertEqual(result.current_profile, 2)
        self.assertTrue(any(report[1] == 16 and report[5:7] == b'\x01\x02' for report in self.transport.sent))
        with self.assertRaises(ValidationError):
            self.service.switch_profile(True)

    def test_core_imports_without_gui_or_hid(self):
        source = Path(__file__).resolve().parents[1] / 'src'
        code = "import sys; sys.path.insert(0, sys.argv[1]); import vela.service; assert 'hid' not in sys.modules; assert 'PySide6' not in sys.modules"
        result = subprocess.run([sys.executable, '-S', '-c', code, str(source)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
