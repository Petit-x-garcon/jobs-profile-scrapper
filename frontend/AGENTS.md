<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# Frontend (Next.js): agent instructions

Web app for Job Scraper: Next.js 16 (App Router) + React 19, in an npm + Turborepo workspace. This file is the main source of instructions: `CLAUDE.md` imports it. Leave the managed block above as it is; `next dev` rewrites it.

| Workspace | What it is |
|---|---|
| `apps/web` | The app (package name `web`) |
| `packages/ui` | shadcn/ui components, Tailwind styles, `cn()` (`@workspace/ui`) |
| `packages/eslint-config`, `packages/typescript-config` | Shared lint and TypeScript config |

## Topic rules

They live in `.claude/rules/` (the only copy), which Claude Code loads automatically. Read the matching file before changing that area:

| File | Applies to | Covers |
|---|---|---|
| `api-contract.md` | everything | URLs, error shape, pagination shared with the backend |
| `frontend-data.md` | `apps/web/lib`, `hooks`, `components`, `app` | API client, zod schemas, TanStack Query, zustand |
| `frontend-ui.md` | `apps/web/components`, `app`, `packages/ui` | shadcn/ui, Tailwind, colors, responsive layout, icons |
| `frontend-typescript.md` | any `.ts` / `.tsx` file | Types, naming, client vs server components, size limits |


## Commands

Run from `frontend/`. The backend must be running (default `http://localhost:8000`) for pages to load data.

```bash
npm install
npm run dev -w web                  # http://localhost:3000 (web app only, no turbo)
npm run build                       # production build
npm run lint                        # ESLint, all workspaces
npm run typecheck                   # tsc --noEmit, all workspaces
npm run format                      # Prettier --write, all workspaces

npm run lint -w web                 # one workspace only (also: typecheck, format)
npx prettier --write <files>        # format only the files you changed
npx prettier --check "apps/web/**/*.{ts,tsx}"

cd apps/web && npx shadcn@latest add <component>   # add a shadcn/ui component into packages/ui
```

There are no automated frontend tests yet. Check UI changes in the browser at mobile and desktop widths, in light and dark themes.

## Definition of done

1. `npm run lint` and `npm run typecheck` pass.
2. The files you changed are formatted (`npx prettier --write <files>`). Don't reformat unrelated files in a feature change.
3. A backend response shape you rely on matches the zod schema in `lib/api/schemas.ts` (see `api-contract.md`).
4. The page works at small, medium and large widths, and in light and dark themes.

## Environment

`apps/web/.env` (never edit, print or commit it):
- `NEXT_PUBLIC_API_URL`: backend base URL the axios client calls. Default `http://localhost:8000`.

## Layout (`apps/web`)

| Path | Holds |
|---|---|
| `app/` | Routes |
| `components/<feature>/` | Feature UI, one folder per feature (mirrors the backend modules), plus `shared/` and `layout/` |
| `lib/api/<resource>.ts` | One module per backend resource with its request functions; zod schemas in `schemas.ts`; `client.ts` is the axios client |
| `hooks/` | Shared hooks |
| `providers/` | App-wide providers (React Query) |

Folders are created when the first feature needs them; not all exist yet.

## Stack and conventions

- **UI:** shadcn/ui components from `packages/ui`. If none fits, hand-write one in the same style.
- **API calls:** axios through `lib/api/client.ts`, never `fetch` or axios directly in components.
- **Validation:** zod for API responses, forms and environment values.
- **Server state:** TanStack Query. Never fetch in `useEffect`.
- **Client state:** zustand for state shared across the tree; `useState` or context for local state.
- **Layout:** responsive and mobile-first, for small, medium and large screens.
- **Fonts:** Poppins (400–700) and Geist Mono via `next/font/google`.
- **Colors:** flat, solid colors only. No gradients and no pastel palettes.
