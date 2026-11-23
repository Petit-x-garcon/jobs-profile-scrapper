---
paths:
  - "frontend/apps/web/lib/**"
  - "frontend/apps/web/hooks/**"
  - "frontend/apps/web/components/**"
  - "frontend/apps/web/app/**"
---

# Frontend: data fetching and state

## API modules (`apps/web/lib/api/`)
- One module per backend resource. Each exports zod schemas, `z.infer` types and plain `async` request functions.
- Every request goes through the shared axios client in `lib/api/client.ts` (auth header, error handling). Never call `fetch` or axios from components or hooks.
- `.parse()` every response with its zod schema. Use `.nullish()` for fields the backend may omit; never `z.any()`.
- Build query strings with `URLSearchParams` and keep the backend's trailing slashes.

## Server state (TanStack Query)
- Read with `useQuery`. Write with `useMutation`, then `invalidateQueries`. Never fetch in `useEffect`.
- Query keys are arrays starting with the resource name (`["users", page, search]`). Every parameter that changes the result goes in the key. Shared keys live in one exported constant.

## Client state (zustand)
- Only for state shared across distant parts of the tree (for example auth). Use `useState` or context for local state.
- Never copy server data into a store; TanStack Query is the cache.

## Errors
- Show the backend `detail` message to the user. Distinguish 401/403/404 by status code.
