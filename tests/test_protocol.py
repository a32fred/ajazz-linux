import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from vela.domain import DpiStage, Macro, MouseSettings, ValidationError, ProtocolError, DeviceError
from vela.protocol import build_frame, parse_frame, eeprom_frame, encode_dpi, decode_dpi, ProtocolClient


class QueueTransport:
    def __init__(self, responses=(), short_write=False):
        self.responses = list(responses)
        self.queue = []
        self.sent = []
        self.short_write = short_write

    def send(self, data):
        self.sent.append(data)
        self.queue.extend(self.responses)
        self.responses = []
        return 5 if self.short_write else len(data)

    def receive(self, timeout_ms):
        return self.queue.pop(0) if self.queue else b''


class ProtocolTests(unittest.TestCase):
    def test_captured_current_profile(self):
        self.assertEqual(build_frame(0x0e).hex(' '), '08 0e 00 00 00 00 00 00 00 00 00 00 00 00 00 00 3f')
        reply = parse_frame(bytes.fromhex('09 0e 00 00 00 01 00 00 00 00 00 00 00 00 00 00 3d'))
        self.assertEqual((reply.command, reply.status, reply.data), (14, 0, b'\0'))

    def test_eeprom_query_and_capture(self):
        self.assertEqual(eeprom_frame(8, 0, 10).hex(' '), '08 08 00 00 00 0a 00 00 00 00 00 00 00 00 00 00 3b')
        reply = parse_frame(bytes.fromhex('09 08 00 00 00 0a 01 54 03 52 00 55 00 55 00 55 91'))
        self.assertEqual(reply.data, bytes.fromhex('01 54 03 52 00 55 00 55 00 55'))
        self.assertEqual(eeprom_frame(8, 0x1234, 2)[3:6], bytes.fromhex('12 34 02'))

    def test_malformed_frames(self):
        good = bytes.fromhex('09 0e 00 00 00 01 00 00 00 00 00 00 00 00 00 00 3d')
        for value in (good[:-1], good + b'\0', good[:-1] + b'\0', bytes([8]) + good[1:]):
            with self.subTest(value=value), self.assertRaises(ProtocolError):
                parse_frame(value)

    def test_bad_status_is_error(self):
        transport = QueueTransport([build_frame(14, status=1, report_id=9)])
        with self.assertRaises(ProtocolError):
            ProtocolClient(transport).query(14)

    def test_notifications_and_wrong_replies_do_not_satisfy_query(self):
        transport = QueueTransport([build_frame(10, report_id=9)] * 100)
        with self.assertRaises(DeviceError):
            ProtocolClient(transport, timeout_ms=10, max_reports=8).query(14)
        self.assertEqual(len(transport.sent), 1)

    def test_read_rejects_wrong_address_or_size(self):
        for address, size in ((1, 2), (0, 1)):
            transport = QueueTransport([build_frame(8, address=address, size=size, data=b'\0' * size, report_id=9)])
            with self.subTest(address=address, size=size), self.assertRaises(DeviceError):
                ProtocolClient(transport, timeout_ms=10).read_eeprom(0, 2)

    def test_short_feature_write_is_error(self):
        with self.assertRaises(DeviceError):
            ProtocolClient(QueueTransport(short_write=True)).query(14)

    def test_old_queued_same_command_cannot_satisfy_new_request(self):
        transport = QueueTransport()
        transport.queue.append(bytes.fromhex('09 0e 00 00 00 01 00 00 00 00 00 00 00 00 00 00 3d'))
        with self.assertRaises(DeviceError):
            ProtocolClient(transport, timeout_ms=5).query(14)

    def test_malformed_and_unrelated_reports_before_valid_reply(self):
        transport = QueueTransport([b'\0', build_frame(3, report_id=9),
                                    bytes.fromhex('09 0e 00 00 00 01 00 00 00 00 00 00 00 00 00 00 3d')])
        self.assertEqual(ProtocolClient(transport).query(14).data, b'\0')

    def test_write_ack_only_needs_command_and_status_then_exact_readback(self):
        class AckTransport(QueueTransport):
            def send(self, data):
                self.sent.append(data)
                # No address/size echo was established for write ACKs.
                if data[1] == 7:
                    self.queue.append(build_frame(7, report_id=9))
                else:
                    self.queue.append(build_frame(8, address=0x1234, size=2, data=b'\x01\x54', report_id=9))
                return len(data)
        transport = AckTransport()
        ProtocolClient(transport).write_eeprom(0x1234, b'\x01\x54')
        self.assertEqual([r[1] for r in transport.sent], [7, 8])

    def test_eeprom_bounds_reject_before_sending(self):
        transport = QueueTransport()
        client = ProtocolClient(transport)
        for address, size in ((-1, 1), (65535, 2), (0, 0), (True, 2)):
            with self.subTest(address=address, size=size), self.assertRaises(ValidationError):
                client.read_eeprom(address, size)
        self.assertEqual(transport.sent, [])

    def test_dpi_high_bits_and_bounds(self):
        self.assertEqual(encode_dpi(26000, 26000), bytes.fromhex('07 07 88 bf'))
        self.assertEqual(encode_dpi(50, 12850), bytes.fromhex('00 00 40 15'))
        self.assertEqual(decode_dpi(bytes.fromhex('07 07 88 bf')), (26000, 26000))
        for bad in (0, 51, 26050, True, 50.0):
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                encode_dpi(bad, 50)

    def test_numeric_settings_validation(self):
        for key, value in (('active_stage', True), ('polling_hz', 2000), ('debounce_ms', 31), ('lod_mm', 0), ('idle_seconds', 11)):
            settings = MouseSettings()
            setattr(settings, key, value)
            with self.subTest(key=key), self.assertRaises(ValidationError):
                settings.validate()
        settings = MouseSettings(stages=[DpiStage(800, 800, '#ffffff', False)])
        with self.assertRaises(ValidationError):
            settings.validate()

    def test_macro_name_invalid_utf16_is_validation_error(self):
        with self.assertRaises(ValidationError):
            Macro(1, '\ud800', []).validate()


if __name__ == '__main__':
    unittest.main()
