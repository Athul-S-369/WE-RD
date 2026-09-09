import Link from "next/link";
import { api, type EditionListItem } from "@/lib/api";
export default async function ArchivePage() {
  const editions = await api<EditionListItem[]>("/editions").catch(() => []);
  return (
    <main className="py-6 md:py-8">
      <div className="rule-double">
        <h1 className="font-serif text-5xl">Archive</h1>
        <p className="font-serif text-xl italic">Previous Sundays.</p>
      </div>
      <div className="bento mt-0 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
        {editions.map((ed, i) => (
          <Link
            key={ed.issue_number}
            href={`/issue/${ed.issue_number}`}
            className={`bento-cell block ${i === 0 ? "bento-cell-ink sm:col-span-2 lg:col-span-1" : ""}`}
          >
            <span className={`font-mono text-[10px] uppercase tracking-widest ${i === 0 ? "text-paper/60" : "text-muted"}`}>
              {ed.week_end.slice(0, 10)}
            </span>
            <span className={`mt-2 block font-serif text-3xl ${i === 0 ? "text-paper" : ""}`}>
              Issue {String(ed.issue_number).padStart(3, "0")}
            </span>
            <span className={`mt-2 block font-mono text-[11px] uppercase tracking-widest ${i === 0 ? "text-paper/70" : "text-muted"}`}>
              {ed.story_count} stories
            </span>
          </Link>
        ))}
      </div>
    </main>
  );
}
