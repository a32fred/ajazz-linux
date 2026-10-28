# Changelog

## Unreleased - 0.1.0 preparation

No public release is recorded by this changelog yet.

### Added

- Original Vela branding and four native Qt pages: sensitivity, six button assignments, lighting and macros.
- HIDAPI service and explicitly labeled simulator sharing report codecs, readback checks and staged Apply behavior.
- Native JSON workspaces with four local profiles, atomic saves, and bounded legacy JMM/JMA/DCT compatibility.
- Focused macro recording, event editing, keyboard/media assignments and local profile import/export.
- Read-only scan/status CLI, Linux launcher/desktop/uaccess files and configured Linux CI.
- Scroll wheel light controls (effect, brightness, breathing speed) for the DPI light register, with the layout and hardware observations recorded in [hardware findings](docs/reference/HARDWARE_FINDINGS.md).
- EEPROM backup before every Apply, a lightweight status poll that tolerates a missed check, automatic reconnect that keeps the local draft, a refusal to remove the last Left click, and a write allowlist of known EEPROM regions.
- Number fields with large minus/plus buttons, hold-to-repeat and type-to-replace; dark theme with one accent.
- MIT license, dependency notices, contribution/security/conduct guidance and issue/PR templates.

### Validation and known limits

- Recorded local verification: 97 tests passed on Windows, plus source/wheel builds and demo CLI/native screenshots.
- Ubuntu 24.04 headless CI passed 97 tests, builds and demo rendering with Python 3.10 and 3.13 ([run](https://github.com/a32fred/vela-mouse-studio/actions/runs/40155183815)). Live desktops/udev integration, physical hardware writes, macro playback and persistence remain unvalidated.
- Legacy exports are limited to confirmed layouts; a fresh default profile cannot export to JMA. Native JSON supports the local domain. See [compatibility details](docs/reference/FORMAT_COMPATIBILITY.md).
- Native HID calls can stall beyond an application-controlled timeout. Local saves are explicit; concurrent instances do not merge changes.
