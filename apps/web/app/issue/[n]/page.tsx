import { api, listIssueNumbers, type Edition } from "@/lib/api";
import { Numbers } from "@/components/Numbers";
import { StoryTeaser } from "@/components/StoryTeaser";
import { notFound } from "next/navigation";
export async function generateStaticParams() {
  const nums = await listIssueNumbers();
  return nums.map((n) => ({ n: String(n) }));
}

export default async function IssuePage({ params }: { params: Promise<{ n: string }> }) {
  const { n } = await params;
  let edition: Edition;
  try {
    edition = await api<Edition>(`/editions/${n}`);
  } catch {
    notFound();
  }
  return (
    <main className="py-10">
      <p className="font-mono text-xs uppercase tracking-[0.2em]">Issue {String(edition.issue_number).padStart(3, "0")}</p>
      <h1 className="font-serif text-5xl">{edition.masthead}</h1>
      <Numbers data={edition.week_in_numbers} />
      {edition.stories.map((row) => (
        <div key={`${row.section}-${row.story.slug}`}>
          <p className="mt-8 font-mono text-[11px] uppercase tracking-[0.2em] text-accent">{row.section}</p>
          <StoryTeaser story={row.story} featured={row.featured} />
        </div>
      ))}
    </main>
  );
}
