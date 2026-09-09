export default function AboutPage() {
  return (
    <main className="prose-story max-w-3xl py-10 font-serif text-lg leading-relaxed">
      <h1 className="font-serif text-5xl">What is WE-RD?</h1>
      <p className="mt-6 italic">Pronounced “weird.” The hyphen is the logo.</p>
      <p className="mt-4">
        WE-RD is an automated weekly technical-curiosity newspaper. It is not a generic technology-news site, not an RSS
        reader, and not a pile of AI recaps. It hunts for work that makes engineers say: I did not know this existed —
        wait, how did they actually build that? — I need to see the source.
      </p>
      <p className="mt-4">
        The pipeline is the other product: discovery, normalization, deduplication, clustering, scoring, credibility,
        rabbit-hole detection, then Sunday publication. Popularity is a weak signal. A 70-star repository can beat a
        million-view recap.
      </p>
      <p className="mt-4">
        CRACKED SCORE is personality. WE-RD SCORE is the serious weighted interestingness model. Neither invents
        benchmarks. If the sources do not establish a number, the article says so.
      </p>
    </main>
  );
}
