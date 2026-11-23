"use client"

import { useState } from "react"
import { PlusIcon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@workspace/ui/components/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@workspace/ui/components/dialog"
import { Input } from "@workspace/ui/components/input"
import { Label } from "@workspace/ui/components/label"
import { Textarea } from "@workspace/ui/components/textarea"
import { useImportJob } from "@/hooks/use-jobs"

export function ImportDialog() {
  const [open, setOpen] = useState(false)
  const importJob = useImportJob()

  function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = e.currentTarget
    const data = new FormData(form)
    const field = (k: string) => String(data.get(k) ?? "").trim() || null
    importJob.mutate(
      {
        url: field("url"),
        title: field("title"),
        text: String(data.get("text")),
      },
      {
        onSuccess: () => {
          toast.success("Job imported")
          form.reset()
          setOpen(false)
        },
        onError: (err) => toast.error(err.message),
      }
    )
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">
          <PlusIcon />
          Import job
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={submit} className="flex flex-col gap-4">
          <DialogHeader>
            <DialogTitle>Import a job</DialogTitle>
            <DialogDescription>
              Paste a LinkedIn or any job post.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-2">
            <Label htmlFor="import-text">Job text</Label>
            <Textarea id="import-text" name="text" required rows={8} />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="import-url">URL (optional)</Label>
            <Input id="import-url" name="url" type="url" />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="import-title">Title (optional)</Label>
            <Input id="import-title" name="title" />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={importJob.isPending}>
              Import
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
