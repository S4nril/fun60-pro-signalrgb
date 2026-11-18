#!/usr/bin/env python3
"""
FUN60 Pro (device ID 2304) firmware flasher - EXPERIMENTAL. Validated on real hardware by the maintainer
on one keyboard (model 2304, V309); not tested on anything else.

It re-implements the USB update protocol that the MonsGeek web driver uses for this keyboard
family (read from the driver's code), and it only accepts three exact files:

  * the original ID2304 V309 image (as downloaded from the vendor server, or inflated),
  * the experimental live-RGB image built by build_pro_patch.py.

Commands
  plan   <image>                 offline: validates the file and prints the frames. Touches no USB.
  inspect                        read-only: lists the keyboard and reads its identity / LED mode.
  flash  <image> [--arm]         without --arm it only runs the checks. With --arm it flashes
                                 after you type a confirmation phrase.

Install the USB library first:   py -3 -m pip install hidapi

Protocol (vendor driver, class chain o_a -> rxa -> Wda):
  1. feature report 7F 55 AA 55 AA 00 00 82   -> keyboard re-enumerates as VID 3151 / PID 502A
  2. image = file[0x5000:]  (the first 0x5000 bytes are the bootloader and are never sent)
  3. start  : BA C0 <nBlocks LE16> <length LE24>, then wait for any reply
  4. data   : 64-byte blocks, one feature report each (last block zero padded)
  5. end    : BA C2 <nBlocks LE16> <sum of all image bytes LE32> <length LE32>
              success = reply byte 4 equals 0x55 (read 100 ms after sending)

There is no automatic retry after a failure. If something goes wrong, stop and use the
vendor's documented recovery procedure.
"""
import argparse
import hashlib
import json
import math
import struct
import sys
import time
import zlib

VID = 0x3151
PID_NORMAL = 0x502D
PID_BOOT = 0x502A
MODEL_ID = 2304
FW_VERSION = 0x0309
APP_OFFSET = 0x5000
CHUNK = 64
ENTER_BOOT = [0x7F, 0x55, 0xAA, 0x55, 0xAA, 0x00, 0x00, 0x82]
MARKER = b"F6PK"

KNOWN_IMAGES = {
    "237bbe74f2f718a08bf2b8bb9caf6ca026b86817b6baae6130e0a7794d72a6ac": "stock",
    "5934caf51604877baa53c3ddf0b81b8506d8af6a1a73c5f969c020a663f8eb03": "patched",
}

LOG = []


def sleep(seconds):  # separate so tests can replace it
    time.sleep(seconds)


class Abort(Exception):
    pass


def log(event, **kw):
    LOG.append({"t": round(time.time(), 3), "event": event, **kw})


# ------------------------------------------------------------------ image handling

def load_image(path):
    data = open(path, "rb").read()
    digest = hashlib.sha256(data).hexdigest()
    if digest not in KNOWN_IMAGES:
        try:  # the vendor download is a raw-deflate stream
            inflated = zlib.decompress(data, -15)
            if hashlib.sha256(inflated).hexdigest() in KNOWN_IMAGES:
                data, digest = inflated, hashlib.sha256(inflated).hexdigest()
        except zlib.error:
            pass
    if digest not in KNOWN_IMAGES:
        raise Abort("This file is not one of the known ID2304 images (SHA-256 mismatch). Refusing.")
    return data, KNOWN_IMAGES[digest], digest


def build_frames(image):
    body = image[APP_OFFSET:]
    n = math.ceil(len(body) / CHUNK)
    total = sum(body)
    start = bytes([0xBA, 0xC0]) + struct.pack("<H", n) + struct.pack("<I", len(body))[:3]
    end = bytes([0xBA, 0xC2]) + struct.pack("<H", n) + struct.pack("<I", total & 0xFFFFFFFF) + struct.pack("<I", len(body))
    return body, n, total, start, end


def print_plan(image, kind, digest):
    body, n, total, start, end = build_frames(image)
    print(f"image kind     : {kind}")
    print(f"sha256         : {digest}")
    print(f"image size     : {len(image)} bytes (bootloader part skipped: first {APP_OFFSET:#x})")
    print(f"bytes sent     : {len(body)} in {n} blocks of {CHUNK}")
    print(f"sum of bytes   : {total:#010x}")
    print(f"start frame    : {start.hex()}")
    print(f"end frame      : {end.hex()}")
    return body, n, start, end


# ------------------------------------------------------------------ USB helpers

def import_hid():
    try:
        import hid  # package "hidapi"
        return hid
    except ImportError:
        raise Abort("The USB library is missing. Run:  py -3 -m pip install hidapi")


