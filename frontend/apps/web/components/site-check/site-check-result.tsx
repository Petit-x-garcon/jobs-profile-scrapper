import { useMutation } from "@tanstack/react-query"

import { Alert, AlertDescription } from "@workspace/ui/components/alert"
import { Button } from "@workspace/ui/components/button"
import { addScrapeSite } from "@/lib/api/site-check"
import { Badge } from "@workspace/ui/components/badge"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/card"
import type { SiteCheck } from "@/lib/api/schemas"

const RESULT: Record<
  SiteCheck["result"],
  {
    label: string
    variant: "default" | "destructive" | "secondary" | "outline"
  }
> = {
  successful: { label: "Successful", variant: "default" },
  failed: { label: "Failed", variant: "destructive" },
  restricted: { label: "Restricted", variant: "secondary" },
  inconclusive: { label: "Inconclusive", variant: "outline" },
}

const ROBOTS: Record<SiteCheck["robots_status"], string> = {
  allowed: "Allowed for this URL",
  disallowed: "Disallowed for this URL",
  not_found: "No robots.txt (no rules)",
  unavailable: "Could not be read",
}

function Row({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex flex-col gap-0.5 sm:flex-row sm:gap-3">
      <dt className="w-40 shrink-0 text-sm text-muted-foreground">{label}</dt>
      <dd className="min-w-0 text-sm break-all">{children}</dd>
    </div>
  )
}

export function SiteCheckResult({ check }: { check: SiteCheck }) {
  const result = RESULT[check.result]
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Result <Badge variant={result.variant}>{result.label}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <p className="text-sm">{check.message}</p>
        <dl className="flex flex-col gap-2">
          <Row label="Website URL">{check.url}</Row>
          {check.final_url && check.final_url !== check.url && (
            <Row label="Redirected to">{check.final_url}</Row>
          )}
          <Row label="HTTP status">{check.http_status ?? "No response"}</Row>
          <Row label="robots.txt">{ROBOTS[check.robots_status]}</Row>
        </dl>
        {check.result === "successful" && <AddScrapeSite url={check.url} />}
        {check.content_preview && (
          <div className="flex flex-col gap-1.5">
            <h3 className="text-sm font-medium">Content preview</h3>
            <pre className="max-h-80 overflow-auto rounded-md bg-muted p-3 text-xs whitespace-pre-wrap">
              {check.content_preview}
            </pre>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function AddScrapeSite({ url }: { url: string }) {
  const add = useMutation({ mutationFn: addScrapeSite })
  return (
    <div className="space-y-2">
      <Button
        type="button"
        disabled={add.isPending || add.isSuccess}
        onClick={() => add.mutate(url)}
      >
        {add.isSuccess
          ? "Added to scraper"
          : add.isPending
            ? "Adding…"
            : "Add to scraper"}
      </Button>
      <p className="text-sm text-muted-foreground" role="status">
        {add.isSuccess
          ? "This URL will be checked during future scrape runs."
          : "Future scrape runs will import a job if this URL contains structured job posting data."}
      </p>
      {add.error && (
        <Alert variant="destructive">
          <AlertDescription>{add.error.message}</AlertDescription>
        </Alert>
      )}
    </div>
  )
}
