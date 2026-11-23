"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "cn"

import { ThemeToggle } from "@/components/shared/theme-toggle"

const LINKS = [
  { href: "/", label: "Jobs" },
  { href: "/profile", label: "Profile" },
]

export function SiteNav() {
  const pathname = usePathname()
  return (
    <header className="border-b">
      <nav className="mx-auto flex h-14 max-w-4xl items-center gap-1 px-4">
        <span className="mr-3 font-semibold">Job Scraper</span>
        {LINKS.map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "rounded-md px-3 py-1.5 text-sm",
              pathname === href
                ? "bg-muted font-medium"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            {label}
          </Link>
        ))}
        <div className="ml-auto">
          <ThemeToggle />
        </div>
      </nav>
    </header>
  )
}
