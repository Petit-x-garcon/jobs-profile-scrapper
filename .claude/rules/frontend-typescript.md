---
paths:
  - "frontend/**/*.ts"
  - "frontend/**/*.tsx"
---

# Frontend: TypeScript and React

- Strict TypeScript; `npm run typecheck` must pass. No `any`: use `unknown` and narrow, or `z.infer` from a zod schema.
- API types come from the zod schemas, not hand-written duplicates.
- Import app code with `@/` and shared UI with `@workspace/ui/...`. No `../../../`.
- Server components by default. Add `"use client"` only for state, effects, browser APIs or event handlers, as low in the tree as possible.
- Never import server-only code (`next/headers`, route handlers) into client components.
- Hooks go in `hooks/` once two components share them; files are `use-<thing>.ts`.
- Files kebab-case, components PascalCase, functions and variables camelCase, constants UPPER_SNAKE_CASE.
- Component file: aim under ~300 lines, split past ~500. Component body: aim under ~50 lines, extract subcomponents or hooks.
- Run `npx prettier --write` on the files you changed only. Don't reformat unrelated files.
- Read `node_modules/next/dist/docs/` before using a Next.js API you are unsure of.
