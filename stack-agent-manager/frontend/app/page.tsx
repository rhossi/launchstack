"use client"

import { LandingPage } from "@/components/landing/landing-page"

export default function Home() {
  // Always show landing page - no redirects, no auth checks
  // Let individual pages handle their own authentication
  return <LandingPage />
}

