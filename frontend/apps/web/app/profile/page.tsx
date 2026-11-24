import { CvUpload } from "@/components/profile/cv-upload"
import { ProfileForm } from "@/components/profile/profile-form"

export default function ProfilePage() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold">Profile & CV</h1>
      <CvUpload />
      <ProfileForm />
    </div>
  )
}
