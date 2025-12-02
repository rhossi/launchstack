"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { RegisterForm } from "@/components/auth/register-form"
import { isAuthenticated } from "@/lib/auth"

export default function RegisterPage() {
  const router = useRouter()

  useEffect(() => {
    if (isAuthenticated()) {
      router.push("/stacks")
    }
  }, [router])

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <RegisterForm />
    </div>
  )
}

