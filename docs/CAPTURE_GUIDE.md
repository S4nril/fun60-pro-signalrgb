# Capturing the vendor driver's USB traffic

Use this to confirm the notes in [PROTOCOL.md](PROTOCOL.md) on your own keyboard, to check key slots, or to analyse another model.

**Privacy:** a capture records everything on that USB hub, **including your keystrokes**. Use the mouse while capturing, never type
passwords, and do not publish `.pcapng` files. Share only the specific packets you need.

## Setup

1. Install Wireshark from wireshark.org and tick **USBPcap** in the installer; reboot if asked.
2. Open Wireshark. The interfaces `USBPcap1`, `USBPcap2`... are USB hubs. Expand each (Capture > Options) and pick the one that lists your keyboard
   (replug it into another port if none does).
3. Close SignalRGB and any other RGB software. Keep the vendor driver closed until the capture is running if you want to see its
   identification requests.

## Capturing

1. Start the capture on the hub, then open the vendor driver (web driver with its local service).
2. Do one action at a time with a pause of about 3 seconds, and note the order: paint a key, press *Apply*, change brightness, change effect.
3. Stop the capture and save it. Do **not** run firmware update, factory reset or calibration while capturing.

## Filters (type into the display-filter bar, then Enter)

| Goal | Filter |
|---|---|
| every write to the configuration interface | `frame contains 21:09:00:03:02:00:40:00` |
| only per-key color pages | `frame contains 21:09:00:03:02:00:40:00:0c:00:ff` |
| writes only (hide reads, whose first data byte is `>= 0x80`) | `frame contains 21:09:00:03:02:00:40:00 && frame[36] < 0x80` |
| all `SET_REPORT` requests | `usb.bRequest == 9` |

The `frame contains` form works across Wireshark versions; field names such as `usb.setup.wIndex` vary. The 36 in `frame[36]` is the
28-byte USBPcap header plus the 8-byte setup packet, i.e. the first data byte.

## Reading the packets

* The data bytes are shown in the **Data Fragment** field of *Setup Data*. Right-click it > *Apply as Column* to see the bytes of every packet in the list.
* To copy a packet: right-click > *Copy* > *...as a Hex Stream*. Drop the first 36 bytes (72 hex characters) to get the 64 data bytes.
* A color page begins `0c 00 ff <page> <size> <flag> 00 <checksum>`; slot `s` starts at stream byte `3*s` (R, G, B). Concatenate the bodies of
  pages 0-6 (56 bytes each, the last one 42) to get the 378-byte stream, then list the non-zero slots.

## Mapping keys to slots (what was done for [KEYMAP.md](KEYMAP.md))

1. In the driver, paint a few keys with distinct pure colors (red, green, blue, white, yellow, cyan, magenta) and leave everything else dark.
2. Press *Apply* once, capture, decode the 7 pages, and read which slot holds which color.
3. Paste the hex as text. If you only have a screenshot, make sure the whole data column is visible and legible; small screenshots are easy to misread.
