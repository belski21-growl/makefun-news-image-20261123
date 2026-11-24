#!/usr/bin/env python3
"""news-image-20261123 (ronde 4 + polish Goldfish: plume asap tebal,
kubah ranjau dihapus, bahu baris belakang COP31) — salin entry.png ke
direktori output.

Stdlib saja. Memeriksa ukuran (<= 1 MiB), SHA-256, dan penanda PNG
(SOI/EOI) SEBELUM dan SESUDAH penyalinan bertahap (chunk 64 KiB).
Menolak bila direktori output tidak diset / tidak ada, dan bila sumber
dan tujuan adalah file yang sama.
"""
import hashlib
import os
import sys

EXPECTED_SHA256 = "19b5998efe8546270e84f36a4956ab8994c89a062a7cac614d3caece7106ace0"
EXPECTED_SIZE = 312655
MAX_BYTES = 1048576
BLOCK = 65536
PNG_HEAD = b"\x89\x50"
PNG_TAIL = b"\x60\x82"


def abort(reason):
    sys.stderr.write("FAIL: %s\n" % reason)
    sys.exit(1)


def digest_file(path):
    """Kembalikan (ukuran, sha256, 2 byte awal, 2 byte akhir)."""
    try:
        total = os.path.getsize(path)
    except OSError as exc:
        abort("cannot stat %s: %s" % (path, exc))
    sha = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            head = handle.read(2)
            handle.seek(0)
            while True:
                block = handle.read(BLOCK)
                if not block:
                    break
                sha.update(block)
            handle.seek(-2, os.SEEK_END)
            tail = handle.read(2)
    except OSError as exc:
        abort("cannot read %s: %s" % (path, exc))
    return total, sha.hexdigest(), head, tail


def verify(path, which):
    total, digest, head, tail = digest_file(path)
    if total > MAX_BYTES:
        abort("%s: size %d > 1 MiB" % (which, total))
    if total != EXPECTED_SIZE:
        abort("%s: size %d != expected %d" % (which, total, EXPECTED_SIZE))
    if digest != EXPECTED_SHA256:
        abort("%s: sha256 mismatch: %s" % (which, digest))
    if head != PNG_HEAD:
        abort("%s: bad SOI marker" % which)
    if tail != PNG_TAIL:
        abort("%s: bad EOI marker" % which)


def run():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "")
    if not out_dir:
        abort("MAKEFUN_OUTPUT_DIR is not set")
    if not os.path.isdir(out_dir):
        abort("output dir does not exist: " + out_dir)
    dst = os.path.join(out_dir, "entry.png")
    if os.path.abspath(src) == os.path.abspath(dst):
        abort("source and destination are the same file")
    if os.path.exists(dst):
        try:
            if os.path.samefile(src, dst):
                abort("source and destination are the same file")
        except OSError as exc:
            abort("samefile check failed: %s" % exc)
    verify(src, "source")
    try:
        with open(src, "rb") as fin, open(dst, "wb") as fout:
            while True:
                block = fin.read(BLOCK)
                if not block:
                    break
                fout.write(block)
    except OSError as exc:
        abort("copy failed: %s" % exc)
    verify(dst, "output")
    print("OK: entry.png (%d bytes, sha256 %s)"
          % (EXPECTED_SIZE, EXPECTED_SHA256))


if __name__ == "__main__":
    run()
