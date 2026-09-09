"use client";

import { useState } from "react";

type Health = {
  sources: { name: string; active: boolean; last_error: string | null; credibility_kind: string }[];
  latest_runs: { kind: string; status: string; started_at: string | null; metrics: Record<string, unknown>; error: string | null }[];
  story_counts: Record<string, number>;
  article_count: number;
  cluster_count: number;
  processing_mode?: Record<string, string | boolean>;
};

export default function AdminPage() {
  const [token, setToken] = useState("");
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");

  const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  async function load() {
    setError("");
    const res = await fetch(`${api}/admin/health`, { headers: { "x-admin-token": token } });
    if (!res.ok) {
      setError(`Denied (${res.status}). Set WEIRD_ADMIN_TOKEN.`);
      setHealth(null);
      return;
    }
    setHealth(await res.json());
  }

  async function run(path: "daily" | "sunday") {
    setBusy(path);
    setError("");
    try {
      const res = await fetch(`${api}/admin/pipeline/${path}`, {
        method: "POST",
        headers: { "x-admin-token": token },
      });
      if (!res.ok) {
        setError(`Pipeline ${path} failed (${res.status}).`);
        return;
      }
      await load();
    } finally {
      setBusy("");
    }
  }

  return (
    <main className="py-10">
      <h1 className="font-serif text-5xl">The desk</h1>
      <p className="mt-2 max-w-xl font-serif text-lg">
        Source health, pipeline runs, clusters. Protected by <code className="font-mono">WEIRD_ADMIN_TOKEN</code>.
      </p>
      <div className="mt-6 flex flex-wrap gap-3">
        <input
          type="password"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder="admin token"
          className="border-[3px] border-ink bg-paper px-3 py-2 font-mono"
        />
        <button onClick={load} className="border-[3px] border-ink px-4 font-mono text-xs uppercase tracking-widest">
          Open
        </button>
        <button
          onClick={() => run("daily")}
          disabled={!token || !!busy}
          className="border-[3px] border-ink px-4 font-mono text-xs uppercase tracking-widest disabled:opacity-40"
        >
          {busy === "daily" ? "Running…" : "Run daily"}
        </button>
        <button
          onClick={() => run("sunday")}
          disabled={!token || !!busy}
          className="border-[3px] border-ink px-4 font-mono text-xs uppercase tracking-widest disabled:opacity-40"
        >
          {busy === "sunday" ? "Running…" : "Run Sunday"}
        </button>
      </div>
      {error && <p className="mt-4 text-accent">{error}</p>}
      {health && (
        <div className="mt-8 grid gap-8">
          <section className="grid gap-4 md:grid-cols-3">
            <Stat label="Articles" value={health.article_count} />
            <Stat label="Clusters" value={health.cluster_count} />
            <Stat
              label="Stories"
              value={Object.values(health.story_counts).reduce((a, b) => a + b, 0)}
            />
          </section>
          {health.processing_mode && (
            <section>
              <h2 className="border-y border-ink py-2 font-mono text-xs uppercase tracking-[0.22em]">
                Processing mode
              </h2>
              <pre className="mt-3 overflow-auto border border-ink bg-card p-4 font-mono text-xs leading-relaxed">
                {JSON.stringify(health.processing_mode, null, 2)}
              </pre>
            </section>
          )}
          <section>
            <h2 className="border-y border-ink py-2 font-mono text-xs uppercase tracking-[0.22em]">Story status</h2>
            <dl className="mt-3 grid gap-2 font-mono text-sm md:grid-cols-3">
              {Object.entries(health.story_counts).map(([k, v]) => (
                <div key={k}>
                  <dt className="uppercase tracking-widest text-muted">{k}</dt>
                  <dd className="font-serif text-2xl">{v}</dd>
                </div>
              ))}
            </dl>
          </section>
          <section>
            <h2 className="border-y border-ink py-2 font-mono text-xs uppercase tracking-[0.22em]">Sources</h2>
            <ul className="mt-3 divide-y divide-ink/20 font-mono text-sm">
              {health.sources.map((s) => (
                <li key={s.name} className="flex flex-wrap items-baseline justify-between gap-2 py-2">
                  <span>
                    {s.name}{" "}
                    <span className="text-muted">({s.credibility_kind})</span>
                  </span>
                  <span className={s.last_error ? "text-accent" : ""}>
                    {s.active ? (s.last_error ? `error: ${s.last_error.slice(0, 80)}` : "ok") : "inactive"}
                  </span>
                </li>
              ))}
            </ul>
          </section>
          <section>
            <h2 className="border-y border-ink py-2 font-mono text-xs uppercase tracking-[0.22em]">Recent runs</h2>
            <pre className="mt-3 overflow-auto border border-ink bg-card p-4 font-mono text-xs leading-relaxed">
              {JSON.stringify(health.latest_runs, null, 2)}
            </pre>
          </section>
        </div>
      )}
    </main>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="border border-ink p-4">
      <div className="font-mono text-xs uppercase tracking-[0.2em] text-muted">{label}</div>
      <div className="mt-1 font-serif text-4xl">{value}</div>
    </div>
  );
}
