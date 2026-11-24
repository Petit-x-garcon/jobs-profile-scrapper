import { api } from "@/lib/api/client"
import {
  jobPageSchema,
  jobSchema,
  scrapeResponseSchema,
} from "@/lib/api/schemas"

export type JobFilters = {
  page: number
  size: number
  source?: string
  min_score?: number
  q?: string
}

export type ImportJobInput = {
  url: string | null
  title: string | null
  text: string
}

export async function listJobs(params: JobFilters) {
  const { data } = await api.get("/api/jobs", { params })
  return jobPageSchema.parse(data)
}

export async function importJob(body: ImportJobInput) {
  const { data } = await api.post("/api/jobs/import", body)
  return jobSchema.parse(data)
}

export async function startScrape(query: string) {
  const { data } = await api.post("/api/scrape", { query })
  return scrapeResponseSchema.parse(data)
}
