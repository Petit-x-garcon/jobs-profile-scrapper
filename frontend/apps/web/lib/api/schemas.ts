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
  matching_skills: z.array(z.string()).nullish(),
  missing_skills: z.array(z.string()).nullish(),
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
  experience: z.array(z.string()),
  education: z.array(z.string()),
  projects: z.array(z.string()),
  certifications: z.array(z.string()),
})

export const profileSchema = profileInputSchema.extend({
  id: z.string(),
  updated_at: z.string(),
})

export const recommendationsSchema = z.object({
  items: z.array(jobSchema),
  analyzed: z.number(),
  failed: z.number(),
})

export const cvSchema = z.object({
  id: z.string(),
  filename: z.string(),
  content_type: z.string(),
  size_bytes: z.number(),
  text: z.string(),
  uploaded_at: z.string(),
})

export const cvUploadSchema = z.object({
  cv: cvSchema,
  profile: profileSchema,
})

export const siteCheckSchema = z.object({
  url: z.string(),
  final_url: z.string().nullish(),
  http_status: z.number().nullish(),
  robots_status: z.enum(["allowed", "disallowed", "not_found", "unavailable"]),
  result: z.enum(["successful", "failed", "restricted", "inconclusive"]),
  message: z.string(),
  content_preview: z.string().nullish(),
})

export type Job = z.infer<typeof jobSchema>
export type JobPage = z.infer<typeof jobPageSchema>
export type Profile = z.infer<typeof profileSchema>
export type ProfileInput = z.infer<typeof profileInputSchema>
export type Recommendations = z.infer<typeof recommendationsSchema>
export type Cv = z.infer<typeof cvSchema>
export type SiteCheck = z.infer<typeof siteCheckSchema>
