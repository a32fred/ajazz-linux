# Delivery verification - 2026-10-24

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

- Live Linux desktop sessions, uaccess/desktop integration, real hardware writes, macro playback and hardware persistence remain **UNVALIDATED**. Automated headless Ubuntu checks are recorded above. Source availability does not guarantee every Linux distribution/architecture has compatible dependency binaries.
- Unknown firmware/sensor fields and independent device profile banks remain unconfirmed; unsupported features are not exposed as working controls.
- Legacy file support is the evidenced subset described in [format compatibility](reference/FORMAT_COMPATIBILITY.md); fresh default profiles cannot export to JMA. Native JSON preserves the supported local domain.
- A native HID driver call stalled indefinitely cannot be safely interrupted; the worker preserves GUI responsiveness but shutdown may wait. Local saves are explicit, and concurrent app instances do not merge changes.

[Install and run](../README.md).
