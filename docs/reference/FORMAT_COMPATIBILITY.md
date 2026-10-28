# Ajazz Linux file and binding compatibility

Ajazz Linux implements these layouts independently from `CLONE_SPEC.md`. Tests use
constructed fixtures and the simulated transport. Compatibility with an actual
vendor application or physical macro playback has not been tested.

## Native workspace

`ProfileStore(root=None)` stores `workspace.json` under `$XDG_CONFIG_HOME/vela`,
or `~/.config/vela` when XDG_CONFIG_HOME is absent or relative. An explicit root
is used directly. `load()` returns defaults only when the file does not exist;
invalid existing data raises `FileFormatError` and is never overwritten by load.

Schema 1 contains `schema_version`, `profiles`, `macros`, and `selected_profile`.
Exactly four profiles, at most 2000 distinct macro IDs, and a selected index0..3
are required. Profile objects contain `name` and `settings`; macro and settings
objects use the domain dataclass field names. Unknown/duplicate fields, future
schemas, invalid types, and booleans in integer fields are rejected. The file
limit is32MiB. Profile names allow1..128 Unicode code points without NUL; macro
names allow1..39 UTF-16 units without NUL. Names are stored as data, never paths.

Optional `legacy` metadata retains imported opaque bytes through native saves:
profiles contain `{ "profile": "<2116-byte hex>", "jma": "<optional 10456-byte hex>" }`,
macros contain an834-byte decoded hex string. Each blob is size/magic/field
validated with the same bounded legacy parser, never interpreted as an address.
Known values edited after import are reserialized while unrelated bytes remain.

Saves validate before creating a temporary file, write and fsync a temporary
file in the destination directory, then atomically replace the old file.
Failures before replacement preserve the previous file and remove the temporary
file. This does not claim power-loss durability of directory metadata or
coordination between concurrent application processes.

## Legacy files

| Format | Supported boundary |
| --- | --- |
| JMM | Exactly834 bytes; bytewise ROR2 export/ROL2 import; decoded magic FACB99A0; nonzero uint32 ID; up to70 events, 65535ms delays, 39 UTF-16 name units, cycles1..250. |
| JMA | Exactly10456 bytes; magic FCAA1234; nonzero state token; 2116-byte profile plus ten decoded macro slots; at most ten distinct nonzero macro IDs. All48 binding records are checked for missing macro references. |
| Profile DCT | Four-byte opaque prefix plus one to four complete2116-byte profiles. Valid names and supported settings required. Macro references are rejected because this format provides no macro bodies. |

`mac.dct`, the separate large aggregate macro cache, is not the profile DCT
format and is unsupported. Truncated and oversized legacy files are rejected.
No imported state token, ID, pointer-like value or filename is dereferenced.

JMM translates the documented Windows VK table only within this adapter; the
application domain uses HID usages. VK_RETURN cannot distinguish keypad Enter;
import resolves it to regular Enter and fresh export of HID58 is rejected.
Movement uses signed byte components; zero movement with zero delay is a file
terminator and cannot be exported as an event. Unsupported mouse/wheel codes,
unknown event flags, unrepresentable movement/key data, and oversized values
raise errors rather than becoming zero or losing fields.

JMA settings cover the documented polling codes, active DPI list/index, RGB
colors, LOD, ripple, angle snapping, lighting controls, idle-light timeout and
debounce. Windows pointer/scroll fields and unknown sensor fields remain opaque.
Only contiguous active stages with flag0 and stage count1..6 are supported.

Fresh legacy action exports are limited to the explicit spec codes: left,
left double/triple click, DPI up/down/cycle, polling/light/profile cycle and
macro references. The per-field legacy encodings of keyboard/consumer actions,
right/middle/back/forward and disabled actions are not fully established by the
spec. Those fresh exports fail with a native-JSON suggestion. In particular,
an unmodified fresh default profile cannot be exported to JMA. Imported opaque
binding records can remain unchanged and are displayed as `legacy:<hex>`;
applying a newly imported unsupported record to hardware is rejected.

An unchanged imported JMM/JMA exports byte-for-byte, including unused macro
slot positions. After edits, supported fields are reserialized and unknown
profile bytes/binding records are retained; JMA macro slots may be compacted.
The adapter does not mutate global libraries or automatically apply imports.

The UI exports only macros required by the selected profile, including references
in retained opaque binding banks. `select_profile_macros(settings, macros)` uses
the actual exported binding records to select that subset without changing the
library. `save_profile` still includes every explicitly supplied macro, including
unreferenced entries, and applies the ten-slot limit to its supplied selection.

## Device bindings and macros

`Binding('keyboard', keys=[...], modifiers=...)` uses HID keyboard usages and
Ctrl/Shift/Alt/Win mask1/2/4/8. At most three distinct keys and four modifiers
are allowed, and total pressed keys plus modifiers must be at most five to fit
the32-byte slot. `Binding('consumer:00e9')` is an example consumer action;
`protocol.CONSUMER_USAGES` provides the supported labeled catalog.

`Binding('macro', macro_id=...)` references an explicit library macro. The
service validates all requested bindings before writes, confirms auxiliary
slots first, then enables matrix entries. Combinations use100h+matrix*32;
macros use300h+matrix*180h. Reapplying unchanged auxiliary bytes causes no writes.
`_binding_records(settings, macros)` is the service extension seam for this
validation/preparation phase, not an independent transport or UI write path.

Macro event codes use HID usages, E0..E7 modifier usages, and reserved F0..F4
mouse buttons. F3 means forward mask10h and F4 back mask08h. Wheel F5/F6 are
rejected. Hardware cannot distinguish right Win from left Win, so E7 hardware
export is rejected; legacy files can retain it. Hardware movement components
must fit signed bytes. HID32/64 are outside the evidenced keyboard table.

Hardware names truncate to15 UTF-16 units without splitting surrogate pairs.
Event delays are big-endian16-bit. Checksum covers count/events, excluding the
name header. Transfer length is L+4 for N<=69 and L+1=383 for N=70, L=32+5N.

`MouseService.macros` returns independent copies of decoded active slots whose
IDs match snapshot bindings. Hardware contains slot positions, not library IDs:
reconnect uses IDs80000000h+matrix. Same-session IDs are retained only when body
and mode match; identical shared IDs are deduplicated. Unknown/unsupported macro
bodies leave the binding opaque and preservable for unrelated edits. Transport
failures still propagate. Hardware readback retains final event delays but
cannot recover host-only automatic-delay settings, unencoded repeat counts for
held/toggle modes, or characters beyond the hardware name limit. Preserve the
local library when applying; adopting device data represents the readable state.
