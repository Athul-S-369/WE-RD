import { api, type Edition } from "@/lib/api";
import { Numbers } from "@/components/Numbers";
import { StoryTeaser } from "@/components/StoryTeaser";
import { MastheadVisual } from "@/components/StoryVisual";
import Link from "next/link";

export default async function HomePage() {
  let edition: Edition | null = null;
  try {
    edition = await api<Edition>("/editions/current");
  } catch {
    edition = null;
  }

  if (!edition) {
    return (
      <main className="py-12">
        <div className="bento max-w-xl">
          <div className="bento-cell">
            <h1 className="font-serif text-5xl leading-none">
              THE STRANGE
              <br />
              SIDE OF
              <br />
              ENGINEERING.
            </h1>
            <p className="mt-6 font-serif text-xl">The press is offline. Start the API, then reload.</p>
          </div>
        </div>
      </main>
    );
  }

  const featured = edition.stories.find((s) => s.featured) ?? edition.stories[0];
  const rest = edition.stories.filter(
    (row) => !(featured && row.story.slug === featured.story.slug && row.featured),
  );

  const lead = rest[0];
  const rail = rest.slice(1, 4);
  const more = rest.slice(4);

  const bySection = new Map<string, typeof edition.stories>();
  for (const row of more) {
    const list = bySection.get(row.section) ?? [];
    list.push(row);
    bySection.set(row.section, list);
  }

  const issueDate = edition.published_at
    ? new Intl.DateTimeFormat("en-US", { month: "long", day: "numeric", year: "numeric" }).format(
        new Date(edition.published_at),
      )
    : null;

  return (
    <main className="min-w-0 overflow-x-clip">
      <section className="animate-fade-up bento mb-4 grid-cols-1 sm:mb-6 md:grid-cols-12">
        <div className="bento-cell bento-cell-ink md:col-span-5">
          <p className="font-mono text-[10px] uppercase tracking-[0.28em] text-paper/65">This week&apos;s edition</p>
          <p className="mt-2 font-serif text-[clamp(2.5rem,10vw,3.75rem)] leading-[0.92] text-paper md:mt-3 md:text-6xl">
            WE<span className="text-accent">-</span>RD
          </p>
          <p className="mt-3 font-serif text-xl leading-tight text-paper/90 sm:mt-4 sm:text-2xl md:text-3xl">
            THE STRANGE
            <br />
            SIDE OF
            <br />
            ENGINEERING.
          </p>
        </div>
        <div className="bento-cell md:col-span-4">
          <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-muted">On the stands</p>
          <p className="mt-2 font-serif text-3xl leading-none sm:text-4xl">
            Issue {String(edition.issue_number).padStart(3, "0")}
          </p>
          {issueDate && (
            <p className="mt-2 font-mono text-[10px] uppercase tracking-widest text-muted sm:text-xs">{issueDate}</p>
          )}
          <p className="mt-3 font-serif text-lg italic leading-snug sm:mt-4 sm:text-xl">{edition.masthead}</p>
        </div>
        <div className="bento-cell md:col-span-3">
          <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-accent">Hot this week</p>
          <div className="mt-2 sm:mt-3">
            <MastheadVisual />
          </div>
          <p className="mt-2 font-serif text-base leading-snug italic sm:mt-3 sm:text-lg">
            Things worth falling down a rabbit hole for.
          </p>
          <p className="mt-2 font-mono text-[10px] uppercase tracking-widest text-muted sm:mt-3">
            {edition.stories.length} dispatches · scored for fascination
          </p>
        </div>
      </section>

      {featured && (
        <section className="animate-fade-up-delay mb-6 sm:mb-8">
          <div className="rule-double">
            <h2 className="font-mono text-xs uppercase tracking-[0.25em] text-accent">The front page</h2>
          </div>
          <div className="bento grid-cols-1 md:grid-cols-12">
            <div className="bento-cell md:col-span-8">
              <p className="mb-2 font-mono text-[10px] uppercase tracking-[0.25em] text-accent sm:mb-3">The big WE-RD</p>
              <StoryTeaser story={featured.story} variant="featured" />
              <Link
                href={`/story/${featured.story.slug}/technical`}
                className="mt-4 inline-block border-2 border-ink px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] transition-colors hover:bg-ink hover:text-paper sm:mt-5 sm:px-4 sm:text-[11px]"
              >
                Go technical →
              </Link>
            </div>

            <div className="bento-cell md:col-span-4">
              {lead && (
                <div className="mb-1">
                  <p className="mb-2 font-mono text-[10px] uppercase tracking-[0.2em] text-muted">{lead.section}</p>
                  <StoryTeaser story={lead.story} variant="lead" />
                </div>
              )}
              <div className={lead ? "story-rail mt-4" : ""}>
                <p className="mb-3 font-mono text-[10px] uppercase tracking-[0.2em] text-muted">Also hot</p>
                {rail.map((row) => (
                  <div key={row.story.slug} className="story-rail">
                    <StoryTeaser story={row.story} variant="rail" />
                  </div>
                ))}
                {rail.length === 0 && (
                  <p className="font-serif italic text-muted">More dispatches below the fold.</p>
                )}
              </div>
            </div>
          </div>
        </section>
      )}

      <Numbers data={edition.week_in_numbers} />

      {[...bySection.entries()].map(([section, rows]) => (
        <section key={section} className="mb-6 sm:mb-8">
          <div className="rule-double">
            <h2 className="font-mono text-xs uppercase tracking-[0.22em]">{section}</h2>
          </div>
          <div className="bento grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
            {rows.map((row, idx) => (
              <div key={`${section}-${row.story.slug}`} className="bento-cell">
                <StoryTeaser story={row.story} variant={idx === 0 ? "lead" : "tile"} />
              </div>
            ))}
          </div>
        </section>
      ))}
    </main>
  );
}
