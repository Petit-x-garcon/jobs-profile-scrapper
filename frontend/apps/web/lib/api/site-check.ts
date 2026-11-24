import { z } from "zod"

import { api } from "@/lib/api/client"
import { type CrawlJob, siteCheckSchema } from "@/lib/api/schemas"

const CHECK_TIMEOUT_MS = 90_000

const statusSchema = z.object({
  id: z.uuid(),
  url: z.string(),
  status: z.enum(["queued", "running", "completed", "stopped", "failed"]),
  current_url: z.string().nullable(),
  checked: z.number().int(),
  discovered: z.number().int(),
  job_count: z.number().int(),
  error: z.string().nullable(),
})

export async function latestCrawl() {
  const { data } = await api.get("/api/site-check/runs/latest")
  return statusSchema.nullable().parse(data)
}

export async function startCrawl(url: string) {
  const { data } = await api.post("/api/site-check/runs", { url })
  return statusSchema.parse(data)
}

export async function stopCrawl(id: string) {
  const { data } = await api.post(`/api/site-check/runs/${id}/stop`)
  return statusSchema.parse(data)
}

export async function crawlPages(id: string, offset: number) {
  const { data } = await api.get(`/api/site-check/runs/${id}/pages`, {
    params: { offset },
  })
  return z.array(siteCheckSchema).parse(data)
}

export async function addScrapeSite(url: string) {
  const { data } = await api.post(
    "/api/site-check/sources",
    { url },
    { timeout: CHECK_TIMEOUT_MS }
  )
  return z.object({ id: z.uuid(), url: z.url() }).parse(data)
}

export const SOURCES_KEY = ["scrape-sources"] as const

export async function listScrapeSites() {
  const { data } = await api.get("/api/site-check/sources")
  return z.array(z.url()).parse(data)
}

export async function saveCrawlJobs(jobs: CrawlJob[]) {
  let added = 0
  let skipped = 0
  for (let start = 0; start < jobs.length; start += 100) {
    const { data } = await api.post("/api/site-check/import", {
      jobs: jobs.slice(start, start + 100),
    })
    const batch = z
      .object({ added: z.number().int(), skipped: z.number().int() })
      .parse(data)
    added += batch.added
    skipped += batch.skipped
  }
  return { added, skipped }
}
