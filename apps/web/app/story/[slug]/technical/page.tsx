import Link from "next/link";
import { notFound } from "next/navigation";
import { api, listStorySlugs, type StoryDetail } from "@/lib/api";
export async function generateStaticParams() {
  const slugs = await listStorySlugs();
  return slugs.map((slug) => ({ slug }));
}

function text(value: unknown) {
  return typeof value === "string" ? value : "";
}

export default async function TechnicalPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  let story: StoryDetail;
  try {
    story = await api<StoryDetail>(`/stories/${slug}`);
  } catch {
    notFound();
  }

  return (
    <main className="min-w-0 overflow-x-clip py-6 sm:py-8 md:py-10">
      <Link href={`/story/${story.slug}`} className="font-mono text-xs uppercase tracking-widest hover:text-accent">
        ← Back to story
      </Link>
      <p className="mt-4 font-mono text-[10px] uppercase tracking-[0.2em] text-accent sm:text-xs">
        {story.category_label} · technical read
      </p>
      <h1 className="mt-2 break-words font-serif text-[clamp(1.6rem,5.5vw,3rem)] leading-tight md:text-5xl">
        {story.title}
      </h1>

      <section className="mt-6 border-y border-ink py-4 sm:mt-8 sm:py-6">
        <h2 className="font-mono text-xs uppercase tracking-[0.2em]">Quick read · 30–60s</h2>
        <p className="mt-2 max-w-2xl font-serif text-lg sm:text-xl">{text(story.analysis.quick_read)}</p>
      </section>

      <section className="mt-6 sm:mt-8">
        <h2 className="font-mono text-xs uppercase tracking-[0.2em]">Technical read</h2>
        <p className="mt-2 font-serif text-base leading-relaxed sm:text-lg">{text(story.analysis.how_it_works)}</p>
        <p className="mt-4 font-serif text-base leading-relaxed sm:text-lg">{text(story.analysis.under_the_hood)}</p>
        <p className="mt-4 font-serif text-base leading-relaxed sm:text-lg">{text(story.analysis.what_was_difficult)}</p>
      </section>

      <section className="mt-8 border-[3px] border-ink p-4 sm:mt-10 sm:p-6">
        <h2 className="font-mono text-xs uppercase tracking-[0.22em]">Source dive</h2>
        <p className="mt-2 font-serif">The point is not the recap. The point is where you go next.</p>
        <div className="mt-4 grid gap-6 md:grid-cols-3">
          <div>
            <h3 className="font-mono text-[11px] uppercase tracking-widest text-accent">Source code</h3>
            <ul className="mt-2 space-y-2 font-mono text-sm">
              {story.projects.length === 0 && <li>No repository attached.</li>}
              {story.projects.map((p) => (
                <li key={p.url}>
                  <a className="underline" href={p.url}>
                    {p.name}
                  </a>
                  {p.language ? ` · ${p.language}` : ""}
                  {p.stars != null ? ` · ${p.stars}★` : ""}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="font-mono text-[11px] uppercase tracking-widest text-accent">Watch</h3>
            <ul className="mt-2 space-y-2 font-mono text-sm">
              {story.videos.length === 0 && <li>No technical video until YouTube is configured.</li>}
              {story.videos.map((v) => (
                <li key={v.video_id}>
                  <a className="underline" href={v.url}>
                    {v.title}
                  </a>
                  <div className="text-[11px] text-muted">{v.channel}</div>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="font-mono text-[11px] uppercase tracking-widest text-accent">Read</h3>
            <ul className="mt-2 space-y-2 font-mono text-sm">
              {story.sources.map((s) => (
                <li key={s.url}>
                  <a className="underline" href={s.url}>
                    {s.title || s.url}
                  </a>
                  <div className="text-[11px] text-muted">
                    {s.role} · {s.credibility_kind}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>
    </main>
  );
}
