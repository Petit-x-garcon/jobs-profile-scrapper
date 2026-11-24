"use client"

import { SparklesIcon } from "lucide-react"

import { Alert, AlertDescription } from "@workspace/ui/components/alert"
import { Button } from "@workspace/ui/components/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/card"
import { Skeleton } from "@workspace/ui/components/skeleton"
import { RecommendationItem } from "@/components/recommendations/recommendation-item"
import { useAnalyzeJobs } from "@/hooks/use-recommendations"
import type { Recommendations } from "@/lib/api/schemas"

function Results({ data }: { data: Recommendations }) {
  const notes = [
    `${data.items.length} ranked`,
    `${data.analyzed} newly analyzed`,
    data.failed > 0 && `${data.failed} failed`,
  ].filter(Boolean)
  return (
    <div className="flex flex-col gap-3">
      <p className="text-muted-foreground text-sm">{notes.join(" · ")}</p>
      {data.items.length === 0 ? (
        <p className="text-muted-foreground text-sm">
          No job could be analyzed. Try again in a moment.
        </p>
      ) : (
        <ol className="flex flex-col gap-3">
          {data.items.map((job, i) => (
            <RecommendationItem key={job.id} job={job} rank={i + 1} />
          ))}
        </ol>
      )}
    </div>
  )
}

/** Mount with a `key` tied to the filters so results reset when they change. */
export function RecommendationsPanel({ jobIds }: { jobIds: string[] }) {
  const analyze = useAnalyzeJobs()
  const busy = analyze.isPending
  return (
    <Card>
      <CardHeader>
        <CardTitle>AI recommendations</CardTitle>
        <CardDescription>
          Match the {jobIds.length} jobs shown against your latest CV and
          profile. Jobs analyzed before are reused, not re-sent.
        </CardDescription>
        <CardAction>
          <Button
            onClick={() => analyze.mutate(jobIds)}
            disabled={busy || jobIds.length === 0}
          >
            <SparklesIcon className={busy ? "animate-pulse" : ""} />
            {busy ? "Analyzing…" : "Analyze with AI"}
          </Button>
        </CardAction>
      </CardHeader>
      {(busy || analyze.error || analyze.data) && (
        <CardContent aria-live="polite">
          {busy && (
            <div className="flex flex-col gap-3">
              <p className="text-muted-foreground text-sm">
                Analyzing jobs. This can take up to a minute.
              </p>
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
            </div>
          )}
          {analyze.error && (
            <Alert variant="destructive">
              <AlertDescription>{analyze.error.message}</AlertDescription>
            </Alert>
          )}
          {analyze.data && !busy && <Results data={analyze.data} />}
        </CardContent>
      )}
    </Card>
  )
}
