"""Runs tools/fun60pro_flasher.py against a SIMULATED keyboard and bootloader.
Checks frames, block reassembly, safety refusals, failure handling and the recovery path.
It proves the code does what the protocol notes say; it does not prove a real bootloader agrees."""
import builtins, contextlib, io, struct, sys, types, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import load_module, load_stock, skip, check

STOCK = load_stock()
if STOCK is None:
    skip("original ID2304 V309 image not found in firmware/ (see firmware/README.md)")
fl = load_module("fl", "tools/fun60pro_flasher.py")
bp = load_module("bp", "tools/build_pro_patch.py")
fl.sleep = lambda s: None
PATCHED = bp.build(STOCK, *bp.PRESETS["pro2304"])
PATCHED2 = bp.build_v2(STOCK, *bp.PRESETS["pro2304-v2"])
import hashlib, tempfile
check(hashlib.sha256(PATCHED).hexdigest() in fl.KNOWN_IMAGES and hashlib.sha256(PATCHED2).hexdigest() in fl.KNOWN_IMAGES,
      "both builder outputs (v1 and v2) are images the flasher accepts")
tmp = tempfile.mkdtemp()
open(os.path.join(tmp, "stock.bin"), "wb").write(STOCK)
open(os.path.join(tmp, "patched.bin"), "wb").write(PATCHED)
open(os.path.join(tmp, "patched2.bin"), "wb").write(PATCHED2)
bad = bytearray(STOCK); bad[0x10000] ^= 1
open(os.path.join(tmp, "bad.bin"), "wb").write(bad)
P = lambda n: os.path.join(tmp, n)


class Sim:
    def __init__(s, mode='normal', model=2304, version=0x0309, marker=b'\0\0\0\0', marker9=b'\0\0\0\0', normal_count=1,
                 fail_chunk=None, end_status=0x55, start_silent=False):
        s.mode = mode; s.model = model; s.version = version; s.marker = marker; s.marker9 = marker9; s.normal_count = normal_count
        s.fail_chunk = fail_chunk; s.end_status = end_status; s.start_silent = start_silent
        s.sent = []; s.reply = []; s.entered = False; s.started = False; s.expected = 0
        s.chunks = []; s.end = None; s.start = None; s.flashed = None

    def identity(s):
        d = [0x8F, s.model & 255, s.model >> 8] + list(s.marker) + [s.version & 255, s.version >> 8] + list(s.marker9)
        return d + [0] * (64 - len(d))


class FakeDev:
    def __init__(s, sim): s.sim = sim
    def open_path(s, p): pass
    def close(s): pass

    def send_feature_report(s, data):
        sim = s.sim
        assert len(data) == 65 and data[0] == 0, "frame must be report ID 0 + 64 bytes"
        pl = bytes(data[1:]); sim.sent.append((sim.mode, pl))
        if sim.mode == 'normal':
            c = pl[0]
            if c == 0x8F: sim.reply = sim.identity()
            elif c == 0x87: sim.reply = [0x87, 5, 5, 3, 0, 255, 255, 255] + [0] * 56
            elif pl[:5] == bytes([0x7F, 0x55, 0xAA, 0x55, 0xAA]):
                assert pl[7] == 0x82; sim.entered = True; sim.mode = 'boot'
        else:
            if pl[0] == 0xBA and pl[1] == 0xC0 and not sim.chunks:  # (re)start; may be resent up to 10 times
                sim.started = True; sim.start = pl[:7]; sim.expected = struct.unpack('<H', pl[2:4])[0]
                sim.reply = [] if sim.start_silent else [1] + [0] * 63
            elif sim.started and len(sim.chunks) < sim.expected:
                if sim.fail_chunk is not None and len(sim.chunks) == sim.fail_chunk:
                    raise IOError("simulated write failure")
                sim.chunks.append(pl)
            elif sim.started and pl[0] == 0xBA and pl[1] == 0xC2:
                sim.end = pl[:12]; r = [0] * 64; r[4] = sim.end_status; sim.reply = r
                if sim.end_status == 0x55:
                    length = struct.unpack('<I', pl[8:12])[0]
                    sim.flashed = b''.join(sim.chunks)[:length]
                    sim.marker = fl.MARKER if sim.flashed == PATCHED[fl.APP_OFFSET:] else b'\0\0\0\0'
                    sim.marker9 = fl.MARKER if sim.flashed == PATCHED2[fl.APP_OFFSET:] else b'\0\0\0\0'
                    sim.mode = 'normal'; sim.started = False
        return len(data)

    def get_feature_report(s, rid, n):
        r = list(s.sim.reply) if s.sim.reply else []
        if not r: raise IOError("no data")
        return [0] + (r + [0] * 64)[:64]  # hidapi on Windows keeps the report ID byte in front


