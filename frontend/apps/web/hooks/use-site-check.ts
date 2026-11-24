import { useEffect } from "react"
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"

import {
  crawlPages,
  latestCrawl,
  startCrawl,
  stopCrawl,
} from "@/lib/api/site-check"

const STATUS_KEY = ["site-check", "latest"] as const

export function useCrawlStatus() {
  return useQuery({
    queryKey: STATUS_KEY,
    queryFn: latestCrawl,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === "queued" || status === "running" || query.state.error
        ? 1500
        : false
    },
    refetchOnWindowFocus: true,
  })
}

export function useSiteCheck() {
  const cache = useQueryClient()
  const status = useCrawlStatus()
  const run = status.data
  const update = (result: Awaited<ReturnType<typeof startCrawl>>) =>
    cache.setQueryData(STATUS_KEY, result)
  const start = useMutation({ mutationFn: startCrawl, onSuccess: update })
  const stop = useMutation({ mutationFn: stopCrawl, onSuccess: update })
  const checked = run?.checked ?? 0
  const results = useInfiniteQuery({
    queryKey: ["site-check", "pages", run?.id],
    queryFn: ({ pageParam }) => crawlPages(run!.id, pageParam),
    initialPageParam: 0,
    enabled: !!run && checked > 0,
    staleTime: Infinity,
    getNextPageParam: (last, _pages, offset) =>
      offset + last.length < checked ? offset + last.length : undefined,
  })
  const { hasNextPage, isFetching, isError, fetchNextPage } = results
  useEffect(() => {
    if (hasNextPage && !isFetching && !isError) void fetchNextPage()
  }, [hasNextPage, isFetching, isError, fetchNextPage, results.dataUpdatedAt])

  return {
    url: run?.url ?? "",
    currentUrl: run?.current_url,
    pages: results.data?.pages.flat() ?? [],
    checked,
    pageCount: run?.discovered ?? 0,
    jobCount: run?.job_count ?? 0,
    submittedAt: run?.id,
    queued: run?.status === "queued",
    failed: run?.status === "failed",
    isPending:
      start.isPending || run?.status === "queued" || run?.status === "running",
    loading: status.isPending,
    stopped: run?.status === "stopped",
    error:
      start.error ??
      stop.error ??
      status.error ??
      results.error ??
      (run?.error ? new Error(run.error) : null),
    start: start.mutate,
    stop: () => {
      if (run) stop.mutate(run.id)
    },
  }
}
