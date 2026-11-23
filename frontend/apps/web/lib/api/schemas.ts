import { z } from "zod"

export const jobSchema = z.object({
  id: z.string(),
  source: z.string(),
  url: z.string(),
  title: z.string(),
  company: z.string().nullish(),
  location: z.string().nullish(),
  description: z.string(),
  posted_at: z.string().nullish(),
  summary: z.string().nullish(),
  score: z.number().nullish(),
  match_reason: z.string().nullish(),
  scraped_at: z.string(),
})

export const jobPageSchema = z.object({
  items: z.array(jobSchema),
  total: z.number(),
  page: z.number(),
  size: z.number(),
})

export const scrapeResponseSchema = z.object({ task_id: z.string() })

export const profileInputSchema = z.object({
  headline: z.string(),
  skills: z.array(z.string()),
  years_experience: z.number(),
  locations: z.array(z.string()),
  remote_ok: z.boolean(),
  min_salary: z.number().nullable(),
  summary: z.string(),
})

export const profileSchema = profileInputSchema.extend({
  id: z.string(),
  updated_at: z.string(),
})

export type Job = z.infer<typeof jobSchema>
export type JobPage = z.infer<typeof jobPageSchema>
export type Profile = z.infer<typeof profileSchema>
export type ProfileInput = z.infer<typeof profileInputSchema>
