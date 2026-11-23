import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { JOBS_KEY } from "@/hooks/use-jobs"
import { getProfile, updateProfile } from "@/lib/api/profile"

export const PROFILE_KEY = ["profile"] as const

export function useProfile() {
  return useQuery({ queryKey: PROFILE_KEY, queryFn: getProfile })
}

export function useUpdateProfile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: updateProfile,
    onSuccess: (profile) => {
      queryClient.setQueryData(PROFILE_KEY, profile)
      // Saving re-scores jobs on the backend.
      return queryClient.invalidateQueries({ queryKey: JOBS_KEY })
    },
  })
}
