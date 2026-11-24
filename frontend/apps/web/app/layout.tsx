import type { Metadata } from "next"
import { Geist_Mono, Poppins } from "next/font/google"

import "@workspace/ui/globals.css"
import { SiteNav } from "@/components/shared/site-nav"
import { ThemeProvider } from "@/components/theme-provider"
import { QueryProvider } from "@/providers/query-provider"

// Poppins has no variable version, so each weight is listed.
const fontSans = Poppins({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-sans",
})

const fontMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
})

export const metadata: Metadata = { title: "Job Scraper" }

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${fontSans.variable} ${fontMono.variable} font-sans antialiased`}
    >
      <body>
        <ThemeProvider>
          <QueryProvider>
            <SiteNav />
            <main className="mx-auto max-w-7xl px-4 py-6 sm:px-8 sm:py-10">
              {children}
            </main>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
