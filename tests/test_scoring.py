from weird.scoring import extract_tags, score_item
from weird.constants import cracked_blurb


def test_popularity_does_not_dominate():
    obscure = score_item(
        title="Rewrote libc-adjacent parser in Rust preserving ABI",
        text="from scratch FFI ABI memory safety kernel llvm posix tests",
        category="BUILD",
        credibility=0.9,
        stars=70,
        comments=4,
        source_count=2,
        entities=["Rust", "ABI", "FFI"],
    )
    viral = score_item(
        title="New smartphone announced",
        text="product launch event marketing keynote",
        category="SOURCE",
        credibility=0.4,
        stars=40000,
        comments=9000,
        source_count=12,
    )
    assert obscure.signal > viral.signal
    assert obscure.cracked > 50


def test_extract_tags_prefers_linux_kernel():
    tags = extract_tags("patches landed in the Linux kernel scheduler")
    assert "Linux Kernel" in tags


def test_cracked_blurb_extreme():
    assert "did not need" in cracked_blurb(96).lower()
