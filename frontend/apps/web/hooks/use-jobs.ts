import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"

import {
  importJob,
  listJobs,
  startScrape,
  type JobFilters,
} from "@/lib/api/jobs"

export const JOBS_KEY = ["jobs"] as const

export function useJobs(filters: JobFilters) {
  return useQuery({
    queryKey: [...JOBS_KEY, filters],
    queryFn: () => listJobs(filters),
    placeholderData: keepPreviousData,
  })
}

export function useImportJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: importJob,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: JOBS_KEY }),
  })
}

export function useScrape() {
  return useMutation({ mutationFn: startScrape })
}