def strip_report_id(resp):
    if resp is None:
        return None
    resp = list(resp)
    return resp[1:] if len(resp) == 65 else resp


def send_feature(dev, data64):
    payload = list(data64) + [0] * (64 - len(data64))
    if len(payload) != 64:
        raise Abort("internal error: frame longer than 64 bytes")
    try:
        n = dev.send_feature_report([0x00] + payload)
    except (IOError, OSError, ValueError) as e:
        raise Abort("USB write failed: %s" % e)
    if n is not None and n < 0:
        raise Abort("USB write failed")


def read_feature(dev, delay_ms):
    sleep(delay_ms / 1000.0)
    try:
        return strip_report_id(dev.get_feature_report(0x00, 65))
    except (IOError, OSError, ValueError):
        return None


def query(dev, cmd):
    """Read-type command: <cmd> 00 00 00 00 00 00 <0xFF-cmd>, then GET_REPORT."""
    send_feature(dev, [cmd, 0, 0, 0, 0, 0, 0, (0xFF - cmd) & 0xFF])
    resp = read_feature(dev, 20)
    if not resp or len(resp) < 9:
        return None
    if resp[0] == cmd:
        return resp
    if resp[1] == cmd:
        return resp[1:]
    return None


def parse_identity(d):
    if not d:
        return None
    return {
        "model": d[1] | (d[2] << 8),
        "marker": bytes(d[3:7]),
        "version": d[7] | (d[8] << 8),
    }


def normal_devices(hid):
    out = []
    for d in hid.enumerate(VID, PID_NORMAL):
        if d.get("usage_page") == 0xFFFF and d.get("interface_number", 2) in (2, -1):
            out.append(d)
    return out


def boot_devices(hid):
    return [d for d in hid.enumerate(VID, PID_BOOT)]


def open_dev(hid, info):
    dev = hid.device()
    dev.open_path(info["path"])
    return dev


def describe(ident):
    if not ident:
        return "no valid reply"
    kind = "marker " + ident["marker"].decode("ascii", "replace") if ident["marker"] == MARKER else (
        "original (no marker)" if ident["marker"] == b"\x00\x00\x00\x00" else "unknown marker " + ident["marker"].hex())
    return "model %d, version 0x%04x, %s" % (ident["model"], ident["version"], kind)


# ------------------------------------------------------------------ commands

def cmd_plan(args):
    image, kind, digest = load_image(args.image)
    print_plan(image, kind, digest)
    print("\nNothing was sent to any device.")


def cmd_inspect(args):
    hid = import_hid()
    nd, bd = normal_devices(hid), boot_devices(hid)
    print("keyboards in normal mode (3151:502D, interface 2):", len(nd))
    print("devices in bootloader mode (3151:502A):", len(bd))
    for info in nd:
        dev = open_dev(hid, info)
        try:
            ident = parse_identity(query(dev, 0x8F))
            print("identity:", describe(ident))
            led = query(dev, 0x87)
            if led:
                print("LED settings: mode %d, speed raw %d, brightness %d, option %d, rgb %d/%d/%d" % tuple(led[1:8]))
        finally:
            dev.close()
    print("Only read requests were sent.")


def wait_for(fn, timeout, step=0.5):
    end = time.time() + timeout
    while True:
        r = fn()
        if r:
            return r
        if time.time() >= end:
            return None
        sleep(step)


