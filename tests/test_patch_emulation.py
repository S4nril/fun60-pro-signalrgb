"""CPU emulation (Unicorn, Thumb-2) of the patched Pro image. Needs: pip install unicorn capstone
Checks the identity snippet and the hook paths. It validates the mechanical correctness of the
port; it does NOT validate the meaning of the RAM fields on real hardware."""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import load_module, load_stock, skip, check
STOCK = load_stock()
if STOCK is None: skip("original ID2304 V309 image not found in firmware/")
try:
    from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS
    from unicorn.arm_const import *
except ImportError:
    skip("unicorn is not installed (pip install unicorn)")
bp = load_module("bp", "tools/build_pro_patch.py")
IMG = bp.build(STOCK, *bp.PRESETS["pro2304"])
FL, RAM = 0x08000000, 0x20000000
REPORT, STATUS, MODE, ST2, LED = RAM + 0x6d14, RAM + 0x11c, RAM + 0x5ea8, RAM + 0x6f60, RAM + 0x6b94


def mk(img):
    mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
    mu.mem_map(FL, 0x40000); mu.mem_write(FL, img); mu.mem_map(RAM, 0x10000)
    return mu


# identity builder snippet
mu = mk(IMG); BUF = RAM + 0x7000
mu.reg_write(UC_ARM_REG_R4, BUF); mu.reg_write(UC_ARM_REG_R6, 0); mu.reg_write(UC_ARM_REG_LR, FL + 0x1f001)
mu.reg_write(UC_ARM_REG_SP, RAM + 0xff00); mu.mem_write(BUF, b'\xaa' * 16)
mu.emu_start(FL + 0x11d8c | 1, FL + 0x11da0, count=200)
b = bytes(mu.mem_read(BUF, 12))
check(int.from_bytes(b[3:5], 'little') == 2304 and b[5:9] == b'F6PK' and int.from_bytes(b[9:11], 'little') == 0x0309,
      "identity reply: model 2304, marker F6PK, version 0x0309 (r0 preserved)")


def setup(img, flag, mode=13, status=0x40, sel=0xff, page=6, length=0x2a, st2=0):
    mu = mk(img)
    mu.mem_write(REPORT + 0x24b, bytes([flag])); mu.mem_write(STATUS, bytes([status]))
    mu.mem_write(REPORT + 0x245, bytes([sel])); mu.mem_write(REPORT + 0x246, bytes([page]))
    mu.mem_write(REPORT + 0x248, struct.pack('<H', length))
    mu.mem_write(MODE + 8, bytes([mode])); mu.mem_write(ST2 + 0x1c, bytes([st2]))
    data = bytes((i * 7 + 3) & 0xff for i in range(378)); mu.mem_write(REPORT + 0x42, data); mu.mem_write(LED, b'\0' * 378)
    regs = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6,
            UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_R12)
    for r, v in zip(regs, range(0x100, 0x10d)): mu.reg_write(r, v)
    mu.reg_write(UC_ARM_REG_LR, FL + 0x1f001); mu.reg_write(UC_ARM_REG_SP, RAM + 0xff00)
    return mu, data


def touched_original(hits): return any(FL + 0x12390 <= h < FL + 0x12600 for h in hits)


def run_to(mu, until):
    hits = []
    from unicorn import UC_HOOK_CODE
    mu.hook_add(UC_HOOK_CODE, lambda uc, a, s, u: hits.append(a))
    mu.emu_start(FL + 0x1238c | 1, until, count=3000)
    return hits


# flag != 2: state at the original handler body must equal the stock image's
def state(img):
    mu, _ = setup(img, 1)
    mu.emu_start(FL + 0x1238c | 1, FL + 0x12390, count=100)
    names = ('R0', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9', 'R10', 'R11', 'R12', 'SP', 'LR', 'PC')
    st = [mu.reg_read(globals()['UC_ARM_REG_' + n]) for n in names]
    sp = mu.reg_read(UC_ARM_REG_SP)
    return st, bytes(mu.mem_read(sp, 28)), bytes(mu.mem_read(RAM, 0x10000))
check(state(STOCK) == state(IMG), "flag=1 (vendor driver): registers, stack and RAM at 0x12390 identical to the stock image")

mu, data = setup(IMG, 2); hits = run_to(mu, FL + 0x1f000)
check(bytes(mu.mem_read(LED, 378)) == data and not touched_original(hits) and (mu.mem_read(STATUS, 1)[0] & 0x40) == 0,
      "flag=2 and mode 13: 378 bytes copied to the LED buffer, original handler skipped")
mu, data = setup(IMG, 2, mode=5); hits = run_to(mu, FL + 0x1f000)
check(bytes(mu.mem_read(LED, 378)) == b'\0' * 378 and not touched_original(hits), "flag=2 and mode != 13: nothing copied, original handler still skipped")

# ---- v2 image: same hook, marker moved to identity bytes 9-12, model bytes untouched
IMG2 = bp.build_v2(STOCK, *bp.PRESETS["pro2304-v2"])
mu = mk(IMG2); BUF = RAM + 0x7000
mu.reg_write(UC_ARM_REG_R4, BUF); mu.reg_write(UC_ARM_REG_R6, 0); mu.reg_write(UC_ARM_REG_R0, 0x1234); mu.reg_write(UC_ARM_REG_LR, FL + 0x1f001)
mu.reg_write(UC_ARM_REG_SP, RAM + 0xff00); mu.mem_write(BUF, b'\xaa' * 24)
mu.emu_start(FL + 0x11d8c | 1, FL + 0x1233c, count=400)
b = bytes(mu.mem_read(BUF, 24))
check(b[3:11] == bytes([0x00, 0x09, 0x00, 0x00, 0x00, 0x00, 0x09, 0x03]), "v2 identity: model bytes 00 09 00 00 untouched, version 0x0309")
check(b[11:15] == b'F6PK' and b[15] == 0xaa, "v2 identity: marker at data bytes 9-12 and nothing else written")
check(mu.reg_read(UC_ARM_REG_R0) == 3, "v2 identity: r0 is 3 on return to the epilogue, as in the original code")
check(state(STOCK) == state(IMG2), "v2, flag=1: registers, stack and RAM at 0x12390 identical to the stock image")
mu, data = setup(IMG2, 2); hits = run_to(mu, FL + 0x1f000)
check(bytes(mu.mem_read(LED, 378)) == data and not touched_original(hits) and (mu.mem_read(STATUS, 1)[0] & 0x40) == 0,
      "v2, flag=2 and mode 13: 378 bytes copied to the LED buffer, original handler skipped")
mu, data = setup(IMG2, 2, mode=5); hits = run_to(mu, FL + 0x1f000)
check(bytes(mu.mem_read(LED, 378)) == b'\0' * 378 and not touched_original(hits), "v2, flag=2 and mode != 13: nothing copied")
print("\nALL EMULATION TESTS PASSED")
