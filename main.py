#!/usr/bin/env python3
"""Ship the R2 entry: copy entry.png to $MAKEFUN_OUTPUT_DIR and verify it.

Stdlib only — no PIL, so this runs even without the generator's deps.
"""
import hashlib
import os
import struct
import sys

MAX_BYTES = 1048576
MAX_DIM = 1024
PNG_SIG = b"\x89PNG\r\n\x1a\n"
# Measured from the R2 render itself (entry.png shipped with this repo).
EXPECTED_BYTES = 180839  # filled in by the builder after rendering; see below
EXPECTED_SHA256 = "b270dca6dcbd109a1261c9a081204ec93cda50b4ac953ce26ea197f1de8c6019"


def fail(msg):
    print("FAIL: %s" % msg, file=sys.stderr)
    sys.exit(1)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    dst = os.path.join(outdir, "entry.png")
    with open(src, "rb") as f:
        data = f.read()
    if not data.startswith(PNG_SIG):
        fail("not a PNG (bad signature)")
    if len(data) > MAX_BYTES:
        fail("too large: %d bytes > %d" % (len(data), MAX_BYTES))
    w, h = struct.unpack(">II", data[16:24])
    if w > MAX_DIM or h > MAX_DIM:
        fail("too big: %dx%d > %dx%d" % (w, h, MAX_DIM, MAX_DIM))
    with open(dst, "wb") as f:
        f.write(data)
    sha = hashlib.sha256(data).hexdigest()
    print("entry.png: %d bytes, %dx%d, sha256=%s" % (len(data), w, h, sha))
    if EXPECTED_BYTES and len(data) != EXPECTED_BYTES:
        fail("byte size %d != expected %d" % (len(data), EXPECTED_BYTES))
    if EXPECTED_SHA256 and sha != EXPECTED_SHA256:
        fail("sha256 mismatch vs expected")
    print("verified against shipped artefact: OK")


if __name__ == "__main__":
    main()
