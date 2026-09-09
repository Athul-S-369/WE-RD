from weird.clustering import ClusterMember, cluster_items, should_merge
from weird.dedup import is_duplicate
from weird.embeddings import hashed_embedding
from weird.textutil import canonicalize_url


def test_url_canonicalization():
    a = canonicalize_url("https://WWW.Example.com/foo/?utm_source=x")
    b = canonicalize_url("https://example.com/foo")
    assert a == b


def test_duplicate_by_url_and_title():
    existing = [("https://example.com/a", "Rust rewrite of a C library", "hash")]
    assert is_duplicate(url="https://example.com/a?utm_campaign=1", title="other", text="x", existing=existing)
    assert is_duplicate(
        url="https://other.example/b",
        title="Rust rewrite of a C library",
        text="x",
        existing=existing,
    )


def test_cluster_same_story():
    e = hashed_embedding("rust c library abi ffi rewrite")
    a = ClusterMember("1", "C library rewritten in Rust", "https://a.example/1", e, {"rust", "abi"})
    b = ClusterMember("2", "Rewriting a C library in Rust", "https://b.example/2", e, {"rust", "abi"})
    c = ClusterMember("3", "Potato farming almanac", "https://c.example/3", hashed_embedding("potato soil"), {"farm"})
    assert should_merge(a, b)
    groups = cluster_items([a, b, c])
    assert len(groups) == 2
