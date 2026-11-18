#!/usr/bin/env python3
"""
Build the experimental live-RGB patch for the MonsGeek FUN60 Pro (device ID 2304, V309)
by porting the approach of sinsaintly/fun60-signalrgb-fix (ID 2381 "F6PK").

This script only reads and writes files on your computer. It does not talk to any
keyboard and it does not flash anything.

What it changes in the stock image (same idea as the Ultra patch):
  1. Hook site  : the 4-byte function prologue `push.w {r4-r9,lr}` of the HID report
                  handler is replaced by `b.w <new code>`.
  2. Identity   : the 8 bytes of four `strb r6,[r4,#5..#8]` (zeros in the identity
                  reply) are replaced by `bl <marker routine>` + 2 NOPs, so bytes 3..6
                  of the identity data read as the marker (default "F6PK").
  3. New code   : 274 bytes appended after the image (+ 0xFF padding).

New code behaviour (read from the Ultra disassembly):
  - if the page's apply flag (byte at report_buffer+0x24b) is not 2, run the original
    handler unchanged;
  - if it is 2, mark the report as consumed, check command 0x0C / selector 0xFF /
    page 6 / length 0x2A, check mode == 13, then copy 378 bytes to a RAM LED buffer
    and return without running the original handler.

Usage:
  python build_pro_patch.py pro  <stock_pro_image> <out.bin>
  python build_pro_patch.py selftest <ultra_stock.bin> <ultra_F6PK.bin>
"""
import hashlib
import struct
import sys
import zlib

CODE_BASE = 0x1E700      # where the new code lives (same as the Ultra image)
MARKER_ADDR = 0x1E800    # marker routine address (same as the Ultra image)
MARKER = b"F6PK"         # 4 ASCII bytes written to identity data bytes 3..6

# New-code template, copied from the Ultra F6PK image at 0x1E700..0x1E763 (100 bytes).
# It is position independent apart from the final B.W, which is regenerated below.
CODE_HEAD = bytes.fromhex(
    "0fb4194890f84b12022928d1174a1378"
    "13f0400f21d023f04003137090f84512"
    "ff291ad190f84612062916d1b0f84812"
    "2a2912d10e4a117a0d290ed10d4a117f"
    "00290ad100f142000b4940f27a1210f8"
    "013b01f8013b013af9d10fbc70470fbc"
    "2de9f043"
)
# Literal pool at 0x1E768..0x1E77B: five RAM addresses.
LITERALS = bytes.fromhex("146d00201c010020a85e0020606f0020946b0020")

PRESETS = {
    # name: (identity_site, hook_site, expected_identity_bytes, expected_hook_bytes)
    "pro2304": (0x11D92, 0x1238C),
    "ultra2381": (0x11D8C, 0x12388),
}
EXPECT_ID = bytes.fromhex("6671a671e6712672")  # strb r6,[r4,#5],#6,#7,#8
EXPECT_HOOK = bytes.fromhex("2de9f043")         # push.w {r4-r9,lr}
PRO_STOCK_SHA256 = "237bbe74f2f718a08bf2b8bb9caf6ca026b86817b6baae6130e0a7794d72a6ac"


def _thumb_branch(src, dst, link):
    """Encode a Thumb-2 B.W (link=False) or BL (link=True) located at `src`."""
    off = dst - (src + 4)
    assert off % 2 == 0 and -(1 << 24) <= off < (1 << 24), "branch out of range"
    s = (off >> 24) & 1
    i1 = (off >> 23) & 1
    i2 = (off >> 22) & 1
    j1 = (~(i1 ^ s)) & 1
    j2 = (~(i2 ^ s)) & 1
    hw1 = 0xF000 | (s << 10) | ((off >> 12) & 0x3FF)
    hw2 = (0xD000 if link else 0x9000) | (j1 << 13) | (j2 << 11) | ((off >> 1) & 0x7FF)
    return struct.pack("<HH", hw1, hw2)


