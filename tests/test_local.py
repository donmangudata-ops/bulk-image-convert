from pathlib import Path

import pytest
from PIL import Image

from bulk_image_convert.cli import main
from bulk_image_convert.cloud import build_run_input
from bulk_image_convert.local import convert_file


@pytest.fixture
def sample(tmp_path):
    img = Image.effect_noise((400, 300), 40).convert("RGB")
    p = tmp_path / "in" / "photo.png"
    p.parent.mkdir()
    img.save(p)
    return p


def test_webp_smaller_and_resized(sample, tmp_path):
    r = convert_file(sample, tmp_path / "out", "webp", 70, max_width=200)
    assert r.ok and r.output.suffix == ".webp"
    assert r.saved > 0
    assert Image.open(r.output).width == 200


def test_jpeg_from_transparent_png(tmp_path):
    p = tmp_path / "t.png"
    Image.new("RGBA", (50, 50), (255, 0, 0, 0)).save(p)
    r = convert_file(p, tmp_path / "o", "jpeg")
    assert r.ok and Image.open(r.output).mode == "RGB"


def test_cli_folder(sample, tmp_path, capsys):
    code = main([str(sample.parent), "-o", str(tmp_path / "o"), "-f", "jpeg", "-q", "60"])
    assert code == 0
    assert (tmp_path / "o" / "photo.jpg").exists()
    assert "bytes saved" in capsys.readouterr().out


def test_bad_file_reported(tmp_path):
    p = tmp_path / "x.png"
    p.write_text("nope")
    assert not convert_file(p, tmp_path / "o").ok


def test_cloud_needs_token(monkeypatch, capsys):
    monkeypatch.delenv("APIFY_TOKEN", raising=False)
    assert main(["https://example.com/a.jpg", "--cloud"]) == 2
    assert "APIFY_TOKEN" in capsys.readouterr().err


def test_cloud_input_keys():
    d = build_run_input(["u"], "webp", 80, 800, None, False, False)
    assert d["imageUrls"] == ["u"] and d["outputFormat"] == "webp" and d["maxWidth"] == 800
