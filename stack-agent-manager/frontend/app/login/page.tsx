"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { LoginForm } from "@/components/auth/login-form"
import { isAuthenticated } from "@/lib/auth"

export default function LoginPage() {
  const router = useRouter()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    // Only redirect if authenticated, otherwise show login form
    if (isAuthenticated()) {
      router.push("/stacks")
      return
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Prevent hydration mismatch by only rendering after mount
  if (!mounted) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-background">
        <div>Loading...</div>
      </div>
    )
  }

  // Always show login form - useEffect handles redirect if authenticated
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <LoginForm />
    </div>
  )
}

