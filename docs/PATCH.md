# The firmware patch

The patch is a port of the FUN60 Ultra "F6PK" patch from
[sinsaintly/fun60-signalrgb-fix](https://github.com/sinsaintly/fun60-signalrgb-fix) to the Pro (V309).
The 100-byte entry routine and the 20-byte literal pool used by `tools/build_pro_patch.py` are copied from the Ultra project's
published image (they are position independent); the branch targets are regenerated for the Pro. Check that project's license
and credit it if you reuse this.

All offsets are **file offsets**. The file is a flash dump mapped at `0x08000000`, so file offset `X` is address `0x08000000 + X`.

## What changes in the original image (124,668 bytes -> 124,950 bytes)

| Where (Pro) | Original | Patched | Meaning |
|---|---|---|---|
| `0x11d92`, 8 bytes | `66 71 a6 71 e6 71 26 72` | `0c f0 35 fd 00 bf 00 bf` | four `strb r6,[r4,#5..#8]` (zeros in the identity reply) become `bl 0x1e800` + two `nop` |
| `0x1238c`, 4 bytes | `2d e9 f0 43` | `0c f0 b8 b9` | `push.w {r4-r9,lr}` (first instruction of the report handler) becomes `b.w 0x1e700` |
| `0x1e6fc`-`0x1e6ff` | (end of file) | `ff ff ff ff` | alignment padding |
| `0x1e700`-`0x1e77b` | | new code | hook routine, 124 bytes (below) |
| `0x1e77c`-`0x1e7ff` | | `ff` | fill |
| `0x1e800`-`0x1e815` | | marker routine, 22 bytes | writes "F6PK" to `r4+5..r4+8`, preserving `r0` |

Ultra equivalents: sites `0x11d8c` and `0x12388`; the image ends at `0x1e812`.

## The hook routine (as read from the disassembly, confirmed by emulation)

```
entry (replaces the handler's first instruction):
    push {r0-r3}
    if report_buffer[0x24b] != 2:          # apply flag of the page; the vendor driver sends 1
        pop {r0-r3}
        push.w {r4-r9, lr}                 # the instruction that was replaced
        b.w   <handler + 4>                # = 0x12390, original behaviour
    # flag == 2: this path never reaches the original handler
    if (status_byte & 0x40) == 0: pop {r0-r3}; return      # nothing pending
    clear bit 0x40 of the status byte      # marks the report as consumed
    if report_buffer[0x245] == 0xFF       # selector
       and report_buffer[0x246] == 6      # page index
       and u16(report_buffer[0x248]) == 0x2A   # length of the last page
       and mode_struct[+8] == 13          # "User Picture"
       and other_struct[+0x1c] == 0:
        copy 378 bytes from report_buffer+0x42 to the RAM LED buffer
    pop {r0-r3}; return
```

The command byte `0x0C` itself is not tested by the routine; the original dispatcher has already routed the report to this handler.
This pseudocode is a reading of the 100-byte routine, not vendor documentation.

RAM addresses (the same in the Ultra and Pro images; semantics inferred from the Ultra project and the code):

| Address | Use |
|---|---|
| `0x20006d14` | report buffer (the apply flag is at `+0x24b`, the accumulated color data at `+0x42`) |
| `0x2000011c` | status byte; bit `0x40` = "report pending" |
| `0x20005ea8` | mode structure; byte at `+8` must be `13` ("User Picture") |
| `0x20006f60` | second structure; byte at `+0x1c` must be `0` |
| `0x20006b94` | RAM LED frame buffer (378 bytes) |

## Differences from the Ultra patch

1. Different offsets (`+4` for the handler, `+6` for the identity site) and a different return address (`0x12390`).
2. **`r0` is preserved** by the marker routine (`push {r0}` / `pop {r0}`). The Pro's code right after the identity site reuses `r0`
   (value 9) to store the firmware version; without this the version would read `0x034B`.
3. Four bytes of padding instead of eight before the new code, so the new code lands at the same address (`0x1e700`).

## Variant v2: keep the vendor driver working

With v1 the marker overwrites identity data bytes 3-6. The vendor driver reads the model as a 32-bit value from identity bytes 1-4 (per the Ultra
project's notes), so bytes 3-4 are part of the model ID and the driver no longer finds the keyboard in its device table. v2 changes where the
marker goes, nothing else:

| Where (Pro) | Original | v2 | Meaning |
|---|---|---|---|
| `0x11da0`, 4 bytes | `00 f0 cc ba` | `0c f0 2e bd` | the identity builder's final `b.w 0x1233c` becomes `b.w 0x1e800` |
| `0x1238c`, 4 bytes | `2d e9 f0 43` | `0c f0 b8 b9` | the same hook as v1 |
| `0x1e800`-`0x1e817`, 24 bytes | | marker routine | `push {r0}`, writes "F6PK" to `[r4+0xb .. r4+0xe]`, `pop {r0}`, `b.w 0x1233c` |

The image is 124,952 bytes (v1: 124,950). The four zero stores to `[r4+5..r4+8]` stay in place, so identity bytes 1-8 are exactly the original's
(`00 09 00 00 00 00 09 03`), and the marker sits in identity data bytes 9-12 (data index = buffer offset - 2), which are zero in the original reply.

Assumptions behind v2: that the vendor driver does not choke on bytes 9-12; that the reply buffer is zeroed before the identity builder runs (the
captured original replies are zero from byte 9 on); and that the shared epilogue at `0x1233c` leaves the buffer alone. **On hardware** the maintainer
reports that, with v2 flashed, the vendor driver recognises the keyboard (one keyboard). The `inspect` output after flashing (whether the marker is
visible in the reply) was not recorded. If the marker does not survive, the plugin simply refuses to stream (it never guesses).
Checked in CPU emulation: model bytes untouched, version `0x0309`, marker at bytes 9-12, `r0 == 3` on return, and the hook behaves exactly like v1.

## How it was checked

* `tools/build_pro_patch.py selftest <ultra_stock> <ultra_F6PK>` reproduces the published Ultra image byte for byte.
* `tests/test_patch_emulation.py` runs the patched image in a CPU emulator (identity reply, `flag=1` state identical to the original
  at `0x12390`, `flag=2` copies to RAM, `flag=2` with another mode copies nothing and still skips the original handler).
* On real hardware the maintainer reports that the patched image was accepted and that live streaming worked on one keyboard
  (FUN60 Pro, model 2304, V309), so the Pro's RAM fields and the code layout behave as the emulation assumed, at least on that unit.
* Not independently checked: that nothing important lives in flash between `0x1e6fc` and the end of the chip's flash (it did not
  matter on the tested keyboard), and anything on other units, revisions or ID variants.

## Inspecting it yourself

```python
from capstone import *            # pip install capstone
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB + CS_MODE_MCLASS)
img = open("ID2304-V309-livepatch.bin", "rb").read()
for i in md.disasm(img[0x1e700:0x1e77c], 0x1e700):
    print(hex(i.address), i.mnemonic, i.op_str)
```
