#!/usr/bin/env python3
"""news-image-20261121 entrypoint: "The World in One Day".

The judged image is entry.png, a one-page illustrated sheet summing up
Saturday 21 November 2026 (34 stories, all dated that day). The sheet was
drawn ahead of time by render.py, a deterministic procedural renderer in
this repository. This entrypoint does the one thing the grader needs: it
places a copy of that sheet at <output>/entry.png, where <output> is the
directory named by MAKEFUN_OUTPUT_DIR (or ./output when the variable is
absent). Standard library only: it reads the repository, writes only to
the output directory, and needs no network, no fonts and no third-party
packages, so it runs in the grader's read-only sandbox as well as here.
"""
import hashlib
import os
import shutil
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "entry.png")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1 << 20
MAX_SIDE = 1024


def check_png(blob: bytes) -> None:
    """Refuse anything that is not a whole PNG within the size limits."""
    if not blob.startswith(PNG_SIGNATURE):
        raise SystemExit(f"{SOURCE} does not start with a PNG signature")
    if len(blob) > MAX_BYTES:
        raise SystemExit(f"{SOURCE} is {len(blob)} bytes, over the 1 MiB cap")
    if blob[12:16] != b"IHDR":
        raise SystemExit(f"{SOURCE} has no IHDR chunk where one belongs")
    width, height = struct.unpack(">II", blob[16:24])
    if width > MAX_SIDE or height > MAX_SIDE:
        raise SystemExit(
            f"{SOURCE} is {width}x{height}, over the 1024x1024 cap")
    print(f"checked {SOURCE}: {width}x{height}, {len(blob)} bytes")


def main() -> int:
    with open(SOURCE, "rb") as handle:
        blob = handle.read()
    check_png(blob)
    target_dir = os.environ.get(
        "MAKEFUN_OUTPUT_DIR", os.path.join(HERE, "output"))
    os.makedirs(target_dir, exist_ok=True)
    target = os.path.join(target_dir, "entry.png")
    shutil.copyfile(SOURCE, target)
    digest = hashlib.sha256(blob).hexdigest()
    print(f"wrote {target} ({len(blob)} bytes, sha256 {digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
