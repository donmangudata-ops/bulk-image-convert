"""Local conversion with Pillow. No network, no key."""
from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional

from PIL import Image, ImageOps

try:  # optional HEIC support
    import pillow_heif

    pillow_heif.register_heif_opener()
except Exception:  # pragma: no cover
    pass

try:  # AVIF is built into Pillow 11.3+, or comes from pillow-avif-plugin
    import pillow_avif  # noqa: F401
except Exception:  # pragma: no cover
    pass

INPUT_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".heic", ".heif", ".gif", ".tif", ".tiff", ".bmp"}
FORMATS = {"webp": ("WEBP", ".webp"), "avif": ("AVIF", ".avif"), "jpeg": ("JPEG", ".jpg"), "png": ("PNG", ".png")}


@dataclass
class Result:
    source: Path
    output: Optional[Path]
    in_bytes: int
    out_bytes: int
    ok: bool
    error: Optional[str] = None

    @property
    def saved(self) -> int:
        return self.in_bytes - self.out_bytes


def find_images(paths: Iterable[Path], recursive: bool = False) -> Iterator[Path]:
    for p in paths:
        p = Path(p)
        if p.is_dir():
            it = p.rglob("*") if recursive else p.glob("*")
            for f in sorted(it):
                if f.is_file() and f.suffix.lower() in INPUT_EXTS:
                    yield f
        elif p.is_file():
            yield p


def _encode(img: Image.Image, fmt: str, quality: int, lossless: bool) -> bytes:
    buf = io.BytesIO()
    pil_fmt = FORMATS[fmt][0]
    if pil_fmt == "JPEG":
        if img.mode in ("RGBA", "LA", "P"):
            rgba = img.convert("RGBA")
            bg = Image.new("RGB", rgba.size, (255, 255, 255))
            bg.paste(rgba, mask=rgba.split()[-1])
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
        img.save(buf, "JPEG", quality=quality, optimize=True)
    elif pil_fmt == "PNG":
        img.save(buf, "PNG", optimize=True)
    elif pil_fmt == "WEBP":
        img.save(buf, "WEBP", quality=quality, lossless=lossless, method=6)
    else:
        img.save(buf, "AVIF", quality=quality)
    return buf.getvalue()


def convert_file(
    src: Path,
    out_dir: Optional[Path] = None,
    fmt: str = "webp",
    quality: int = 80,
    max_width: Optional[int] = None,
    max_height: Optional[int] = None,
    lossless: bool = False,
    keep_metadata: bool = False,
) -> Result:
    src = Path(src)
    in_bytes = src.stat().st_size
    try:
        with Image.open(src) as im:
            exif = im.info.get("exif") if keep_metadata else None
            im = ImageOps.exif_transpose(im)
            if max_width or max_height:
                box = (max_width or im.width, max_height or im.height)
                if im.width > box[0] or im.height > box[1]:
                    im.thumbnail(box, Image.LANCZOS)
            if fmt == "same":
                f = (src.suffix.lower().lstrip(".") or "jpeg").replace("jpg", "jpeg")
                use = f if f in FORMATS else "png"
            else:
                use = fmt
            if im.mode not in ("RGB", "RGBA", "L", "LA"):
                im = im.convert("RGBA" if "transparency" in im.info or im.mode in ("P", "PA") else "RGB")
            data = _encode(im, use, quality, lossless)
            _ = exif  # metadata is dropped by default; kept simple
        target_dir = Path(out_dir) if out_dir else src.parent
        target_dir.mkdir(parents=True, exist_ok=True)
        out = target_dir / (src.stem + FORMATS[use][1])
        if out.resolve() == src.resolve():
            out = target_dir / (src.stem + ".min" + FORMATS[use][1])
        out.write_bytes(data)
        return Result(src, out, in_bytes, len(data), True)
    except Exception as e:
        return Result(src, None, in_bytes, 0, False, f"{type(e).__name__}: {e}")


def convert_paths(paths: Iterable[Path], recursive: bool = False, **kw) -> list:
    return [convert_file(f, **kw) for f in find_images(paths, recursive)]
