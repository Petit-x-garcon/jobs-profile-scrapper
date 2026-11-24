"use client"

import { GlobeIcon } from "lucide-react"

import { Alert, AlertDescription } from "@workspace/ui/components/alert"
import { Button } from "@workspace/ui/components/button"
import { Input } from "@workspace/ui/components/input"
import { Label } from "@workspace/ui/components/label"
import { Skeleton } from "@workspace/ui/components/skeleton"
import { SiteCheckResult } from "@/components/site-check/site-check-result"
import { useSiteCheck } from "@/hooks/use-site-check"

export function SiteCheckForm() {
  const check = useSiteCheck()

  function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const url = String(new FormData(e.currentTarget).get("url") ?? "").trim()
    if (url) check.mutate(url)
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold">Site check</h1>
        <p className="text-sm text-muted-foreground">
          Test whether a public page can be reached, what its robots.txt allows,
          and whether readable content can be extracted. Logins, CAPTCHAs and
          bot protection are never bypassed.
        </p>
      </div>
      <form onSubmit={submit} className="flex flex-col gap-2">
        <Label htmlFor="site-url">Website URL</Label>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Input
            id="site-url"
            name="url"
            type="url"
            required
            placeholder="https://example.com/jobs"
          />
          <Button type="submit" disabled={check.isPending}>
            <GlobeIcon className={check.isPending ? "animate-pulse" : ""} />
            {check.isPending ? "Testing…" : "Test Scraping"}
          </Button>
        </div>
      </form>
      {check.isPending && <Skeleton className="h-48 w-full" />}
      {check.error && (
        <Alert variant="destructive">
          <AlertDescription>{check.error.message}</AlertDescription>
        </Alert>
      )}
      {check.data && !check.isPending && (
        <SiteCheckResult key={check.submittedAt} check={check.data} />
      )}
      <p className="text-xs text-muted-foreground">
        Technical access is not permission: even a successful test does not mean
        the site allows ongoing scraping. Check its terms of service.
      </p>
    </div>
  )
}
