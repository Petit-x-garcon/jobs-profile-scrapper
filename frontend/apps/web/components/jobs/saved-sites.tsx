import Link from "next/link"
import { useQuery } from "@tanstack/react-query"
import { listScrapeSites, SOURCES_KEY } from "@/lib/api/site-check"

export function SavedSites() {
  const sites = useQuery({ queryKey: SOURCES_KEY, queryFn: listScrapeSites })
  return (
    <section className="space-y-2 rounded-xl border bg-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-medium">Saved scrape sites</h2>
        <Link className="text-sm underline" href="/site-check">
          Add a site
        </Link>
      </div>
      {sites.error && <p role="alert">{sites.error.message}</p>}
      {sites.isPending && <p className="text-sm">Loading sites…</p>}
      {sites.data?.length === 0 && (
        <p className="text-sm text-muted-foreground">
          Save a site to include it in future scrape runs.
        </p>
      )}
      {!!sites.data?.length && (
        <ul className="text-sm">
          {sites.data.map((url) => (
            <li key={url} className="break-all">
              {url}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
