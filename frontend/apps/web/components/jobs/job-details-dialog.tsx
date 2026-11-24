import { ExternalLinkIcon } from "lucide-react"

import { Button } from "@workspace/ui/components/button"
import {
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@workspace/ui/components/dialog"
import { JobDescription } from "@/components/jobs/job-description"
import type { Job } from "@/lib/api/schemas"

export function JobDetailsDialog({ job }: { job: Job }) {
  const posted = job.posted_at
    ? new Date(job.posted_at).toLocaleDateString()
    : null
  const meta = [
    job.company,
    job.location,
    job.source,
    posted && `Posted ${posted}`,
  ]
    .filter(Boolean)
    .join(" · ")

  return (
    <DialogContent className="flex max-h-[90dvh] flex-col gap-0 p-0 sm:max-w-2xl">
      <DialogHeader className="border-b p-5 pr-12 [overflow-wrap:anywhere]">
        <DialogTitle className="text-xl leading-snug font-semibold">
          {job.title}
        </DialogTitle>
        <DialogDescription>{meta}</DialogDescription>
      </DialogHeader>
      <div
        tabIndex={0}
        aria-label="Job details"
        role="region"
        className="min-h-0 space-y-5 overflow-y-auto p-5 [overflow-wrap:anywhere] focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring"
      >
        {job.summary?.trim() && (
          <section className="rounded-lg bg-muted p-4">
            <h2 className="mb-1 font-semibold">Summary</h2>
            <p className="whitespace-pre-line text-muted-foreground">
              {job.summary}
            </p>
          </section>
        )}
        <JobDescription description={job.description} />
        {job.match_reason && (
          <section className="border-t pt-4">
            <h2 className="mb-1 font-semibold">Why this score</h2>
            <p className="whitespace-pre-line text-muted-foreground">
              {job.match_reason}
            </p>
          </section>
        )}
      </div>
      {/^https?:\/\//i.test(job.url) && (
        <DialogFooter className="m-0 px-5">
          <Button asChild>
            <a href={job.url} target="_blank" rel="noopener noreferrer">
              View original posting <ExternalLinkIcon />
            </a>
          </Button>
        </DialogFooter>
      )}
    </DialogContent>
  )
}
