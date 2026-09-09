from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from weird.config import get_settings
from weird.constants import CATEGORY_LABELS, Category, EditionStatus
from weird.db import get_db, init_db
from weird.embeddings import embedding_backend
from weird.graph import build_source_graph, concept_index
from weird.llm import provider_status
from weird.logging import configure_logging
from weird.models import Article, Edition, EditionStory, PipelineRun, Project, Source, Story, Video
from weird.schemas import (
    AdminHealth,
    CapabilitiesOut,
    CategoryOut,
    EditionListItem,
    EditionOut,
    ProjectOut,
    SearchResponse,
    SourceOut,
    VideoOut,
)
from weird.search import hybrid_search, search_mode_label
from weird.seed import seed
from weird.serializers import to_card, to_detail, to_edition, to_edition_list_item

settings = get_settings()
configure_logging(settings.weird_log_level)
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="WE-RD API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()
    from weird.db import get_session_factory

    cfg = get_settings()
    session = get_session_factory()()
    try:
        if cfg.weird_demo_mode:
            seed(session)
            session.commit()
    finally:
        session.close()


def require_admin(request: Request) -> None:
    cfg = get_settings()
    token = request.headers.get("x-admin-token") or request.query_params.get("token")
    if not token or token != cfg.weird_admin_token:
        raise HTTPException(status_code=401, detail="admin token required")


@app.get("/health")
def health():
    return {"ok": True, "name": "WE-RD"}


@app.get("/capabilities", response_model=CapabilitiesOut)
def capabilities():
    cfg = get_settings()
    return CapabilitiesOut(
        processing_mode=cfg.processing_mode(),
        search=search_mode_label(),
        llm=provider_status(cfg),
        embeddings=embedding_backend(),
    )


@app.get("/editions", response_model=list[EditionListItem])
@limiter.limit("60/minute")
def list_editions(request: Request, db: Session = Depends(get_db)):
    rows = (
        db.query(Edition)
        .filter(Edition.status == EditionStatus.PUBLISHED)
        .order_by(Edition.issue_number.desc())
        .all()
    )
    return [to_edition_list_item(e) for e in rows]


@app.get("/editions/current", response_model=EditionOut)
@limiter.limit("60/minute")
def current_edition(request: Request, db: Session = Depends(get_db)):
    edition = (
        db.query(Edition)
        .options(joinedload(Edition.stories).joinedload(EditionStory.story).joinedload(Story.sources))
        .filter(Edition.status == EditionStatus.PUBLISHED)
        .order_by(Edition.issue_number.desc())
        .first()
    )
    if not edition:
        raise HTTPException(404, "No published edition")
    return to_edition(edition)


@app.get("/editions/{issue_number}", response_model=EditionOut)
@limiter.limit("60/minute")
def get_edition(issue_number: int, request: Request, db: Session = Depends(get_db)):
    edition = (
        db.query(Edition)
        .options(joinedload(Edition.stories).joinedload(EditionStory.story).joinedload(Story.sources))
        .filter(Edition.issue_number == issue_number)
        .first()
    )
    if not edition:
        raise HTTPException(404, "Edition not found")
    return to_edition(edition)


@app.get("/stories")
@limiter.limit("60/minute")
def list_stories(
    request: Request,
    db: Session = Depends(get_db),
    category: str | None = None,
    tag: str | None = None,
    q: str | None = None,
    min_score: float | None = None,
    confidence: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    query = db.query(Story).options(joinedload(Story.sources))
    if category:
        query = query.filter(Story.category == category.upper())
    if confidence:
        query = query.filter(Story.confidence == confidence)
    if min_score is not None:
        query = query.filter(Story.signal_score >= min_score)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Story.title.ilike(like), Story.description.ilike(like), Story.dek.ilike(like)))
    stories = query.order_by(Story.signal_score.desc()).all()
    if tag:
        needle = tag.lower()
        stories = [s for s in stories if needle in [t.lower() for t in (s.tags or [])]]
    total = len(stories)
    start = (page - 1) * page_size
    page_items = stories[start : start + page_size]
    return {"items": [to_card(s) for s in page_items], "page": page, "total": total}


@app.get("/stories/{slug}")
@limiter.limit("60/minute")
def get_story(slug: str, request: Request, db: Session = Depends(get_db)):
    story = (
        db.query(Story)
        .options(
            joinedload(Story.sources),
            joinedload(Story.timeline),
            joinedload(Story.videos),
            joinedload(Story.projects),
        )
        .filter(Story.slug == slug)
        .first()
    )
    if not story:
        raise HTTPException(404, "Story not found")
    graph = build_source_graph(db, story)
    return to_detail(
        story,
        related=graph.related,
        source_graph={
            "nodes": [n.__dict__ for n in graph.nodes],
            "edges": [e.__dict__ for e in graph.edges],
        },
    )


