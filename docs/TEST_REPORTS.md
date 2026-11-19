# Hardware test reports

**Status of the maintainer's own hardware validation: successful on one keyboard** (FUN60 Pro, model 2304, firmware V309),
reported by S4nril, for both the v1 and the v2 image. The details are still to be added in the rows below.

Please add a row (or open an issue) for every real-hardware attempt, successful or not. Failures are as valuable as successes.

| Date | Model ID / firmware | Layout | Steps done | Result | Notes (errors, logs, surprises) | Reporter |
|---|---|---|---|---|---|---|
| to be added | 2304 / 0x0309 | ANSI 61 (as used for the key-map captures) | to be confirmed by the maintainer (flash of the patched image and live streaming from SignalRGB were reported as successful) | Success (reported by the maintainer) | To add: OS, Python and SignalRGB versions; whether a rehearsal flash of the original image was done; restore to the original; vendor-driver behaviour with the marker; which key slots were checked with Debug slot | S4nril |
| to be added | 2304 / 0x0309 | ANSI 61 | v2 image (`pro-v2`) flashed (starting state to be confirmed by the maintainer) | Success (reported by the maintainer): everything worked and the vendor driver recognises the keyboard | To add: `inspect` output after flashing, FN/actuation editing in the vendor driver, live RGB with v2, whether saved settings survived the flash | S4nril |
| | | | | | | |

## Report template

```
Date:
Keyboard: FUN60 Pro, model ID ____ (from `inspect`), firmware ____, layout (ANSI/ISO/other) ____
OS / Python / SignalRGB version:
Steps completed (inspect / rehearsal flash / patched flash / plugin):
Result (what worked, what did not):
Flasher output and flash-pro-log.json (remove personal paths):
Wrong or missing key slots (use the plugin's Debug slot):
Vendor driver behaviour with the marker present:
Did you restore the original image? Result:
```

Do **not** attach raw USB captures (they contain keystrokes).
