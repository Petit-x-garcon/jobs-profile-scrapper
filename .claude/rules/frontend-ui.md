---
paths:
  - "frontend/apps/web/components/**"
  - "frontend/apps/web/app/**"
  - "frontend/packages/ui/**"
---

# Frontend: UI and styling

- **shadcn/ui first.** Import from `@workspace/ui/components/<name>`. Missing one: `cd apps/web && npx shadcn@latest add <name>`. Only if shadcn has nothing, hand-write one in the same style (cva variants, `cn()`, `data-slot`).
- Don't hand-edit generated shadcn files beyond small fixes. Wrap them in an app component.
- Feature components in `apps/web/components/<feature>/`, reused ones in `components/shared/`.
- Icons from `lucide-react`.
- Tailwind utility classes only, merged with `cn()` from `@workspace/ui/lib/utils`. No inline `style`, no new CSS files.
- Colors from theme tokens (`bg-background`, `text-muted-foreground`, `bg-primary`), no hex values. Flat solid colors, no gradients. Both light and dark themes must work.
- Mobile-first: style small screens first, then `sm:` / `md:` / `lg:`.
- Interactive elements work by keyboard and have an accessible name. Icon-only buttons need an `aria-label`.
- Confirmations use `alert-dialog` or `dialog`, never `window.confirm`.