def install(sim):
    m = types.ModuleType('hid')
    def enum(vid, pid):
        out = []
        if sim.mode == 'normal' and pid == fl.PID_NORMAL:
            for i in range(sim.normal_count):
                out.append(dict(vendor_id=vid, product_id=pid, usage_page=0xFFFF, usage=2, interface_number=2, path=b'n%d' % i))
            out.append(dict(vendor_id=vid, product_id=pid, usage_page=1, usage=6, interface_number=0, path=b'kb'))
        if sim.mode == 'boot' and pid == fl.PID_BOOT:
            out.append(dict(vendor_id=vid, product_id=pid, usage_page=0xFF01, usage=1, interface_number=0, path=b'b0'))
        return out
    m.enumerate = enum; m.device = lambda: FakeDev(sim); sys.modules['hid'] = m


def run(args, sim, typed=None):
    install(sim); fl.LOG.clear()
    ns = fl.argparse.Namespace(**args); inp = builtins.input
    if typed is not None: builtins.input = lambda p='': typed
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            try: ns.fn(ns); res = "OK"
            except fl.Abort as e: res = "ABORT: " + str(e)
    finally: builtins.input = inp
    return res, buf.getvalue()


def fa(img, arm=True, rec=False): return dict(image=P(img), arm=arm, recover_in_bootloader=rec, pace_ms=0, fn=fl.cmd_flash)


