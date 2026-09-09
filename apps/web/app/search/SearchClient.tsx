"use client";

import { useMemo, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { StoryTeaser } from "@/components/StoryTeaser";
import type { StoryCard } from "@/lib/api";

function contentUrl(rel: string) {
  const base = process.env.NEXT_PUBLIC_BASE_PATH || "";
  return `${base}/content/${rel}`;
}

export default function SearchClient() {
  const sp = useSearchParams();
  const q = sp.get("q") ?? "";
  const category = sp.get("category") ?? "";
  const tag = sp.get("tag") ?? "";
  const minScore = sp.get("min_score") ?? "";
  const confidence = sp.get("confidence") ?? "";

  const [all, setAll] = useState<StoryCard[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(contentUrl("stories-index.json"))
      .then((r) => {
        if (!r.ok) throw new Error(`content ${r.status}`);
        return r.json();
      })
      .then((data) => setAll(data))
      .catch(async () => {
        try {
          const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
          const params = new URLSearchParams();
          if (q) params.set("q", q);
          if (category) params.set("category", category);
          if (tag) params.set("tag", tag);
          if (minScore) params.set("min_score", minScore);
          if (confidence) params.set("confidence", confidence);
          const res = await fetch(`${api}/search?${params}`);
          if (!res.ok) throw new Error("api search failed");
          const body = await res.json();
          setAll(body.items || []);
        } catch (e) {
          setError(e instanceof Error ? e.message : "search unavailable");
        }
      });
  }, [q, category, tag, minScore, confidence]);

  const items = useMemo(() => {
    let rows = [...all];
    if (category) rows = rows.filter((s) => s.category.toUpperCase() === category.toUpperCase());
    if (tag) rows = rows.filter((s) => s.tags.some((t) => t.toLowerCase() === tag.toLowerCase()));
    if (minScore) rows = rows.filter((s) => s.signal_score >= Number(minScore));
    if (confidence) rows = rows.filter((s) => s.confidence === confidence);
    if (q.trim()) {
      const tokens = q.toLowerCase().split(/\s+/).filter(Boolean);
      rows = rows
        .map((s) => {
          const hay = `${s.title} ${s.dek} ${s.description} ${s.tags.join(" ")} ${s.category}`.toLowerCase();
          const hits = tokens.filter((t) => hay.includes(t)).length;
          return { s, hits };
        })
        .filter((x) => x.hits > 0)
        .sort((a, b) => b.hits - a.hits)
        .map((x) => x.s);
    }
    return rows;
  }, [all, q, category, tag, minScore, confidence]);

  return (
    <main className="py-6 md:py-8">
      <div className="rule-double">
        <h1 className="font-serif text-5xl">Search</h1>
        <p className="font-serif text-lg">Search the published WE-RD archive.</p>
      </div>
      <form className="bento mt-0 grid-cols-1 md:grid-cols-12">
        <div className="bento-cell md:col-span-5">
          <input
            name="q"
            defaultValue={q}
            placeholder="weird things built in C"
            className="w-full bg-transparent font-serif text-lg outline-none placeholder:text-ink/35"
          />
        </div>
        <div className="bento-cell md:col-span-2">
          <select name="category" defaultValue={category} className="w-full bg-transparent font-mono text-xs uppercase outline-none">
            <option value="">All desks</option>
            {["BUILD", "WHY", "DEEP", "LANG", "BREAK", "AI", "MACHINE", "LAB", "SOURCE", "WATCH", "LEAK"].map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div className="bento-cell md:col-span-1">
          <input name="tag" defaultValue={tag} placeholder="tag" className="w-full bg-transparent font-mono text-xs uppercase outline-none" />
        </div>
        <div className="bento-cell md:col-span-1">
          <input name="min_score" defaultValue={minScore} placeholder="min" className="w-full bg-transparent font-mono text-xs outline-none" />
        </div>
        <div className="bento-cell md:col-span-2">
          <select name="confidence" defaultValue={confidence} className="w-full bg-transparent font-mono text-xs uppercase outline-none">
            <option value="">Any confidence</option>
            {["confirmed", "likely", "unverified", "rumor", "demo"].map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div className="bento-cell bento-cell-ink md:col-span-1">
          <button className="w-full font-mono text-xs uppercase tracking-widest text-paper">Find</button>
        </div>
      </form>
      <p className="mt-4 font-mono text-xs uppercase text-muted">{items.length} matches</p>
      {error && <p className="mt-2 text-accent">{error}</p>}
      <div className="bento mt-2 grid-cols-1 md:grid-cols-2">
        {items.map((story) => (
          <div key={story.slug} className="bento-cell">
            <StoryTeaser story={story} variant="tile" />
          </div>
        ))}
      </div>
      {!items.length && !error && (
        <p className="mt-8 font-serif text-lg text-ink/70">
          No matches. Browse the <Link href="/archive">archive</Link>.
        </p>
      )}
    </main>
  );
}
