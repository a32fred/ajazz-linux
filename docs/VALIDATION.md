# Delivery verification - 2026-10-24

## Fedora hardware check - 2026-10-27

The installed hidapi wheel exposes `hid` (libusb) and `hidraw` backends. The
libusb enumeration returned USB interface paths and zero usage metadata, so
Vela's descriptor-based discovery returned no devices. Linux now explicitly
loads `hidraw`; other platforms retain `hid`.

On Fedora 44, discovery found both 25a7:fa7b (wired mouse) and 25a7:fa7c
(receiver). Both configuration hidraw nodes could be opened without root.
The wired mouse completed the read-only CLI status operation, returning battery
100%, device profile 0 and EEPROM settings including a 1200 DPI stage.
The receiver was discovered but did not confirm an active mouse connection
during this check. Wireless status remains unvalidated. No settings writes,
reset, firmware update or persistence tests were performed.

Follow-up: the device picker now distinguishes the USB cable from the wireless
receiver. The UI polls settings every two seconds while connected, visible and
without pending edits or macro recording. Clean drafts follow device readback;
pending edits remain local. Simulator regressions cover periodic readback and
the absence of writes during polling. The user reported that physical settings
effects do not match the successful readback message; this remains unresolved.
A later read returned lighting color `#1c71d8`, which establishes stored data
only. It does not establish visible lighting, DPI response or button behavior.

The user subsequently confirmed physical operation of all Sensitivity controls.
Buttons, lighting and macro playback are not covered by that confirmation.
The button codec now follows the back/forward values in USB-P08 of CLONE_SPEC;
this corrects a source/spec discrepancy, pending a physical button check.
Shortcut capture replaces released keys instead of accumulating them, and both
shortcut and macro editors display key names. Macro recording is available
without first creating a library entry, with direct draft assignment to a side
or DPI button. Main lighting controls require explicit experimental opt-in;
writing a lighting register is not evidence of a visible effect on this variant.

Verification: 106 unit/UI tests passed with offscreen Qt. A separate simulated
click-through recorded A, assigned it to a side button, applied/read back the
macro and saved the workspace. Key names round-tripped for all supported Qt
mapping entries and modifier/mouse codes; Ctrl+K was captured in the assignment
dialog. The macro page was rendered at 1100x800 and 800x580. No physical button
or macro writes were performed for these changes.

Automatic refresh follow-up: periodic reads now use a separate background worker
operation. They do not set the foreground busy state, disable the editors, stop
macro recording or reload unchanged settings. Edits begun during a background
read are preserved, and foreground Apply queues after that read on the same
worker. Slow-transport UI regressions cover editing/recording during polling
and applying a change while polling. Lighting remains physically unconfirmed;
its experimental controls are hidden until explicitly enabled.

Connection/button usability follow-up: opening the application now scans and
tries each enumerated connection until one completes the existing connection
and settings reads. Enumeration order prefers the wired PID; inactive or
unavailable interfaces are skipped with their errors retained if all fail.
Manual device selection remains available. Saved and pending drafts are kept
on automatic connection. The six numbered areas of the mouse drawing are now
native, keyboard-focusable buttons that open the same assignment dialog as the
text list. Assignments still require explicit Apply.

Verification: 112 tests passed, including failed-first-interface fallback,
automatic connection in real UI mode with a simulator, pending-draft retention,
and all six diagram targets plus keyboard activation. An offscreen real-device
window automatically read the wired AJ199 and returned battery 100% without
writing settings. The connected Buttons page was inspected at 1100x800;
an 800x580 render was also generated. Button mapping/playback effects still
require physical user confirmation.

Visual revision: the fixed sidebar/header/footer were condensed, file import and
export moved into the sidebar, and Sensitivity's DPI/battery summary became a
single strip. Macros uses library/editor columns on wider windows and stacks
them below 760 pixels of page width. Button assignments use left-aligned values;
the drawing's wheel/DPI outlines no longer imply selection. A shared Qt proxy
style supplies visible checkbox ticks and control arrows without image assets.

All four pages were rendered and visually reviewed at 1100x800 and 800x580.
The compact-layout regression checks at least 340 pixels of page height in the
smaller window, the macro layout's direction at both sizes and the absence of
horizontal scrolling. Vertical scrolling remains intentional for longer pages.
This revision changes presentation, not physical device capability or protocol.

