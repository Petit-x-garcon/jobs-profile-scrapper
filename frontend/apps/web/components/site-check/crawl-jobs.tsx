import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Button } from "@workspace/ui/components/button"
import { JOBS_KEY } from "@/hooks/use-jobs"
import type { SiteCheck } from "@/lib/api/schemas"
import { saveCrawlJobs } from "@/lib/api/site-check"

export function CrawlJobs({ pages }: { pages: SiteCheck[] }) {
  const cache = useQueryClient()
  const save = useMutation({
    mutationFn: saveCrawlJobs,
    onSettled: () => cache.invalidateQueries({ queryKey: JOBS_KEY }),
  })
  const jobs = [
    ...new Map(
      pages.flatMap((page) =>
        (page.jobs ?? []).map((job) => [job.url, job] as const)
      )
    ).values(),
  ]
  return (
    <div className="space-y-3">
      <p>{jobs.length} jobs with a title and description are ready to save.</p>
      <Button
        disabled={!jobs.length || save.isPending}
        onClick={() => save.mutate(jobs)}
      >
        {save.isPending ? "Saving jobs…" : "Save jobs to database"}
      </Button>
      {save.data && (
        <p role="status">
          {save.data.added} added · {save.data.skipped} already saved
        </p>
      )}
      {save.error && (
        <p role="alert">{save.error.message} You can retry safely.</p>
      )}
      <ul className="space-y-2">
        {jobs.map((job) => (
          <li key={job.url}>
            <details className="rounded-md border p-3">
              <summary className="cursor-pointer font-medium">
                {job.title}
              </summary>
              <p className="mt-2 text-sm whitespace-pre-wrap">
                {job.description}
              </p>
            </details>
          </li>
        ))}
      </ul>
    </div>
  )
}
