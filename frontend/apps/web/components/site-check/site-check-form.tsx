"use client"

import { useState } from "react"
import { GlobeIcon } from "lucide-react"

import { Alert, AlertDescription } from "@workspace/ui/components/alert"
import { Button } from "@workspace/ui/components/button"
import { Input } from "@workspace/ui/components/input"
import { Label } from "@workspace/ui/components/label"
import { CrawlJobs } from "@/components/site-check/crawl-jobs"
import { SiteCheckResult } from "@/components/site-check/site-check-result"
import { useSiteCheck } from "@/hooks/use-site-check"

export function SiteCheckForm() {
  const check = useSiteCheck()
  const [jobsOnly, setJobsOnly] = useState(false)

  function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const url = String(new FormData(e.currentTarget).get("url") ?? "").trim()
    setJobsOnly(false)
    if (url) void check.start(url)
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold">Site check</h1>
        <p className="text-sm text-muted-foreground">
          Follow links on a public website to collect readable page content and
          count job postings.
        </p>
      </div>
      <form onSubmit={submit} className="flex flex-col gap-2">
        <Label htmlFor="site-url">Website URL</Label>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Input
            id="site-url"
            name="url"
            key={check.submittedAt}
            defaultValue={check.url}
            readOnly={check.isPending}
            type="url"
            required
            placeholder="https://example.com/jobs"
          />
          <Button type="submit" disabled={check.isPending || check.loading}>
            <GlobeIcon className={check.isPending ? "animate-pulse" : ""} />
            {check.queued
              ? "Queued"
              : check.isPending
                ? "Crawling…"
                : "Crawl website"}
          </Button>
        </div>
      </form>
      {check.isPending && (
        <Button variant="outline" onClick={check.stop}>
          Stop crawl
        </Button>
      )}
      {(check.isPending || check.stopped || check.pages.length > 0) && (
        <section className="space-y-3">
          <h2 className="font-semibold" role="status">
            {check.stopped
              ? "Crawl stopped"
              : check.isPending
                ? check.queued
                  ? "Waiting for the crawl worker"
                  : "Crawling website"
                : check.failed
                  ? "Crawl failed"
                  : "Crawl results"}
          </h2>
          <p>
            {check.checked} of {check.pageCount} discovered pages checked ·{" "}
            {check.jobCount} unique jobs found
          </p>
          {check.currentUrl && (
            <p className="text-sm break-all text-muted-foreground">
              Checking {check.currentUrl}
            </p>
          )}
          {check.pages[0] && !check.isPending && (
            <SiteCheckResult key={check.submittedAt} check={check.pages[0]} />
          )}
          {!check.isPending && check.pages.length === check.checked && (
            <Button
              variant="outline"
              aria-pressed={jobsOnly}
              onClick={() => setJobsOnly(!jobsOnly)}
            >
              {jobsOnly
                ? "Show crawled pages"
                : "Filter to jobs with descriptions"}
            </Button>
          )}
          {jobsOnly ? (
            <CrawlJobs pages={check.pages} />
          ) : (
            <ul className="space-y-2">
              {check.pages.map((page) => (
                <li key={page.url}>
                  <details className="rounded-md border p-3 text-sm">
                    <summary className="cursor-pointer break-all">
                      {page.url} ·{" "}
                      {page.job_count == null
                        ? page.result
                        : `${page.job_count} jobs`}
                    </summary>
                    <p className="mt-2">{page.message}</p>
                    {Object.entries(page.job_tabs ?? {}).map(
                      ([tab, titles]) => (
                        <div key={tab} className="mt-2">
                          <h3 className="font-medium">
                            {tab} ({titles.length})
                          </h3>
                          <ul className="list-inside list-disc">
                            {titles.map((title, index) => (
                              <li key={index}>{title}</li>
                            ))}
                          </ul>
                        </div>
                      )
                    )}
                    {page.content_text && (
                      <pre className="mt-2 max-h-80 overflow-auto whitespace-pre-wrap">
                        {page.content_text}
                      </pre>
                    )}
                  </details>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
      {check.error && (
        <Alert variant="destructive">
          <AlertDescription>{check.error.message}</AlertDescription>
        </Alert>
      )}
      <p className="text-xs text-muted-foreground">
        Technical access is not permission: even a successful test does not mean
        the site allows ongoing scraping. Check its terms of service.
      </p>
    </div>
  )
}
