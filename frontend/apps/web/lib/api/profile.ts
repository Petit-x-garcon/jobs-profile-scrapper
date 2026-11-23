import { api } from "@/lib/api/client"
import { profileSchema, type ProfileInput } from "@/lib/api/schemas"

export async function getProfile() {
  const { data } = await api.get("/api/profile")
  return profileSchema.parse(data)
}

export async function updateProfile(body: ProfileInput) {
  const { data } = await api.put("/api/profile", body)
  return profileSchema.parse(data)
}
