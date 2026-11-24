"use client"

import { useState } from "react"
import { RefreshCwIcon } from "lucide-react"

import { Alert, AlertDescription } from "@workspace/ui/components/alert"
import { Button } from "@workspace/ui/components/button"
import { Skeleton } from "@workspace/ui/components/skeleton"
import { ImportDialog } from "@/components/jobs/import-dialog"
import { JobCard } from "@/components/jobs/job-card"
import { JobFilters } from "@/components/jobs/job-filters"
import { SavedSites } from "@/components/jobs/saved-sites"
import { ScrapeControl } from "@/components/jobs/scrape-button"
import { useJobs } from "@/hooks/use-jobs"

const SIZE = 20
const REFETCH_DELAY_MS = 60_000

export function JobsReport() {
  const [page, setPage] = useState(1)
  const [keywords, setKeywords] = useState("")
  const [source, setSource] = useState<string>()
  const [minScore, setMinScore] = useState("")
  const parsed = minScore === "" ? NaN : Number(minScore)
  const filters = {
    source,
    min_score: Number.isNaN(parsed) ? undefined : parsed,
    q: keywords || undefined,
  }
  const { data, error, isPending, isFetching, refetch } = useJobs({
    page,
    size: SIZE,
    ...filters,
  })
  const pages = data ? Math.max(1, Math.ceil(data.total / data.size)) : 1

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4 rounded-2xl border border-border bg-card p-5 sm:p-7">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Job scraper
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Jobs appear in the order they were saved, newest first.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <ImportDialog />
          <ScrapeControl
            onStarted={() => setTimeout(() => refetch(), REFETCH_DELAY_MS)}
          />
        </div>
      </div>
      <SavedSites />
      <div className="flex flex-wrap items-end justify-between gap-3 rounded-xl border border-border bg-card p-4">
        <JobFilters
          keywords={keywords}
          onKeywords={(v) => {
            setKeywords(v)
            setPage(1)
          }}
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
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 4 }, (_, i) => (
            <Skeleton key={i} className="h-52 w-full rounded-xl" />
          ))}
        </div>
      )}
      {data?.items.length === 0 && (
        <p className="py-10 text-center text-sm text-muted-foreground">
          {keywords || source || minScore
            ? "No jobs match these filters."
            : "No jobs yet. Scrape now or import a job post."}
        </p>
      )}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
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
          <span className="text-sm text-muted-foreground">
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
