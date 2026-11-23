#!/usr/bin/env python3
"""Ship the R3 entry: copy entry.png to $MAKEFUN_OUTPUT_DIR and verify it.

Stdlib only. Verifies PNG signature, size <= 1 MiB, dimensions <= 1024x1024
(read from the PNG header, bytes 16:24), then checks the copy against the
expected byte size + sha256 measured from the R3 render.
"""
import hashlib
import os
import struct
import sys

EXPECTED_BYTES = 183607  # filled from the R3 render
EXPECTED_SHA256 = "57da8dcf1f8525a48e4b0a1c12dfcca66d979d3309a742dff4b85aa5eb507901"  # filled from the R3 render

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    with open(SRC, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        print("FAIL: not a PNG", file=sys.stderr)
        return 1
    if len(data) > 1048576:
        print("FAIL: size %d > 1048576" % len(data), file=sys.stderr)
        return 1
    w, h = struct.unpack(">II", data[16:24])
    if w > 1024 or h > 1024:
        print("FAIL: dimensions %dx%d > 1024x1024" % (w, h), file=sys.stderr)
        return 1
    sha = hashlib.sha256(data).hexdigest()
    print("size=%d dimensions=%dx%d sha256=%s" % (len(data), w, h, sha))
    if len(data) != EXPECTED_BYTES or sha != EXPECTED_SHA256:
        print("FAIL: mismatch expected bytes=%d sha256=%s" % (
            EXPECTED_BYTES, EXPECTED_SHA256), file=sys.stderr)
        return 1
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)
    print("OK: entry.png -> %s" % out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