body_p = PATCHED[fl.APP_OFFSET:]
r, out = run(dict(image=P("stock.bin"), fn=fl.cmd_plan), Sim())
check("bac05c06fc9601" in out and "bac25c06cabe8800fc960100" in out, "plan(stock) prints the expected start/end frames")
r, out = run(dict(image=P("patched.bin"), fn=fl.cmd_plan), Sim())
check("bac06106169801" in out and "bac261061978890016980100" in out, "plan(patched) prints the expected start/end frames")
s = Sim(); r, out = run(fa("bad.bin"), s, "FLASH 2304")
check(r.startswith("ABORT") and not s.sent, "unknown image refused before any USB traffic")
s = Sim(); r, out = run(fa("stock.bin", arm=False), s)
check(r == "OK" and not s.entered and all(p[0] != 0x7F for m, p in s.sent) and "Nothing was sent" in out, "flash without --arm sends only the identity read")
s = Sim(model=2381); r, out = run(fa("patched.bin"), s, "FLASH 2304")
check(r.startswith("ABORT") and "2381" in r and not s.entered, "model 2381 refused, no enter-bootloader command sent")
s = Sim(version=0x0302); r, out = run(fa("patched.bin"), s, "FLASH 2304")
check(r.startswith("ABORT") and not s.entered, "unexpected firmware version refused")
s = Sim(normal_count=2); r, out = run(fa("stock.bin"), s, "FLASH 2304")
check(r.startswith("ABORT") and not s.entered, "two keyboards connected refused")
s = Sim(); r, out = run(fa("patched.bin"), s, "yes")
check(r.startswith("ABORT") and not s.entered, "wrong confirmation phrase -> nothing sent")
s = Sim(); r, out = run(fa("patched.bin"), s, "FLASH 2304")
check(r == "OK" and s.entered, "flash(patched) completes")
check(s.flashed == body_p, "received blocks reassemble to image[0x5000:] exactly")
check(s.start.hex() == "bac06106169801" and s.end.hex() == "bac261061978890016980100", "start/end frames sent equal the planned ones")
check(len(s.chunks) == 1633 and all(len(c) == 64 for c in s.chunks), "1633 blocks of 64 bytes")
check("marker F6PK" in out, "post-flash identity shows the marker")
check(all(m == 'boot' for m, p in s.sent if p[:2] in (bytes([0xBA, 0xC0]), bytes([0xBA, 0xC2]))), "BA frames only sent to the bootloader device")
s = Sim(marker=fl.MARKER); r, out = run(fa("stock.bin"), s, "FLASH 2304")
check(r == "OK" and s.flashed == STOCK[fl.APP_OFFSET:] and "original (no marker)" in out, "restore stock over the patched firmware")
s = Sim(fail_chunk=700); r, out = run(fa("patched.bin"), s, "FLASH 2304")
check(r.startswith("ABORT") and s.end is None and len(s.chunks) == 700, "mid-transfer failure aborts, no end frame, no retry")
s = Sim(end_status=0x00); r, out = run(fa("patched.bin"), s, "FLASH 2304")
check(r.startswith("ABORT") and "0x55" in r, "missing 0x55 confirmation reported as failure")
s = Sim(start_silent=True); r, out = run(fa("patched.bin"), s, "FLASH 2304")
check(r.startswith("ABORT") and not s.chunks, "no answer to the start frame -> no data written")
s = Sim(mode='boot'); r, out = run(fa("stock.bin"), s, "RECOVER 2304")
check(r.startswith("ABORT") and not s.sent, "bootloader-only without --recover-in-bootloader refused")
s = Sim(mode='boot'); r, out = run(fa("patched.bin", rec=True), s, "RECOVER 2304")
check(r.startswith("ABORT") and not s.sent, "patched image refused in recovery mode")
s = Sim(mode='boot'); r, out = run(fa("stock.bin", rec=True), s, "RECOVER 2304")
check(r == "OK" and s.flashed == STOCK[fl.APP_OFFSET:] and not s.entered, "recovery flash of stock from bootloader mode")
s = Sim(); r, out = run(dict(fn=fl.cmd_inspect), s)
check(r == "OK" and all(p[0] in (0x8F, 0x87) for m, p in s.sent) and "model 2304" in out, "inspect sends only 0x8F / 0x87 reads")
# ---- v2 image (marker at identity bytes 9-12, model bytes untouched)
_, n2, _, st2, en2 = fl.build_frames(PATCHED2)
r, out = run(dict(image=P("patched2.bin"), fn=fl.cmd_plan), Sim())
check(st2.hex() in out and en2.hex() in out and "image kind     : patched2" in out, "plan(patched2) prints its own start/end frames")
s = Sim(); r, out = run(fa("patched2.bin"), s, "FLASH 2304")
check(r == "OK" and s.flashed == PATCHED2[fl.APP_OFFSET:] and len(s.chunks) == n2, "flash(patched2) completes and the blocks reassemble exactly")
check("marker F6PK at bytes 9-12 (v2 image)" in out and "identity matches the flashed image" in out, "post-flash identity shows the v2 marker and the model bytes intact")
check(s.model == 2304 and s.marker == b'\0\0\0\0', "v2 leaves identity bytes 3-6 (model upper bytes) at zero")
s = Sim(marker=fl.MARKER); r, out = run(fa("patched2.bin"), s, "FLASH 2304")
check(r == "OK" and s.flashed == PATCHED2[fl.APP_OFFSET:] and "bytes 9-12" in out, "v2 flashes over a keyboard that runs the v1 image")
s = Sim(marker9=fl.MARKER); r, out = run(fa("stock.bin"), s, "FLASH 2304")
check(r == "OK" and "original (no marker)" in out, "restore stock over the v2 image")
s = Sim(mode='boot'); r, out = run(fa("patched2.bin", rec=True), s, "RECOVER 2304")
check(r.startswith("ABORT") and not s.sent, "v2 image refused in recovery mode (stock only)")
print("\nALL FLASHER SIMULATION TESTS PASSED")
