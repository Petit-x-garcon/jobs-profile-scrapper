---
paths:
  - "**/*.ts"
  - "**/*.tsx"
---

# TypeScript and React style

## Types
- Strict TypeScript; `npm run typecheck` must pass. No `any`. Use `unknown` and narrow it, or derive the type from a zod schema with `z.infer`.
- API types come from the zod schemas in `lib/api/`, not from hand-written interfaces that duplicate them.
- Import app code through the `@/` alias (`@/lib/api/documents`) and shared UI through `@workspace/ui/...`. No long relative paths like `../../../`.

## React and Next.js
- Components are server components by default. Add `"use client"` only to files that need state, effects, browser APIs or event handlers, and keep it as low in the tree as you can.
- Never import server-only code (route handlers, `next/headers`) into client components.
- Hooks go in `hooks/` once two components share them. Their names start with `use`, and their files are named `use-<thing>.ts`.
- Group UI by feature (`components/<feature>/`), mirroring the backend modules where it makes sense. Shared pieces go in `components/shared/`.

## Naming and formatting
- Files: kebab-case (`users-page.tsx`, `auth-store.ts`). Components: PascalCase. Functions and variables: camelCase. Constants: UPPER_SNAKE_CASE.
- Prettier formats everything (`.prettierrc`). Don't format by hand. Run `npx prettier --write` on the files you changed.

## Size (guidelines, not hard limits)
- Component file: aim for under ~300 lines; split past ~500 by extracting subcomponents, hooks or helpers into the same feature folder.
- Function or component body: aim for under ~50 lines; extract sections into named subcomponents.
- `packages/ui/src/components/*` is generated shadcn code; leave its size alone.
