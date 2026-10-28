import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from vela.domain import DeviceError
from vela.transport import HidTransport, descriptor_collections
from vela.protocol import ProtocolClient


# Two application collections, Input ID9 and Feature ID8, 16 payload bytes each.
DESCRIPTOR = bytes.fromhex('06 01 ff 09 00 a1 01 85 09 75 08 95 10 81 02 c0 '
                           '06 02 ff 09 02 a1 01 85 08 75 08 95 10 b1 02 c0')


def row(path, page, usage, serial='one', **extra):
    return dict(path=path, vendor_id=0x25a7, product_id=0xfa7b,
                usage_page=page, usage=usage, serial_number=serial, **extra)


class FakeHandle:
    def __init__(self, api):
        self.api = api
        self.closed = False

    def open_path(self, path):
        if path in self.api.denied:
            raise OSError('permission denied')
        self.path = path

    def close(self):
        self.closed = True

    def send_feature_report(self, data):
        return len(data)

    def set_nonblocking(self, value):
        self.nonblocking = value

    def read(self, size, timeout_ms=0):
        if timeout_ms == 0 and not getattr(self, 'nonblocking', False):
            raise RuntimeError('zero timeout hid_read would block')
        return []


class FakeHid:
    def __init__(self, rows):
        self.rows = rows
        self.denied = set()
        self.handles = []

    def enumerate(self, vid, pid):
        return [r for r in self.rows if r['vendor_id'] == vid and (not pid or r['product_id'] == pid)]

    def device(self):
        handle = FakeHandle(self)
        self.handles.append(handle)
        return handle


class DiscoveryTests(unittest.TestCase):
    def test_linux_uses_hidraw_backend_for_real_device_discovery(self):
        api = FakeHid([row(b'/dev/hidraw5', 0, 0, '')])
        with patch('sys.platform', 'linux'), patch(
                'vela.transport.importlib.import_module',
                side_effect=lambda name: api if name == 'hidraw' else FakeHid([])) as load:
            devices = HidTransport(descriptor_reader=lambda path: DESCRIPTOR).scan()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].command_path, b'/dev/hidraw5')
        self.assertIn('USB cable', devices[0].name)
        load.assert_called_once_with('hidraw')

    def test_windows_keeps_hid_backend(self):
        api = FakeHid([row(b'cmd', 0xff02, 2), row(b'in', 0xff01, 0)])
        with patch('sys.platform', 'win32'), patch(
                'vela.transport.importlib.import_module', return_value=api) as load:
            self.assertEqual(len(HidTransport().scan()), 1)
        load.assert_called_once_with('hid')

    def test_split_collections_and_small_reports(self):
        api = FakeHid([row(b'cmd', 0xff02, 2, feature_report_length=17),
                       row(b'in', 0xff01, 0, input_report_length=17),
                       row(b'small', 0xff04, 2, feature_report_length=8)])
        devices = HidTransport(hid_module=api).scan()
        self.assertEqual(len(devices), 1)
        self.assertEqual((devices[0].command_path, devices[0].notification_path), (b'cmd', b'in'))
        self.assertEqual(api.handles, [])  # discovery never opens a device

    def test_shared_linux_collection_from_descriptor(self):
        api = FakeHid([row(b'/dev/hidraw3', 0xff02, 2)])
        transport = HidTransport(hid_module=api, descriptor_reader=lambda path: DESCRIPTOR)
        device = transport.scan()[0]
        self.assertEqual(device.notification_path, b'/dev/hidraw3')
        transport.open(device)
        self.assertEqual(len(api.handles), 1)
        transport.close()
        self.assertTrue(api.handles[0].closed)

    def test_shared_path_with_multiple_enumeration_entries(self):
        api = FakeHid([row(b'/dev/hidraw1', 0xff02, 2), row(b'/dev/hidraw1', 0xff01, 0)])
        devices = HidTransport(hid_module=api, descriptor_reader=lambda path: None).scan()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].command_path, devices[0].notification_path)

    def test_multiple_serials_remain_separate(self):
        api = FakeHid([row(b'cmd1', 0xff02, 2), row(b'in1', 0xff01, 0),
                       row(b'cmd2', 0xff02, 2, 'two'), row(b'in2', 0xff01, 0, 'two')])
        devices = HidTransport(hid_module=api).scan()
        self.assertEqual(len(devices), 2)
        self.assertEqual(len({d.id for d in devices}), 2)
        self.assertEqual({(d.command_path, d.notification_path) for d in devices}, {(b'cmd1', b'in1'), (b'cmd2', b'in2')})

    def test_ambiguous_pair_is_not_guessed(self):
        api = FakeHid([row(b'cmd1', 0xff02, 2, ''), row(b'cmd2', 0xff02, 2, ''),
                       row(b'in1', 0xff01, 0, ''), row(b'in2', 0xff01, 0, '')])
        self.assertEqual(HidTransport(hid_module=api).scan(), [])

    def test_short_config_report_is_rejected(self):
        api = FakeHid([row(b'cmd', 0xff02, 2, feature_report_length=8), row(b'in', 0xff01, 0)])
        self.assertEqual(HidTransport(hid_module=api).scan(), [])

    def test_descriptor_bounds_and_report_lengths(self):
        collections = descriptor_collections(DESCRIPTOR)
        self.assertIn((0xff01, 0, 'input', 9, 17), collections)
        self.assertIn((0xff02, 2, 'feature', 8, 17), collections)
        for bad in (DESCRIPTOR[:-2], b'\x75', DESCRIPTOR * 200):
            with self.subTest(bad_length=len(bad)), self.assertRaises(DeviceError):
                descriptor_collections(bad)

    def test_missing_hidapi_is_actionable(self):
        with patch('vela.transport.importlib.import_module', side_effect=ImportError('missing')):
            with self.assertRaisesRegex(DeviceError, 'hidapi'):
                HidTransport().scan()

    def test_permission_failure_closes_partially_opened_pair(self):
        api = FakeHid([row(b'cmd', 0xff02, 2), row(b'in', 0xff01, 0)])
        transport = HidTransport(hid_module=api)
        device = transport.scan()[0]
        api.denied.add(b'cmd')
        with self.assertRaisesRegex(DeviceError, 'permission'):
            transport.open(device)
        self.assertTrue(all(h.closed for h in api.handles))

    def test_timeout_has_no_unbounded_read(self):
        api = FakeHid([row(b'cmd', 0xff02, 2), row(b'in', 0xff01, 0)])
        transport = HidTransport(hid_module=api)
        transport.open(transport.scan()[0])
        with self.assertRaisesRegex(DeviceError, 'Timed out'):
            ProtocolClient(transport, timeout_ms=5).query(14)
        transport.close()
        self.assertTrue(all(h.closed for h in api.handles))


if __name__ == '__main__':
    unittest.main()
