"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Button } from "@workspace/ui/components/button"
import { Checkbox } from "@workspace/ui/components/checkbox"
import { Dialog, DialogTrigger } from "@workspace/ui/components/dialog"
import { JobFilters } from "@/components/jobs/job-filters"
import { JobDetailsDialog } from "@/components/jobs/job-details-dialog"
import { ScoreBadge } from "@/components/jobs/score-badge"
import { useAnalyzeJobs } from "@/hooks/use-recommendations"
import { getRankingPage, type MatchFilters } from "@/lib/api/recommendations"
import type { LocalMatch } from "@/lib/api/schemas"

function RankedJobs({ items }: { items: LocalMatch[] }) {
  const analyze = useAnalyzeJobs()
  const [excluded, setExcluded] = useState<string[]>([])
  const selected = items.filter(({ job }) => !excluded.includes(job.id))
  const fresh = selected.filter(({ job }) => job.score === null).length
  return (
    <section className="space-y-3">
      <Button
        disabled={analyze.isPending || !selected.length}
        onClick={() => analyze.mutate(selected.map(({ job }) => job.id))}
      >
        {analyze.isPending
          ? "Analyzing…"
          : !selected.length
            ? "Select jobs to analyze"
            : fresh
              ? `Analyze ${fresh} new ${fresh === 1 ? "job" : "jobs"} on this page`
              : "Show saved analyses"}
      </Button>
      {analyze.error && <p role="alert">{analyze.error.message}</p>}
      {analyze.data && (
        <p role="status">
          {analyze.data.analyzed} newly analyzed ·{" "}
          {analyze.data.items.length - analyze.data.analyzed} reused ·{" "}
          {analyze.data.failed} failed
        </p>
      )}
      <ol start={items[0]?.rank} className="space-y-2">
        {items.map(({ job, rank, role_match, matching_skills }) => (
          <li
            key={job.id}
            className="flex items-start gap-3 rounded-lg border bg-card p-4"
          >
            <Checkbox
              className="mt-1"
              aria-label={`Select ${job.title} for analysis`}
              checked={!excluded.includes(job.id)}
              disabled={analyze.isPending}
              onCheckedChange={(value) => {
                setExcluded((old) =>
                  value === true
                    ? old.filter((id) => id !== job.id)
                    : [...old, job.id]
                )
                analyze.reset()
              }}
            />
            <span className="text-muted-foreground tabular-nums">#{rank}</span>
            <div className="min-w-0 flex-1 space-y-1">
              <Dialog>
                <DialogTrigger className="text-left font-semibold hover:underline">
                  {job.title}
                </DialogTrigger>
                <JobDetailsDialog job={job} />
              </Dialog>
              {job.company && <p className="text-sm">{job.company}</p>}
              <p className="text-sm text-muted-foreground">
                {[
                  role_match && "Title matches your profile",
                  ...matching_skills,
                ]
                  .filter(Boolean)
                  .join(" · ") || "No matching title or skills"}
              </p>
              {job.match_reason && (
                <p className="text-sm">{job.match_reason}</p>
              )}
            </div>
            <ScoreBadge score={job.score} />
          </li>
        ))}
      </ol>
    </section>
  )
}

export function RecommendationsPanel() {
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState<MatchFilters>({})
  const results = useQuery({
    queryKey: ["job-rankings", filters, page],
    queryFn: () => getRankingPage(filters, page),
  })
  const data = results.data
  function filter(changes: MatchFilters) {
    setFilters({ ...filters, ...changes })
    setPage(1)
  }
  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-3xl font-semibold">Job rankings</h1>
        <p className="text-muted-foreground">
          Ranked by title match, then matching skills. Open a job title for
          details or analyze the selected jobs on this page.
        </p>
      </header>
      <div className="rounded-lg border p-4">
        <JobFilters
          keywords={filters.q ?? ""}
          source={filters.source}
          minScore={String(filters.min_score ?? "")}
          onKeywords={(q) => filter({ q })}
          onSource={(source) => filter({ source })}
          onMinScore={(score) =>
            filter({ min_score: score ? Number(score) : undefined })
          }
        />
      </div>
      {results.isPending && <p role="status">Ranking jobs…</p>}
      {results.error && <p role="alert">{results.error.message}</p>}
      {data && (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p>
              {data.total} jobs · Page {page} of{" "}
              {Math.max(1, Math.ceil(data.total / data.size))}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                disabled={page * data.size >= data.total}
                onClick={() => setPage(page + 1)}
              >
                Next
              </Button>
            </div>
          </div>
          {data.items.length ? (
            <RankedJobs
              key={JSON.stringify([filters, page])}
              items={data.items}
            />
          ) : (
            <p>No jobs match these filters.</p>
          )}
        </>
      )}
    </div>
  )
}
