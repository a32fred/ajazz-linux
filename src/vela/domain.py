"""Dependency-free application values and validation boundaries."""
from dataclasses import dataclass, field
import re


class VelaError(Exception):
    """An error that can be presented to the user."""


class ValidationError(VelaError):
    pass


class ProtocolError(VelaError):
    pass


class DeviceError(VelaError):
    pass


class FileFormatError(VelaError):
    pass


class ApplyError(DeviceError):
    """Application stopped; the device may contain some requested changes."""
    def __init__(self, message, completed_writes=0, partial=True):
        super().__init__(message)
        self.completed_writes = completed_writes
        self.partial = partial


def integer(value, minimum, maximum, name):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValidationError(f'{name} must be an integer from {minimum} to {maximum}.')
    return value


def color(value):
    if not isinstance(value, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', value):
        raise ValidationError('Color must be #RRGGBB.')
    return value


def dpi(value):
    integer(value, 50, 26000, 'DPI')
    if value % 50:
        raise ValidationError('DPI must be a multiple of 50.')
    return value


@dataclass
class DpiStage:
    x: int
    y: int
    color: str
    enabled: bool = True

    def validate(self):
        dpi(self.x)
        dpi(self.y)
        color(self.color)
        if self.enabled is not True:
            raise ValidationError('Individual stage disabling is unavailable; remove the stage instead.')


@dataclass
class LightingSettings:
    mode: int = 1
    brightness: int = 6
    speed: int = 6
    color: str = '#ff00ff'

    def validate(self):
        integer(self.mode, 0, 6, 'Lighting mode')
        if self.mode not in (0, 1, 2, 4, 6):
            raise ValidationError('This lighting mode is unavailable on AJ199.')
        integer(self.brightness, 1, 10, 'Brightness')
        integer(self.speed, 1, 10, 'Speed')
        color(self.color)


@dataclass
class DpiEffect:
    """Scroll wheel light (EEPROM 0x4C): brightness step 1..10; mode and param are as the mouse
    reported them, because only modes 0 to 2 and breathing speed 1 to 8 are known."""
    mode: int = 1
    brightness: int = 10
    param: int = 3

    def validate(self):
        integer(self.mode, 0, 255, 'DPI light mode')
        integer(self.brightness, 1, 10, 'DPI light brightness')
        integer(self.param, 0, 255, 'DPI light parameter')


@dataclass
class Binding:
    action: str
    keys: list[int] = field(default_factory=list)
    modifiers: int = 0
    macro_id: int | None = None

    def validate(self):
        if not isinstance(self.action, str) or not self.action:
            raise ValidationError('A button action is required.')
        if not isinstance(self.keys, list) or len(self.keys) > 3:
            raise ValidationError('A combination supports at most three keys.')
        for key in self.keys:
            integer(key, 1, 255, 'Keyboard usage')
        integer(self.modifiers, 0, 15, 'Modifiers')
        if self.macro_id is not None:
            integer(self.macro_id, 0, 0xffffffff, 'Macro ID')


@dataclass
class MacroEvent:
    """HID usage code; E0..E7 modifiers and reserved F0..F4 mouse buttons."""
    kind: str
    code: int = 0
    delay_ms: int = 0
    dx: int = 0
    dy: int = 0

    def validate(self):
        if self.kind not in ('down', 'up', 'move'):
            raise ValidationError('Unsupported macro event; wheel macros are unavailable.')
        integer(self.code, 0, 255, 'Event code')
        if self.kind != 'move' and self.code in (0xf5, 0xf6):
            raise ValidationError('Wheel macros are unavailable.')
        integer(self.delay_ms, 0, 65535, 'Event delay')
        integer(self.dx, -32768, 32767, 'Horizontal movement')
        integer(self.dy, -32768, 32767, 'Vertical movement')


@dataclass
class Macro:
    id: int
    name: str
    events: list[MacroEvent]
    loop_mode: str = 'count'
    repeat: int = 1
    auto_delay: bool = True

    def validate(self):
        integer(self.id, 0, 0xffffffff, 'Macro ID')
        if not isinstance(self.name, str) or not self.name or '\0' in self.name:
            raise ValidationError('Macro name must contain 1 to 39 UTF-16 units without NUL.')
        try:
            name_units = len(self.name.encode('utf-16-le')) // 2
        except UnicodeEncodeError as exc:
            raise ValidationError('Macro name contains invalid Unicode.') from exc
        if name_units > 39:
            raise ValidationError('Macro name exceeds 39 UTF-16 units.')
        if not isinstance(self.events, list) or len(self.events) > 70:
            raise ValidationError('A macro supports at most 70 events.')
        for event in self.events:
            if not isinstance(event, MacroEvent):
                raise ValidationError('Invalid macro event.')
            event.validate()
        if self.loop_mode not in ('count', 'held', 'toggle'):
            raise ValidationError('Invalid macro loop mode.')
        integer(self.repeat, 1, 250, 'Repeat count')
        if type(self.auto_delay) is not bool:
            raise ValidationError('Automatic delay must be boolean.')


def default_stages():
    return [DpiStage(value, value, shade) for value, shade in
            ((800, '#ff5050'), (1600, '#50ff50'), (2400, '#5070ff'))]


def default_bindings():
    return [Binding(action) for action in ('left', 'right', 'middle', 'back', 'forward', 'dpi_cycle')]


@dataclass
class MouseSettings:
    stages: list[DpiStage] = field(default_factory=default_stages)
    active_stage: int = 0
    polling_hz: int = 1000
    debounce_ms: int = 8
    lod_mm: int = 1
    angle_snapping: bool = False
    ripple: bool = False
    light_on: bool = True
    light_off_while_moving: bool = True
    idle_seconds: int = 60
    lighting: LightingSettings = field(default_factory=LightingSettings)
    bindings: list[Binding] = field(default_factory=default_bindings)
    dpi_effect: DpiEffect | None = None

    def validate(self):
        if not isinstance(self.stages, list) or not 1 <= len(self.stages) <= 6:
            raise ValidationError('Choose from one to six DPI stages.')
        for stage in self.stages:
            if not isinstance(stage, DpiStage):
                raise ValidationError('Invalid DPI stage.')
            stage.validate()
        integer(self.active_stage, 0, len(self.stages) - 1, 'Active stage')
        integer(self.polling_hz, 125, 1000, 'Polling rate')
        if self.polling_hz not in (125, 250, 500, 1000):
            raise ValidationError('Polling rate must be 125, 250, 500 or 1000 Hz.')
        integer(self.debounce_ms, 0, 30, 'Debounce')
        integer(self.lod_mm, 1, 2, 'Lift-off distance')
        integer(self.idle_seconds, 10, 2400, 'Idle seconds')
        if self.idle_seconds not in (10, 30, 60, 300, 600, 900, 1200, 1500, 1800, 2100, 2400):
            raise ValidationError('Unsupported idle duration.')
        for name in ('angle_snapping', 'ripple', 'light_on', 'light_off_while_moving'):
            if type(getattr(self, name)) is not bool:
                raise ValidationError(f'{name} must be boolean.')
        if not isinstance(self.lighting, LightingSettings):
            raise ValidationError('Invalid lighting settings.')
        self.lighting.validate()
        if self.dpi_effect is not None:
            if not isinstance(self.dpi_effect, DpiEffect):
                raise ValidationError('Invalid DPI light settings.')
            self.dpi_effect.validate()
        if not isinstance(self.bindings, list) or len(self.bindings) != 6:
            raise ValidationError('Exactly six physical button bindings are required.')
        for binding in self.bindings:
            if not isinstance(binding, Binding):
                raise ValidationError('Invalid button binding.')
            binding.validate()


@dataclass(frozen=True)
class DeviceInfo:
    id: str
    name: str
    vid: int
    pid: int
    command_path: bytes | str
    notification_path: bytes | str | None
    serial: str = ''


@dataclass
class DeviceSnapshot:
    device: DeviceInfo
    settings: MouseSettings
    battery_percent: int | None
    current_profile: int
    firmware: str | None
    charging: bool | None


def validate_name(value, maximum=128):
    if not isinstance(value, str) or not value or '\0' in value or len(value) > maximum:
        raise ValidationError(f'Name requires 1 to {maximum} Unicode characters without NUL.')
    try:
        value.encode('utf-8')
    except UnicodeError as exc:
        raise ValidationError('Name contains invalid Unicode.') from exc


@dataclass
class Profile:
    name: str
    settings: MouseSettings = field(default_factory=MouseSettings)

    def validate(self):
        validate_name(self.name)
        if not isinstance(self.settings, MouseSettings):
            raise ValidationError('Invalid profile settings.')
        self.settings.validate()


@dataclass
class Workspace:
    profiles: list[Profile]
    macros: list[Macro] = field(default_factory=list)
    selected_profile: int = 0

    def validate(self):
        if not isinstance(self.profiles, list) or len(self.profiles) != 4:
            raise ValidationError('Exactly four local profiles are required.')
        integer(self.selected_profile, 0, 3, 'Selected profile')
        if not isinstance(self.macros, list) or len(self.macros) > 2000:
            raise ValidationError('At most 2000 macros are supported.')
        ids = set()
        for macro in self.macros:
            if not isinstance(macro, Macro):
                raise ValidationError('Invalid macro.')
            macro.validate()
            if macro.id in ids:
                raise ValidationError('Macro IDs must be unique.')
            ids.add(macro.id)
        for profile in self.profiles:
            if not isinstance(profile, Profile):
                raise ValidationError('Invalid profile.')
            profile.validate()
            for binding in profile.settings.bindings:
                if binding.action == 'macro' and binding.macro_id not in ids:
                    raise ValidationError('Profile references a missing macro.')


def default_workspace():
    return Workspace([Profile(f'Profile {index + 1}') for index in range(4)])