def marker_routine(marker, preserve_r0):
    """Write the 4 marker bytes to r4+5..r4+8 and return (bx lr).

    r4 = identity reply buffer. With preserve_r0=True the routine wraps the body in
    push {r0} / pop {r0}: the Pro handler reuses r0 (=9) right after this site to store
    the firmware version low byte, so r0 must survive. (The Ultra handler reloads r0,
    which is why the published Ultra routine does not need this.)
    """
    assert len(marker) == 4
    # Thumb encodings: movs r0,#c = 0x2000|c ; strb r0,[r4,#imm5] = 0x7000|imm<<6|rn<<3|rt
    out = struct.pack("<H", 0xB401) if preserve_r0 else b""        # push {r0}
    for k, c in enumerate(marker):
        out += struct.pack("<H", 0x2000 | c)                              # movs r0, #c
        out += struct.pack("<H", 0x7000 | ((5 + k) << 6) | (4 << 3) | 0)  # strb r0,[r4,#5+k]
    if preserve_r0:
        out += struct.pack("<H", 0xBC01)                                  # pop {r0}
    out += b"\x70\x47"                                                    # bx lr
    return out


def build(stock, identity_site, hook_site, marker=MARKER, preserve_r0=True):
    assert stock[identity_site:identity_site + 8] == EXPECT_ID, "identity site mismatch"
    assert stock[hook_site:hook_site + 4] == EXPECT_HOOK, "hook site mismatch"
    assert len(stock) <= CODE_BASE, "stock image too long for this layout"
    out = bytearray(stock)
    # 1) hook the handler prologue
    out[hook_site:hook_site + 4] = _thumb_branch(hook_site, CODE_BASE, link=False)
    # 2) identity marker call + two NOPs
    out[identity_site:identity_site + 8] = (
        _thumb_branch(identity_site, MARKER_ADDR, link=True) + b"\x00\xbf\x00\xbf"
    )
    # 3) appended code
    out += b"\xff" * (CODE_BASE - len(stock))
    code = bytearray(CODE_HEAD)
    code += _thumb_branch(CODE_BASE + len(code), hook_site + 4, link=False)  # back to handler body
    code += LITERALS
    out += code
    out += b"\xff" * (MARKER_ADDR - (CODE_BASE + len(code)))
    out += marker_routine(marker, preserve_r0)
    return bytes(out)


def load_stock(path):
    data = open(path, "rb").read()
    if hashlib.sha256(data).hexdigest() != PRO_STOCK_SHA256:
        try:  # the vendor download is a raw-deflate stream
            inflated = zlib.decompress(data, -15)
            if hashlib.sha256(inflated).hexdigest() == PRO_STOCK_SHA256:
                return inflated
        except zlib.error:
            pass
        sys.exit("Input is not the expected Pro ID2304 V309 image (SHA-256 mismatch). Stopping.")
    return data


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "pro":
        stock = load_stock(sys.argv[2])
        site_id, site_hook = PRESETS["pro2304"]
        patched = build(stock, site_id, site_hook)
        open(sys.argv[3], "wb").write(patched)
        print("stock  sha256:", hashlib.sha256(stock).hexdigest(), len(stock))
        print("patched sha256:", hashlib.sha256(patched).hexdigest(), len(patched))
    elif len(sys.argv) == 4 and sys.argv[1] == "selftest":
        ultra_stock = open(sys.argv[2], "rb").read()
        ultra_f6pk = open(sys.argv[3], "rb").read()
        site_id, site_hook = PRESETS["ultra2381"]
        rebuilt = build(ultra_stock, site_id, site_hook, preserve_r0=False)
        print("rebuilt == published F6PK image:", rebuilt == ultra_f6pk, len(rebuilt), len(ultra_f6pk))
        sys.exit(0 if rebuilt == ultra_f6pk else 1)
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
