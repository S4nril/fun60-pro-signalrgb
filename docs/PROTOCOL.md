# Protocol notes (FUN60 Pro, model 2304)

Everything here was read from USB captures of the vendor driver, from the vendor driver's JavaScript, and from the firmware.
Items marked *(inferred)* were not observed directly.

## Transport

* HID **feature reports**, report ID 0, **64 data bytes** (65 bytes including the report ID in `hidapi` / SignalRGB calls).
* Vendor configuration interface: USB **interface 2**, usage page `0xFFFF`, usage 2. USB ID `3151:502D`.
* Writes are `SET_REPORT` (`bmRequestType 0x21`, `wValue 0x0300`, `wIndex 2`); reads are `GET_REPORT` (`0xA1`).
* Windows `hidapi` keeps the report-ID byte in front of what `get_feature_report` returns; parse by locating the echoed command byte.

## Checksums

| Command family | Checksum byte | Rule |
|---|---|---|
| read commands (`0x8F`, `0x87`) and color pages (`0x0C`) | index 7 | `0xFF - (sum(bytes 0..6) & 0xFF)` |
| LED settings write (`0x07`) | index 8 | `0xFF - (sum(bytes 0..7) & 0xFF)` |
| bootloader update frames | none | raw |

For color pages the checksum covers the 7 header bytes only, not the body. Verified on every captured packet.

## Identity (`0x8F`)

Request `8F 00 00 00 00 00 00 70`. Reply bytes (index 0 is the echoed command):

| Index | Meaning | Original firmware | Patched firmware |
|---|---|---|---|
| 1-2 | model ID, little endian | `00 09` (2304) | `00 09` |
| 3-6 | zero on the original | `00 00 00 00` | marker `46 36 50 4B` ("F6PK") |
| 7-8 | firmware version, little endian | `09 03` (0x0309, "V309") | `09 03` |

The vendor driver reads the model as a 32-bit value from indices 1-4 (per the Ultra project's notes), which is why a marker in
indices 3-6 confuses it. The firmware server names versions like `V309`, parsed as hexadecimal.

## LED settings (`0x87` read, `0x07` write)

`07 <mode> <speedRaw> <brightness> <option> <R> <G> <B> <checksum@8>`; the read reply has the same fields at indices 1-7.
Captured example (an effect applied from the driver): `07 05 02 04 07 fa ff fa f3`.
From the driver's code, **mode 13 = "User Picture"** (per-key). The driver writes it as `07 0d 05 <brightness> 00 00 c8 c8 <chk>`
(option `0` = picture slot 1, fixed color 0/200/200). Writing LED settings is a normal setting change that the keyboard saves.

## Per-key colors (`0x0C`)

126 LED slots x RGB = 378 bytes, sent as 7 pages:

```
0C 00 FF <page> <size> <flag> 00 <checksum> <56 body bytes, zero padded>
page 0..5: size 0x38 (56) flag 00      page 6: size 0x2A (42), flag = apply flag
```

The body is the continuous 378-byte stream (a slot can straddle two pages). Slot `s` occupies stream bytes `3s..3s+2` as R, G, B.
`slot = column * 6 + row`; see [KEYMAP.md](KEYMAP.md).

**Apply flag.** The vendor driver sends `01` on the last page: **this saves permanently** (tested by replugging). Flag `02` is the
RAM-only value of the *patched* firmware and must never be sent to the original firmware, where its effect is unknown.
The vendor driver spaces the pages 12-16 ms apart, about 80 ms per frame.

## Bootloader update

| Item | Value |
|---|---|
| Enter bootloader | feature report `7F 55 AA 55 AA 00 00 82` |
| Bootloader USB ID | `3151:502A`, usage page `0xFF01`, usage 1 (driver device name `helpRy5088`) |
| Image sent | `firmware_file[0x5000:]` (the first `0x5000` bytes are the bootloader and are not sent) |
| Start frame | `BA C0 <blocks LE16> <length LE24>`, then wait 5 ms and read; the driver retries up to 10 times, 1 s apart |
| Data | 64-byte blocks, one feature report each, last block zero padded |
| End frame | `BA C2 <blocks LE16> <sum32 LE> <length LE32>`; wait 100 ms and read; success if reply byte 4 is `0x55` |
| `sum32` | sum of every byte of the image that was sent |

Image layout: `0x0000-0x4FFF` bootloader (vector table at 0), `0x5000` ASCII header `AT32F405 8KMKB  `, application vector table
at `0x5200` (SP `0x2000bec8`, reset `0x080054f9`). Everything the protocol checks is additive; whether the bootloader checks more is unknown.

## Firmware server (vendor)

* `POST https://api2.rongyuan.tech:3816/api/v2/get_fw_version` with `{"dev_id": 2304}` returns JSON `{code, data: {file_path, version_str, ...}}`.
* `GET https://api2.rongyuan.tech:3816/download/<file_path>` returns the file. For this model it is a raw-deflate stream (inflate with
  `zlib.decompress(data, -15)`). The driver's code treats multi-part versions (`version_str` with `_`) as a ZIP; not seen for this model.
* The server may later offer a different version; the tools in this repo only accept the V309 image with the known SHA-256.
