import type { NextConfig } from "next";

const apiHost = process.env.INTERNAL_API_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  transpilePackages: ["@cinematch/api-client"],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiHost}/api/:path*`,
      },
      {
        source: "/health",
        destination: `${apiHost}/health`,
      },
    ];
  },
};

export default nextConfig;
