# Testing

## Run the simulation tests

You need your own copy of the original firmware in `firmware/` (see [../firmware/README.md](../firmware/README.md)); tests that need it
print `SKIPPED` without it.

```
python tests/test_flasher_sim.py        # flasher vs a simulated keyboard + bootloader
python tests/test_patch_emulation.py    # CPU emulation of the patched image (pip install unicorn capstone)
node   tests/test_plugin_sim.js         # plugin vs a mock of the SignalRGB device API (Node.js only)
python tools/build_pro_patch.py selftest <ultra_stock.bin> <ultra_F6PK.bin>   # needs the Ultra project's two images
```

## What they cover

| Suite | Checks |
|---|---|
| `test_flasher_sim.py` | planned frames (`bac05c06fc9601` ... for the original, `bac06106169801` ... for the patched image); received blocks reassemble to `image[0x5000:]`; refusals (unknown image, model 2381, wrong version, two keyboards, wrong typed phrase, bootloader without the flag, patched image in recovery); no retry and no end frame after a failed block; missing `0x55` confirmation; read-only `inspect` |
| `test_patch_emulation.py` | identity reply (model, marker, version with `r0` preserved) for v1 and v2 (v2: model bytes untouched, marker at bytes 9-12); with `flag = 1` registers, stack and RAM at the original handler body equal the unpatched image; with `flag = 2` and mode 13 the 378 bytes reach the RAM buffer and the original handler is skipped; with another mode nothing is copied |
| `test_plugin_sim.js` | refuses on original firmware, wrong version, wrong model; mode-13 write once with a valid checksum; a frame is 7 pages with flag `2` only on the last; flag `1` never sent; restore on exit; pages byte-identical to pages captured from the vendor driver; 61 unique slots; debug slot |
| `build_pro_patch.py selftest` | rebuilds the Ultra project's published patched image byte for byte |

## What they cannot show

The simulators were written from the same understanding as the code under test. They prove internal consistency, not that the real
bootloader, the real SignalRGB, or the real LED hardware agree. Only the frame formats and checksums are anchored to real captures.
The hardware validation reported in [TEST_REPORTS.md](TEST_REPORTS.md) is what covers those points.

## Hardware validation checklist (for people who try it)

The maintainer reports a successful validation on one keyboard; which of the steps below were covered is still to be recorded in
[TEST_REPORTS.md](TEST_REPORTS.md).

Do these in order and stop at the first surprise. Record each result with the template in [TEST_REPORTS.md](TEST_REPORTS.md).

1. `inspect` before anything: model, version, marker.
2. Rehearsal: flash the **original** image over the original; `inspect` again.
3. Flash the patched image; `inspect` must show marker `F6PK`; type on the keyboard (normal typing must still work).
4. Open SignalRGB with the plugin: the log should say live mode is enabled; check colors on a few keys.
5. Use the plugin's *Debug slot* property to walk the 61 key slots and report any key that lights the wrong LED.
6. Check what happens with the vendor driver while the marker is present.
7. Restore the original image and confirm `inspect` shows no marker.
8. After every flash (not only restores) use the vendor driver's *Retrieve Current Setting* or *Reset* and recalibrate, as in [RECOVERY.md](RECOVERY.md); record whether your settings survived.
