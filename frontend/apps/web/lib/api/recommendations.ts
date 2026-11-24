import { api } from "@/lib/api/client"
import type { JobFilters } from "@/lib/api/jobs"
import {
  rankingPageSchema,
  shortlistSchema,
  recommendationsSchema,
} from "@/lib/api/schemas"

/** AI calls run per job on the server, so allow more than the default timeout. */
const ANALYZE_TIMEOUT_MS = 180_000

export async function analyzeJobs(jobIds: string[]) {
  const { data } = await api.post(
    "/api/recommendations",
    { job_ids: jobIds },
    { timeout: ANALYZE_TIMEOUT_MS }
  )
  return recommendationsSchema.parse(data)
}

export type MatchFilters = Omit<JobFilters, "page" | "size">

export async function getRankingPage(filters: MatchFilters, page: number) {
  const { data } = await api.get("/api/recommendations/rankings", {
    params: { ...filters, page },
  })
  return rankingPageSchema.parse(data)
}

// Older tabs can still invoke this export during a development hot reload.
export async function findBestMatches(filters: MatchFilters, page?: number) {
  if (typeof page === "number") return getRankingPage(filters, page)
  const { data } = await api.get("/api/recommendations/shortlist", {
    params: filters,
  })
  return shortlistSchema.parse(data)
}
