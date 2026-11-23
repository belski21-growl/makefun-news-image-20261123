#!/usr/bin/env python3
"""news-image-20261123 (Cairo renderer) — copy entry.png to output dir.

Stdlib only. Verifies size <= 1 MiB + SHA-256 + SOI/EOI BEFORE and AFTER
the chunked copy (64 KiB chunks). Samefile + output-dir guards.
"""
import hashlib
import os
import sys

EXPECTED_SHA256 = "a311a7b6df4b0ecf592c85899ff4b28bb99122fa32ccc968fd09c8f1a357ce4c"
EXPECTED_SIZE = 280568
MAX_SIZE = 1048576
CHUNK = 65536


def fail(msg):
    print("FAIL: " + msg, file=sys.stderr)
    sys.exit(1)


def check(path, label):
    try:
        size = os.path.getsize(path)
    except OSError as e:
        fail(label + ": cannot stat: " + str(e))
    if size > MAX_SIZE:
        fail(label + ": size %d > 1 MiB" % size)
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            head = f.read(2)
            f.seek(0)
            while True:
                data = f.read(CHUNK)
                if not data:
                    break
                h.update(data)
            f.seek(-2, os.SEEK_END)
            tail = f.read(2)
    except OSError as e:
        fail(label + ": cannot read: " + str(e))
    if head != b"\x89\x50":
        fail(label + ": bad SOI marker")
    if tail != b"\x60\x82":
        fail(label + ": bad EOI marker")
    digest = h.hexdigest()
    if digest != EXPECTED_SHA256:
        fail(label + ": sha256 mismatch: " + digest)
    if size != EXPECTED_SIZE:
        fail(label + ": size mismatch: %d != %d" % (size, EXPECTED_SIZE))
    return size


def main():
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "")
    if not out_dir:
        fail("MAKEFUN_OUTPUT_DIR is not set")
    if not os.path.isdir(out_dir):
        fail("output dir does not exist: " + out_dir)
    dst = os.path.join(out_dir, "entry.png")
    if os.path.abspath(src) == os.path.abspath(dst):
        fail("source and destination are the same file")
    if os.path.exists(dst) and os.path.samefile(src, dst):
        fail("source and destination are the same file")
    check(src, "source")
    try:
        with open(src, "rb") as fin, open(dst, "wb") as fout:
            while True:
                data = fin.read(CHUNK)
                if not data:
                    break
                fout.write(data)
    except OSError as e:
        fail("copy failed: " + str(e))
    check(dst, "output")
    print("OK: entry.png (%d bytes, sha256 %s)" % (EXPECTED_SIZE,
                                                   EXPECTED_SHA256))


if __name__ == "__main__":
    main()
