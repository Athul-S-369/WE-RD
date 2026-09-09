from __future__ import annotations

"""
Sample newspaper corpus grounded in real, public projects.

This is not live weekly discovery — it is a faithful preview of how a published
WE-RD issue looks and reads, using primary sources you can open yourself.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from weird.constants import Category, Confidence, EditionStatus, SecurityStatus, StoryStatus
from weird.models import (
    Article,
    Edition,
    EditionStory,
    Project,
    Source,
    Story,
    StorySource,
    StoryTimeline,
    Video,
    LlmCache,
    PipelineRun,
)
from weird.pipeline.ingest import ensure_sources
from weird.scoring import score_item


def seed(session: Session, *, force: bool = False) -> None:
    ensure_sources(session)
    existing = session.query(Story).first()
    if existing and not force:
        _ensure_editions(session)
        return
    if force:
        _wipe_corpus(session)
    source = session.query(Source).filter_by(name="Hacker News").one_or_none()
    stories = _real_stories(session, source)
    _editions(session, stories)
    session.flush()


def _wipe_corpus(session: Session) -> None:
    session.query(EditionStory).delete()
    session.query(Edition).delete()
    session.query(Video).delete()
    session.query(Project).delete()
    session.query(StoryTimeline).delete()
    session.query(StorySource).delete()
    session.query(Story).delete()
    session.query(Article).delete()
    session.query(PipelineRun).delete()
    session.query(LlmCache).delete()
    session.flush()


def _ensure_editions(session: Session) -> None:
    if session.query(Edition).count() == 0:
        stories = session.query(Story).all()
        if stories:
            _editions(session, stories)


def _article(session: Session, source, title: str, url: str, content: str) -> Article:
    from weird.textutil import canonicalize_url, content_hash

    canon = canonicalize_url(url)
    existing = session.query(Article).filter_by(canonical_url=canon).one_or_none()
    if existing:
        return existing
    article = Article(
        source_id=source.id if source else None,
        title=title,
        url=url,
        canonical_url=canon,
        content=content,
        summary=content[:280],
        content_hash=content_hash(title + content),
        extra={},
    )
    session.add(article)
    session.flush()
    return article


def _attach(session, story, article, role="primary", kind="official_project_repository", score=0.9):
    session.add(
        StorySource(
            story_id=story.id,
            article_id=article.id,
            role=role,
            url=article.url,
            title=article.title,
            credibility_kind=kind,
            credibility_score=score,
        )
    )


def _scored(title, text, category, credibility=0.9, **kwargs):
    return score_item(title=title, text=text, category=category, credibility=credibility, **kwargs)


def _timeline(session, story, events: list[tuple[str, str]], start: datetime | None = None):
    # Anchor timelines near "this week" so the edition feels current.
    start = start or datetime(2026, 9, 1, tzinfo=timezone.utc)
    for i, (headline, body) in enumerate(events):
        session.add(
            StoryTimeline(
                story_id=story.id,
                occurred_at=start + timedelta(days=i * 14),
                headline=headline,
                body=body,
            )
        )


def _make_story(
    session,
    source,
    *,
    title: str,
    slug: str,
    dek: str,
    description: str,
    category: str,
    cracked: int,
    rabbit: int,
    tags: list[str],
    analysis: dict,
    url: str,
    project: str | None = None,
    lang: str | None = None,
    stars: int | None = None,
    project_desc: str = "",
    video: dict | None = None,
    security: dict | None = None,
    confidence: str = Confidence.CONFIRMED,
    supporting: list[tuple[str, str, str]] | None = None,
    timeline: list[tuple[str, str]] | None = None,
    cracked_blurb: str = "",
) -> Story:
    text = description + " " + " ".join(analysis.get("rabbit_holes") or tags)
    b = _scored(title, text, category, entities=tags, stars=stars, source_count=2 + len(supporting or []))
    story = Story(
        title=title,
        slug=slug,
        dek=dek,
        description=description,
        category=category,
        signal_score=max(b.signal, 78),
        cracked_score=cracked,
        rabbit_hole_score=rabbit,
        confidence=confidence,
        status=StoryStatus.PUBLISHED,
        is_demo=False,
        tags=tags,
        analysis=analysis,
        security=security,
        extra={
            "cracked_blurb": cracked_blurb or b.cracked_blurb,
            "rabbit_paths": analysis.get("rabbit_holes") or tags,
            "processing_mode": "sample-issue (real primary sources)",
            "dimensions": b.dimensions,
            "contributions": b.contributions,
        },
    )
    session.add(story)
    session.flush()
    article = _article(session, source, title, url, description)
    _attach(session, story, article)
    for s_title, s_url, kind in supporting or []:
        a = _article(session, source, s_title, s_url, s_title)
        _attach(session, story, a, "supporting", kind, 0.85)
    if project:
        session.add(
            Project(
                story_id=story.id,
                name=project,
                url=f"https://github.com/{project}",
                host="github",
                stars=stars,
                language=lang,
                description=project_desc,
            )
        )
    if video:
        session.add(Video(story_id=story.id, **video))
    _timeline(session, story, timeline or [("Primary source published", description)])
    return story


def _real_stories(session: Session, source) -> list[Story]:
    stories = []

    stories.append(
        _make_story(
            session,
            source,
            title="Ladybird: a browser engine that refuses to be a skin",
            slug="ladybird-independent-browser-engine",
            dek="From-scratch HTML, CSS, JS — not Chromium with a new coat of paint.",
            description="Ladybird is an independent browser engine and browser, forked out of SerenityOS work, now developed as its own project with the Ladybird Browser Initiative.",
            category=Category.BUILD,
            cracked=94,
            rabbit=96,
            tags=["C++", "Browsers", "HTML", "CSS", "JavaScript", "SerenityOS"],
            stars=48000,
            project="LadybirdBrowser/ladybird",
            lang="C++",
            project_desc="Independent web browser from scratch.",
            url="https://ladybird.org/",
            supporting=[
                ("Ladybird Browser Initiative announcement", "https://ladybird.org/posts/announcement/", "original_author"),
                ("Ladybird on GitHub", "https://github.com/LadybirdBrowser/ladybird", "official_project_repository"),
            ],
            video={
                "video_id": "cbw0KrMGHvc",
                "title": "Ladybird browser update (June 2024)",
                "channel": "Andreas Kling",
                "url": "https://www.youtube.com/watch?v=cbw0KrMGHvc",
                "description": "Project update covering the split from SerenityOS and engine work.",
                "relevance_score": 0.95,
                "technical": True,
            },
            cracked_blurb="Building a modern browser from scratch is the kind of ambition that looks insane until the commits keep coming.",
            timeline=[
                ("Engine work inside SerenityOS", "LibWeb / Ladybird grew as a from-scratch web stack."),
                ("Standalone browser focus", "Ladybird separated to focus on being a browser, not an OS."),
                ("Ladybird Browser Initiative", "Nonprofit structure announced to support independent development."),
            ],
            analysis={
                "why_you_should_care": "Almost every 'new browser' is Chromium. Ladybird is attempting the rare thing: a real independent engine, which means HTML, CSS, layout, painting, and JS as engineering problems again.",
                "what_happened": "Andreas Kling and contributors built LibWeb into Ladybird, then spun the browser into its own organization and repository so the engine could grow without carrying an entire OS.",
                "how_it_works": "A multi-process browser architecture with from-scratch parsing, style, layout, and painting pipelines, plus a JavaScript engine path — implemented primarily in C++ with the project's own libraries rather than embedding Blink/WebKit.",
                "under_the_hood": "Start at the Ladybird repo: browser chrome, LibWeb (engine), and the supporting Serenity-derived libraries. The interesting files are layout, CSS cascade, and how they choose which web platform features to implement next.",
                "why_they_built_it": "Independence. A web that is not permanently downstream of one corporate engine.",
                "what_was_difficult": "The web platform is a moving target measured in thousands of tests. Compatibility is the product; everything else is scaffolding.",
                "performance": "Treat only project-published updates and traces as evidence. Do not invent Speedometer deltas.",
                "trade_offs": "Total ownership of the stack versus years of catch-up against Chromium's compatibility surface.",
                "what_is_surprising": "They keep shipping monthly technical updates that show the engine, not a marketing site.",
                "quick_read": "An independent browser engine — the rabbit hole is the entire web platform.",
                "rabbit_holes": ["browser engines", "CSS layout", "JS runtimes", "multi-process browsers", "web standards"],
                "further_reading_notes": "ladybird.org, the GitHub org, and Andreas Kling's update videos.",
            },
        )
    )

    stories.append(
        _make_story(
            session,
            source,
            title="sudo-rs: privilege escalation, rewritten in Rust",
            slug="sudo-rs-memory-safe-sudo",
            dek="Same dangerous job. Different language. Compatibility is the hard part.",
            description="sudo-rs is a memory-safe implementation of sudo and su, started under ISRG Prossimo and now maintained by the Trifecta Tech Foundation — and adopted as default sudo in Ubuntu 25.10.",
            category=Category.BUILD,
            cracked=88,
            rabbit=90,
            tags=["Rust", "Linux", "Security", "sudo", "Privilege boundaries"],
            stars=4300,
            project="trifectatechfoundation/sudo-rs",
            lang="Rust",
            project_desc="Memory-safe sudo and su.",
            url="https://github.com/trifectatechfoundation/sudo-rs",
            supporting=[
                ("Trifecta: sudo-rs project", "https://trifectatech.org/projects/sudo-rs/", "original_author"),
                ("Prossimo: sudo-rs headed to Ubuntu", "https://www.memorysafety.org/blog/sudo-rs-headed-to-ubuntu/", "respected_technical_publication"),
            ],
            cracked_blurb="Replacing sudo means your Rust has to behave like decades of C habits and policy files.",
            timeline=[
                ("ISRG / Prossimo funding", "Initial Rust reimplementation of sudo/su begins."),
                ("Trifecta maintenance", "Long-term stewardship moves to Trifecta Tech Foundation."),
                ("Ubuntu default path", "Ubuntu adopts sudo-rs as default in 25.10 (C sudo remains available)."),
            ],
            analysis={
                "why_you_should_care": "sudo sits on the privilege boundary of almost every Linux box. A Rust rewrite is only interesting if behavior and policy compatibility survive contact with the real world.",
                "what_happened": "ISRG funded a memory-safe sudo/su; Trifecta now maintains sudo-rs; Ubuntu made it the default sudo implementation in 25.10 while keeping classic sudo installable.",
                "how_it_works": "Command-line and policy compatibility with familiar sudo semantics, implemented in Rust, with an explicit goal of shrinking memory-unsafety at the privilege boundary.",
                "under_the_hood": "Read the upstream FAQ and tree: parsing, policy, authentication hooks, and where they deliberately do not clone every obscure sudo feature on day one.",
                "why_they_built_it": "Memory safety for software that runs as root when you type a password.",
                "what_was_difficult": "Matching user expectations and distribution packaging without turning sudo into a research toy.",
                "performance": "Not the point. Correctness and safety are. Use only project/distro statements for claims.",
                "trade_offs": "Memory safety and a clearer attack surface versus decades of edge-case compatibility in classic sudo.",
                "what_is_surprising": "A major distro was willing to change the default for such a sacred binary.",
                "quick_read": "sudo, but in Rust — and actually shipping as a distro default.",
                "rabbit_holes": ["privilege boundaries", "Rust FFI", "PAM", "Linux packaging", "memory safety"],
            },
        )
    )

    stories.append(
        _make_story(
            session,
            source,
            title="Cosmopolitan Libc: actually portable executable, taken seriously",
            slug="cosmopolitan-libc-ape",
            dek="One binary. Many operating systems. The linker tricks are the plot.",
            description="Cosmopolitan Libc builds C programs as Actually Portable Executables that can run across Unix-like systems and Windows without the usual portability tax of rewrite-everything.",
            category=Category.WHY,
            cracked=97,
            rabbit=93,
            tags=["C", "Linkers", "ABI", "Portability", "Compilers"],
            stars=19000,
            project="jart/cosmopolitan",
            lang="C",
            project_desc="C library for actually portable executables.",
            url="https://github.com/jart/cosmopolitan",
            cracked_blurb="Someone looked at OS boundaries and said: what if the binary just refused to care?",
            analysis={
                "why_you_should_care": "Portability usually means #ifdef hell or a runtime. Cosmopolitan attacks the problem at the binary and libc boundary — which is either brilliant or cursed, depending on your taste.",
                "what_happened": "Justine Tunney's Cosmopolitan project publishes a libc and toolchain approach for APE binaries that aim to run across multiple OS ABIs.",
                "how_it_works": "Fat/polyglot executable tricks plus a libc that understands multiple system call surfaces, so a single artifact can boot on different platforms.",
                "under_the_hood": "Start with the project's documentation on APE format, then the syscall shims. The linker and header strategy are the real curriculum.",
                "why_they_built_it": "Because 'write once, run anywhere' for C was always a polite fiction.",
                "what_was_difficult": "Making undefined platform behavior look defined without lying to the program.",
                "performance": "Cite only author benchmarks. Platform variance is the point.",
                "trade_offs": "Incredible portability experiments versus conventional distribution packaging expectations.",
                "what_is_surprising": "It is not a joke repo. People ship real tools on it.",
                "quick_read": "A C libc that tries to make one binary enough.",
                "rabbit_holes": ["APE", "ELF", "PE", "syscalls", "polyglot binaries", "libc"],
            },
        )
    )

    stories.append(
        _make_story(
            session,
            source,
            title="Hare: a systems language that wants to stay small",
            slug="hare-systems-language",
            dek="Opinionated simplicity next to C — not another kitchen-sink successor.",
            description="Hare is a systems programming language designed by Drew DeVault and contributors as a smaller, simpler alternative in the C niche, with its own standard library and toolchain.",
            category=Category.LANG,
            cracked=82,
            rabbit=88,
            tags=["Hare", "Compilers", "Systems programming", "C"],
            url="https://harelang.org/",
            supporting=[
                ("Hare on SourceHut", "https://git.sr.ht/~sircmpwn/hare", "official_project_repository"),
            ],
            cracked_blurb="Designing a new systems language in 2020s is either hubris or hygiene. Hare bets on hygiene.",
            analysis={
                "why_you_should_care": "Most 'C replacements' grow until they are something else. Hare's pitch is restraint: a language you can hold in your head for systems work.",
                "what_happened": "The Hare project published a language specification, standard library, and toolchain oriented toward systems programming without C's sharpest edges — and without trying to be Rust.",
                "how_it_works": "Statically typed language with manual memory management culture, its own build/tooling story, and a standard library sized for systems tasks.",
                "under_the_hood": "Read the language docs and stdlib. Compare error handling and slices to C and to Rust's ownership model — Hare is making different bets.",
                "why_they_built_it": "C's incumbency is not the same thing as C being finished.",
                "what_was_difficult": "Bootstrapping culture and refusing feature creep while still being useful.",
                "performance": "The available sources do not establish a universal benchmark winner. Language choice claims need workloads.",
                "trade_offs": "Simplicity versus ecosystem gravity. Fewer features means fewer escape hatches.",
                "what_is_surprising": "The aesthetic is almost aggressively unfashionable — on purpose.",
                "quick_read": "A small systems language with strong opinions about staying small.",
                "rabbit_holes": ["language design", "manual memory", "bootstrapping", "C ABI"],
            },
        )
    )

    stories.append(
        _make_story(
            session,
            source,
            title="xz-utils backdoor: when the supply chain became the exploit",
            slug="xz-utils-backdoor-cve-2024-3094",
            dek="CONFIRMED. Patched. A lesson in trust, not a thriller trailer.",
            description="CVE-2024-3094 covered a supply-chain backdoor in xz-utils / liblzma that targeted SSH authentication paths via systemd dependencies — discovered by Andres Freund and widely documented by vendors.",
            category=Category.BREAK,
            cracked=92,
            rabbit=94,
            tags=["Security", "Supply chain", "Linux", "SSH", "xz"],
            confidence=Confidence.VENDOR_CONFIRMED,
            url="https://nvd.nist.gov/vuln/detail/CVE-2024-3094",
            supporting=[
                ("NVD: CVE-2024-3094", "https://nvd.nist.gov/vuln/detail/CVE-2024-3094", "vendor_advisory"),
                ("OSS Security discussion / discovery context", "https://www.openwall.com/lists/oss-security/2024/03/29/4", "respected_technical_publication"),
            ],
            security={
                "cve": "CVE-2024-3094",
                "affected_software": "xz-utils / liblzma (specific compromised releases)",
                "affected_versions": "See vendor advisories; notably 5.6.0/5.6.1 era packages in some distributions",
                "vulnerability_class": "supply-chain backdoor",
                "root_cause": "Malicious upstream commits/build artifacts designed to interfere with downstream SSH authentication when linked via dependencies",
                "severity": "Critical (per major vendor assessments)",
                "patch_status": "Distributions shipped emergency updates / package downgrades",
                "exploitation_status": "Discovery preceded widespread known exploitation reports; treat vendor statements as authoritative",
                "status": SecurityStatus.CONFIRMED,
                "advisory": "https://nvd.nist.gov/vuln/detail/CVE-2024-3094",
            },
            cracked_blurb="The terrifying part was not flashy shellcode — it was patience inside a packaging graph.",
            analysis={
                "why_you_should_care": "This is what 'supply chain' means when it stops being a slide: a compression library became a path into SSH trust.",
                "what_happened": "Andres Freund noticed anomalous sshd behavior and traced it to malicious changes in xz/liblzma. Distributions and NVD catalogued CVE-2024-3094; emergency updates followed.",
                "how_it_works": "At a high level: compromised upstream release machinery inserted a backdoor that could affect sshd when liblzma was pulled into the process via dependencies such as systemd components — exact mechanics are documented in advisories; this article will not reproduce operational exploit steps.",
                "under_the_hood": "Read the OSS-Security thread and distro advisories. Focus on build-system concealment and why maintainers missed it — not on weaponization.",
                "why_they_built_it": "Attacker motivation is attributed in public analyses; WE-RD cares about the engineering failure modes of trust.",
                "what_was_difficult": "Detecting malice that looks like ordinary packaging complexity.",
                "performance": "Not applicable.",
                "trade_offs": "Convenience of shared libraries versus blast radius.",
                "what_is_surprising": "How far social and packaging trust can carry a malicious commit before performance weirdness exposes it.",
                "quick_read": "A confirmed xz supply-chain backdoor affecting SSH paths — read the advisory, not a dramatization.",
                "rabbit_holes": ["supply chain", "reproducible builds", "sshd", "systemd", "maintainer trust"],
            },
        )
    )

    stories.append(
        _make_story(
            session,
            source,
            title="TigerBeetle: an OLTP database obsessed with the hardware",
            slug="tigerbeetle-oltp-database",
            dek="Distributed financial transactions with a systems paper's attention span.",
            description="TigerBeetle is an open-source distributed database for financial transaction processing, designed around explicit fault models, deterministic simulation testing, and careful use of modern storage hardware.",
            category=Category.SOURCE,
            cracked=90,
            rabbit=92,
            tags=["Databases", "Zig", "Distributed systems", "OLTP"],
            stars=14000,
            project="tigerbeetle/tigerbeetle",
            lang="Zig",
            project_desc="The financial transactions database designed for mission-critical safety.",
            url="https://github.com/tigerbeetle/tigerbeetle",
            supporting=[
                ("TigerBeetle docs", "https://docs.tigerbeetle.com/", "original_author"),
            ],
            cracked_blurb="They treated an OLTP database like an avionics problem. That is a compliment.",
            analysis={
                "why_you_should_care": "Most databases inherit decades of 'good enough' durability stories. TigerBeetle starts from fault models and simulation testing as first-class engineering.",
                "what_happened": "The TigerBeetle project published an open-source OLTP database implemented in Zig, with public docs emphasizing safety and performance for transaction workloads.",
                "how_it_works": "A purpose-built transaction protocol and storage engine oriented around double-entry style financial transactions, with deterministic simulation testing to hunt protocol bugs.",
                "under_the_hood": "Read the docs on architecture and DST. The Zig implementation and IO strategy are where the systems taste shows.",
                "why_they_built_it": "Financial ledgers are unforgiving; 'eventual' is not a personality trait you want in money.",
                "what_was_difficult": "Proving protocol correctness under disk/network faults without drowning in Heisenbugs.",
                "performance": "Use only TigerBeetle-published benchmarks and methodology. Do not invent TPS.",
                "trade_offs": "Specialized OLTP focus versus general-purpose SQL comfort.",
                "what_is_surprising": "How much of the pitch is testing philosophy rather than buzzwords.",
                "quick_read": "An OLTP database written in Zig with simulation testing in its bones.",
                "rabbit_holes": ["deterministic simulation", "consensus", "storage faults", "Zig", "double-entry"],
            },
        )
    )

    stories.append(
        _make_story(
            session,
            source,
            title="llama.cpp: large models on the machines you already own",
            slug="llama-cpp-local-inference",
            dek="Quantization and careful C/C++ — not another API wrapper.",
            description="llama.cpp is a popular open-source project for running LLaMA-family and related models locally, with a focus on efficient CPU/GPU inference and quantization formats.",
            category=Category.AI,
            cracked=85,
            rabbit=89,
            tags=["AI", "C++", "Inference", "Quantization", "GGUF"],
            stars=80000,
            project="ggerganov/llama.cpp",
            lang="C++",
            project_desc="LLM inference in C/C++.",
            url="https://github.com/ggerganov/llama.cpp",
            cracked_blurb="The cracked move was treating consumer hardware as a first-class inference target.",
            analysis={
                "why_you_should_care": "A lot of 'AI infrastructure' is rental GPUs. llama.cpp made local inference a systems programming problem: memory layouts, quantization, and backends.",
                "what_happened": "Georgi Gerganov and contributors built a widely used C/C++ inference stack for running LLMs locally across CPUs and various accelerators.",
                "how_it_works": "Model weights in compact formats (e.g. GGUF), quantized matmuls, and backends that map work onto CPU SIMD / GPU APIs depending on build.",
                "under_the_hood": "Look at ggml primitives, quantization types, and how backends register kernels. The README's hardware matrix is part of the design.",
                "why_they_built_it": "So running a model does not require asking permission from a cloud.",
                "what_was_difficult": "Numerics under quantization and keeping performance portable without forking the universe per vendor.",
                "performance": "Tokens/sec depend on model, quant, and hardware. Cite your own runs or project examples — do not invent a leaderboard.",
                "trade_offs": "Local control and efficiency versus the absolute ceiling of huge datacenter kernels.",
                "what_is_surprising": "How much of the ecosystem's practical freedom came from a ruthlessly pragmatic C++ codebase.",
                "quick_read": "Local LLM inference as a systems project.",
                "rabbit_holes": ["quantization", "GGUF", "SIMD", "KV cache", "ggml"],
            },
        )
    )

    stories.append(
        _make_story(
            session,
            source,
            title="Watch: Andreas Kling's Ladybird engine updates",
            slug="watch-andreas-kling-ladybird-june-2024",
            dek="A primary-source engineering diary, not a reaction video.",
            description="Andreas Kling's June 2024 Ladybird update walks through the browser/OS split and engine progress — the kind of technical primary source WE-RD files under WATCH.",
            category=Category.WATCH,
            cracked=78,
            rabbit=86,
            tags=["Browsers", "C++", "Conference-style updates"],
            url="https://www.youtube.com/watch?v=cbw0KrMGHvc",
            video={
                "video_id": "cbw0KrMGHvc",
                "title": "Ladybird browser update (June 2024)",
                "channel": "Andreas Kling",
                "url": "https://www.youtube.com/watch?v=cbw0KrMGHvc",
                "description": "Technical monthly update from the Ladybird founder.",
                "relevance_score": 0.97,
                "technical": True,
            },
            cracked_blurb="The best browser documentation is sometimes a human narrating diffs.",
            analysis={
                "why_you_should_care": "Engine work is easy to mythologize. Primary-source updates show what actually moved: process model, dependencies, and the boring unblockers.",
                "what_happened": "Kling published a June 2024 video update covering Ladybird's direction after focusing the project as a browser.",
                "how_it_works": "The talk is the artifact. Use it as a map into the repo, not as a substitute for reading code.",
                "under_the_hood": "Listen for dependency policy changes, removed OS coupling, and what they chose to stop reinventing.",
                "why_they_built_it": "To keep contributors and sponsors synchronized with reality.",
                "what_was_difficult": "Explaining multi-year engine work in a watchable slice.",
                "performance": "Not applicable.",
                "trade_offs": "Depth versus runtime — these updates stay surprisingly technical.",
                "what_is_surprising": "How much architectural truth appears in a 'monthly update' format.",
                "quick_read": "A technical browser update worth watching before you open the repo.",
                "rabbit_holes": ["Ladybird", "LibWeb", "browser architecture"],
            },
        )
    )

    stories.append(
        _make_story(
            session,
            source,
            title="SerenityOS: a desktop OS someone is actually writing",
            slug="serenityos-from-scratch",
            dek="Kernel, windowing, apps — the joy of building the whole machine.",
            description="SerenityOS is a from-scratch Unix-like desktop operating system with its own kernel, GUI, and userspace culture — the seedbed that also produced Ladybird's web engine.",
            category=Category.MACHINE,
            cracked=95,
            rabbit=94,
            tags=["Operating systems", "C++", "Kernels", "GUI"],
            stars=32000,
            project="SerenityOS/serenity",
            lang="C++",
            project_desc="The Serenity Operating System.",
            url="https://github.com/SerenityOS/serenity",
            cracked_blurb="Nobody needed another OS. That is exactly why it is fascinating.",
            analysis={
                "why_you_should_care": "Hobby OS projects usually stall at 'boots a shell'. Serenity kept going into a coherent desktop system — which is a different difficulty class.",
                "what_happened": "A community built SerenityOS as a modern, nostalgic, from-scratch OS with substantial GUI and application work, later spinning browser work into Ladybird.",
                "how_it_works": "Homegrown kernel and userspace libraries, a window server, and applications written against Serenity's own APIs.",
                "under_the_hood": "Kernel/, Libraries/, and Applications/ in the monorepo. Follow a single system call from app to kernel if you want the full rabbit hole.",
                "why_they_built_it": "Because building the whole stack teaches what abstractions cost.",
                "what_was_difficult": "Consistency across an entire OS while remaining approachable to contributors.",
                "performance": "Not a cloud benchmark game. Judge by engineering completeness.",
                "trade_offs": "Cohesive homemade stack versus leveraging Linux userspace.",
                "what_is_surprising": "The project culture treats 'we wrote that too' as a feature.",
                "quick_read": "A from-scratch desktop OS — open the monorepo and pick a subsystem.",
                "rabbit_holes": ["kernels", "window servers", "libc", "drivers", "IPC"],
            },
        )
    )

    stories.append(
        _make_story(
            session,
            source,
            title="Zig: a language for systems programmers who want explicitness",
            slug="zig-language-systems",
            dek="No hidden allocations. A linker you can argue with. Cross-compilation as a feature.",
            description="Zig is a systems programming language focused on explicit control, predictable performance, and superb cross-compilation — increasingly used for serious infrastructure (including projects like TigerBeetle).",
            category=Category.DEEP,
            cracked=84,
            rabbit=91,
            tags=["Zig", "Compilers", "Linkers", "Systems programming"],
            stars=40000,
            project="ziglang/zig",
            lang="Zig",
            project_desc="Zig programming language.",
            url="https://github.com/ziglang/zig",
            supporting=[
                ("Zig language site", "https://ziglang.org/", "original_author"),
            ],
            cracked_blurb="Zig's whole personality is refusing to let the language surprise you at runtime.",
            analysis={
                "why_you_should_care": "Zig sits in the space between C and Rust with a different answer: make control explicit, keep the toolchain ruthlessly useful for cross builds.",
                "what_happened": "The Zig project continues to ship a language, standard library, and integrated toolchain used by real systems software.",
                "how_it_works": "Manual memory culture, comptime metaprogramming, and a compiler/toolchain stack that treats cross-compilation as normal rather than exotic.",
                "under_the_hood": "Read ziglang.org docs on comptime and the build system. Then look at how real projects structure `build.zig`.",
                "why_they_built_it": "C is ubiquitous and sharp. Zig wants the ubiquity without the undefined superstition.",
                "what_was_difficult": "Bootstrapping a self-hosted compiler world while staying honest about status.",
                "performance": "Depends on code. Zig's claim is control, not magic speedups.",
                "trade_offs": "Explicitness versus the comfort of a borrow checker; younger ecosystem versus C's everything.",
                "what_is_surprising": "How often 'the Zig way' shows up as better packaging of existing systems ideas.",
                "quick_read": "A systems language where explicitness is the feature.",
                "rabbit_holes": ["comptime", "cross-compilation", "LLVM", "allocators", "ABI"],
            },
        )
    )

    return stories


def _editions(session: Session, stories: list[Story]) -> None:
    if session.query(Edition).filter_by(issue_number=1).one_or_none():
        return

    week_start = datetime(2026, 9, 8, tzinfo=timezone.utc)
    week_end = datetime(2026, 9, 14, 23, 59, tzinfo=timezone.utc)
    edition = Edition(
        issue_number=1,
        week_start=week_start,
        week_end=week_end,
        status=EditionStatus.PUBLISHED,
        published_at=datetime(2026, 9, 14, 8, 0, tzinfo=timezone.utc),
        masthead="Hot from the strange corners of engineering.",
        is_demo=False,
        week_in_numbers={
            "sources_scanned": session.query(Source).count(),
            "candidate_stories": session.query(Article).count(),
            "story_clusters": len(stories),
            "high_signal_stories": sum(1 for s in stories if s.signal_score >= 70),
            "published": len(stories),
            "rabbit_holes_discovered": sum(1 for s in stories if s.rabbit_hole_score >= 70),
            "extremely_cracked": sum(1 for s in stories if s.cracked_score >= 90),
        },
    )
    session.add(edition)
    session.flush()

    section_map = [
        ("ladybird-independent-browser-engine", "THE BIG WE-RD", True),
        ("sudo-rs-memory-safe-sudo", "HOW THE HELL DID THEY BUILD THIS?", False),
        ("cosmopolitan-libc-ape", "WHY DOES THIS EXIST?", False),
        ("serenityos-from-scratch", "MACHINE", False),
        ("zig-language-systems", "DEEP END", False),
        ("hare-systems-language", "LANG", False),
        ("xz-utils-backdoor-cve-2024-3094", "BREAK", False),
        ("tigerbeetle-oltp-database", "SOURCE", False),
        ("llama-cpp-local-inference", "AI", False),
        ("watch-andreas-kling-ladybird-june-2024", "WATCH", False),
        ("ladybird-independent-browser-engine", "RABBIT HOLE", False),
    ]
    by_slug = {s.slug: s for s in stories}
    for order, (slug, section, featured) in enumerate(section_map):
        story = by_slug.get(slug)
        if not story:
            continue
        session.add(
            EditionStory(
                edition_id=edition.id,
                story_id=story.id,
                section=section,
                sort_order=order,
                featured=featured,
            )
        )


def main() -> None:
    import os

    from weird.db import get_session_factory, init_db
    from weird.config import get_settings

    get_settings.cache_clear()
    init_db()
    session = get_session_factory()()
    try:
        force = os.environ.get("WEIRD_FORCE_SEED", "").lower() in {"1", "true", "yes"}
        seed(session, force=force)
        session.commit()
        print("seeded" + (" (forced)" if force else ""))
    finally:
        session.close()


if __name__ == "__main__":
    main()
