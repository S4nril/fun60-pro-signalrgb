# FUN60 Pro live RGB (experimental) - MonsGeek FUN60 Pro, device ID 2304

> **EXPERIMENTAL. READ [docs/SAFETY.md](docs/SAFETY.md) BEFORE YOU DO ANYTHING.**
> This project modifies keyboard firmware. A mistake can leave the keyboard unusable, and nobody here can promise recovery.
> **Status: validated on real hardware by the maintainer, on one keyboard only** (FUN60 Pro, model 2304, firmware V309).
> Not tested on any other unit, variant or layout. What was and was not covered: [What has and has not been verified](#what-has-and-has-not-been-verified)
> and [docs/TEST_REPORTS.md](docs/TEST_REPORTS.md).

Unofficial work to get **per-key live RGB from SignalRGB** on the **MonsGeek FUN60 Pro** (USB `3151:502D`, device/model ID **2304**,
firmware **V309**). It builds on the approach published for the FUN60 Ultra in
[sinsaintly/fun60-signalrgb-fix](https://github.com/sinsaintly/fun60-signalrgb-fix), ports it to the Pro, and documents how every
step was found so that others can check it, reuse it, or adapt it to another model.
Maintained by [S4nril](https://github.com/S4nril).

Not affiliated with, endorsed by, or supported by MonsGeek, Akko, Rongyuan or SignalRGB. All trademarks belong to their owners.

## Why a firmware patch is needed

With the original firmware the only way to set per-key colors is the vendor driver's *Apply*, and that command **saves to the
keyboard's permanent memory** (tested: colors survive unplugging). Streaming frames that way, many times per second, would be
a stream of flash writes. The Ultra project solved this with a tiny firmware patch that adds a RAM-only path; this repo ports that
patch to the Pro image and wraps it in tools that refuse to do anything unsafe they can detect.

## What is in the box

| Path | What it is |
|---|---|
| `tools/build_pro_patch.py` | Builds the patched image **from your own copy of the original firmware** (12 bytes changed in place + 282 appended). Self-tests against the Ultra project's published image. |
| `tools/fun60pro_flasher.py` | Flasher that follows the vendor driver's USB update protocol. `plan` and `inspect` never write; `flash` needs `--arm` and a typed phrase. |
| `plugin/MonsGeek_FUN60_Pro_LiveRGB.js` | SignalRGB plugin. Refuses to stream unless the keyboard proves it runs the patched firmware. |
| `tests/` | Simulation tests (flasher vs a fake bootloader, plugin vs a fake SignalRGB, CPU emulation of the patched image). |
| `docs/` | How it was done, protocol notes, patch notes, key map, capture guide, safety, test-report template. |
| `firmware/` | **Empty on purpose.** Vendor firmware is not redistributed; the README there says how to get it. |

## Which keyboards

Only a FUN60 Pro that answers the identity request with **model 2304** and **firmware 0x0309**. The vendor driver lists more FUN60 Pro
IDs (2305, 2463, 2464, 2505, 2600 and others) that this project has **not** looked at. Do not flash them with these files. The tools
check the model and version and stop if they do not match. The key map covers the ANSI 61-key layout only.

## Overview of the workflow

1. `py -3 -m pip install hidapi`, then `py -3 tools/fun60pro_flasher.py inspect` (read-only): confirm model 2304 / version 0x0309.
2. Download the original firmware for your own keyboard, see [firmware/README.md](firmware/README.md).
3. `py -3 tools/build_pro_patch.py pro firmware/fw_2304.bin ID2304-V309-livepatch.bin`
4. Read [docs/SAFETY.md](docs/SAFETY.md) and confirm you have a recovery path.
5. `py -3 tools/fun60pro_flasher.py plan <image>`, then `flash <image>` (checks only), then `flash <image> --arm` when you decide to.
   Flashing the **original** image first, as a rehearsal, is recommended.
6. Copy `plugin/MonsGeek_FUN60_Pro_LiveRGB.js` to `Documents\WhirlwindFX\Plugins` (keep a single FUN60 plugin there) and restart SignalRGB.

## What has and has not been verified

**Checked by simulation, USB captures and code reading**

* Frame format, checksums and page layout match USB captures of the vendor driver, byte for byte.
* The builder reproduces the Ultra project's published image byte for byte from the Ultra original.
* CPU emulation: identity reply, normal reports unchanged, flag-2 frames copied to RAM only.
* Flasher logic against a simulated bootloader, including refusals and failures.
* Update protocol read from the vendor driver's code; 22 of 61 key slots seen in captures, the other 39 derived by column counting.

**Reported working on real hardware** (one keyboard, tested by the maintainer S4nril: FUN60 Pro, model 2304, firmware V309)

* The patched firmware was accepted and runs on the keyboard.
* Live per-key RGB from SignalRGB with the plugin.

This is a sample of one. The step-by-step record (software versions, rehearsal flash, restore, key checks) is still to be written down in
[docs/TEST_REPORTS.md](docs/TEST_REPORTS.md).

**Not reported yet / still unverified**

* Any other keyboard: other FUN60 Pro IDs (2305, 2463, 2464, 2505, 2600 and others), other revisions, ISO or other layouts.
* The 39 derived key slots checked one by one, and the `Debug slot` walk-through of all 61 keys.
* Restoring the original image on real hardware, and recovery from bootloader mode (only simulation tests exist; no hardware test of either has been reported).
* How the vendor driver behaves while the live-mode marker is present (it stopped recognising the Ultra until patched).
* Long-term effects: flash wear, and whether anything important lives in flash right after the end of the image.

## Documentation

* [docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md) - the whole method, step by step, with the tools used
* [docs/PROTOCOL.md](docs/PROTOCOL.md) - USB protocol notes (identity, LED mode, color pages, bootloader update, firmware server)
* [docs/PATCH.md](docs/PATCH.md) - exactly what the firmware patch changes and why
* [docs/KEYMAP.md](docs/KEYMAP.md) - the 61-key slot table, verified vs derived
* [docs/CAPTURE_GUIDE.md](docs/CAPTURE_GUIDE.md) - how to capture and read the vendor driver's USB traffic
* [docs/SAFETY.md](docs/SAFETY.md) - risks, checklist, recovery
* [docs/TESTING.md](docs/TESTING.md) and [docs/TEST_REPORTS.md](docs/TEST_REPORTS.md) - tests and how to report hardware results

## Provenance

The analysis and code in this repository were produced with the help of an AI assistant working from USB captures,
the vendor driver's published JavaScript, the firmware images, and the Ultra project's public files. Treat everything as
unreviewed until you have read it yourself; the tests are there so you can check the claims. The maintainer then validated the
result on one real keyboard (see the status above).

## License

MIT for the original code and documentation, see [LICENSE](LICENSE). The approach and the small machine-code routine
appended by the patch come from the FUN60 Ultra project linked above; see [docs/PATCH.md](docs/PATCH.md). Vendor firmware is not included.
