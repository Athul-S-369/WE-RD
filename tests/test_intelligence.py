from weird.analysis_fallback import editorial_heuristic, evidence_first_analysis
from weird.dedup import is_duplicate
from weird.embeddings import bm25_lite, cosine, hashed_embedding, hybrid_rank_score, tokenize
from weird.enrichment.youtube import YouTubeClient
from weird.scoring import score_item
from weird.search import hybrid_search


def test_hybrid_rank_prefers_overlap():
    q = tokenize("rust abi rewrite from scratch")
    good = tokenize("rust abi rewrite from scratch ffi memory safety")
    bad = tokenize("smartphone launch marketing keynote")
    qv = hashed_embedding("rust abi rewrite from scratch")
    k1, s1, c1 = hybrid_rank_score(q, good, qv, hashed_embedding(" ".join(good)))
    k2, s2, c2 = hybrid_rank_score(q, bad, qv, hashed_embedding(" ".join(bad)))
    assert c1 > c2
    assert k1 > k2
    assert bm25_lite(q, good) > bm25_lite(q, bad)


def test_score_breakdown_is_explainable():
    breakdown = score_item(
        title="Rewrote libc-adjacent parser in Rust preserving ABI",
        text="from scratch FFI ABI memory safety kernel llvm posix tests",
        category="BUILD",
        credibility=0.9,
        stars=70,
        comments=4,
        source_count=2,
        entities=["Rust", "ABI", "FFI"],
    )
    assert breakdown.contributions
    assert abs(sum(breakdown.contributions.values()) - breakdown.signal) < 0.2
    assert "novelty" in breakdown.explanations
    assert breakdown.weights["community"] < breakdown.weights["difficulty"]


def test_evidence_first_does_not_invent_benchmarks():
    analysis = evidence_first_analysis(
        title="Tiny kernel toy",
        text="Built a toy kernel for fun. https://github.com/example/toy-kernel",
        category="WHY",
        sources="https://github.com/example/toy-kernel",
    )
    assert "benchmark" in analysis["performance"].lower() or "do not establish" in analysis["performance"].lower()
    assert analysis["generation_mode"] == "deterministic_fallback"
    assert analysis["evidence"]["has_primary_source"] is True


def test_editorial_heuristic_quality_floor():
    weak = editorial_heuristic({"signal_score": 20, "cracked_score": 10, "rabbit_hole_score": 10})
    strong = editorial_heuristic({"signal_score": 80, "cracked_score": 88, "rabbit_hole_score": 70})
    assert weak["keep"] is False
    assert strong["keep"] is True


def test_youtube_zero_key_no_fake_ids():
    client = YouTubeClient()
    status = client.search_with_status(["rust compiler talk"])
    assert status["status"] == "NO VIDEO FOUND"
    assert status["results"] == []
    assert client.provider.name == "none"


def test_semantic_dedup_optional(session):
    existing = [("https://a.example/x", "Rust ABI rewrite from scratch", "hash1")]
    emb = [("Rust ABI rewrite from scratch", hashed_embedding("Rust ABI rewrite from scratch"))]
    assert is_duplicate(
        url="https://b.example/y",
        title="Rust ABI rewrite from scratch ffi",
        text="Rust ABI rewrite from scratch ffi",
        existing=existing,
        existing_embeddings=emb,
        title_threshold=0.99,
        semantic_threshold=0.5,
    )


def test_hybrid_search_api_and_graph(client, session):
    caps = client.get("/capabilities")
    assert caps.status_code == 200
    body = caps.json()
    assert body["search"]["search"] == "hybrid"
    assert body["llm"]["active"] == "mock"

    search = client.get("/search", params={"q": "portable executable libc", "tag": "C"})
    assert search.status_code == 200
    payload = search.json()
    assert payload["mode"]["search"] == "hybrid"
    assert any(i["slug"] == "cosmopolitan-libc-ape" for i in payload["items"])

    story = client.get("/stories/sudo-rs-memory-safe-sudo")
    assert story.status_code == 200
    detail = story.json()
    assert "score_breakdown" in detail
    assert "related" in detail
    assert "source_graph" in detail
    assert detail["source_graph"]["nodes"]

    graph = client.get("/stories/sudo-rs-memory-safe-sudo/graph")
    assert graph.status_code == 200
    assert graph.json()["edges"]

    hits = hybrid_search(session, q="Rust ABI", limit=10)
    assert hits
    assert cosine(hashed_embedding("rust abi"), hashed_embedding("rust abi")) > 0.99


def test_zero_key_acceptance(client):
    """Core read paths work with mock/no cloud keys."""
    assert client.get("/health").json()["ok"] is True
    assert client.get("/editions/current").status_code == 200
    assert client.get("/capabilities").json()["processing_mode"]["zero_key"] is True
    assert client.get("/search", params={"q": "compiler"}).status_code == 200
