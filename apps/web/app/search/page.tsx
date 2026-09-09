import { Suspense } from "react";
import SearchClient from "./SearchClient";

export default function SearchPage() {
  return (
    <Suspense fallback={<main className="py-10 font-serif text-xl">Loading the archive…</main>}>
      <SearchClient />
    </Suspense>
  );
}
