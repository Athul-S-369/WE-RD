from pathlib import Path

from weird.pipeline.export_site import export_static_site


def test_export_static_site(session, tmp_path: Path):
    out = tmp_path / "content"
    metrics = export_static_site(session, content_dir=out)
    assert metrics["editions"] >= 1
    assert metrics["stories"] >= 1
    assert (out / "current.json").exists()
    assert (out / "editions.json").exists()
    assert (out / "stories-index.json").exists()
    assert (out / "meta.json").exists()
