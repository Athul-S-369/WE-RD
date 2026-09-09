import Link from "next/link";

function todayFolio() {
  return new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date());
}

export function SiteHeader() {
  return (
    <header className="mb-2">
      <div className="folio flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1 border-b border-ink/25 pb-2 text-[9px] sm:text-[10px]">
        <span>Vol. I · Technical curiosity</span>
        <span className="order-last w-full text-center sm:order-none sm:w-auto">{todayFolio()}</span>
        <span className="hidden sm:inline">Open source edition</span>
      </div>

      <div className="rule-double mt-2 text-center">
        <Link
          href="/"
          className="inline-block font-serif text-[clamp(2.75rem,12vw,6rem)] leading-none tracking-tight md:text-8xl"
        >
          WE<span className="masthead-hyphen">-</span>RD
        </Link>
        <p className="mx-auto mt-2 max-w-xl px-1 font-serif text-base italic leading-snug text-ink/75 sm:text-lg md:text-xl">
          Things worth falling down a rabbit hole for.
        </p>
      </div>

      <nav className="rule-double-b mt-2 flex flex-wrap items-center justify-center gap-x-3 gap-y-2 py-2.5 font-mono text-[10px] uppercase tracking-[0.16em] sm:gap-x-5 sm:py-3 sm:text-[11px] sm:tracking-[0.2em]">
        <Link href="/" className="hover:text-accent">
          Front page
        </Link>
        <span className="text-ink/30" aria-hidden>
          |
        </span>
        <Link href="/archive" className="hover:text-accent">
          Archive
        </Link>
        <span className="text-ink/30" aria-hidden>
          |
        </span>
        <Link href="/search" className="hover:text-accent">
          Search
        </Link>
        <span className="text-ink/30" aria-hidden>
          |
        </span>
        <Link href="/about" className="hover:text-accent">
          About
        </Link>
        <span className="text-ink/30" aria-hidden>
          |
        </span>
        <Link href="/admin" className="hover:text-accent">
          The desk
        </Link>
      </nav>
    </header>
  );
}
