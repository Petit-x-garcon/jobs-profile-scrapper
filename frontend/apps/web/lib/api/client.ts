import axios, { type AxiosError } from "axios"

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  timeout: 30_000,
})

/** Turns backend `{detail}` errors into a plain Error with that message. */
api.interceptors.response.use(
  undefined,
  (error: AxiosError<{ detail?: unknown }>) => {
    const detail = error.response?.data?.detail
    const message =
      typeof detail === "string"
        ? detail
        : error.response
          ? `Request failed (${error.response.status})`
          : "Cannot reach the server"
    return Promise.reject(new Error(message))
  }
)
