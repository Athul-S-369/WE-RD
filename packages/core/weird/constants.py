from __future__ import annotations

from enum import StrEnum


class Category(StrEnum):
    BUILD = "BUILD"
    WHY = "WHY"
    DEEP = "DEEP"
    LANG = "LANG"
    BREAK = "BREAK"
    AI = "AI"
    MACHINE = "MACHINE"
    LAB = "LAB"
    SOURCE = "SOURCE"
    WATCH = "WATCH"
    LEAK = "LEAK"


CATEGORY_LABELS = {
    Category.BUILD: "WE-RD / BUILD",
    Category.WHY: "WE-RD / WHY",
    Category.DEEP: "WE-RD / DEEP",
    Category.LANG: "WE-RD / LANG",
    Category.BREAK: "WE-RD / BREAK",
    Category.AI: "WE-RD / AI",
    Category.MACHINE: "WE-RD / MACHINE",
    Category.LAB: "WE-RD / LAB",
    Category.SOURCE: "WE-RD / SOURCE",
    Category.WATCH: "WE-RD / WATCH",
    Category.LEAK: "WE-RD / LEAK",
}


class StoryStatus(StrEnum):
    CANDIDATE = "candidate"
    CLUSTERED = "clustered"
    ANALYZED = "analyzed"
    SELECTED = "selected"
    PUBLISHED = "published"
    REJECTED = "rejected"


class EditionStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


class Confidence(StrEnum):
    CONFIRMED = "confirmed"
    VENDOR_CONFIRMED = "vendor_confirmed"
    STRONGLY_CORROBORATED = "strongly_corroborated"
    PLAUSIBLE = "plausible"
    UNVERIFIED = "unverified"
    RUMOR = "rumor"
    DEMO = "demo"


class SecurityStatus(StrEnum):
    DISCLOSED = "disclosed"
    CONFIRMED = "confirmed"
    EXPLOIT_DEMONSTRATED = "exploit_demonstrated"
    EXPLOITED_IN_THE_WILD = "exploited_in_the_wild"
    THEORETICAL = "theoretical"
    UNVERIFIED = "unverified"


class LeakStatus(StrEnum):
    UNVERIFIED = "unverified"
    CORROBORATED = "corroborated"
    CONFIRMED = "confirmed"


class CredibilityKind(StrEnum):
    OFFICIAL_REPO = "official_project_repository"
    ORIGINAL_AUTHOR = "original_author"
    RESEARCH_PAPER = "research_paper"
    ACADEMIC = "academic_institution"
    VENDOR_ADVISORY = "vendor_advisory"
    RESPECTED_PUBLICATION = "respected_technical_publication"
    SECONDARY = "secondary_reporting"
    COMMUNITY = "community_post"
    ANONYMOUS = "anonymous_source"
    UNVERIFIED_SOCIAL = "unverified_social_media"


EDITION_SECTIONS = [
    "THE BIG WE-RD",
    "HOW THE HELL DID THEY BUILD THIS?",
    "WHY DOES THIS EXIST?",
    "DEEP END",
    "BREAK",
    "LANG",
    "MACHINE",
    "AI",
    "LAB",
    "SOURCE",
    "WATCH",
    "RABBIT HOLE",
]

CRACKED_BLURBS = [
    (95, "Someone absolutely did not need to build this."),
    (88, "This is the kind of project that ruins weekends."),
    (80, "Technically unnecessary. Emotionally inevitable."),
    (70, "A respectable amount of chaos."),
    (60, "Curious enough to warrant a second look."),
    (0, "Interesting, but not yet unhinged."),
]


def cracked_blurb(score: int) -> str:
    for threshold, line in CRACKED_BLURBS:
        if score >= threshold:
            return line
    return CRACKED_BLURBS[-1][1]
