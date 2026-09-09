/** Prefix public asset URLs with NEXT_PUBLIC_BASE_PATH for GitHub project Pages. */
export function publicUrl(assetPath: string): string {
  const base = (process.env.NEXT_PUBLIC_BASE_PATH || "").replace(/\/$/, "");
  const path = assetPath.startsWith("/") ? assetPath : `/${assetPath}`;
  return `${base}${path}`;
}
