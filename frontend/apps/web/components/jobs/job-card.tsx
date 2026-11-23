import { ChevronDownIcon, ExternalLinkIcon } from "lucide-react"

import { Badge } from "@workspace/ui/components/badge"
import { Button } from "@workspace/ui/components/button"
import { Card, CardContent } from "@workspace/ui/components/card"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@workspace/ui/components/collapsible"
import { ScoreBadge } from "@/components/jobs/score-badge"
import type { Job } from "@/lib/api/schemas"

function Toggle({ children }: { children: React.ReactNode }) {
  return (
    <CollapsibleTrigger asChild>
      <Button variant="ghost" size="sm" className="-ml-2 self-start">
        {children}
        <ChevronDownIcon />
      </Button>
    </CollapsibleTrigger>
  )
}

export function JobCard({ job }: { job: Job }) {
  const meta = [job.company, job.location].filter(Boolean).join(" · ")
  const posted = job.posted_at
    ? new Date(job.posted_at).toLocaleDateString()
    : null
  return (
    <Card>
      <CardContent className="flex flex-col gap-2">
        <div className="flex items-start justify-between gap-3">
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex min-w-0 items-center gap-1 font-medium hover:underline"
          >
            <span className="break-words">{job.title}</span>
            <ExternalLinkIcon className="size-3.5 shrink-0" />
          </a>
          <ScoreBadge score={job.score} />
        </div>
        <div className="text-muted-foreground flex flex-wrap items-center gap-x-2 gap-y-1 text-sm">
          {meta && <span>{meta}</span>}
          <Badge variant="outline">{job.source}</Badge>
          {posted && <span>{posted}</span>}
        </div>
        <p className="text-sm">
          {job.summary ?? (
            <span className="text-muted-foreground">Summary pending</span>
          )}
        </p>
        {job.match_reason && (
          <Collapsible className="flex flex-col">
            <Toggle>Why this score</Toggle>
            <CollapsibleContent className="text-muted-foreground text-sm">
              {job.match_reason}
            </CollapsibleContent>
          </Collapsible>
        )}
        <Collapsible className="flex flex-col">
          <Toggle>Show full description</Toggle>
          <CollapsibleContent className="text-muted-foreground text-sm whitespace-pre-wrap">
            {job.description}
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  )
}
