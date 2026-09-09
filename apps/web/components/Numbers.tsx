export function Numbers({ data }: { data: Record<string, number> }) {
  const items = [
    ["sources_scanned", "sources scanned"],
    ["candidate_stories", "candidates"],
    ["story_clusters", "clusters"],
    ["high_signal_stories", "high-signal"],
    ["published", "published"],
    ["rabbit_holes_discovered", "rabbit holes"],
    ["extremely_cracked", "extremely cracked"],
  ] as const;

  return (
    <section className="my-6 animate-fade-up-delay sm:my-8">
      <div className="rule-double">
        <h2 className="font-mono text-xs uppercase tracking-[0.25em]">Week in numbers</h2>
        <p className="font-mono text-[10px] uppercase text-muted">From the pipeline — never fabricated.</p>
      </div>
      <div className="bento grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7">
        {items.map(([key, label], i) => (
          <div key={key} className={`bento-cell ${i === 0 ? "bento-cell-ink col-span-2 sm:col-span-1" : ""}`}>
            <div className={`font-serif text-2xl tabular-nums sm:text-3xl md:text-4xl ${i === 0 ? "text-paper" : ""}`}>
              {data[key] ?? 0}
            </div>
            <div
              className={`mt-1 font-mono text-[9px] uppercase tracking-widest sm:text-[10px] ${
                i === 0 ? "text-paper/70" : "text-muted"
              }`}
            >
              {label}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
