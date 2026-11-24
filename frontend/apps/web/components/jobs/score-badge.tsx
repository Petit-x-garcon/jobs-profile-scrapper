import { cn } from "cn"

import { Badge } from "@workspace/ui/components/badge"

function bandClass(score: number) {
  if (score >= 75) return "bg-primary text-primary-foreground"
  if (score >= 50) return "bg-secondary text-secondary-foreground"
  return "bg-muted text-muted-foreground"
}

export function ScoreBadge({ score }: { score: number | null | undefined }) {
  if (score == null) return <Badge variant="outline">Not analyzed</Badge>
  return (
    <Badge className={cn(bandClass(score))}>{Math.round(score)} / 100</Badge>
  )
}
