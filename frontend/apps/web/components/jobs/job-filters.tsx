"use client"

import { SearchIcon } from "lucide-react"

import { Button } from "@workspace/ui/components/button"
import { Input } from "@workspace/ui/components/input"
import { Label } from "@workspace/ui/components/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@workspace/ui/components/select"

const ALL = "all"
const SOURCES = ["dodojob", "jobify", "manual", "website"]

type Props = {
  keywords: string
  onKeywords: (v: string) => void
  source: string | undefined
  minScore: string
  onSource: (v: string | undefined) => void
  onMinScore: (v: string) => void
}

function KeywordSearch({
  keywords,
  onKeywords,
}: Pick<Props, "keywords" | "onKeywords">) {
  function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    onKeywords(String(new FormData(e.currentTarget).get("q") ?? "").trim())
  }
  return (
    <form onSubmit={submit} className="flex w-full flex-col gap-1.5 sm:w-auto">
      <Label htmlFor="keywords">Keywords</Label>
      <div className="flex gap-2">
        <Input
          id="keywords"
          name="q"
          type="search"
          defaultValue={keywords}
          placeholder="e.g. AI Engineer, Remote"
          className="w-full sm:w-64"
        />
        <Button type="submit" variant="outline" size="icon" aria-label="Search">
          <SearchIcon />
        </Button>
      </div>
    </form>
  )
}

export function JobFilters({
  keywords,
  onKeywords,
  source,
  minScore,
  onSource,
  onMinScore,
}: Props) {
  return (
    <div className="flex flex-wrap items-end gap-3">
      <KeywordSearch keywords={keywords} onKeywords={onKeywords} />
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="job-source">Source</Label>
        <Select
          value={source ?? ALL}
          onValueChange={(v) => onSource(v === ALL ? undefined : v)}
        >
          <SelectTrigger id="job-source" className="w-36">
            <SelectValue />
          </SelectTrigger>
          <SelectContent position="popper" align="start">
            <SelectItem value={ALL}>All sources</SelectItem>
            {SOURCES.map((s) => (
              <SelectItem key={s} value={s}>
                {s === "dodojob"
                  ? "DodoJob"
                  : s === "jobify"
                    ? "Jobify"
                    : s === "website"
                      ? "Website"
                      : "Manual"}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="min-score">Min score</Label>
        <Input
          id="min-score"
          type="number"
          min={0}
          max={100}
          value={minScore}
          onChange={(e) => onMinScore(e.target.value)}
          className="w-24"
        />
      </div>
    </div>
  )
}
