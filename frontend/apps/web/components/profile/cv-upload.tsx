"use client"

import { ChevronDownIcon, FileTextIcon, UploadIcon } from "lucide-react"
import { toast } from "sonner"

import { Alert, AlertDescription } from "@workspace/ui/components/alert"
import { Button } from "@workspace/ui/components/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/card"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@workspace/ui/components/collapsible"
import { Input } from "@workspace/ui/components/input"
import { Label } from "@workspace/ui/components/label"
import { Skeleton } from "@workspace/ui/components/skeleton"
import { useCv, useUploadCv } from "@/hooks/use-cv"
import type { Cv } from "@/lib/api/schemas"

const ACCEPT =
  ".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"

function CurrentCv({ cv }: { cv: Cv }) {
  return (
    <div className="flex flex-col gap-2 rounded-lg border p-3">
      <div className="flex items-center gap-2 font-medium">
        <FileTextIcon className="size-4 shrink-0" />
        <span className="break-all">{cv.filename}</span>
      </div>
      <p className="text-muted-foreground text-sm">
        Uploaded {new Date(cv.uploaded_at).toLocaleString()} ·{" "}
        {Math.ceil(cv.size_bytes / 1024)} KB
      </p>
      <Collapsible className="flex flex-col">
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm" className="-ml-2 self-start">
            Show extracted text
            <ChevronDownIcon />
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="text-muted-foreground max-h-80 overflow-auto text-sm whitespace-pre-wrap">
          {cv.text}
        </CollapsibleContent>
      </Collapsible>
    </div>
  )
}

export function CvUpload() {
  const { data: cv, error, isPending } = useCv()
  const upload = useUploadCv()

  function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = e.currentTarget
    const file = new FormData(form).get("file")
    if (!(file instanceof File) || file.size === 0) return
    upload.mutate(file, {
      onSuccess: () => {
        toast.success("CV uploaded and profile updated")
        form.reset()
      },
    })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>CV</CardTitle>
        <CardDescription>
          PDF or Word (.docx), up to 5 MB. Uploading replaces the current CV and
          the profile details extracted from it.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {isPending && <Skeleton className="h-20 w-full" />}
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error.message}</AlertDescription>
          </Alert>
        )}
        {cv && <CurrentCv cv={cv} />}
        {cv === null && (
          <p className="text-muted-foreground text-sm">No CV uploaded yet.</p>
        )}
        <form onSubmit={submit} className="flex flex-col gap-2">
          <Label htmlFor="cv-file">{cv ? "Replace CV" : "Upload CV"}</Label>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Input
              id="cv-file"
              name="file"
              type="file"
              accept={ACCEPT}
              required
            />
            <Button type="submit" disabled={upload.isPending}>
              <UploadIcon className={upload.isPending ? "animate-pulse" : ""} />
              {upload.isPending ? "Processing…" : "Upload"}
            </Button>
          </div>
          {upload.isPending && (
            <p className="text-muted-foreground text-sm" aria-live="polite">
              Extracting your profile. This can take a few seconds.
            </p>
          )}
        </form>
        {upload.error && (
          <Alert variant="destructive">
            <AlertDescription>{upload.error.message}</AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  )
}
