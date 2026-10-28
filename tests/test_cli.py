import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from vela.cli import run
from vela.service import MouseService


class CliTests(unittest.TestCase):
    def test_scan_and_status_use_explicit_simulator(self):
        for command in ('scan', 'status'):
            output = io.StringIO()
            result = run([command, '--demo'], stdout=output)
            self.assertEqual(result, 0)
            document = json.loads(output.getvalue())
            self.assertTrue(document['demo'])
            if command == 'status':
                self.assertEqual(document['settings']['stages'][0]['x'], 800)
            else:
                self.assertEqual(len(document['devices']), 1)

    def test_dump_is_read_only_and_matches_the_simulated_memory(self):
        from vela.simulator import SimulatedTransport
        output = io.StringIO()
        self.assertEqual(run(['dump', '--demo', '--length', '0x20'], stdout=output), 0)
        document = json.loads(output.getvalue())
        self.assertEqual(bytes.fromhex(document['regions']['0x0000']), bytes(SimulatedTransport().memory[:0x20]))

    def test_listen_collects_reports_without_sending(self):
        output = io.StringIO()
        self.assertEqual(run(['listen', '--demo', '--seconds', '1'], stdout=output), 0)
        document = json.loads(output.getvalue())
        self.assertEqual((document['seconds'], document['reports']), (1, []))

    def test_restore_shows_a_plan_and_writes_only_with_yes(self):
        import tempfile
        from vela.simulator import SimulatedTransport
        transport = SimulatedTransport()
        class Shared(MouseService):
            def __init__(self, demo=False):
                super().__init__(transport=transport)
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'dump.json'
            dump = io.StringIO()
            self.assertEqual(run(['dump', '--length', '0x100'], service_factory=Shared, stdout=dump), 0)
            path.write_text(dump.getvalue())
            transport.memory[0xa9:0xab] = bytes([3, 0x55 - 3])  # debounce changed after the dump
            plan = io.StringIO()
            self.assertEqual(run(['restore', '--file', str(path)], service_factory=Shared, stdout=plan), 0)
            document = json.loads(plan.getvalue())
            self.assertFalse(document['written'])
            self.assertEqual([c['address'] for c in document['changes']], ['0x00a9'])
            self.assertEqual(transport.memory[0xa9], 3)
            error = io.StringIO()
            self.assertEqual(run(['restore', '--file', root + '/missing.json'], service_factory=Shared, stderr=error), 1)
            self.assertIn('Cannot use', error.getvalue())

    def test_status_requires_selection_if_multiple_devices(self):
        class Multiple(MouseService):
            def __init__(self, demo=False):
                super().__init__(demo=True)
            def scan(self):
                device = super().scan()[0]
                from dataclasses import replace
                return [device, replace(device, id='second')]
        error = io.StringIO()
        self.assertEqual(run(['status'], service_factory=Multiple, stderr=error), 1)
        self.assertIn('--device', error.getvalue())

    def test_module_cli_never_imports_qt(self):
        result = subprocess.run([sys.executable, '-c',
            "import sys; from vela.app import main; code=main(['--cli','status','--demo']); "
            "assert not any(k.startswith('PySide6') for k in sys.modules); sys.exit(code)"],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['demo'])

    def test_preview_save_failure_exits_nonzero_after_clean_shutdown(self):
        with tempfile.TemporaryDirectory() as root:
            result = subprocess.run([sys.executable, '-m', 'vela', '--demo', '--workspace', root,
                '--screenshot', root], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn('preview', result.stderr.lower())
            self.assertNotIn('QThread: Destroyed', result.stderr)

    def test_preview_startup_failure_exits_nonzero_without_waiting_forever(self):
        script = '''
from functools import partial
from unittest.mock import patch
from vela.app import main
from vela.ui.window import MainWindow
from vela.service import MouseService
from vela.simulator import SimulatedTransport
class BrokenDemo(SimulatedTransport):
    def scan(self):
        return []
with patch('vela.ui.window.MainWindow', partial(MainWindow, service=MouseService(transport=BrokenDemo()))):
    raise SystemExit(main(['--demo', '--screenshot', 'unused.png', '--workspace', __import__('sys').argv[1]]))
'''
        with tempfile.TemporaryDirectory() as root:
            result = subprocess.run([sys.executable, '-c', script, root], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn('preview', result.stderr.lower())
            self.assertNotIn('QThread: Destroyed', result.stderr)
