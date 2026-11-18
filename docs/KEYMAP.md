# Key map (ANSI 61-key layout, FUN60 Pro model 2304)

The keyboard exposes **126 LED slots**: 21 columns x 6 rows, `slot = column * 6 + row`. Row 0 is the function row,
which a 60% keyboard does not have, so Esc sits on slot 1 (column 0, row 1).

* **verified** = seen in a USB capture of the vendor driver painting that key (22 keys).
* **derived** = not captured individually. Each row's first and last letter keys are verified and the keys between them occupy
  consecutive columns with no gap (12 keys for columns 1-12 on the number and Q rows, 11 for columns 1-11 on the A row,
  10 for columns 2-11 on the Z row); Tab (slot 2) and Caps Lock (slot 3) are the two remaining slots of column 0 (39 keys).

Only the ANSI 61-key layout is covered. ISO and other layouts, and the other FUN60 Pro device IDs, are untested.

The plugin has a *Debug* property that lights a single slot, which is the easiest way to confirm a derived key on real hardware.


## Number row

| Key | Slot | Column | Row | Status |
|---|---|---|---|---|
| Esc | 1 | 0 | 1 | verified |
| 1 | 7 | 1 | 1 | verified |
| 2 | 13 | 2 | 1 | derived |
| 3 | 19 | 3 | 1 | derived |
| 4 | 25 | 4 | 1 | derived |
| 5 | 31 | 5 | 1 | derived |
| 6 | 37 | 6 | 1 | derived |
| 7 | 43 | 7 | 1 | derived |
| 8 | 49 | 8 | 1 | derived |
| 9 | 55 | 9 | 1 | derived |
| 0 | 61 | 10 | 1 | derived |
| - | 67 | 11 | 1 | derived |
| = | 73 | 12 | 1 | verified |
| Backspace | 79 | 13 | 1 | verified |

## Q row

| Key | Slot | Column | Row | Status |
|---|---|---|---|---|
| Tab | 2 | 0 | 2 | derived |
| Q | 8 | 1 | 2 | verified |
| W | 14 | 2 | 2 | derived |
| E | 20 | 3 | 2 | derived |
| R | 26 | 4 | 2 | derived |
| T | 32 | 5 | 2 | derived |
| Y | 38 | 6 | 2 | derived |
| U | 44 | 7 | 2 | derived |
| I | 50 | 8 | 2 | derived |
| O | 56 | 9 | 2 | derived |
| P | 62 | 10 | 2 | derived |
| [ | 68 | 11 | 2 | derived |
| ] | 74 | 12 | 2 | verified |
| \ | 80 | 13 | 2 | verified |

## A row

| Key | Slot | Column | Row | Status |
|---|---|---|---|---|
| Caps Lock | 3 | 0 | 3 | derived |
| A | 9 | 1 | 3 | verified |
| S | 15 | 2 | 3 | derived |
| D | 21 | 3 | 3 | derived |
| F | 27 | 4 | 3 | derived |
| G | 33 | 5 | 3 | derived |
| H | 39 | 6 | 3 | derived |
| J | 45 | 7 | 3 | derived |
| K | 51 | 8 | 3 | derived |
| L | 57 | 9 | 3 | derived |
| ; | 63 | 10 | 3 | derived |
| ' | 69 | 11 | 3 | verified |
| Enter | 81 | 13 | 3 | verified |

## Z row

| Key | Slot | Column | Row | Status |
|---|---|---|---|---|
| Left Shift | 4 | 0 | 4 | verified |
| Z | 16 | 2 | 4 | verified |
| X | 22 | 3 | 4 | derived |
| C | 28 | 4 | 4 | derived |
| V | 34 | 5 | 4 | derived |
| B | 40 | 6 | 4 | derived |
| N | 46 | 7 | 4 | derived |
| M | 52 | 8 | 4 | derived |
| , | 58 | 9 | 4 | derived |
| . | 64 | 10 | 4 | derived |
| / | 70 | 11 | 4 | verified |
| Right Shift | 76 | 12 | 4 | verified |

## Bottom row

| Key | Slot | Column | Row | Status |
|---|---|---|---|---|
| Left Ctrl | 5 | 0 | 5 | verified |
| Left Win | 17 | 2 | 5 | verified |
| Left Alt | 23 | 3 | 5 | verified |
| Space | 41 | 6 | 5 | verified |
| Right Alt | 65 | 10 | 5 | verified |
| Fn | 71 | 11 | 5 | verified |
| Menu | 77 | 12 | 5 | verified |
| Right Ctrl | 83 | 13 | 5 | verified |
