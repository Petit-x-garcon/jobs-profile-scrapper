"use client"

import { useState } from "react"
import { RefreshCwIcon } from "lucide-react"

import { Alert, AlertDescription } from "@workspace/ui/components/alert"
import { Button } from "@workspace/ui/components/button"
import { Skeleton } from "@workspace/ui/components/skeleton"
import { ImportDialog } from "@/components/jobs/import-dialog"
import { JobCard } from "@/components/jobs/job-card"
import { JobFilters } from "@/components/jobs/job-filters"
import { ScrapeControl } from "@/components/jobs/scrape-button"
import { useJobs } from "@/hooks/use-jobs"

const SIZE = 20
const REFETCH_DELAY_MS = 60_000

export function JobsReport() {
  const [page, setPage] = useState(1)
  const [source, setSource] = useState<string>()
  const [minScore, setMinScore] = useState("")
  const parsed = minScore === "" ? NaN : Number(minScore)
  const { data, error, isPending, isFetching, refetch } = useJobs({
    page,
    size: SIZE,
    source,
    min_score: Number.isNaN(parsed) ? undefined : parsed,
  })
  const pages = data ? Math.max(1, Math.ceil(data.total / data.size)) : 1

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">Job report</h1>
        <div className="flex flex-wrap gap-2">
          <ImportDialog />
          <ScrapeControl
            onStarted={() => setTimeout(() => refetch(), REFETCH_DELAY_MS)}
          />
        </div>
      </div>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <JobFilters
          source={source}
          minScore={minScore}
          onSource={(v) => {
            setSource(v)
            setPage(1)
          }}
          onMinScore={(v) => {
            setMinScore(v)
            setPage(1)
          }}
        />
        <Button
          variant="outline"
          onClick={() => refetch()}
          disabled={isFetching}
        >
          <RefreshCwIcon className={isFetching ? "animate-spin" : ""} />
          Refresh
        </Button>
      </div>
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      )}
      {isPending && !error && (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 4 }, (_, i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      )}
      {data?.items.length === 0 && (
        <p className="text-muted-foreground py-10 text-center text-sm">
          No jobs yet. Scrape now or import a job post.
        </p>
      )}
      <div className="flex flex-col gap-3">
        {data?.items.map((job) => (
          <JobCard key={job.id} job={job} />
        ))}
      </div>
      {data && data.total > 0 && (
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </Button>
          <span className="text-muted-foreground text-sm">
            Page {data.page} of {pages} ({data.total} jobs)
          </span>
          <Button
            variant="outline"
            disabled={page >= pages}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  )
}
