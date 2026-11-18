"""Shared helpers for the tests. The tests never ship vendor firmware: put your own copy of the
original image in firmware/ (see firmware/README.md). Without it the tests that need it are skipped."""
import hashlib, os, sys, zlib, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOCK_SHA256 = "237bbe74f2f718a08bf2b8bb9caf6ca026b86817b6baae6130e0a7794d72a6ac"


def load_module(name, relpath):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, relpath))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_stock():
    """Return the original ID2304 V309 image (inflated), or None if it is not available."""
    for name in ("stock-ID2304-V309.bin", "fw_2304.bin"):
        p = os.path.join(ROOT, "firmware", name)
        if os.path.exists(p):
            data = open(p, "rb").read()
            if hashlib.sha256(data).hexdigest() != STOCK_SHA256:
                try:
                    data = zlib.decompress(data, -15)  # raw deflate, as served by the vendor
                except zlib.error:
                    pass
            if hashlib.sha256(data).hexdigest() == STOCK_SHA256:
                return data
    return None


def skip(msg):
    print("SKIPPED:", msg)
    sys.exit(0)


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        sys.exit(1)
