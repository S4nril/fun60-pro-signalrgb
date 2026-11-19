# How this was done

This is the whole method in the order it happened, so anyone can repeat it, check it, or apply it to another model.
Each step says what was done, which tool was used, what was learned, and how sure we are.

## 0. Starting point

The FUN60 **Ultra** (model 2381) already had a working live-RGB approach in
[sinsaintly/fun60-signalrgb-fix](https://github.com/sinsaintly/fun60-signalrgb-fix): a SignalRGB plugin plus a small firmware patch
("F6PK"). Its `TECHNICAL.md` and firmware README explain the idea: per-key frames are sent as 7 feature-report pages, and the patched
firmware accepts them into RAM when the apply flag is `2`. The question here was whether the same idea carries over to the **Pro**.

## 1. Identify the keyboard

* Windows Device Manager, *Hardware Ids* of the HID keyboard: `VID_3151&PID_502D`. The Ultra uses the same pair, so the USB ID
  does **not** tell the models apart.
* A USB capture (step 2) of the vendor driver's identity request showed the model ID: **2304** (`0x0900`), firmware `0x0309`.
* The vendor web driver's device table (step 3) confirms it: `{id: 2304, vid: 0x3151, pid: 0x502D, displayName: "FUN60 PRO"}`.
  The same table lists other FUN60 Pro IDs, which is why this project only claims 2304.

## 2. Capture the vendor driver's USB traffic

* Tools: Wireshark with USBPcap (see [CAPTURE_GUIDE.md](CAPTURE_GUIDE.md)). The vendor web driver was used to change colors; the
  traffic was captured on the keyboard's USB hub.
* Useful filters: all feature-report writes to interface 2 `frame contains 21:09:00:03:02:00:40:00`, only color pages
  `... :0c:00:ff`, and "writes only" by hiding commands whose first data byte is `>= 0x80` (those are reads).
* Findings: identity (`0x8F`) and LED-setting (`0x87`/`0x07`) commands, and the 7-page color frame (`0x0C`) with a checksum
  rule that was verified on every captured packet. Details in [PROTOCOL.md](PROTOCOL.md).
* **Persistence test:** paint keys in the driver, press *Apply*, unplug and replug the keyboard. The colors stayed, so the
  driver's `flag = 1` write is permanent. That is the reason streaming needs the patch.

## 3. Read the vendor driver's JavaScript

The web driver is a public JavaScript bundle. Reading it (as text, never executed) gave:

* command names and numbers (`FEA_CMD_SET_LEDPARAM = 7`, `FEA_CMD_SET_USERPIC = 12`, bootloader command `127`), which matched the
  captures; and that **LED mode 13 is "User Picture"** (per-key colors) - the same mode number the Ultra patch checks;
* the device table (model IDs, VID/PID, which class handles the Pro);
* the **firmware download** flow (`get_fw_version` then `download/<file_path>`, payload is a raw-deflate stream);
* the **USB update protocol** and the bootloader's USB ID (`3151:502A`), including the checksum (a plain sum of bytes, found as
  Ramda's `sum`). See [PROTOCOL.md](PROTOCOL.md).

The local `iot_driver.exe` service the web driver talks to was inspected statically (strings only). It is a thin bridge
(`sendRawFeature` / `readRawFeature` over a local gRPC port) and contains no firmware.

## 4. Get the original firmware and compare it with the Ultra's

* The firmware was fetched with the same two requests the driver makes (see [../firmware/README.md](../firmware/README.md)) and
  inflated. The inflated image is 124,668 bytes; the Ultra's is 124,664.
* Comparison: the two images are the same code base. About 18% of bytes differ, almost all of them small shifts of branch
  targets (+2 / +4 bytes) because the Pro image is 4 bytes longer.
* The part of the file the updater actually sends starts at offset `0x5000`. There is an ASCII header `AT32F405 8KMKB  `
  (identical in both images) and the application vector table is at `0x5200`.

## 5. Understand the Ultra patch by disassembling it

`stock-ID2381-V302.bin` vs `ID2381-V302-F6PK.bin` (Capstone, Thumb-2): **12 bytes change in place and 282 bytes are appended.**

1. Four store instructions in the identity-reply builder are replaced by a call that writes the marker `F6PK`.
2. The first instruction of the report handler is replaced by a jump to new code. That code checks the page's apply flag;
   if it is not `2` it replays the original instruction and continues unchanged; if it is `2` and the conditions hold, it copies the
   378 color bytes to a RAM LED buffer and returns without running the original handler (which is what would save to flash).

## 6. Port the patch to the Pro

* The two patch sites were located by byte signature (the handler prologue is unique in the image) and by position relative to the
  Ultra: Pro `0x1238c` / `0x11d92` versus Ultra `0x12388` / `0x11d8c`.
* The RAM addresses used by the new code (`0x20006d14`, `0x2000011c`, `0x20005ea8`, `0x20006f60`, `0x20006b94`) appear with the same
  number of references at the same positions in both images.
* `tools/build_pro_patch.py` rebuilds the patch. **Self-test:** run on the Ultra original it reproduces the published F6PK image
  **byte for byte**, which validates the branch encoder and the layout.
* **A bug found by reading the disassembly:** the Pro's code after the identity site reuses register `r0` (value 9) to store the
  firmware version. The Ultra's code reloads `r0`, the Pro's does not, so the marker routine would have corrupted the version to
  `0x034B`. The Pro build saves and restores `r0`.
* **CPU emulation** (Unicorn): the identity reply is correct; for `flag = 1` (what the vendor driver sends) registers, stack and RAM
  at the handler body are identical to the unpatched image; for `flag = 2` the 378 bytes land in the RAM buffer and the original handler is skipped.

## 7. Key map

Slot index = `column * 6 + row` (126 slots). Three capture rounds, painting known keys with distinct colors and pressing *Apply*,
confirmed 22 keys; the rest follows from column counting (see [KEYMAP.md](KEYMAP.md)). The captured hex was decoded either from
copied hex streams or, when only screenshots were available, by template-matching the monospaced hex text against the known packet
headers. Pasting the hex as text is more reliable and is what the capture guide recommends.

## 8. Plugin

`plugin/MonsGeek_FUN60_Pro_LiveRGB.js` encodes frames exactly like the vendor driver's pages (checked byte for byte against
captured pages) except for the apply flag, and it is built around one rule: **never stream unless the identity proves the patched
firmware** (model 2304, version 0x0309, marker `F6PK`). It was first tested against a mock of the SignalRGB device API, because the real API was not available
to the analysis; it was later validated on real hardware (step 10).

