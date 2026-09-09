import { StoryTeaser } from "@/components/StoryTeaser";
import { api, type StoryCard } from "@/lib/api";
export async function generateStaticParams() {
  return ["BUILD", "WHY", "DEEP", "LANG", "BREAK", "AI", "MACHINE", "LAB", "SOURCE", "WATCH", "LEAK"].map(
    (slug) => ({ slug }),
  );
}

export default async function CategoryPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const data = await api<{ items: StoryCard[] }>(`/stories?category=${encodeURIComponent(slug)}`).catch(() => ({
    items: [],
  }));
  return (
    <main className="py-10">
      <h1 className="font-serif text-5xl">WE-RD / {slug.toUpperCase()}</h1>
      {data.items.map((story) => (
        <StoryTeaser key={story.slug} story={story} />
      ))}
    </main>
  );
}
