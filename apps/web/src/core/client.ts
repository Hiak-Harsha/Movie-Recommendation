import { CineMatchClient } from "@cinematch/api-client";

// In browser, hits same-origin /api which Next.js rewrites to http://127.0.0.1:8000/api
// This ensures cm_sid cookie is first-party and credentials: "include" works seamlessly.
export const api = new CineMatchClient(
  typeof window !== "undefined" ? "" : process.env.INTERNAL_API_URL || "http://127.0.0.1:8000"
);
