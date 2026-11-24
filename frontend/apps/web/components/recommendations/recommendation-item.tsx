import { ExternalLinkIcon } from "lucide-react"

import { Badge } from "@workspace/ui/components/badge"
import { ScoreBadge } from "@/components/jobs/score-badge"
import type { Job } from "@/lib/api/schemas"

function SkillList({
  label,
  skills,
  variant,
}: {
  label: string
  skills: string[] | null | undefined
  variant: "secondary" | "outline"
}) {
  if (!skills?.length) return null
  return (
    <div className="flex flex-wrap items-center gap-1.5 text-sm">
      <span className="text-muted-foreground mr-1">{label}:</span>
      {skills.map((s) => (
        <Badge key={s} variant={variant}>
          {s}
        </Badge>
      ))}
    </div>
  )
}

export function RecommendationItem({ job, rank }: { job: Job; rank: number }) {
  const meta = [job.company, job.location].filter(Boolean).join(" · ")
  return (
    <li className="flex flex-col gap-2 rounded-lg border p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 flex-col gap-0.5">
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 font-medium hover:underline"
          >
            <span className="text-muted-foreground">#{rank}</span>
            <span className="break-words">{job.title}</span>
            <ExternalLinkIcon className="size-3.5 shrink-0" />
          </a>
          {meta && (
            <span className="text-muted-foreground text-sm">{meta}</span>
          )}
        </div>
        <ScoreBadge score={job.score} />
      </div>
      {job.match_reason && <p className="text-sm">{job.match_reason}</p>}
      <SkillList
        label="Matching"
        skills={job.matching_skills}
        variant="secondary"
      />
      <SkillList
        label="Missing"
        skills={job.missing_skills}
        variant="outline"
      />
    </li>
  )
}
