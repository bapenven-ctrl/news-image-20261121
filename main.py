#!/usr/bin/env python3
"""news-image-20261121 V2 entrypoint (stdlib only).

Copies the pre-rendered entry.png from this repository to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output). The image itself is drawn
by render.py in the same directory during the build session; the grader
only needs this copier plus the PNG bytes. No network, no clock, no
randomness: two runs write byte-identical output.
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
MAX_BYTES = 1048576
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def main():
    if not os.path.isfile(SRC):
        print("entry.png not found next to main.py", file=sys.stderr)
        return 1
    with open(SRC, "rb") as f:
        data = f.read()
    if len(data) > MAX_BYTES:
        print(f"entry.png too large: {len(data)} bytes", file=sys.stderr)
        return 1
    if data[:8] != PNG_MAGIC:
        print("entry.png is not a PNG file", file=sys.stderr)
        return 1
    # IHDR: bytes 16-20 width, 20-24 height (big-endian); must be 1024x1024.
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    if (width, height) != (1024, 1024):
        print(f"entry.png is {width}x{height}, expected 1024x1024", file=sys.stderr)
        return 1
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    with open(dst, "wb") as f:
        f.write(data)
    print(f"wrote {dst}: {len(data)} bytes sha256={hashlib.sha256(data).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
