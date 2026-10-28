import json
import os
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from vela.domain import Binding, Macro, MacroEvent, ValidationError, FileFormatError, default_workspace
from vela.storage import ProfileStore, MAX_JSON_BYTES
from vela.formats import save_profile, load_profile


class StorageTests(unittest.TestCase):
    def test_roundtrip_four_profiles_unicode_and_macros(self):
        with tempfile.TemporaryDirectory() as root:
            store = ProfileStore(Path(root))
            value = store.load()
            self.assertEqual(len(value.profiles), 4)
            value.profiles[0].name = '配置 🚀 / arbitrary'
            value.macros = [Macro(12, 'Ç / 🚀', [MacroEvent('down', 4)])]
            value.profiles[0].settings.bindings[1] = Binding('macro', macro_id=12)
            store.save(value)
            self.assertEqual(store.load(), value)
            self.assertEqual(json.loads(store.path.read_text(encoding='utf-8'))['schema_version'], 1)

    def test_workspace_saved_before_the_dpi_light_field_still_loads(self):
        from vela.storage import settings_from_dict
        from dataclasses import asdict
        from vela.domain import MouseSettings, DpiEffect
        old = asdict(MouseSettings())
        del old['dpi_effect']
        self.assertIsNone(settings_from_dict(old).dpi_effect)
        saved = asdict(MouseSettings(dpi_effect=DpiEffect(1, 7, 3)))
        self.assertEqual(settings_from_dict(saved).dpi_effect, DpiEffect(1, 7, 3))

    def test_invalid_json_bounds_and_types(self):
        with tempfile.TemporaryDirectory() as root:
            store = ProfileStore(Path(root))
            store.save(default_workspace())
            valid = json.loads(store.path.read_text(encoding='utf-8'))
            for mutate in (lambda d: d.update(schema_version=True), lambda d: d.update(schema_version=2),
                           lambda d: d.update(selected_profile=True), lambda d: d.update(profiles=[]),
                           lambda d: d['profiles'][0]['settings'].update(debounce_ms=False),
                           lambda d: d['profiles'][0].update(name='x' * 129),
                           lambda d: d.update(unrecognized=1)):
                document = json.loads(json.dumps(valid))
                mutate(document)
                store.path.write_text(json.dumps(document), encoding='utf-8')
                with self.subTest(document=document), self.assertRaises(FileFormatError):
                    store.load()
            store.path.write_bytes(b' ' * (MAX_JSON_BYTES + 1))
            with self.assertRaises(FileFormatError):
                store.load()

    def test_write_failure_keeps_previous_file_and_cleans_temporary(self):
        with tempfile.TemporaryDirectory() as root:
            store = ProfileStore(Path(root))
            value = default_workspace()
            store.save(value)
            previous = store.path.read_bytes()
            value.selected_profile = 1
            with patch('vela.storage.os.replace', side_effect=OSError('disk failure')):
                with self.assertRaises(OSError):
                    store.save(value)
            self.assertEqual(store.path.read_bytes(), previous)
            self.assertEqual(list(Path(root).iterdir()), [store.path])

    def test_xdg_default_path_and_validation_before_write(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {'XDG_CONFIG_HOME': root}):
            store = ProfileStore()
            self.assertEqual(store.path, Path(root) / 'vela' / 'workspace.json')
            value = default_workspace()
            value.profiles[0].settings.bindings[0] = Binding('macro', macro_id=999)
            with self.assertRaises(ValidationError):
                store.save(value)
            self.assertFalse(store.path.exists())

    def test_wheel_codes_cannot_enter_native_library(self):
        value = default_workspace()
        value.macros = [Macro(1, 'x', [MacroEvent('down', 0xf5)])]
        with self.assertRaises(ValidationError):
            value.validate()

    def test_native_roundtrip_retains_opaque_legacy_export_metadata(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'legacy.jma'
            value = default_workspace()
            settings = value.profiles[0].settings
            settings.bindings = [Binding('dpi_cycle') for _ in range(6)]
            save_profile(path, settings, [])
            raw = bytearray(path.read_bytes())
            raw[0x100:0x104] = b'\x12\x34\x56\x78'
            path.write_bytes(raw)
            settings, macros = load_profile(path)
            value.profiles[0].settings = settings
            value.macros = macros
            store = ProfileStore(Path(root) / 'native')
            store.save(value)
            restored = store.load()
            save_profile(path, restored.profiles[0].settings, restored.macros)
            self.assertEqual(path.read_bytes(), raw)
            restored.profiles[0].settings.debounce_ms = 22
            store.save(restored)
            restored = store.load()
            save_profile(path, restored.profiles[0].settings, restored.macros)
            self.assertEqual(path.read_bytes()[0x100:0x104], b'\x12\x34\x56\x78')

    def test_legacy_preservation_metadata_is_strictly_validated(self):
        with tempfile.TemporaryDirectory() as root:
            store = ProfileStore(Path(root))
            store.save(default_workspace())
            source = json.loads(store.path.read_text(encoding='utf-8'))
            for legacy in (None, {}, {'profile': '00'}, {'profile': 'zz' * 2116},
                           {'profile': '00' * 2116}, {'profile': '00' * 2116, 'extra': 1}):
                document = json.loads(json.dumps(source))
                document['profiles'][0]['legacy'] = legacy
                store.path.write_text(json.dumps(document), encoding='utf-8')
                with self.subTest(legacy=legacy), self.assertRaises(FileFormatError):
                    store.load()
