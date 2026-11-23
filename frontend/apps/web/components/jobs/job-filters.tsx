"use client"

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
const SOURCES = ["dodojob", "jobify", "manual"]

type Props = {
  source: string | undefined
  minScore: string
  onSource: (v: string | undefined) => void
  onMinScore: (v: string) => void
}

export function JobFilters({ source, minScore, onSource, onMinScore }: Props) {
  return (
    <div className="flex flex-wrap items-end gap-3">
      <div className="flex flex-col gap-1.5">
        <Label>Source</Label>
        <Select
          value={source ?? ALL}
          onValueChange={(v) => onSource(v === ALL ? undefined : v)}
        >
          <SelectTrigger className="w-36">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>All sources</SelectItem>
            {SOURCES.map((s) => (
              <SelectItem key={s} value={s}>
                {s}
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
