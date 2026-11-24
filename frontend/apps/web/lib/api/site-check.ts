import { z } from "zod"

import { api } from "@/lib/api/client"
import { siteCheckSchema } from "@/lib/api/schemas"

const CHECK_TIMEOUT_MS = 90_000

export async function checkSite(url: string) {
  const { data } = await api.post(
    "/api/site-check",
    { url },
    { timeout: CHECK_TIMEOUT_MS }
  )
  return siteCheckSchema.parse(data)
}

export async function addScrapeSite(url: string) {
  const { data } = await api.post(
    "/api/site-check/sources",
    { url },
    { timeout: CHECK_TIMEOUT_MS }
  )
  return z.object({ id: z.uuid(), url: z.url() }).parse(data)
}
