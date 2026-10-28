# Hardware findings: AJAZZ AJ199 (USB cable, PID 0xFA7B)

Observed on one physical unit on 2026-10-28, using the Ajazz Linux transport (feature report 8, 17 bytes) and static reading of the vendor's Windows driver for interpretation. Everything marked **observed** was read from, or written to and read back from, that unit. **Inferred** means interpretation without a direct test. Other units, firmware revisions and the wireless receiver (PID 0xFA7C) were not tested.

Register layout used below: a value is stored as a pair `(value, 0x55 - value)`; a color is `(r, g, b, 0x55 - r - g - b)`; all arithmetic is modulo 256.

## Scroll wheel light (the only light on this unit)

The light on the scroll wheel is the **DPI effect** at EEPROM `0x4C..0x53`, not the "main lighting" block at `0xA0`.

| Offset | Content |
|---|---|
| `0x4C` | mode, as a pair |
| `0x4E` | brightness level, as a pair (see table) |
| `0x50` | parameter, as a pair (breathing speed) |
| `0x52` | padding pair `(0x00, 0x55)` |

Brightness levels 1 to 10 map to `0x10, 0x1E, 0x3C, 0x5A, 0x80, 0x96, 0xB4, 0xD2, 0xE6, 0xFF` (table taken from the vendor driver; only levels 1 and 10 were exercised on hardware). The unit shipped with level 1, which is dim enough that stage color changes looked like no effect.

The light shows the color of the active DPI stage (`0x2C + 4 * stage`). Observed: changing a stage color is stored, and the scroll light shows it once brightness is raised.

### Modes (observed by eye, brightness 10, parameter 3 unless noted)

| Mode | Result |
|---|---|
| 0 | off |
| 1 | steady |
| 2 | breathing |
| 3, 4, 6, 7, 8 | dark |
| 5 | steady |

The firmware accepted every value written and read it back identically. Modes above 8 were not tried.

### Parameter in breathing mode (mode 2)

| Parameter | Result |
|---|---|
| 1 | slow |
| 5 | about one second per cycle |
| 8 | fast (vendor default is 8) |
| 9 | slow, less than 10 |
| 10 | slow |
| 20 | very slow |

The useful range is 1 to 8. Values above 8 behave unpredictably and the app does not offer them.

### Unexplained

The mode byte read `05` instead of `01` once, after a long session in which it had been restored to `01`. It was not caused by pressing the DPI button, by command `0x02`, or by writing `0xB5` or `0xB7` (each tested separately). A 7 minute watch with the mouse untouched (reads every 15 s, which may itself keep the mouse awake) showed no change in `0x04` or `0x4C..0x53`. The cause is unknown.

## Other registers

| Offset | Observed | Notes |
|---|---|---|
| `0x00` | polling rate | stored as `1, 2, 4, 8` for 1000, 500, 250, 125 Hz |
| `0x02` | DPI stage count | the vendor driver accepts up to 8; its config for this model uses 6 |
| `0x04` | active DPI stage | changed by the DPI button; see notifications |
| `0x06`, `0x08` | `00 55` | unknown, never written by this project |
| `0x0A` | lift-off distance | 1 or 2 mm |
| `0x0C..0x2B` | 8 DPI slots | all 8 populated; unused slots hold the 26000 default |
| `0x2C..0x4B` | 8 stage colors | |
| `0x54..0x5D` | secondary light | valid record: color, mode 0 (off), brightness level 5, parameter 3. The vendor config hides this light for this model. No physical effect was tested. |
| `0x60..0x9F` | key matrix, 16 entries | see below |
| `0xA0..0xA6` | main light block | the vendor config sets `ShowMainEffect=0` for this model; the Ajazz Linux Lighting page used to edit this block and had no visible effect |
| `0xA7` | `00 55` | unknown, never written by this project |
| `0xA9` debounce, `0xAB` light on, `0xAD` idle (x10 s), `0xAF` angle snapping, `0xB1` ripple, `0xB3` light off while moving | | known |
| `0xB5`, `0xB7` | `ff ff` (uninitialized) | the firmware **accepts and stores** writes to both (tested with `06 4f` and `01 54`, then restored to `ff ff`). Whether they have a physical effect is unknown; the vendor driver treats them as auto-sleep and a sensor option (Motion Sync candidate). |

### Light options that did not affect the scroll light

Each was changed and then restored, with the scroll light watched by eye:

| Register | Change | Scroll light |
|---|---|---|
| `0xB3` light off while moving | `01` to `00` (it was `01`, and the light stayed on while the mouse moved) | no change |
| `0xAB` light on | `01` to `00` | no change |
| `0xAD` idle timeout | 300 s to 10 s, mouse still for 20 s | no change |

These belong to the main lighting block, which the vendor config hides for this model. The app keeps them behind the experimental option.

Nothing other than `0x00..0xB4` is populated in `0x0000..0x0FFF` on this unit (no key combinations, no macros). Memory above `0x1000` was not scanned.

## Key matrix entries 6 to 10 (`0x78..0x8B`)

The entries after the six physical buttons are the vendor's factory actions for keys this unit has no button for:

| Entry | Bytes | Action |
|---|---|---|
| 6 | `04 0a 03` | three quick clicks (interval `0x0A`) |
| 7 | `08 00 00` | light on/off |
| 8 | `07 00 00` | polling switch |
| 9 | `02 02 00` | DPI up |
| 10 | `02 03 00` | DPI down |

## Notifications

The mouse sends unsolicited reports (report id 9, command `0x0A`). Observed: pressing the DPI button sends one with bit 0 set and the new stage index as value (stage 2 to 0 to 1 produced values 0 then 1), and `0x04` in EEPROM changes in step. Mouse movement, scroll and ordinary clicks produced no notification. From the vendor driver, six notification types exist; the others were not triggered.

The client now keeps these reports when a query drains them and `pump()` reads them without sending anything. In the app a stage change reaches the screen and a desktop toast in under a second (checked by hand on this unit).

## Commands

| Command | Observation |
|---|---|
| `0x03` | connection check, `01` on the cable device; `0xFA7C` (receiver) did not respond |
| `0x04` | battery and charging, `64 00` (100 percent, not charging) |
| `0x0E` | current profile, `00` |
| `0x0F` | state, always `01` in every state tried |
| `0x02` | acknowledged with status 0 for P5 = 1 and P5 = 0; no change in any register or in `0x0F` |

## Safety notes from testing

- Every write was preceded by a backup and followed by a read back; all values were restored afterwards except where stated.
- The app refuses to remove the last Left click and refuses to write outside `0x0000..0x00B8`, `0x0100..0x01BF` and `0x0300..0x0AFF`.
- Registers `0x06`, `0x08` and `0xA7` were not written: an unknown register may trigger an action when written.
