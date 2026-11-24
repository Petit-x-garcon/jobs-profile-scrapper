"use client"

import { useState } from "react"
import { toast } from "sonner"

import { Alert, AlertDescription } from "@workspace/ui/components/alert"
import { Button } from "@workspace/ui/components/button"
import { Checkbox } from "@workspace/ui/components/checkbox"
import { Input } from "@workspace/ui/components/input"
import { Label } from "@workspace/ui/components/label"
import { Skeleton } from "@workspace/ui/components/skeleton"
import { Textarea } from "@workspace/ui/components/textarea"
import { CvEntryFields } from "@/components/profile/cv-entry-fields"
import { useProfile, useUpdateProfile } from "@/hooks/use-profile"
import type { Profile } from "@/lib/api/schemas"

const list = (v: string) =>
  v
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)

const lines = (v: string) =>
  v
    .split("\n")
    .map((s) => s.trim())
    .filter(Boolean)

const SECTIONS = [
  { name: "projects", label: "Projects" },
  { name: "certifications", label: "Certifications" },
  { name: "awards", label: "Awards" },
] as const

const CONTACT_FIELDS = [
  { name: "name", label: "Full name", type: "text" },
  { name: "phone", label: "Phone", type: "tel" },
  { name: "email", label: "Professional email", type: "email" },
  { name: "city", label: "City", type: "text" },
  { name: "linkedin", label: "LinkedIn link", type: "text" },
  { name: "portfolio", label: "Portfolio link (optional)", type: "text" },
] as const

const WORK_FIELDS = { company: "Company", title: "Job title", dates: "Dates" }
const EDUCATION_FIELDS = {
  degree: "Degree",
  university: "University",
  year: "Graduation year",
}

function hasEntry(entry: string | Record<string, string>) {
  return typeof entry === "string"
    ? Boolean(entry.trim())
    : Object.values(entry).some((value) => value.trim())
}

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
  const [experience, setExperience] = useState(profile.experience)
  const [education, setEducation] = useState(profile.education)
  const savedMonths = Math.round(profile.years_experience * 12)

  function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    const str = (k: string) => String(d.get(k) ?? "")
    const salary = str("min_salary").trim()
    const totalMonths =
      Number(str("experience_years")) * 12 + Number(str("experience_months"))
    update.mutate(
      {
        headline: str("headline"),
        contact: {
          name: str("name").trim(),
          phone: str("phone").trim(),
          email: str("email").trim(),
          city: str("city").trim(),
          linkedin: str("linkedin").trim(),
          portfolio: str("portfolio").trim(),
        },
        skills: list(str("skills")),
        years_experience:
          totalMonths === savedMonths
            ? profile.years_experience
            : totalMonths / 12,
        locations: list(str("locations")),
        remote_ok: d.get("remote_ok") === "on",
        min_salary: salary === "" ? null : Number(salary),
        summary: str("summary"),
        experience: experience.filter(hasEntry),
        education: education.filter(hasEntry),
        projects: lines(str("projects")),
        certifications: lines(str("certifications")),
        awards: lines(str("awards")),
      },
      {
        onSuccess: () => toast.success("Profile saved"),
        onError: (err) => toast.error(err.message),
      }
    )
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-4">
      <fieldset className="grid gap-4 sm:grid-cols-2">
        <legend className="mb-3 font-medium">Contact details</legend>
        {CONTACT_FIELDS.map(({ name, label, type }) => (
          <Field key={name} id={name} label={label}>
            <Input
              id={name}
              name={name}
              type={type}
              defaultValue={profile.contact[name]}
            />
          </Field>
        ))}
      </fieldset>
      <Field id="headline" label="Headline">
        <Input id="headline" name="headline" defaultValue={profile.headline} />
      </Field>
      <Field id="summary" label="Summary">
        <Textarea
          id="summary"
          name="summary"
          rows={3}
          defaultValue={profile.summary}
        />
      </Field>
      <p className="text-sm text-muted-foreground">
        List your most recent job first.
      </p>
      <CvEntryFields
        title="Work experience"
        fields={WORK_FIELDS}
        value={experience}
        onChange={setExperience}
      />
      <Field id="skills" label="Skills (comma-separated)">
        <Input
          id="skills"
          name="skills"
          defaultValue={profile.skills.join(", ")}
        />
      </Field>
      <CvEntryFields
        title="Education"
        fields={EDUCATION_FIELDS}
        value={education}
        onChange={setEducation}
      />
      {SECTIONS.map(({ name, label }) => (
        <Field key={name} id={name} label={`${label} (one per line)`}>
          <Textarea
            id={name}
            name={name}
            rows={3}
            defaultValue={profile[name].join("\n")}
          />
        </Field>
      ))}
      <h3 className="border-t pt-4 font-medium">Job preferences</h3>
      <fieldset className="grid grid-cols-2 gap-4">
        <legend className="mb-2 font-medium">Professional experience</legend>
        <Field id="experience_years" label="Years">
          <Input
            id="experience_years"
            name="experience_years"
            type="number"
            min={0}
            step={1}
            defaultValue={Math.floor(savedMonths / 12)}
          />
        </Field>
        <Field id="experience_months" label="Months">
          <Input
            id="experience_months"
            name="experience_months"
            type="number"
            min={0}
            max={11}
            step={1}
            defaultValue={savedMonths % 12}
          />
        </Field>
      </fieldset>
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
      <p className="text-sm text-muted-foreground">
        Saving clears AI match scores. Run Analyze with AI again on the jobs
        page.
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
    <section className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h2 className="text-lg font-semibold">Profile details</h2>
        <p className="text-sm text-muted-foreground">
          Filled from your CV. Review and correct anything the extraction got
          wrong.
        </p>
      </div>
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      )}
      {isPending && !error && <Skeleton className="h-96 w-full" />}
      {data && <Form key={data.updated_at} profile={data} />}
    </section>
  )
}
