"use client"

import { cn } from "cn"
import { ChevronDownIcon, FileTextIcon, UploadIcon } from "lucide-react"
import { useRef, useState } from "react"
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
      <p className="text-sm text-muted-foreground">
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
        <CollapsibleContent className="max-h-80 overflow-auto text-sm whitespace-pre-wrap text-muted-foreground">
          {cv.text}
        </CollapsibleContent>
      </Collapsible>
    </div>
  )
}

export function CvUpload() {
  const { data: cv, error, isPending } = useCv()

  return (
    <Card>
      <CardHeader>
        <CardTitle>CV</CardTitle>
        <CardDescription>
          Uploading replaces the current CV and the profile details extracted
          from it.
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
          <p className="text-sm text-muted-foreground">No CV uploaded yet.</p>
        )}
        <CvUploadField />
      </CardContent>
    </Card>
  )
}

function CvUploadField() {
  const input = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)
  const upload = useUploadCv()

  function selectFile(selected: File | undefined) {
    if (!selected || upload.isPending) return
    upload.reset()
    const error = !/\.(pdf|docx)$/i.test(selected.name)
      ? "Choose a PDF or Word (.docx) file."
      : selected.size === 0 || selected.size > 5 * 1024 * 1024
        ? "Choose a non-empty file up to 5 MB."
        : null
    setFileError(error)
    setFile(error ? null : selected)
  }

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!file || upload.isPending) return
    upload.mutate(file, {
      onSuccess: () => {
        setFile(null)
        toast.success("CV uploaded and profile updated")
      },
    })
  }

  const error = fileError ?? upload.error?.message

  return (
    <form
      onSubmit={submit}
      className="flex flex-col gap-3"
      aria-label="Upload CV"
    >
      <Input
        ref={input}
        type="file"
        accept={ACCEPT}
        hidden
        disabled={upload.isPending}
        onChange={(event) => {
          selectFile(event.currentTarget.files?.[0])
          event.currentTarget.value = ""
        }}
      />
      <Button
        type="button"
        variant="outline"
        disabled={upload.isPending}
        aria-describedby="cv-file-format"
        className={cn(
          "h-auto w-full flex-col gap-2 rounded-xl border-dashed px-4 py-6 text-center whitespace-normal",
          dragging && "border-primary bg-accent"
        )}
        onClick={() => input.current?.click()}
        onDragOver={(event) => {
          event.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault()
          setDragging(false)
          selectFile(event.dataTransfer.files[0])
        }}
      >
        <UploadIcon className="size-5" />
        <span>{file ? "Choose another CV" : "Choose or drop your CV"}</span>
        <span id="cv-file-format" className="text-xs text-muted-foreground">
          PDF or Word (.docx), up to 5 MB
        </span>
      </Button>
      {file && (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <p
            className="flex min-w-0 flex-1 items-center gap-2 text-sm"
            role="status"
          >
            <FileTextIcon className="size-4 shrink-0" aria-hidden="true" />
            <span className="min-w-0 wrap-anywhere">{file.name}</span>
          </p>
          <Button type="submit" disabled={upload.isPending}>
            {upload.isPending ? "Processing…" : "Upload CV"}
          </Button>
        </div>
      )}
      {upload.isPending && (
        <p className="text-sm text-muted-foreground" role="status">
          Extracting your profile. This can take a few seconds.
        </p>
      )}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </form>
  )
}
