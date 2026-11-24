import { api } from "@/lib/api/client"
import { recommendationsSchema } from "@/lib/api/schemas"

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
