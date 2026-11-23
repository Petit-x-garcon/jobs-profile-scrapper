---
paths:
  - "apps/web/lib/**"
  - "apps/web/hooks/**"
  - "apps/web/components/**"
  - "apps/web/app/**"
---

# Data fetching and state

## API modules (`apps/web/lib/api/`)
- One module per backend resource (`users.ts`, `documents.ts`, …). Each exports zod schemas for its responses, `z.infer` types, and plain `async` request functions.
- Every request goes through `request()` / `authedFetch()` in `lib/api/client.ts`. That client adds the bearer token, refreshes it on expiry, and turns errors into `ApiError`. Never call `fetch` or `axios` directly from components or hooks.
- `.parse()` every response with its schema (`pageSchema.parse(await request(...))`). Use `paginated(itemSchema)` from `lib/schemas.ts` for paginated lists.
- Use `.nullish()` for fields the backend may omit or send as `null`; don't loosen a schema to `z.any()`.
- Build query strings with `URLSearchParams`, and keep the backend's trailing slashes.

## Server state (TanStack Query)
- Read data with `useQuery`, and write with `useMutation` followed by `queryClient.invalidateQueries`. Never fetch in `useEffect`.
- Query keys are arrays that start with the resource name: `["users"]`, `["document-preview", id]`. Keys shared across components live in one exported constant (for example `USERS_KEY`) and are extended with parameters: `[...USERS_KEY, page, search]`.
- Every parameter that changes the result goes in the key.

## Client state (zustand)
- Use zustand only for state shared across distant parts of the tree (for example auth). Use `useState` or context for anything local.
- Never copy server data into a store. TanStack Query is the cache.

## Errors and feedback
- The client turns every failure into an `ApiError` whose `message` is the backend's `detail` (via `errorMessage()`). Show it with `toast.error(error.message)` from `sonner`, and confirmations with `toast.success(t("…"))`.
- `ApiError.status` lets you tell 401/403/404 apart. The client refreshes an expired session, and logs out when the refresh is rejected.

## Streaming
- SSE streams are consumed in `lib/api/<resource>.ts` and wrapped in a hook. Handle every frame type listed in `api-contract.md`, including `error`.
