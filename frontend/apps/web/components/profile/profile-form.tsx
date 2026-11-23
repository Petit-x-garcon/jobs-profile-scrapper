"use client"

import { toast } from "sonner"

import { Alert, AlertDescription } from "@workspace/ui/components/alert"
import { Button } from "@workspace/ui/components/button"
import { Checkbox } from "@workspace/ui/components/checkbox"
import { Input } from "@workspace/ui/components/input"
import { Label } from "@workspace/ui/components/label"
import { Skeleton } from "@workspace/ui/components/skeleton"
import { Textarea } from "@workspace/ui/components/textarea"
import { useProfile, useUpdateProfile } from "@/hooks/use-profile"
import type { Profile } from "@/lib/api/schemas"

const list = (v: string) =>
  v
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)

function Field({
  id,
  label,
  children,
}: {
  id: string
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      {children}
    </div>
  )
}

function Form({ profile }: { profile: Profile }) {
  const update = useUpdateProfile()

  function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    const str = (k: string) => String(d.get(k) ?? "")
    const salary = str("min_salary").trim()
    update.mutate(
      {
        headline: str("headline"),
        skills: list(str("skills")),
        years_experience: Number(str("years_experience")) || 0,
        locations: list(str("locations")),
        remote_ok: d.get("remote_ok") === "on",
        min_salary: salary === "" ? null : Number(salary),
        summary: str("summary"),
      },
      {
        onSuccess: () => toast.success("Profile saved"),
        onError: (err) => toast.error(err.message),
      }
    )
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-4">
      <Field id="headline" label="Headline">
        <Input id="headline" name="headline" defaultValue={profile.headline} />
      </Field>
      <Field id="skills" label="Skills (comma-separated)">
        <Input
          id="skills"
          name="skills"
          defaultValue={profile.skills.join(", ")}
        />
      </Field>
      <Field id="years_experience" label="Years of experience">
        <Input
          id="years_experience"
          name="years_experience"
          type="number"
          min={0}
          step="any"
          defaultValue={profile.years_experience}
        />
      </Field>
      <Field id="locations" label="Locations (comma-separated)">
        <Input
          id="locations"
          name="locations"
          defaultValue={profile.locations.join(", ")}
        />
      </Field>
      <div className="flex items-center gap-2">
        <Checkbox
          id="remote_ok"
          name="remote_ok"
          defaultChecked={profile.remote_ok}
        />
        <Label htmlFor="remote_ok">Open to remote</Label>
      </div>
      <Field id="min_salary" label="Minimum salary (optional)">
        <Input
          id="min_salary"
          name="min_salary"
          type="number"
          min={0}
          defaultValue={profile.min_salary ?? ""}
        />
      </Field>
      <Field id="summary" label="Summary">
        <Textarea
          id="summary"
          name="summary"
          rows={5}
          defaultValue={profile.summary}
        />
      </Field>
      <p className="text-muted-foreground text-sm">
        Saving re-scores all jobs against this profile.
      </p>
      <Button type="submit" disabled={update.isPending} className="self-start">
        Save profile
      </Button>
    </form>
  )
}

export function ProfileForm() {
  const { data, error, isPending } = useProfile()
  return (
    <div className="flex max-w-xl flex-col gap-4">
      <h1 className="text-xl font-semibold">Profile</h1>
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      )}
      {isPending && !error && <Skeleton className="h-96 w-full" />}
      {data && <Form key={data.updated_at} profile={data} />}
    </div>
  )
}
