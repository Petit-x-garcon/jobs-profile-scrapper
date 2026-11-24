import { ArrowUpRightIcon, BriefcaseBusinessIcon } from "lucide-react"

import { Badge } from "@workspace/ui/components/badge"
import { Button } from "@workspace/ui/components/button"
import { Card, CardContent } from "@workspace/ui/components/card"
import { Dialog, DialogTrigger } from "@workspace/ui/components/dialog"
import { JobDetailsDialog } from "@/components/jobs/job-details-dialog"
import { ScoreBadge } from "@/components/jobs/score-badge"
import type { Job } from "@/lib/api/schemas"

export function JobCard({ job }: { job: Job }) {
  const meta = [job.company, job.location].filter(Boolean).join(" · ")
  const description = (job.summary?.trim() || job.description.trim()).replace(
    /\s+/g,
    " "
  )
  const preview =
    description.length > 240
      ? description
          .slice(0, 241)
          .replace(/\s+\S*$/, "")
          .slice(0, 240) + "…"
      : description
  return (
    <Dialog>
      <Card className="relative h-full transition-colors focus-within:ring-primary hover:ring-primary/50">
        <CardContent className="flex flex-1 flex-col gap-3 [overflow-wrap:anywhere]">
          <div className="flex items-start justify-between gap-3">
            <div className="rounded-lg bg-accent p-2 text-accent-foreground">
              <BriefcaseBusinessIcon className="size-4" aria-hidden />
            </div>
            <ScoreBadge score={job.score} />
          </div>
          <div>
            <h3 className="text-base leading-snug font-semibold">
              <DialogTrigger className="cursor-pointer rounded text-left after:absolute after:inset-0 focus-visible:outline-2 focus-visible:outline-ring">
                {job.title}
              </DialogTrigger>
            </h3>
            {meta && (
              <p className="mt-1 text-sm text-muted-foreground">{meta}</p>
            )}
          </div>
          <p className="line-clamp-3 text-sm leading-relaxed text-muted-foreground">
            {preview || "No description available."}
          </p>
          <div className="mt-auto flex flex-wrap items-center justify-between gap-2 border-t border-border pt-3">
            <Badge variant="secondary" className="capitalize">
              {job.source}
            </Badge>
            {/^https?:\/\//i.test(job.url) && (
              <Button
                asChild
                variant="ghost"
                size="sm"
                className="relative z-10 text-primary"
              >
                <a
                  href={job.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={`View details for ${job.title}`}
                >
                  View details <ArrowUpRightIcon />
                </a>
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
      <JobDetailsDialog job={job} />
    </Dialog>
  )
}
