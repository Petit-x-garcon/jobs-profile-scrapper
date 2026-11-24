import { useMutation, useQueryClient } from "@tanstack/react-query"

import { JOBS_KEY } from "@/hooks/use-jobs"
import { analyzeJobs } from "@/lib/api/recommendations"

export function useAnalyzeJobs() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: analyzeJobs,
    // Scores are saved on the jobs, so the list can show them too.
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: JOBS_KEY }),
        queryClient.invalidateQueries({ queryKey: ["job-rankings"] }),
      ]),
  })
}
