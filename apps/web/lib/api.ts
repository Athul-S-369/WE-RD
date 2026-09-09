import { readFile } from "fs/promises";
import path from "path";

export type StoryCard = {
  slug: string;
  title: string;
  dek: string;
  description: string;
  category: string;
  category_label: string;
  signal_score: number;
  cracked_score: number;
  rabbit_hole_score: number;
  confidence: string;
  tags: string[];
  is_demo: boolean;
  cracked_blurb: string;
  primary_source: string | null;
  score_dimensions?: Record<string, number>;
  processing_mode?: string | null;
};

export type StoryDetail = StoryCard & {
  analysis: Record<string, unknown>;
  security: Record<string, unknown> | null;
  leak: Record<string, unknown> | null;
  timeline: { occurred_at: string; headline: string; body: string; source_url: string | null }[];
  videos: {
    video_id: string;
    title: string;
    channel: string;
    url: string;
    description: string;
    thumbnail: string | null;
    relevance_score: number;
    technical: boolean;
  }[];
  projects: { name: string; url: string; host: string; stars: number | null; language: string | null; description: string }[];
  sources: { role: string; url: string; title: string; credibility_kind: string; credibility_score: number }[];
  score_breakdown?: {
    dimensions?: Record<string, number>;
    contributions?: Record<string, number>;
    weights?: Record<string, number>;
    explanations?: Record<string, string>;
    rabbit_paths?: string[];
  };
  related?: { slug: string; title: string; category: string; score: number; shared: string[] }[];
  source_graph?: { nodes: { kind: string; id: string; label: string; url?: string | null }[]; edges: { source: string; target: string; relation: string }[] };
  youtube_status?: string | null;
  editorial?: Record<string, unknown>;
};

export type Edition = {
  issue_number: number;
  week_start: string;
  week_end: string;
  status: string;
  published_at: string | null;
  masthead: string;
  week_in_numbers: Record<string, number>;
  is_demo: boolean;
  stories: { section: string; sort_order: number; featured: boolean; story: StoryCard }[];
};

export type EditionListItem = {
  issue_number: number;
  week_start: string;
  week_end: string;
  status: string;
  published_at: string | null;
  is_demo: boolean;
  story_count: number;
};

export type Capabilities = {
  processing_mode: Record<string, string | boolean>;
  search: Record<string, string | boolean>;
  llm: Record<string, string | boolean>;
  embeddings: Record<string, string | boolean | number>;
};

function useStaticContent() {
  return process.env.NEXT_PUBLIC_STATIC === "1" || process.env.WEIRD_STATIC_EXPORT === "1";
}

function baseUrl() {
  if (typeof window === "undefined") {
    return process.env.API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

function contentRoot() {
  // Build-time: read from public/content on disk. Runtime static: fetch /content/...
  return path.join(process.cwd(), "public", "content");
}

async function readContentFile<T>(rel: string): Promise<T> {
  const filePath = path.join(contentRoot(), rel);
  const raw = await readFile(filePath, "utf8");
  return JSON.parse(raw) as T;
}

async function loadStatic<T>(apiPath: string): Promise<T> {
  const clean = apiPath.split("?")[0];
  if (clean === "/editions/current") {
    return readContentFile<T>("current.json");
  }
  if (clean === "/editions") {
    return readContentFile<T>("editions.json");
  }
  const editionMatch = clean.match(/^\/editions\/(\d+)$/);
  if (editionMatch) {
    return readContentFile<T>(`editions/${editionMatch[1]}.json`);
  }
  const storyMatch = clean.match(/^\/stories\/([^/]+)$/);
  if (storyMatch) {
    return readContentFile<T>(`stories/${decodeURIComponent(storyMatch[1])}.json`);
  }
  if (clean === "/stories") {
    const params = new URLSearchParams(apiPath.includes("?") ? apiPath.split("?")[1] : "");
    const category = params.get("category");
    const all = await readContentFile<StoryCard[]>("stories-index.json");
    const items = category ? all.filter((s) => s.category.toUpperCase() === category.toUpperCase()) : all;
    return { items, page: 1, total: items.length } as T;
  }
  if (clean === "/search") {
    const params = new URLSearchParams(apiPath.includes("?") ? apiPath.split("?")[1] : "");
    const q = (params.get("q") || "").toLowerCase().trim();
    const category = params.get("category");
    const tag = params.get("tag");
    const minScore = params.get("min_score");
    const confidence = params.get("confidence");
    let items = await readContentFile<StoryCard[]>("stories-index.json");
    if (category) items = items.filter((s) => s.category.toUpperCase() === category.toUpperCase());
    if (tag) items = items.filter((s) => s.tags.some((t) => t.toLowerCase() === tag.toLowerCase()));
    if (minScore) items = items.filter((s) => s.signal_score >= Number(minScore));
    if (confidence) items = items.filter((s) => s.confidence === confidence);
    if (q) {
      const tokens = q.split(/\s+/).filter(Boolean);
      items = items
        .map((s) => {
          const hay = `${s.title} ${s.dek} ${s.description} ${s.tags.join(" ")} ${s.category}`.toLowerCase();
          const hits = tokens.filter((t) => hay.includes(t)).length;
          return { s, score: hits };
        })
        .filter((x) => x.score > 0)
        .sort((a, b) => b.score - a.score)
        .map((x) => x.s);
    }
    return { query: q, total: items.length, items, mode: { search: "static-lexical" } } as T;
  }
  if (clean === "/capabilities") {
    return {
      processing_mode: { zero_key: true, publisher: "github-pages" },
      search: { semantic: "static-lexical" },
      llm: { mode_label: "exported" },
      embeddings: { backend: "exported" },
    } as T;
  }
  if (clean === "/categories") {
    const byCat = await readContentFile<Record<string, StoryCard[]>>("categories.json");
    return Object.entries(byCat).map(([slug, items]) => ({
      slug,
      label: `WE-RD / ${slug}`,
      count: items.length,
    })) as T;
  }
  throw new Error(`No static mapping for ${apiPath}`);
}

export async function api<T>(path: string): Promise<T> {
  if (useStaticContent()) {
    return loadStatic<T>(path);
  }
  try {
    const res = await fetch(`${baseUrl()}${path}`, { next: { revalidate: 30 } });
    if (!res.ok) {
      throw new Error(`API ${path} ${res.status}`);
    }
    return res.json() as Promise<T>;
  } catch (err) {
    // Graceful fallback to committed content when local API is down.
    try {
      return await loadStatic<T>(path);
    } catch {
      throw err;
    }
  }
}

export async function listStorySlugs(): Promise<string[]> {
  try {
    const cards = await readContentFile<StoryCard[]>("stories-index.json");
    return cards.map((c) => c.slug);
  } catch {
    return [];
  }
}

export async function listIssueNumbers(): Promise<number[]> {
  try {
    const editions = await readContentFile<EditionListItem[]>("editions.json");
    return editions.map((e) => e.issue_number);
  } catch {
    return [];
  }
}
