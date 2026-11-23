"use client"

import { useState } from "react"
import { RefreshCwIcon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@workspace/ui/components/button"
import { Input } from "@workspace/ui/components/input"
import { useScrape } from "@/hooks/use-jobs"

export function ScrapeControl({ onStarted }: { onStarted: () => void }) {
  const [query, setQuery] = useState("IT")
  const scrape = useScrape()

  function run() {
    scrape.mutate(query.trim() || "IT", {
      onSuccess: () => {
        toast.success("Scraping started — refresh in a minute")
        onStarted()
      },
      onError: (e) => toast.error(e.message),
    })
  }

  return (
    <div className="flex gap-2">
      <Input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        aria-label="Scrape query"
        className="w-28 sm:w-40"
      />
      <Button onClick={run} disabled={scrape.isPending}>
        <RefreshCwIcon className={scrape.isPending ? "animate-spin" : ""} />
        Scrape now
      </Button>
    </div>
  )
}
