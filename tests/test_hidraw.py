import os
import select
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from vela.hidraw import Hidraw, HidrawDevice, hidiocsfeature


def node(root, name, hid_id, uniq='', hid_name='Compx 2.4G Dual Mode Mouse'):
    folder = root / name / 'device'
    folder.mkdir(parents=True)
    (folder / 'uevent').write_text(f'DRIVER=hid-generic\nHID_ID={hid_id}\nHID_NAME={hid_name}\nHID_UNIQ={uniq}\n')


class HidrawTests(unittest.TestCase):
    def test_ioctl_number_matches_the_kernel_macro_for_the_17_byte_report(self):
        self.assertEqual(hidiocsfeature(17), 0xC0114806)

    def test_enumerate_reads_sysfs_in_numeric_order_and_filters_by_vendor(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            node(root, 'hidraw10', '0003:000025A7:0000FA7C')
            node(root, 'hidraw5', '0003:000025A7:0000FA7B', uniq='abc')
            node(root, 'hidraw2', '0003:0000046D:0000C52B')
            (root / 'hidrawX' / 'device').mkdir(parents=True)  # not a hidraw node name
            node(root, 'hidraw7', 'garbage')
            rows = Hidraw(sysfs=root, dev='/dev').enumerate(0x25a7, 0)
        self.assertEqual([row['path'] for row in rows], [b'/dev/hidraw5', b'/dev/hidraw10'])
        self.assertEqual([row['product_id'] for row in rows], [0xfa7b, 0xfa7c])
        self.assertEqual(rows[0]['serial_number'], 'abc')

    def test_feature_report_goes_through_the_ioctl_and_read_never_blocks(self):
        calls = []
        read_end, write_end = os.pipe()
        try:
            device = HidrawDevice(ioctl=lambda fd, request, buffer: calls.append((request, bytes(buffer))) or len(buffer))
            device._fd = read_end
            self.assertEqual(device.send_feature_report(bytes([8]) + bytes(16)), 17)
            self.assertEqual(calls, [(0xC0114806, bytes([8]) + bytes(16))])
            self.assertEqual(device.read(17, 0), b'')  # nothing pending, returns at once
            os.write(write_end, bytes([9, 10]))
            self.assertEqual(device.read(17, 200), bytes([9, 10]))
        finally:
            os.close(write_end)
            device.close()
        self.assertIsNone(device._fd)


if __name__ == '__main__':
    unittest.main()
