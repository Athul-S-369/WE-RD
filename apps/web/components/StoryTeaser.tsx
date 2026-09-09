import Link from "next/link";
import type { StoryCard } from "@/lib/api";
import { CrackedMeter } from "./CrackedMeter";
import { StoryVisual } from "./StoryVisual";

type Variant = "featured" | "lead" | "tile" | "rail";

export function StoryTeaser({
  story,
  featured = false,
  variant,
}: {
  story: StoryCard;
  featured?: boolean;
  variant?: Variant;
}) {
  const mode: Variant = variant ?? (featured ? "featured" : "tile");

  const titleClass =
    mode === "featured"
      ? "text-[1.65rem] leading-[1.1] sm:text-3xl md:text-5xl"
      : mode === "lead"
        ? "text-xl leading-snug sm:text-2xl md:text-[1.65rem]"
        : mode === "rail"
          ? "text-base leading-snug sm:text-lg"
          : "text-lg leading-snug sm:text-xl md:text-2xl";

  const showVisual = mode !== "rail";

  return (
    <article className="flex h-full min-w-0 flex-col overflow-hidden">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-accent">
        {story.category_label}
      </div>

      {showVisual && (
        <div className="mt-2 mb-1 min-w-0 sm:mt-3">
          <StoryVisual
            story={story}
            size={mode === "featured" ? "lg" : mode === "lead" ? "md" : "sm"}
            preferPhoto={mode === "featured" || mode === "lead"}
            caption={story.title}
          />
        </div>
      )}

      <h2 className={`mt-2 break-words font-serif ${titleClass}`}>
        <Link href={`/story/${story.slug}`} className="hover:text-accent">
          {story.title}
        </Link>
      </h2>

      <p
        className={`mt-2 min-w-0 break-words font-serif text-ink/80 sm:mt-3 ${
          mode === "featured" ? "drop-cap text-base sm:text-lg md:text-xl" : "text-[0.95rem] leading-relaxed"
        } ${
          mode === "rail"
            ? "line-clamp-3 text-sm"
            : mode === "tile"
              ? "line-clamp-3 sm:line-clamp-4"
              : mode === "lead"
                ? "line-clamp-4 md:line-clamp-none"
                : "line-clamp-5 md:line-clamp-none"
        }`}
      >
        {story.dek}
      </p>

      <div className="mt-auto min-w-0 pt-3 sm:pt-4">
        {mode === "featured" || mode === "lead" ? (
          <div className={mode === "featured" ? "flex flex-col gap-3 sm:flex-row sm:items-end sm:gap-8" : ""}>
            <CrackedMeter score={story.cracked_score} blurb={story.cracked_blurb} compact={mode !== "featured"} />
            <div className="font-mono text-[10px] uppercase tracking-widest text-muted">
              WE-RD {Math.round(story.signal_score)}
              <span className="mx-1.5 text-ink/25">·</span>
              Hole {Math.round(story.rabbit_hole_score)}
            </div>
          </div>
        ) : (
          <div className="font-mono text-[10px] uppercase tracking-widest text-muted">
            <span className="text-cracked">Cracked {story.cracked_score}</span>
            <span className="mx-1.5 text-ink/25">·</span>
            WE-RD {Math.round(story.signal_score)}
          </div>
        )}
      </div>

      {story.tags.length > 0 && mode !== "rail" && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {story.tags.slice(0, mode === "featured" ? 4 : 3).map((tag) => (
            <span
              key={tag}
              className="border border-ink/20 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-widest"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </article>
  );
}
