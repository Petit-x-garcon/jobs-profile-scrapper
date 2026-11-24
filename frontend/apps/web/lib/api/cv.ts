import { api } from "@/lib/api/client"
import { cvSchema, cvUploadSchema } from "@/lib/api/schemas"

const UPLOAD_TIMEOUT_MS = 120_000

export async function getCv() {
  const { data } = await api.get("/api/cv")
  return cvSchema.nullable().parse(data)
}

export async function uploadCv(file: File) {
  const body = new FormData()
  body.append("file", file)
  const { data } = await api.post("/api/cv", body, {
    timeout: UPLOAD_TIMEOUT_MS,
  })
  return cvUploadSchema.parse(data)
}
