import type { ReactNode } from "react";
import type { StoryCard } from "@/lib/api";
import { publicUrl } from "@/lib/paths";

type Size = "sm" | "md" | "lg";

function pickKind(story: Pick<StoryCard, "category" | "slug" | "tags">): string {
  const tags = (story.tags || []).map((t) => t.toLowerCase());
  const slug = story.slug.toLowerCase();
  if (slug.includes("cosmopolitan") || tags.includes("portability") || tags.includes("linkers")) return "portable";
  if (slug.includes("ladybird") || tags.includes("browsers") || tags.includes("html")) return "browser";
  if (slug.includes("sudo") || tags.includes("privilege") || tags.includes("security")) return "privilege";
  if (story.category === "AI" || tags.includes("inference") || tags.includes("quantization")) return "ai";
  if (story.category === "MACHINE" || tags.includes("kernels") || tags.includes("operating systems")) return "os";
  if (story.category === "SOURCE" || tags.includes("databases") || tags.includes("oltp")) return "database";
  if (story.category === "LANG" || tags.includes("compilers") || tags.includes("type systems")) return "lang";
  if (story.category === "BREAK") return "break";
  if (story.category === "WATCH") return "watch";
  if (story.category === "DEEP") return "deep";
  return "default";
}

function photoFor(kind: string): string | null {
  if (kind === "portable") return publicUrl("/illustrations/illus-portable-binary.png");
  if (kind === "browser") return publicUrl("/illustrations/illus-browser-engine.png");
  if (kind === "privilege") return publicUrl("/illustrations/illus-privilege.png");
  if (kind === "deep" || kind === "default" || kind === "watch") {
    return publicUrl("/illustrations/illus-rabbit-hole.png");
  }
  return null;
}

const sizeClass: Record<Size, string> = {
  sm: "story-visual--sm",
  md: "story-visual--md",
  lg: "story-visual--lg",
};

export function StoryVisual({
  story,
  size = "md",
  preferPhoto = false,
  caption,
}: {
  story: Pick<StoryCard, "category" | "slug" | "tags" | "title">;
  size?: Size;
  preferPhoto?: boolean;
  caption?: string;
}) {
  const kind = pickKind(story);
  const photo = preferPhoto ? photoFor(kind) : null;

  return (
    <figure className={`story-visual ${sizeClass[size]} w-full max-w-full overflow-hidden border border-ink/30`}>
      {photo ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={photo}
          alt=""
          className="h-full w-full object-cover object-center"
          sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 640px"
        />
      ) : (
        <Diagram kind={kind} />
      )}
      {caption && <figcaption className="sr-only">{caption}</figcaption>}
      <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-ink/55 to-transparent px-2 py-1 sm:py-1.5">
        <span className="font-mono text-[8px] uppercase tracking-[0.16em] text-paper/90 sm:text-[9px] sm:tracking-[0.18em]">
          Fig. · {kind}
        </span>
      </div>
    </figure>
  );
}

export function MastheadVisual() {
  return (
    <figure className="story-visual story-visual--masthead w-full max-w-full overflow-hidden border border-ink/20">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={publicUrl("/illustrations/illus-rabbit-hole.png")}
        alt=""
        className="h-full w-full object-cover object-center opacity-95"
        sizes="(max-width: 768px) 100vw, 280px"
      />
    </figure>
  );
}

const ink = "#16140f";
const accent = "#9c1c12";
const mono = "ui-monospace, 'IBM Plex Mono', monospace";

function Label({
  x,
  y,
  children,
  fill = ink,
  size = 11,
}: {
  x: number;
  y: number;
  children: string;
  fill?: string;
  size?: number;
}) {
  return (
    <text x={x} y={y} fill={fill} fontFamily={mono} fontSize={size} letterSpacing="0.04em">
      {children}
    </text>
  );
}

