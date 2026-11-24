import { useRef, useState } from "react"

import { Button } from "@workspace/ui/components/button"
import { Input } from "@workspace/ui/components/input"
import { Label } from "@workspace/ui/components/label"

export function CvEntryFields<Key extends string>({
  title,
  fields,
  value,
  onChange,
}: {
  title: string
  fields: Record<Key, string>
  value: (string | Record<Key, string>)[]
  onChange: (value: (string | Record<Key, string>)[]) => void
}) {
  const keys = Object.keys(fields) as Key[]
  const [ids, setIds] = useState(() => value.map((_, index) => index))
  const nextId = useRef(value.length)

  function add() {
    const entry = Object.fromEntries(keys.map((key) => [key, ""])) as Record<
      Key,
      string
    >
    setIds([...ids, nextId.current++])
    onChange([...value, entry])
  }

  function remove(index: number) {
    setIds(ids.filter((_, position) => position !== index))
    onChange(value.filter((_, position) => position !== index))
  }

  function change(index: number, entry: string | Record<Key, string>) {
    onChange(
      value.map((current, position) => (position === index ? entry : current))
    )
  }

  return (
    <fieldset className="flex min-w-0 flex-col gap-3">
      <legend className="mb-2 font-medium">{title}</legend>
      {value.map((entry, index) => {
        const id = `${keys[0]}-${ids[index]}`
        return (
          <div
            key={id}
            className="flex min-w-0 flex-col gap-3 rounded-lg border p-3"
          >
            {typeof entry === "string" ? (
              <div className="flex flex-col gap-2">
                <Label htmlFor={id}>Existing entry</Label>
                <Input
                  id={id}
                  value={entry}
                  onChange={(e) => change(index, e.target.value)}
                />
              </div>
            ) : (
              <div className="grid gap-3 sm:grid-cols-3">
                {keys.map((key) => (
                  <div key={key} className="flex min-w-0 flex-col gap-2">
                    <Label htmlFor={`${id}-${key}`}>{fields[key]}</Label>
                    <Input
                      id={`${id}-${key}`}
                      value={entry[key]}
                      onChange={(e) =>
                        change(index, { ...entry, [key]: e.target.value })
                      }
                    />
                  </div>
                ))}
              </div>
            )}
            <Button
              type="button"
              size="sm"
              variant="ghost"
              className="self-end"
              onClick={() => remove(index)}
              aria-label={`Remove ${title.toLowerCase()} entry ${index + 1}`}
            >
              Remove
            </Button>
          </div>
        )
      })}
      <Button
        type="button"
        variant="outline"
        size="sm"
        className="self-start"
        onClick={add}
      >
        Add {title.toLowerCase()}
      </Button>
    </fieldset>
  )
}
