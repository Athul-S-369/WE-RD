export function CrackedMeter({
  score,
  blurb,
  compact = false,
}: {
  score: number;
  blurb: string;
  compact?: boolean;
}) {
  const filled = Math.min(20, Math.max(0, Math.round(score / 5)));
  const bar = "█".repeat(filled) + "░".repeat(20 - filled);
  return (
    <div className="min-w-0 max-w-full overflow-hidden font-mono text-[11px] sm:text-xs">
      <div className="uppercase tracking-[0.2em] text-cracked">Cracked score</div>
      <div className={`font-serif text-ink ${compact ? "text-xl sm:text-2xl" : "text-3xl sm:text-4xl"}`}>
        {score} / 100
      </div>
      <div className="meter-bar text-cracked" aria-hidden>
        {bar}
      </div>
      {!compact && blurb && (
        <p className="mt-1 max-w-xs break-words text-[11px] italic leading-snug text-muted sm:text-xs">{blurb}</p>
      )}
    </div>
  );
}
