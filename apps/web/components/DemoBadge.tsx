export function DemoBadge({ demo }: { demo: boolean }) {
  if (!demo) return null;
  return (
    <span className="border border-ink px-1.5 py-0.5 text-[10px] tracking-[0.2em] text-ink">Demo / example</span>
  );
}
