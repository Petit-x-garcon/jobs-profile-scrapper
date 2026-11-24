import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { JOBS_KEY } from "@/hooks/use-jobs"
import { PROFILE_KEY } from "@/hooks/use-profile"
import { getCv, uploadCv } from "@/lib/api/cv"

export const CV_KEY = ["cv"] as const

export function useCv() {
  return useQuery({ queryKey: CV_KEY, queryFn: getCv })
}

export function useUploadCv() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: uploadCv,
    onSuccess: ({ cv, profile }) => {
      queryClient.setQueryData(CV_KEY, cv)
      queryClient.setQueryData(PROFILE_KEY, profile)
      // A new CV clears job scores on the backend.
      return queryClient.invalidateQueries({ queryKey: JOBS_KEY })
    },
  })
}
