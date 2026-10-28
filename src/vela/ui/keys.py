"""Explicit Qt logical-key to USB HID usage mapping (never ASCII as HID)."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence

KEYS = {getattr(Qt.Key, f'Key_{chr(65 + n)}'): 4 + n for n in range(26)}
KEYS.update({getattr(Qt.Key, f'Key_{n}'): 0x1d + n for n in range(1, 10)})
KEYS[Qt.Key.Key_0] = 0x27
KEYS.update({getattr(Qt.Key, f'Key_F{n}'): 0x39 + n for n in range(1, 13)})
KEYS.update({Qt.Key.Key_Return: 0x28, Qt.Key.Key_Enter: 0x58, Qt.Key.Key_Escape: 0x29,
    Qt.Key.Key_Backspace: 0x2a, Qt.Key.Key_Tab: 0x2b, Qt.Key.Key_Space: 0x2c,
    Qt.Key.Key_Minus: 0x2d, Qt.Key.Key_Equal: 0x2e, Qt.Key.Key_BracketLeft: 0x2f,
    Qt.Key.Key_BracketRight: 0x30, Qt.Key.Key_Backslash: 0x31, Qt.Key.Key_Semicolon: 0x33,
    Qt.Key.Key_Apostrophe: 0x34, Qt.Key.Key_QuoteLeft: 0x35, Qt.Key.Key_Comma: 0x36,
    Qt.Key.Key_Period: 0x37, Qt.Key.Key_Slash: 0x38, Qt.Key.Key_CapsLock: 0x39,
    Qt.Key.Key_Print: 0x46, Qt.Key.Key_ScrollLock: 0x47, Qt.Key.Key_Pause: 0x48,
    Qt.Key.Key_Insert: 0x49, Qt.Key.Key_Home: 0x4a, Qt.Key.Key_PageUp: 0x4b,
    Qt.Key.Key_Delete: 0x4c, Qt.Key.Key_End: 0x4d, Qt.Key.Key_PageDown: 0x4e,
    Qt.Key.Key_Right: 0x4f, Qt.Key.Key_Left: 0x50, Qt.Key.Key_Down: 0x51,
    Qt.Key.Key_Up: 0x52, Qt.Key.Key_NumLock: 0x53, Qt.Key.Key_Menu: 0x65,
    Qt.Key.Key_Control: 0xe0, Qt.Key.Key_Shift: 0xe1, Qt.Key.Key_Alt: 0xe2,
    Qt.Key.Key_Meta: 0xe3, Qt.Key.Key_AltGr: 0xe6})


def hid_key(event):
    """Logical keys follow the active layout; Qt cannot identify modifier sides."""
    if event.modifiers() & Qt.KeyboardModifier.KeypadModifier:
        keypad = {Qt.Key.Key_0: 0x62, Qt.Key.Key_Period: 0x63,
                  Qt.Key.Key_Slash: 0x54, Qt.Key.Key_Asterisk: 0x55,
                  Qt.Key.Key_Minus: 0x56, Qt.Key.Key_Plus: 0x57,
                  Qt.Key.Key_Enter: 0x58, Qt.Key.Key_Equal: 0x67}
        keypad.update({getattr(Qt.Key, f'Key_{n}'): 0x58 + n for n in range(1, 10)})
        return keypad.get(event.key())
    return KEYS.get(event.key())


def key_name(code):
    mouse = {0xf0: 'Mouse left', 0xf1: 'Mouse right', 0xf2: 'Mouse middle',
             0xf3: 'Mouse forward', 0xf4: 'Mouse back'}
    if code in mouse:
        return mouse[code]
    names = {0xe0: 'Left Ctrl', 0xe1: 'Left Shift', 0xe2: 'Left Alt', 0xe3: 'Left Super',
             0xe4: 'Right Ctrl', 0xe5: 'Right Shift', 0xe6: 'Right Alt', 0xe7: 'Right Super'}
    if code in names:
        return names[code]
    key = next((key for key, usage in KEYS.items() if usage == code), None)
    name = QKeySequence(key).toString() if key is not None else f'0x{code:02X}'
    return f'Key {name}' if name.isdigit() else name


def parse_key(text):
    names = {key_name(code).casefold(): code for code in (*KEYS.values(), *range(0xe0, 0xe8), *range(0xf0, 0xf5))}
    if text.casefold() in names:
        return names[text.casefold()]
    return int(text, 16) if text.lower().startswith('0x') else int(text)