def cmd_flash(args):
    image, kind, digest = load_image(args.image)
    body, n, start, end = print_plan(image, kind, digest)
    hid = import_hid()
    nd, bd = normal_devices(hid), boot_devices(hid)

    # ---- which situation are we in?
    recovering = False
    if nd and bd:
        raise Abort("A keyboard in normal mode and a bootloader device are both present. Disconnect everything except one keyboard.")
    if len(nd) > 1:
        raise Abort("More than one 3151:502D keyboard is connected. Disconnect the others.")
    if not nd and not bd:
        raise Abort("No FUN60 keyboard found (3151:502D or bootloader 3151:502A).")
    if bd:
        recovering = True
        if len(bd) > 1:
            raise Abort("More than one bootloader device is connected.")
        if not args.recover_in_bootloader:
            raise Abort("The keyboard is in bootloader mode, so its model cannot be verified. "
                        "If you are sure it is a FUN60 Pro (ID 2304), use the stock image with --recover-in-bootloader.")
        if kind != "stock":
            raise Abort("Recovery from bootloader mode only accepts the original (stock) image.")
        print("\nBootloader mode: model NOT verifiable. Only the stock image is allowed here.")
    else:
        dev = open_dev(hid, nd[0])
        try:
            ident = parse_identity(query(dev, 0x8F))
        finally:
            dev.close()
        print("\ncurrent keyboard:", describe(ident))
        if not ident:
            raise Abort("The keyboard did not answer the identity request. Stopping.")
        if ident["model"] != MODEL_ID:
            raise Abort("This keyboard is model %d, not %d (FUN60 Pro). Refusing." % (ident["model"], MODEL_ID))
        if ident["version"] != FW_VERSION:
            raise Abort("Unexpected firmware version 0x%04x (expected 0x%04x). Refusing." % (ident["version"], FW_VERSION))

    if not args.arm:
        print("\nChecks passed. Nothing was sent (no --arm).")
        return

    phrase = "RECOVER 2304" if recovering else "FLASH 2304"
    typed = input('\nThis will rewrite the keyboard firmware with the "%s" image.\nType %s to continue: ' % (kind, phrase))
    if typed.strip() != phrase:
        raise Abort("Confirmation phrase not typed. Nothing was sent.")

    # ---- step 1: enter bootloader
    if not recovering:
        dev = open_dev(hid, nd[0])
        log("enter_bootloader")
        try:
            try:
                send_feature(dev, ENTER_BOOT)
            except Abort:
                pass  # the device may drop off the bus while answering
        finally:
            try:
                dev.close()
            except Exception:
                pass
        print("waiting for the bootloader (3151:502A)...")
        found = wait_for(lambda: boot_devices(hid), 50)
        if not found:
            raise Abort("The keyboard did not appear in bootloader mode. Nothing was flashed.")
        bd = found
        sleep(1.0)
    cands = [d for d in bd if d.get("usage_page") == 0xFF01] or (bd if len(bd) == 1 else [])
    if not cands:
        raise Abort("Could not pick the bootloader HID interface (usage page 0xFF01).")
    boot = open_dev(hid, cands[0])

    try:
        # ---- step 2: start frame (driver: up to 10 tries, 1 s apart)
        reply = None
        for attempt in range(10):
            send_feature(boot, start)
            reply = read_feature(boot, 5)
            sleep(1.0)
            if reply:
                break
        if not reply:
            raise Abort("The bootloader did not answer the start frame. Nothing was written.")
        log("start_ok", blocks=n)

        # ---- step 3: data blocks
        for p in range(n):
            send_feature(boot, body[p * CHUNK:(p + 1) * CHUNK])
            if args.pace_ms:
                sleep(args.pace_ms / 1000.0)
            if p % 200 == 0:
                print("  block %d / %d" % (p, n))

        # ---- step 4: end frame
        send_feature(boot, end)
        reply = read_feature(boot, 100)
        log("end_reply", reply=(bytes(reply[:8]).hex() if reply else None))
        if not reply or len(reply) < 5 or reply[4] != 0x55:
            raise Abort("The bootloader did not confirm the update (expected 0x55). Do NOT retry blindly; "
                        "see the vendor recovery procedure.")
    finally:
        try:
            boot.close()
        except Exception:
            pass

    print("update confirmed by the bootloader. Waiting for the keyboard to restart...")
    back = wait_for(lambda: normal_devices(hid), 40)
    if not back:
        print("The keyboard did not reappear within 40 s. Unplug and replug it, then run: inspect")
        return
    sleep(1.0)
    dev = open_dev(hid, back[0])
    try:
        ident = parse_identity(query(dev, 0x8F))
    finally:
        dev.close()
    print("after flashing:", describe(ident))
    if ident and ident["model"] == MODEL_ID:
        want_marker = MARKER if kind == "patched" else b"\x00\x00\x00\x00"
        print("identity matches the flashed image." if ident["marker"] == want_marker else
              "WARNING: the marker does not match the flashed image.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("image"); p.set_defaults(fn=cmd_plan)
    p = sub.add_parser("inspect"); p.set_defaults(fn=cmd_inspect)
    p = sub.add_parser("flash"); p.add_argument("image")
    p.add_argument("--arm", action="store_true", help="actually flash (still asks for a typed confirmation)")
    p.add_argument("--recover-in-bootloader", action="store_true", help="stock image only, keyboard already in bootloader mode")
    p.add_argument("--pace-ms", type=float, default=3.0, help="pause after each 64-byte block (default 3)")
    p.set_defaults(fn=cmd_flash)
    args = ap.parse_args()
    try:
        args.fn(args)
        code = 0
    except Abort as e:
        print("\nSTOPPED:", e)
        log("aborted", reason=str(e))
        code = 2
    if args.cmd == "flash":
        open("flash-pro-log.json", "w").write(json.dumps(LOG, indent=1))
    sys.exit(code)


if __name__ == "__main__":
    main()
