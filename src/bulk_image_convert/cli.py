from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .local import convert_paths


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bulk-image-convert",
                                description="Convert and compress images. Local by default, cloud with --cloud.")
    p.add_argument("inputs", nargs="+", help="image files or folders (URLs with --cloud)")
    p.add_argument("-f", "--format", default="webp", choices=["webp", "avif", "jpeg", "png", "same"])
    p.add_argument("-q", "--quality", type=int, default=80, help="1-100, default 80")
    p.add_argument("--max-width", type=int)
    p.add_argument("--max-height", type=int)
    p.add_argument("--lossless", action="store_true", help="lossless WebP")
    p.add_argument("--keep-metadata", action="store_true", help="cloud mode only")
    p.add_argument("-o", "--out", default="converted", help="output folder (default: converted)")
    p.add_argument("-r", "--recursive", action="store_true", help="search folders recursively")
    p.add_argument("--cloud", action="store_true",
                   help="run the hosted Apify Actor on image URLs (needs APIFY_TOKEN)")
    p.add_argument("--version", action="version", version=__version__)
    return p


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    if not 1 <= a.quality <= 100:
        print("quality must be between 1 and 100", file=sys.stderr)
        return 2
    out = Path(a.out)
    if a.cloud:
        from .cloud import run_cloud
        urls = [u for u in a.inputs if u.startswith(("http://", "https://"))]
        if not urls:
            print("Cloud mode takes image URLs, for example https://example.com/a.jpg", file=sys.stderr)
            return 2
        return run_cloud(urls, out, fmt=a.format, quality=a.quality, max_width=a.max_width,
                         max_height=a.max_height, lossless=a.lossless, keep_metadata=a.keep_metadata)
    results = convert_paths([Path(i) for i in a.inputs], a.recursive, out_dir=out, fmt=a.format,
                            quality=a.quality, max_width=a.max_width, max_height=a.max_height,
                            lossless=a.lossless)
    if not results:
        print("No images found.", file=sys.stderr)
        return 1
    tin = tout = bad = 0
    for r in results:
        if r.ok:
            tin += r.in_bytes
            tout += r.out_bytes
            pct = 100 * r.saved / r.in_bytes if r.in_bytes else 0
            print(f"ok    {r.source.name} -> {r.output.name}  {r.in_bytes:,} -> {r.out_bytes:,} bytes ({pct:.1f}% saved)")
        else:
            bad += 1
            print(f"fail  {r.source.name}  {r.error}", file=sys.stderr)
    pct = 100 * (tin - tout) / tin if tin else 0
    print(f"Total: {len(results) - bad} converted, {bad} failed, {tin - tout:,} bytes saved ({pct:.1f}%)")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
