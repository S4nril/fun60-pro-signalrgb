# Recovery: going back to the original firmware, restoring settings, recalibrating

This page joins two things: this repository's own recovery path (the flasher restoring the original image), and a summary, in our own words, of the
recovery guide that **MonsGeek support sent to the maintainer by email**. As far as we know that guide is not a public web page, so there is nothing to
link to. Read [SAFETY.md](SAFETY.md) first.

> **Status.** No hardware test of either recovery path is recorded in [TEST_REPORTS.md](TEST_REPORTS.md). The flasher path has been exercised only against a
> simulated bootloader. The vendor path is summarised from the vendor's guide and was not re-verified here. Add your own results.

**Where to get the vendor's material.** The recovery guide and its tool package come from MonsGeek support: write to them, say you have a FUN60 Pro (model ID 2304),
and ask for the recovery guide and the package for your model. The guide the maintainer received includes a download link for the tool package; we did not check
what that link serves, so use only links that support gives you directly, and look at what you downloaded before running it. The vendor's drivers are at
<https://www.monsgeek.com/download/> and the online driver at <https://app.monsgeek.com/> (Chrome only, per the guide).
This repository does **not** redistribute the vendor's guide, recovery tool or firmware package.

## Which path to use

| Situation | Path |
|---|---|
| The keyboard still works and `inspect` shows model 2304 / version 0x0309 | **A.** this repository's flasher, original image |
| The keyboard shows up as `3151:502A` (bootloader) and does not start | **A.** with `--recover-in-bootloader`, or **B.** |
| The flasher cannot do it, or you prefer the vendor's tool | **B.** the vendor's manual tool |
| The keyboard no longer shows up as a USB device at all | Neither path is known to work. Contact the vendor's support. |

Never flash a firmware that is not for **your exact model**. Both paths below must use the original image for model 2304 (V309).

## A. Restore with this repository's flasher

1. Put your own `fw_2304.bin` (the original, see [../firmware/README.md](../firmware/README.md)) in `firmware/`.
2. Follow the precautions below, then:

```
python tools/fun60pro_flasher.py plan  firmware/fw_2304.bin
python tools/fun60pro_flasher.py flash firmware/fw_2304.bin            # checks only
python tools/fun60pro_flasher.py flash firmware/fw_2304.bin --arm      # type FLASH 2304 when asked
```

3. If the keyboard is already in bootloader mode (`3151:502A`) the model cannot be verified, so the flasher accepts only the original image and asks for an
   explicit flag and phrase:

```
python tools/fun60pro_flasher.py flash firmware/fw_2304.bin --arm --recover-in-bootloader     # type RECOVER 2304 when asked
```

4. After it finishes, `inspect` should show model 2304, version 0x0309 and no marker. Then continue with "After any flash" below.

## B. Restore with the vendor's manual tool (summary of the vendor's guide)

The vendor distributes a firmware package that contains a small Windows upgrade tool (the guide names `royuan_tool.exe` and `ry_upgrade.exe`).
In short, as the guide describes it:

1. Get the package from MonsGeek support (the guide is sent with it or on request) and extract **all** of its files into one folder.
2. Unplug other USB devices, connect the keyboard **directly** to the PC (no hub), and do not open the MonsGeek driver or touch the keyboard during the update.
3. Run the tool as administrator and wait for its window.
4. Pick your keyboard in the device list. If several devices appear, unplug and replug the keyboard: the entry that disappears and comes back is the one.
5. Press the tool's upgrade button and wait until it reports that it is done. Do not close the tool or unplug anything meanwhile.
6. If it fails, the vendor suggests rebooting the PC, replugging the keyboard, and running the tool as administrator again. One deliberate retry like that is reasonable;
   do not loop, and do not try other firmware.

Make sure the package is meant for your model. We have not checked which package the vendor ships for model 2304; if it is unclear, ask the vendor.

## Precautions (both paths)

* Only the keyboard being recovered is connected, directly to a PC port, with a good cable. No hub. A laptop is on mains power and will not sleep.
* SignalRGB, the vendor driver page and `iot_driver.exe` are closed.
* Nothing is typed on the keyboard and nothing is unplugged while the update runs.
* The firmware is for your exact model and version.

## After any flash (including this repository's images)

Flashing outside the vendor driver **resets the keyboard's settings**, according to the vendor's guide, and the driver may then misread the
current configuration. Expect to redo these steps after every flash, even a successful one:

1. Open the vendor driver (desktop, or the online one in Chrome) with SignalRGB closed.
2. Use the driver's **Retrieve Current Setting** (read what the keyboard has) or **Reset** (write a clean configuration) so that the driver and the keyboard agree.
3. **Recalibrate** (magnetic keyboards need it after a recovery): in the driver open *Configuration*, then *Calibration*, read the instructions and start it.
   Press every key all the way down with roughly the same force, hold each at the bottom for about 4-5 seconds, and make sure every key is both pressed and
   released. Finish with the *Calibration is completed* button. If some keys misbehave afterwards, repeat it, making sure each key bottoms out and is released.
4. Re-enter your remaps, FN layers and actuation points. Write them down **before** flashing; none of the images here carry a backup of them.

## Final checklist

- [ ] The update finished without errors.
- [ ] `inspect` shows model 2304, version 0x0309 and the marker you expect (none after restoring the original).
- [ ] The vendor driver detects the keyboard and has retrieved or reset the settings.
- [ ] Calibration is done and every key registers.
- [ ] Nothing odd after unplugging and replugging the keyboard.
- [ ] Your own settings are restored, and only then SignalRGB is started again.
