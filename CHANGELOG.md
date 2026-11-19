# Changelog

Two numbering schemes are used, and they are not the same thing:

* **Repository releases** (`v1.0.0`, `v2.0.0`, git tags): versions of this project as a whole.
* **Firmware image variants** (`v1`, `v2`, built by `tools/build_pro_patch.py pro` and `pro-v2`): two different patched images. Release `2.0.0` is the first
  one that can build the v2 image.

## [2.0.0] - 2026-11 - v2 image: the vendor driver keeps working

### Added
* **v2 image** (`python tools/build_pro_patch.py pro-v2 ...`): the live-mode marker is written to identity bytes 9-12 instead of 3-6, so the model bytes
  stay as in the original firmware and **the vendor driver recognises the keyboard again**. Reported working on one keyboard (FUN60 Pro, model 2304, firmware V309).
  SHA-256 of the v2 image: `f3949cbcd3fe49095c629d6f1e5ffef14d0f6d6fad3fbb34f084f7f8f0653608`.
* The flasher accepts the v2 image and understands both marker positions when it checks the identity after flashing.
* The plugin accepts the marker at either position (v1: bytes 3-6, v2: bytes 9-12).
* Tests for v2 in all three suites (flasher simulation, CPU emulation, plugin simulation).
* `docs/RECOVERY.md`: restoring the original firmware with this repository's flasher or the vendor's tool, resetting settings, recalibrating.

### Changed
* Documentation now states that the project was validated on real hardware by the maintainer (one keyboard), and recommends v2.
* Documentation explains why the vendor driver stopped working with v1 and that flashing outside the driver resets settings and needs recalibration.
* The patched-image file name no longer says "UNTESTED".

### Unchanged
* The v1 image: same builder output, same SHA-256 (`5934caf51604877baa53c3ddf0b81b8506d8af6a1a73c5f969c020a663f8eb03`).

### Known limitations
* Validated on a single keyboard. The 39 derived key slots, other FUN60 Pro IDs, other layouts, and both recovery paths have no recorded hardware test.
* The plugin has no hand-off with the vendor driver: close SignalRGB before using the driver.

## [1.0.0] - 2026-11 - first release

* Port of the FUN60 Ultra live-RGB approach to the FUN60 Pro (model 2304, firmware V309): firmware patch builder (v1 image), flasher following the vendor's USB update
  protocol, SignalRGB plugin, simulation tests, and documentation of how everything was found.
* Side effect of the v1 image: the vendor driver stops recognising the keyboard (fixed by the v2 image in 2.0.0).