@app.get("/stories/{slug}/related")
@limiter.limit("60/minute")
def get_related(slug: str, request: Request, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.slug == slug).first()
    if not story:
        raise HTTPException(404, "Story not found")
    graph = build_source_graph(db, story)
    return {"slug": slug, "related": graph.related}


@app.get("/stories/{slug}/graph")
@limiter.limit("60/minute")
def get_graph(slug: str, request: Request, db: Session = Depends(get_db)):
    story = (
        db.query(Story)
        .options(joinedload(Story.sources), joinedload(Story.videos), joinedload(Story.projects))
        .filter(Story.slug == slug)
        .first()
    )
    if not story:
        raise HTTPException(404, "Story not found")
    graph = build_source_graph(db, story)
    return {
        "slug": slug,
        "nodes": [n.__dict__ for n in graph.nodes],
        "edges": [e.__dict__ for e in graph.edges],
        "related": graph.related,
    }


@app.get("/search", response_model=SearchResponse)
@limiter.limit("30/minute")
def search(
    request: Request,
    q: str = Query("", min_length=0),
    category: str | None = None,
    tag: str | None = None,
    min_score: float | None = None,
    confidence: str | None = None,
    db: Session = Depends(get_db),
):
    hits = hybrid_search(
        db,
        q=q,
        category=category,
        tag=tag,
        min_score=min_score,
        confidence=confidence,
        limit=50,
    )
    cards = [to_card(h.story) for h in hits]
    return SearchResponse(query=q, total=len(cards), items=cards, mode=search_mode_label())


@app.get("/concepts")
@limiter.limit("60/minute")
def concepts(request: Request, db: Session = Depends(get_db)):
    return concept_index(db)


@app.get("/categories", response_model=list[CategoryOut])
def categories(db: Session = Depends(get_db)):
    rows = db.query(Story.category, func.count(Story.id)).group_by(Story.category).all()
    counts = {c: n for c, n in rows}
    return [
        CategoryOut(slug=cat.value, label=CATEGORY_LABELS[cat], count=counts.get(cat.value, 0))
        for cat in Category
    ]


@app.get("/tags")
def tags(db: Session = Depends(get_db)):
    stories = db.query(Story.tags).all()
    freq: dict[str, int] = {}
    for (tag_list,) in stories:
        for tag in tag_list or []:
            freq[tag] = freq.get(tag, 0) + 1
    return sorted(({"tag": k, "count": v} for k, v in freq.items()), key=lambda x: -x["count"])


@app.get("/sources", response_model=list[SourceOut])
def sources(db: Session = Depends(get_db)):
    return [SourceOut.model_validate(s) for s in db.query(Source).order_by(Source.name).all()]


@app.get("/videos", response_model=list[VideoOut])
@limiter.limit("60/minute")
def list_videos(request: Request, db: Session = Depends(get_db), limit: int = Query(50, ge=1, le=200)):
    rows = db.query(Video).order_by(Video.relevance_score.desc()).limit(limit).all()
    return [VideoOut.model_validate(v) for v in rows]


@app.get("/projects", response_model=list[ProjectOut])
@limiter.limit("60/minute")
def list_projects(request: Request, db: Session = Depends(get_db), limit: int = Query(50, ge=1, le=200)):
    rows = db.query(Project).order_by(Project.stars.desc()).limit(limit).all()
    return [ProjectOut.model_validate(p) for p in rows]


@app.get("/admin/health", response_model=AdminHealth)
def admin_health(db: Session = Depends(get_db), _: None = Depends(require_admin)):
    runs = db.query(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(10).all()
    counts = dict(db.query(Story.status, func.count(Story.id)).group_by(Story.status).all())
    return AdminHealth(
        sources=[SourceOut.model_validate(s) for s in db.query(Source).all()],
        latest_runs=[
            {
                "kind": r.kind,
                "status": r.status,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "metrics": r.metrics,
                "error": r.error,
            }
            for r in runs
        ],
        story_counts=counts,
        article_count=db.query(Article).count(),
        cluster_count=db.query(func.count(func.distinct(Story.cluster_key))).scalar() or 0,
        processing_mode=get_settings().processing_mode(),
    )


@app.post("/admin/pipeline/daily")
def admin_daily(_: None = Depends(require_admin)):
    from weird.pipeline.daily import run_daily

    return run_daily()


@app.post("/admin/pipeline/sunday")
def admin_sunday(_: None = Depends(require_admin)):
    from weird.pipeline.sunday import run_sunday

    return run_sunday()