function Diagram({ kind }: { kind: string }) {
  const common = {
    fill: "none",
    stroke: ink,
    strokeWidth: 1.6,
    vectorEffect: "non-scaling-stroke" as const,
  };

  const frame = (children: ReactNode) => (
    <svg
      viewBox="0 0 320 140"
      className="h-full w-full"
      preserveAspectRatio="xMidYMid meet"
      aria-hidden
    >
      {children}
    </svg>
  );

  if (kind === "browser") {
    return frame(
      <>
        <rect x="12" y="14" width="70" height="28" {...common} />
        <Label x={28} y={32}>
          HTML
        </Label>
        <rect x="98" y="14" width="70" height="28" {...common} />
        <Label x={118} y={32}>
          CSS
        </Label>
        <rect x="184" y="14" width="70" height="28" {...common} />
        <Label x={208} y={32}>
          JS
        </Label>
        <path d="M47 42v18M133 42v18M219 42v18" {...common} />
        <rect x="70" y="60" width="180" height="28" {...common} fill="#efe6d4" />
        <Label x={108} y={78}>
          LAYOUT · PAINT
        </Label>
        <path d="M160 88v14" {...common} />
        <rect x="95" y="102" width="130" height="26" {...common} stroke={accent} />
        <Label x={128} y={119} fill={accent}>
          BROWSER
        </Label>
      </>,
    );
  }

  if (kind === "portable") {
    return frame(
      <>
        <rect x="120" y="16" width="80" height="36" {...common} stroke={accent} />
        <Label x={138} y={38} fill={accent}>
          APE.bin
        </Label>
        <path d="M160 52 L60 90 M160 52 L160 90 M160 52 L260 90" {...common} strokeDasharray="3 3" />
        <rect x="20" y="90" width="70" height="30" {...common} />
        <Label x={38} y={109}>
          UNIX
        </Label>
        <rect x="125" y="90" width="70" height="30" {...common} />
        <Label x={144} y={109}>
          WIN
        </Label>
        <rect x="230" y="90" width="70" height="30" {...common} />
        <Label x={248} y={109}>
          BSD
        </Label>
      </>,
    );
  }

  if (kind === "privilege") {
    return frame(
      <>
        <rect x="20" y="20" width="120" height="100" {...common} />
        <Label x={58} y={72} size={14}>
          user
        </Label>
        <rect x="180" y="20" width="120" height="100" {...common} stroke={accent} />
        <Label x={214} y={72} fill={accent} size={14}>
          root
        </Label>
        <path d="M140 70h40" {...common} />
        <circle cx="160" cy="70" r="12" {...common} fill="#efe6d4" />
        <Label x={152} y={74} size={10}>
          su
        </Label>
      </>,
    );
  }

  if (kind === "ai") {
    return frame(
      <>
        {[0, 1, 2, 3].map((i) => (
          <rect key={i} x={30 + i * 8} y={24 + i * 8} width="220" height="22" {...common} />
        ))}
        <Label x={98} y={122} fill={accent}>
          WEIGHTS · KV · QUANT
        </Label>
      </>,
    );
  }

  if (kind === "os") {
    return frame(
      <>
        {["APPS", "WINDOW SERVER", "KERNEL", "HARDWARE"].map((label, i) => (
          <g key={label}>
            <rect
              x="40"
              y={16 + i * 28}
              width="240"
              height="24"
              {...common}
              stroke={i === 2 ? accent : ink}
            />
            <Label x={118} y={32 + i * 28}>
              {label}
            </Label>
          </g>
        ))}
      </>,
    );
  }

  if (kind === "database") {
    return frame(
      <>
        <ellipse cx="160" cy="28" rx="90" ry="16" {...common} />
        <path d="M70 28v70c0 10 40 18 90 18s90-8 90-18V28" {...common} />
        <path d="M70 55c0 10 40 16 90 16s90-6 90-16" {...common} />
        <path d="M70 80c0 10 40 16 90 16s90-6 90-16" {...common} />
        <Label x={122} y={128} fill={accent}>
          PAGES · WAL
        </Label>
      </>,
    );
  }

  if (kind === "lang") {
    return frame(
      <>
        <circle cx="160" cy="30" r="14" {...common} stroke={accent} />
        <Label x={150} y={34} fill={accent} size={10}>
          src
        </Label>
        <path d="M160 44v16M160 60l-50 20M160 60l50 20" {...common} />
        <rect x="70" y="80" width="60" height="24" {...common} />
        <rect x="130" y="80" width="60" height="24" {...common} />
        <rect x="190" y="80" width="60" height="24" {...common} />
        <Label x={88} y={96} size={10}>
          AST
        </Label>
        <Label x={152} y={96} size={10}>
          IR
        </Label>
        <Label x={204} y={96} size={10}>
          CODE
        </Label>
      </>,
    );
  }

  if (kind === "break") {
    return frame(
      <>
        <rect x="30" y="30" width="50" height="50" {...common} />
        <rect x="95" y="40" width="50" height="50" {...common} />
        <rect x="160" y="50" width="50" height="50" {...common} stroke={accent} />
        <rect x="225" y="35" width="50" height="50" {...common} />
        <path d="M80 55h15M145 65h15M210 75h15" {...common} />
        <Label x={170} y={80} fill={accent} size={10}>
          xz?
        </Label>
        <Label x={108} y={128}>
          SUPPLY CHAIN
        </Label>
      </>,
    );
  }

  if (kind === "watch") {
    return frame(
      <>
        <rect x="40" y="25" width="240" height="90" {...common} />
        <polygon points="130,45 130,95 190,70" fill={accent} opacity="0.85" />
        <Label x={108} y={130}>
          TECHNICAL TALK
        </Label>
      </>,
    );
  }

  if (kind === "deep") {
    return frame(
      <>
        <path d="M40 100 H280" {...common} />
        <path d="M60 100 V40 H120 V100" {...common} />
        <path d="M140 100 V55 H200 V100" {...common} stroke={accent} />
        <path d="M220 100 V30 H270 V100" {...common} />
        <Label x={148} y={48} fill={accent} size={10}>
          hot path
        </Label>
      </>,
    );
  }

  return frame(
    <>
      <circle cx="160" cy="70" r="40" {...common} stroke={accent} />
      <path d="M160 30c40 20 40 60 0 80c-40-20-40-60 0-80z" {...common} />
      <Label x={118} y={128}>
        RABBIT HOLE
      </Label>
    </>,
  );
}
