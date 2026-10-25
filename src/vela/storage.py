"""Versioned native JSON, independent of legacy Windows memory layouts."""
from dataclasses import asdict, fields
import json
import os
from pathlib import Path
import tempfile

from .domain import (Binding, DpiStage, FileFormatError, LightingSettings, Macro,
                     MacroEvent, MouseSettings, Profile, Workspace, ValidationError,
                     default_workspace)

MAX_JSON_BYTES = 32 * 1024 * 1024


def atomic_write(path, data):
    """Replace in the same directory only after a full write and file fsync."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f'.{path.name}.', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def bounded_read(path, maximum):
    with Path(path).open('rb') as stream:
        data = stream.read(maximum + 1)
    if len(data) > maximum:
        raise FileFormatError('File exceeds its supported size limit.')
    return data


def _object(cls, data, converters=None):
    if type(data) is not dict or set(data) != {item.name for item in fields(cls)}:
        raise FileFormatError(f'Invalid {cls.__name__} fields.')
    converted = dict(data)
    for key, convert in (converters or {}).items():
        converted[key] = convert(data[key])
    return cls(**converted)


def _list(data, converter, maximum):
    if type(data) is not list or len(data) > maximum:
        raise FileFormatError('Invalid list or too many entries.')
    return [converter(item) for item in data]


def settings_from_dict(data):
    result = _object(MouseSettings, data, {
        'stages': lambda value: _list(value, lambda d: _object(DpiStage, d), 6),
        'lighting': lambda value: _object(LightingSettings, value),
        'bindings': lambda value: _list(value, lambda d: _object(Binding, d), 6),
    })
    result.validate()
    return result


def _no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise FileFormatError('Duplicate JSON field.')
        result[key] = value
    return result


def _hex_blob(value, length):
    if not isinstance(value, str) or len(value) != length * 2:
        raise FileFormatError('Invalid legacy preservation data length.')
    try:
        raw = bytes.fromhex(value)
    except ValueError as exc:
        raise FileFormatError('Invalid legacy preservation data.') from exc
    if len(raw) != length:
        raise FileFormatError('Invalid legacy preservation data.')
    return raw


def _native_macro(data):
    if type(data) is not dict:
        raise FileFormatError('Invalid macro object.')
    document = dict(data)
    has_legacy = 'legacy' in document
    legacy = document.pop('legacy', None)
    result = _object(Macro, document, {
        'events': lambda e: _list(e, lambda v: _object(MacroEvent, v), 70)})
    if has_legacy:
        from .formats import _macro_from_raw
        original = _macro_from_raw(_hex_blob(legacy, 834))
        result._legacy_macro = original._legacy_macro
    return result


def _native_profile(data, macros):
    if type(data) is not dict:
        raise FileFormatError('Invalid profile object.')
    document = dict(data)
    has_legacy = 'legacy' in document
    legacy = document.pop('legacy', None)
    result = _object(Profile, document, {'settings': settings_from_dict})
    if has_legacy:
        if type(legacy) is not dict or set(legacy) not in ({'profile'}, {'profile', 'jma'}):
            raise FileFormatError('Invalid legacy preservation fields.')
        from .formats import _profile_from_raw, _jma_from_raw
        profile_raw = _hex_blob(legacy['profile'], 2116)
        if 'jma' in legacy:
            jma_raw = _hex_blob(legacy['jma'], 10456)
            if jma_raw[:2116] != profile_raw:
                raise FileFormatError('Inconsistent legacy preservation blocks.')
            original, _ = _jma_from_raw(jma_raw)
            result.settings._legacy_jma = original._legacy_jma
        else:
            original = _profile_from_raw(profile_raw, macros)
        result.settings._legacy_profile = original._legacy_profile
    return result


class ProfileStore:
    def __init__(self, root=None):
        if root is None:
            xdg = os.environ.get('XDG_CONFIG_HOME')
            base = Path(xdg) if xdg and Path(xdg).is_absolute() else Path.home() / '.config'
            root = base / 'vela'
        self.path = Path(root) / 'workspace.json'

    def load(self):
        if not self.path.exists():
            return default_workspace()
        try:
            document = json.loads(bounded_read(self.path, MAX_JSON_BYTES).decode('utf-8'), object_pairs_hook=_no_duplicates)
            if type(document) is not dict or set(document) != {'schema_version', 'profiles', 'macros', 'selected_profile'}:
                raise FileFormatError('Invalid workspace fields.')
            if type(document['schema_version']) is not int or document['schema_version'] != 1:
                raise FileFormatError('Unsupported native JSON schema version.')
            macros = _list(document['macros'], _native_macro, 2000)
            workspace = Workspace(_list(document['profiles'], lambda d: _native_profile(d, macros), 4),
                                  macros, document['selected_profile'])
            workspace.validate()
            return workspace
        except (UnicodeError, ValueError, TypeError, RecursionError, ValidationError) as exc:
            raise FileFormatError(f'Invalid native workspace: {exc}') from exc

    def save(self, workspace):
        if not isinstance(workspace, Workspace):
            raise ValidationError('Invalid workspace.')
        workspace.validate()
        document = {'schema_version': 1, **asdict(workspace)}
        for profile, target in zip(workspace.profiles, document['profiles']):
            source = getattr(profile.settings, '_legacy_profile', None)
            if source:
                target['legacy'] = {'profile': source[0].hex()}
                jma = getattr(profile.settings, '_legacy_jma', None)
                if jma:
                    target['legacy']['jma'] = jma[0].hex()
        for macro, target in zip(workspace.macros, document['macros']):
            source = getattr(macro, '_legacy_macro', None)
            if source:
                target['legacy'] = source[0].hex()
        data = json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False).encode('utf-8')
        if len(data) > MAX_JSON_BYTES:
            raise ValidationError('Workspace exceeds storage size limit.')
        atomic_write(self.path, data)