## 9. Flasher

`tools/fun60pro_flasher.py` implements the update protocol read in step 3 and accepts only three known files by SHA-256. It was
tested against a simulated keyboard and bootloader (see [TESTING.md](TESTING.md)). It was written from the vendor driver's code,
not from observing a real update; it was later run on real hardware (step 10).

## 10. Hardware validation

The maintainer (S4nril) reports a successful end-to-end validation on one FUN60 Pro (model 2304, firmware V309): the patched image was
accepted and the plugin streamed per-key colors from SignalRGB. One keyboard is a small sample, and the details of exactly which steps were
covered are to be recorded in [TEST_REPORTS.md](TEST_REPORTS.md).

## 11. After validation: the vendor driver stops working (v1) and the v2 variant

Right after the hardware validation the maintainer found that the vendor driver no longer sees the keyboard, so FN layers and actuation points
cannot be edited. This is the same side effect the Ultra project reported, and it matches the design: v1 writes its marker into identity bytes 3-6,
two of which belong to the 32-bit model ID the driver reads (a statement from the Ultra project's notes; it was not re-verified here, because the identity
is parsed in the vendor's local service, which was only inspected statically).

The firmware code that builds the reply shows a way out: for command `0x8F` it writes the model to `[r4+3]`/`[r4+4]`, four zeros to `[r4+5..8]`, the version to
`[r4+9]`/`[r4+0xa]` and then jumps to the shared epilogue at `0x1233c`; the captured original replies are zero from identity byte 9 on. **v2** leaves all of those stores alone and
replaces only that final jump, so a small routine can write the marker at `[r4+0xb..0xe]` (identity data bytes 9-12) before continuing. The flasher and the
plugin accept either marker position. v2 was built with the same builder (`pro-v2`), checked in CPU emulation, and then flashed by the maintainer: it flashed fine and the vendor driver recognises the keyboard again (one keyboard).

The vendor's own recovery guide adds a second reason the driver can look "broken" after a flash: firmware written outside the driver resets the keyboard's settings, and the
driver may misread the configuration until you use *Retrieve Current Setting* or *Reset* (and recalibrate). So after any flash, do those steps before judging whether the marker
is the cause. See [RECOVERY.md](RECOVERY.md).

## Tools used

Wireshark + USBPcap, Python 3 (`hidapi`, `capstone`, `unicorn`, `Pillow` for screenshot decoding), Node.js (plugin mock),
a text editor and a lot of reading.
