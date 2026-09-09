import Link from "next/link";
import { notFound } from "next/navigation";
import { CrackedMeter } from "@/components/CrackedMeter";
import { StoryVisual } from "@/components/StoryVisual";
import { api, listStorySlugs, type StoryDetail } from "@/lib/api";
export async function generateStaticParams() {
  const slugs = await listStorySlugs();
  return slugs.map((slug) => ({ slug }));
}

function text(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function list(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String) : [];
}

export default async function StoryPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  let story: StoryDetail;
  try {
    story = await api<StoryDetail>(`/stories/${slug}`);
  } catch {
    notFound();
  }

  const sections = [
    ["Why you should care", story.analysis.why_you_should_care],
    ["What happened", story.analysis.what_happened],
    ["How it works", story.analysis.how_it_works],
    ["Under the hood", story.analysis.under_the_hood],
    ["The hard part", story.analysis.what_was_difficult],
    ["Performance", story.analysis.performance],
    ["Trade-offs", story.analysis.trade_offs],
    ["What is surprising", story.analysis.what_is_surprising],
  ] as const;

  return (
    <main className="min-w-0 overflow-x-clip py-4 sm:py-6 md:py-8">
      <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-accent sm:text-xs">
        {story.category_label}
      </p>
      <h1 className="mt-2 max-w-4xl break-words font-serif text-[clamp(1.75rem,6vw,3.75rem)] leading-tight sm:mt-3 md:text-6xl">
        {story.title}
      </h1>
      <p className="mt-3 max-w-2xl font-serif text-lg italic leading-snug text-ink/80 sm:mt-4 sm:text-xl md:text-2xl">
        {story.dek}
      </p>

      <div className="bento mt-6 grid-cols-2 sm:mt-8 md:grid-cols-12">
        <div className="bento-cell col-span-2 md:col-span-5">
          <StoryVisual story={story} size="lg" preferPhoto caption={story.title} />
        </div>
        <div className="bento-cell col-span-2 sm:col-span-1 md:col-span-3">
          <CrackedMeter score={story.cracked_score} blurb={story.cracked_blurb} />
        </div>
        <div className="bento-cell md:col-span-2">
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted sm:text-xs">WE-RD score</div>
          <div className="font-serif text-3xl sm:text-4xl">{Math.round(story.signal_score)} / 100</div>
          <div className="mt-3 font-mono text-[10px] uppercase tracking-[0.2em] text-muted sm:mt-4 sm:text-xs">
            Rabbit-hole
          </div>
          <div className="font-serif text-3xl sm:text-4xl">{Math.round(story.rabbit_hole_score)}</div>
        </div>
        <div className="bento-cell bento-cell-ink col-span-2 sm:col-span-1 md:col-span-2">
          <div className="font-mono text-[10px] uppercase tracking-widest text-paper/70 sm:text-xs">Confidence</div>
          <div className="mt-1 font-serif text-xl text-paper sm:text-2xl">{story.confidence}</div>
          {story.processing_mode && (
            <p className="mt-3 font-mono text-[10px] text-paper/60">Analysis mode: {story.processing_mode}</p>
          )}
          {story.youtube_status && (
            <p className="mt-1 font-mono text-[10px] text-paper/60">YouTube: {story.youtube_status}</p>
          )}
          <Link
            href={`/story/${story.slug}/technical`}
            className="mt-4 inline-block border-2 border-paper px-3 py-2 font-mono text-[10px] uppercase tracking-[0.18em] text-paper transition-colors hover:bg-paper hover:text-ink sm:mt-6 sm:px-4 sm:text-[11px]"
          >
            Go technical →
          </Link>
        </div>
      </div>

      {Object.keys(story.score_breakdown?.contributions || {}).length > 0 && (
        <aside className="my-8 border border-ink/30 p-4">
          <h2 className="font-mono text-xs uppercase tracking-[0.2em]">Score components</h2>
          <ul className="mt-3 grid gap-2 font-mono text-xs md:grid-cols-2">
            {Object.entries(story.score_breakdown?.contributions || {})
              .sort((a, b) => b[1] - a[1])
              .map(([k, v]) => (
                <li key={k} className="flex justify-between gap-4 border-b border-ink/10 pb-1">
                  <span className="uppercase tracking-widest text-muted">{k}</span>
                  <span>
                    {Math.round(story.score_breakdown?.dimensions?.[k] ?? 0)} → contrib {v.toFixed(1)}
                  </span>
                </li>
              ))}
          </ul>
        </aside>
      )}

      {story.security && (
        <aside className="my-8 border border-ink bg-card p-4">
          <h2 className="font-mono text-xs uppercase tracking-[0.2em]">Security status — not sensationalized</h2>
          <dl className="mt-3 grid gap-2 font-mono text-sm md:grid-cols-2">
            {Object.entries(story.security).map(([k, v]) => (
              <div key={k}>
                <dt className="uppercase tracking-widest text-muted">{k}</dt>
                <dd>{String(v)}</dd>
              </div>
            ))}
          </dl>
        </aside>
      )}

      {story.leak && (
        <aside className="my-8 border-[3px] border-accent p-4">
          <h2 className="font-mono text-xs uppercase tracking-[0.2em] text-accent">Leak — labeled, not laundered</h2>
          <dl className="mt-3 grid gap-2 text-sm">
            {Object.entries(story.leak).map(([k, v]) => (
              <div key={k}>
                <dt className="font-mono uppercase tracking-widest text-muted">{k}</dt>
                <dd className="font-serif">{String(v)}</dd>
              </div>
            ))}
          </dl>
        </aside>
      )}

      <div className="prose-story mt-10 grid gap-10 md:grid-cols-12">
        <div className="space-y-10 md:col-span-8">
          {sections.map(([heading, body]) => (
            <section key={heading}>
              <h2 className="font-mono text-xs uppercase tracking-[0.22em] text-accent">{heading}</h2>
              <p className="mt-2 font-serif text-lg leading-relaxed">{text(body)}</p>
            </section>
          ))}
        </div>
        <aside className="md:col-span-4">
          <h2 className="font-mono text-xs uppercase tracking-[0.2em]">Source graph</h2>
          <ul className="mt-3 space-y-2 border-l-2 border-ink pl-4 font-mono text-xs">
            {story.projects.map((p) => (
              <li key={p.url}>
                GITHUB —{" "}
                <a className="underline" href={p.url}>
                  {p.name}
                </a>
              </li>
            ))}
            {story.videos.map((v) => (
              <li key={v.video_id}>
                YOUTUBE —{" "}
                <a className="underline" href={v.url}>
                  {v.title}
                </a>
              </li>
            ))}
            {story.sources.map((s) => (
              <li key={s.url}>
                {s.role.toUpperCase()} —{" "}
                <a className="underline" href={s.url}>
                  {s.title || s.url}
                </a>
              </li>
            ))}
          </ul>

          <h2 className="mt-8 font-mono text-xs uppercase tracking-[0.2em]">Rabbit holes</h2>
          <ul className="mt-2 list-disc pl-4 font-serif">
            {list(story.analysis.rabbit_holes).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>

          {(story.related || []).length > 0 && (
            <>
              <h2 className="mt-8 font-mono text-xs uppercase tracking-[0.2em]">Related rabbit holes</h2>
              <ul className="mt-2 space-y-2 font-serif text-sm">
                {story.related!.map((r) => (
                  <li key={r.slug}>
                    <Link className="underline" href={`/story/${r.slug}`}>
                      {r.title}
                    </Link>
                    {r.shared?.length ? (
                      <span className="ml-2 font-mono text-[10px] uppercase text-muted">
                        via {r.shared.slice(0, 3).join(", ")}
                      </span>
                    ) : null}
                  </li>
                ))}
              </ul>
            </>
          )}

          <h2 className="mt-8 font-mono text-xs uppercase tracking-[0.2em]">Timeline</h2>
          <ol className="mt-2 space-y-3">
            {story.timeline.map((event) => (
              <li key={event.headline} className="border-b border-ink/20 pb-2">
                <div className="font-mono text-[10px] uppercase text-muted">{event.occurred_at.slice(0, 10)}</div>
                <div className="font-serif">{event.headline}</div>
                <p className="text-sm text-ink/70">{event.body}</p>
              </li>
            ))}
          </ol>
        </aside>
      </div>
    </main>
  );
}