The subsequent full visual redesign replaces the dark sidebar with horizontal
navigation and a light mineral/white desktop theme. Text uses graphite and a
restrained sea-green accent. The connection/profile controls, Apply semantics,
background polling and native file flows remain intact. DPI stage colors now
include a swatch of the actual configured value. All four pages and the empty
macro library were rendered at 1100x800 and 800x580 without horizontal scrolling.
Twelve text/control color pairings were measured: secondary text is 5.67:1,
primary action text 6.63:1 and input outlines 3.71:1 against white.

Repeated UI testing exposed an intermittent Qt/Shiboken native crash while
disposing graphical objects; a core also exists from before this light theme.
The test fixture now explicitly drains DeferredDelete on the GUI thread,
verifies that the C++ window was destroyed and collects wrappers before the
next test. Six consecutive full runs and a final run passed (113 tests each)
after that change. This bounds the observed fixture behavior; it does not
establish the unique cause of every historical Qt failure. The demo launcher
also exited successfully after saving a preview. No physical settings were
written as part of the visual redesign.

The checks below describe the earlier delivery snapshot.

The public source snapshot is derived from locally verified application code, on Windows with Python 3.14 and PySide6-Essentials 6.12. This records actual execution, not a Linux certification.

| Check | Result |
|---|---|
| `python -m unittest discover -s tests -v` | 97 tests in the public snapshot, OK, 3.444 seconds; no warnings/errors |
| `python -m vela --cli status --demo` | Exit 0; JSON simulator status |
| `python -m vela --demo --workspace artifacts/final-preview --screenshot artifacts/vela-final.png` | Exit 0; native Windows image inspected |
| Native layouts | Inspected at 1100x800, 1024x720 and 800x580; scrolling content, persistent actions |
| `python -m build` | Isolated source distribution and wheel builds passed; rebuilt for delivery |
| Extracted-wheel CLI | Fresh `python -S` process imported extracted package and returned demo JSON |
| Packaging | Exact original Vela SVG, Linux desktop/rules, source docs; no research binaries, virtualenv or development artifacts |
| Git | Clean source snapshot published to a32fred/vela-mouse-studio; private development history omitted |

Tests cover report/checksum vectors, Linux shared-HID discovery fixtures, bounded command matching, simulated readback and partial failure, macro/combination bounds, independently packed legacy fixtures, strict/atomic native persistence, GUI draft/apply, restart persistence, macro identities/restoration, profile-scoped export, focused recording and ordinary slow-worker shutdown. All device execution used fake HID APIs or the simulator. No physical mouse was enumerated, opened or written during implementation verification.

The public behavioral reference has SHA256 `41c1d26392176e1dcb811816aea8ef1e1131f48a89b4ffc42e83d90d39e837dd`. Only personal paths and the public-edition notice differ from the original analysis reference. Original packaged Vela SVG SHA256: `f9627b398efac0fc2393fcc2f0beb1d6df25a65d1500f738d08d1376e99f2869`.

Final whole-branch review findings were corrected and scoped re-review found no remaining issue. The additional readback-cache regression preserves unapplied local edits separately from actual device macro bodies.

## Linux CI verification

[GitHub Actions run](https://github.com/a32fred/vela-mouse-studio/actions/runs/40155183815) passed on Ubuntu 24.04 with Python 3.10 (97 tests, 3.461 seconds) and Python 3.13 (97 tests, 3.306 seconds). Both jobs also built source/wheel distributions, ran the demo CLI, rendered an offscreen Qt demo and uploaded artifacts. The Linux screenshot was downloaded and visually inspected. CI used no physical mouse.

## Remaining limits

- Live Linux desktop sessions, uaccess/desktop integration, macro playback, button remapping on hardware, the wireless receiver and persistence after power loss remain **UNVALIDATED**; settings, DPI, debounce and scroll light writes were checked by hand on one AJ199 (see Hardware observations). Automated headless Ubuntu checks are recorded above. Source availability does not guarantee every Linux distribution/architecture has compatible dependency binaries.
- Unknown firmware/sensor fields and independent device profile banks remain unconfirmed; unsupported features are not exposed as working controls.
- Legacy file support is the evidenced subset described in [format compatibility](reference/FORMAT_COMPATIBILITY.md); fresh default profiles cannot export to JMA. Native JSON preserves the supported local domain.
- A native HID driver call stalled indefinitely cannot be safely interrupted; the worker preserves GUI responsiveness but shutdown may wait. Local saves are explicit, and concurrent app instances do not merge changes.

[Install and run](../README.md).

## Hardware observations

Reads and reversible writes on one AJ199 (USB cable) are recorded in [hardware findings](reference/HARDWARE_FINDINGS.md): the scroll wheel light register and its modes, notification format, unmapped registers and what was not tested. They come from a single unit and are not a statement about other units, firmware revisions or the wireless receiver.
