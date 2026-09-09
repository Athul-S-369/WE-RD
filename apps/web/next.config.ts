import type { NextConfig } from "next";

const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";
const isStatic = process.env.WEIRD_STATIC_EXPORT === "1";

const nextConfig: NextConfig = {
  output: isStatic ? "export" : "standalone",
  ...(basePath ? { basePath } : {}),
  trailingSlash: isStatic,
  images: { unoptimized: true },
};

export default nextConfig;
