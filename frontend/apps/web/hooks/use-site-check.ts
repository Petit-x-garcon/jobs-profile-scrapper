import { useMutation } from "@tanstack/react-query"

import { checkSite } from "@/lib/api/site-check"

export function useSiteCheck() {
  return useMutation({ mutationFn: checkSite })
}
