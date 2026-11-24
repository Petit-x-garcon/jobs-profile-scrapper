"use client"

import { BriefcaseBusinessIcon } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "cn"

import { useCrawlStatus } from "@/hooks/use-site-check"
import { ThemeToggle } from "@/components/shared/theme-toggle"

const LINKS = [
  { href: "/", label: "Jobs" },
  { href: "/rankings", label: "Job rankings" },
  { href: "/profile", label: "Profile" },
  { href: "/site-check", label: "Site check" },
]

export function SiteNav() {
  const pathname = usePathname()
  const { data: run } = useCrawlStatus()
  const progress =
    run && ["queued", "running"].includes(run.status)
      ? `${run.checked}/${run.discovered}`
      : null
  return (
    <header className="border-b bg-card">
      <nav className="mx-auto flex min-h-16 max-w-7xl flex-wrap items-center gap-1 px-4 sm:px-8">
        <Link
          href="/"
          aria-label="Job Scraper home"
          className="mr-1 flex items-center gap-2 rounded-lg font-semibold text-primary sm:mr-5"
        >
          <BriefcaseBusinessIcon className="size-5" aria-hidden />
          <span className="hidden sm:inline">Job Scraper</span>
        </Link>
        {LINKS.map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            aria-current={pathname === href ? "page" : undefined}
            className={cn(
              "rounded-md px-3 py-1.5 text-sm",
              pathname === href
                ? "bg-accent font-medium text-accent-foreground"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            {label}
            {href === "/site-check" && progress && (
              <span
                className="ml-1 text-xs tabular-nums"
                aria-label={`${progress} pages checked`}
              >
                {progress}
              </span>
            )}
          </Link>
        ))}
        <div className="ml-auto">
          <ThemeToggle />
        </div>
      </nav>
    </header>
  )
}
