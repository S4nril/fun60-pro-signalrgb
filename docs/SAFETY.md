# Safety, risks and recovery

**You are rewriting the firmware of a device you may not be able to repair. Read this page completely.**

## What can go wrong

* **A bricked keyboard.** A failed or interrupted update, an image the bootloader rejects, or a mistake in these files can leave the
  keyboard unresponsive. To the maintainers' knowledge, recovery of a keyboard that no longer shows up as a USB device has not been tested.
* **Tested on one keyboard only.** The maintainer reports a successful validation of the patched image, the plugin and the flasher on
  one FUN60 Pro (model 2304, firmware V309). That is a sample of one: other units, revisions, layouts and ID variants are untested, and
  anything not listed as "reported working" in the README (for example restoring the original image or recovering from bootloader mode on
  hardware) has only been verified in simulation or by reading code.
* **Wrong model or version.** The vendor driver lists several FUN60 Pro IDs. These files are for **model 2304, firmware V309, ANSI 61 keys** only.
* **Settings, calibration and warranty.** Flashing outside the vendor driver resets the keyboard's settings (FN layers, remaps, actuation points), the driver may misread the
  configuration afterwards, and a magnetic keyboard needs recalibrating. Plan for it ([RECOVERY.md](RECOVERY.md)). It may also void the warranty.
* **Vendor software.** With the live-mode marker the vendor driver may stop recognising the keyboard (it did on the Ultra). Going back to the original image fixes that.
* **Flash wear.** The vendor driver's *Apply* (flag 1) is permanent. This project's plugin never sends flag 1 and only makes LED-setting writes
  (one to enter mode 13 if needed, optionally one on exit). Do not write your own code that streams flag-1 frames.

## The vendor driver and the plugin

* With the **v1** image the vendor driver does not recognise the keyboard, so FN layers, actuation points and other settings that only the
  vendor driver edits cannot be changed while v1 is installed. If you need them, flash the original image, change the settings, and decide again.
  Whether your saved settings survive a flash was not recorded; write them down first.
* The **v2** image avoids this problem on the tested keyboard: the maintainer reports that the vendor driver recognises the keyboard with it. It has
  still been validated on only one unit, so it carries all the risks on this page.
* The plugin has no hand-off with the vendor driver. **Close SignalRGB before opening the vendor driver**, and the driver before SignalRGB.

## What the tools do to protect you (and what they cannot do)

* `build_pro_patch.py` and `fun60pro_flasher.py` accept only the exact original V309 image or the exact patched build, by SHA-256.
* The flasher reads the identity first and refuses unless it is **model 2304, version 0x0309**; refuses with more than one keyboard connected;
  never retries after a failure; sends no end frame after a failed transfer; requires `--arm` and a typed phrase (`FLASH 2304`).
* Starting from bootloader mode, where the model cannot be checked, it accepts only the **original** image and needs `--recover-in-bootloader` and the phrase `RECOVER 2304`.
* The plugin sends **only identity/LED-setting reads** unless the identity shows model 2304, version 0x0309 and the `F6PK` marker.
* None of this can detect a bad cable, a power cut, a different hardware revision with the same model ID, or a bootloader that behaves differently than read.

## Checklist before flashing

- [ ] `inspect` shows model **2304**, version **0x0309**, and no marker.
- [ ] You downloaded the original firmware yourself and the hash matches (`firmware/README.md`).
- [ ] You have a **recovery path you understand** (see [RECOVERY.md](RECOVERY.md), which covers this repository's flasher and the vendor's own tool).
- [ ] Only this keyboard is connected, directly to the PC (no hub), by a good cable; the PC will not sleep; a laptop is on mains power.
- [ ] SignalRGB, the vendor driver page and `iot_driver.exe` are closed.
- [ ] You wrote down your remaps and settings; the images do not contain a backup.
- [ ] You rehearsed with the **original** image over the original (`flash <fw_2304.bin> --arm`) and it ended with the identity unchanged.
- [ ] You accept that the v1 image has been validated on only one keyboard, and that v2 has also been validated on that single keyboard only.

## If something goes wrong

* Do not retry in a loop and do not try other firmware. Keep the screen output and `flash-pro-log.json`.
* If the keyboard shows up as `3151:502A` (bootloader), the original image can be restored with
  `python tools/fun60pro_flasher.py flash firmware/fw_2304.bin --arm --recover-in-bootloader`.
  This path has only been tested in simulation; no hardware test of it has been reported.
* Otherwise follow the vendor's documented recovery procedure ([RECOVERY.md](RECOVERY.md)) and contact their support.

## Disclaimer

Provided "as is", with no warranty (see LICENSE). Not affiliated with MonsGeek, Akko, Rongyuan or SignalRGB. You are responsible for what you flash.
