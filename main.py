#!/usr/bin/env python3
"""news-image-20261123 R5 — copy the pre-rendered entry.png to the output.

Stdlib only. Verifies size (<= 1 MiB), SHA-256 and PNG SOI/EOI markers
both before and after the chunked copy, so a truncated or corrupt file
can never pass silently.
"""
import hashlib
import os
import sys

MAX_BYTES = 1048576
CHUNK = 65536
PNG_SOI = b"\x89PNG\r\n\x1a\n"
PNG_EOI = b"IEND"


def fail(msg):
    sys.stderr.write("main.py: error: %s\n" % msg)
    sys.exit(1)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            data = f.read(CHUNK)
            if not data:
                break
            h.update(data)
    return h.hexdigest()


def check_png(path):
    """Return (size, sha256) after verifying PNG structure markers."""
    try:
        size = os.path.getsize(path)
    except OSError as e:
        fail("cannot stat %s: %s" % (path, e))
    if size > MAX_BYTES:
        fail("%s is %d bytes, over the 1 MiB limit" % (path, size))
    if size < 8 + 12:
        fail("%s is too small to be a PNG (%d bytes)" % (path, size))
    with open(path, "rb") as f:
        head = f.read(8)
        f.seek(-12, os.SEEK_END)
        tail = f.read(12)
    if head != PNG_SOI:
        fail("%s does not start with the PNG signature" % path)
    if tail[4:8] != PNG_EOI:
        fail("%s does not end with the PNG IEND chunk" % path)
    return size, sha256_of(path)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    if not outdir:
        fail("MAKEFUN_OUTPUT_DIR is empty")
    if not os.path.isdir(outdir):
        try:
            os.makedirs(outdir)
        except OSError as e:
            fail("cannot create output dir %s: %s" % (outdir, e))
    dst = os.path.join(outdir, "entry.png")
    if os.path.abspath(src) == os.path.abspath(dst):
        fail("source and destination are the same file")
    try:
        if os.path.samefile(src, dst):
            fail("source and destination are the same file")
    except OSError:
        pass  # dst does not exist yet: expected on a fresh run
    src_size, src_sha = check_png(src)
    with open(src, "rb") as fin, open(dst, "wb") as fout:
        while True:
            data = fin.read(CHUNK)
            if not data:
                break
            fout.write(data)
    dst_size, dst_sha = check_png(dst)
    if dst_size != src_size or dst_sha != src_sha:
        fail("copy mismatch: src %d bytes %s, dst %d bytes %s"
             % (src_size, src_sha, dst_size, dst_sha))
    print("wrote %s (%d bytes, sha256 %s)" % (dst, dst_size, dst_sha))


if __name__ == "__main__":
    main()
