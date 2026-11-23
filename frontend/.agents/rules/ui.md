---
paths:
  - "apps/web/components/**"
  - "apps/web/app/**"
  - "packages/ui/**"
---

# UI components and styling

## Components
- Reuse shadcn/ui components from `packages/ui/src/components`, imported as `@workspace/ui/components/<name>` (`button`, `dialog`, `input`, `dropdown-menu`, …).
- Add a missing shadcn component with `cd apps/web && npx shadcn@latest add <name>`; it lands in `packages/ui`. If shadcn has nothing that fits, hand-write the component in the same style (cva variants, `cn()`, `data-slot` attributes).
- Don't hand-edit generated shadcn files in `packages/ui` beyond small fixes. Wrap them in an app component instead.
- Feature components live in `apps/web/components/<feature>/`. Anything reused across features goes in `components/shared/`.
- Icons come from `lucide-react`.

## Styling
- Tailwind CSS 4 utility classes only, merged with `cn()` from `@workspace/ui/lib/utils`. No inline `style` for colors or spacing, and no new CSS files.
- Colors come from the theme tokens in `packages/ui/src/styles/globals.css` (`bg-background`, `text-muted-foreground`, `bg-primary`, …), so light and dark themes (`next-themes`) both work. No hard-coded hex values.
- Flat, solid colors only: no gradients, no pastel palettes.

## Layout and accessibility
- Mobile-first: style the small screen first, then add `sm:` / `md:` / `lg:` overrides. Check every page at phone, tablet and desktop widths.
- Every interactive element is reachable by keyboard and has an accessible name. Icon-only buttons need a translated `aria-label`.
- Use dialogs from `@workspace/ui/components/dialog` / `alert-dialog` for confirmations, never `window.confirm`.
