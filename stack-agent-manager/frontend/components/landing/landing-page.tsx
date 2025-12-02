"use client"

import { useState } from "react"
import Link from "next/link"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { 
  Rocket, 
  Calendar, 
  Cloud, 
  BarChart3, 
  DollarSign, 
  Code, 
  Share2 
} from "lucide-react"

export function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0a0e27] text-white">
      {/* Header */}
      <header className="container mx-auto px-4 py-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Rocket className="h-6 w-6 text-blue-500" />
          <span className="text-xl font-bold">Launch Stack</span>
        </div>
        <nav className="hidden md:flex items-center gap-6">
          <a href="#features" className="hover:text-blue-400 transition-colors">
            Features
          </a>
          <a href="#how-it-works" className="hover:text-blue-400 transition-colors">
            How It Works
          </a>
          <a href="#pricing" className="hover:text-blue-400 transition-colors">
            Pricing
          </a>
        </nav>
        <Button 
          asChild
          className="bg-blue-600 hover:bg-blue-700 text-white"
        >
          <Link href="/login">Get Started</Link>
        </Button>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <h1 className="text-5xl md:text-6xl font-bold leading-tight">
              Deploy Langgraph Agents, Stress-Free.
            </h1>
            <p className="text-xl text-gray-300">
              Go from building to production in minutes. We handle the infrastructure, you focus on your agents.
            </p>
            <Button 
              asChild
              size="lg"
              className="bg-blue-600 hover:bg-blue-700 text-white text-lg px-8 py-6"
            >
              <Link href="/login">Get Started for Free</Link>
            </Button>
          </div>
          <div className="relative w-full h-96 rounded-lg overflow-hidden bg-gray-800 flex items-center justify-center">
            <Image
              src="/hero-image.png"
              alt="Launch Stack - Deploy Langgraph Agents"
              width={800}
              height={600}
              className="w-full h-full object-contain"
              priority
            />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Go from Development to Deployment in Record Time
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Launch Stack provides everything you need to deploy, manage, and scale your Langgraph agents without worrying about the underlying infrastructure.
          </p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mb-4">
                <Calendar className="h-6 w-6 text-white" />
              </div>
              <CardTitle className="text-white">One-Click Deploy</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-gray-300">
                Connect your repository and deploy your agent with a single click.
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mb-4">
                <Cloud className="h-6 w-6 text-white" />
              </div>
              <CardTitle className="text-white">Scalable Infrastructure</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-gray-300">
                Our infrastructure automatically scales to meet your application's demand.
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mb-4">
                <BarChart3 className="h-6 w-6 text-white" />
              </div>
              <CardTitle className="text-white">Real-time Monitoring</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-gray-300">
                Keep an eye on your agent's performance with built-in logging and analytics.
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mb-4">
                <DollarSign className="h-6 w-6 text-white" />
              </div>
              <CardTitle className="text-white">Cost-Effective</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-gray-300">
                Pay only for what you use with our transparent and competitive pricing.
              </CardDescription>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="container mx-auto px-4 py-20">
        <h2 className="text-4xl md:text-5xl font-bold text-center mb-16">
          How It Works
        </h2>
        <div className="max-w-2xl mx-auto space-y-8">
          <div className="flex items-start gap-6 relative">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
                <Code className="h-6 w-6 text-white" />
              </div>
            </div>
            <div className="flex-1 pt-2">
              <h3 className="text-2xl font-bold mb-2">
                Step 1 <span className="font-normal">Build Your Agent</span>
              </h3>
            </div>
            <div className="absolute left-6 top-12 w-0.5 h-16 bg-gray-700"></div>
          </div>

          <div className="flex items-start gap-6 relative">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
                <Share2 className="h-6 w-6 text-white" />
              </div>
            </div>
            <div className="flex-1 pt-2">
              <h3 className="text-2xl font-bold mb-2">
                Step 2 <span className="font-normal">Connect Your Repo</span>
              </h3>
            </div>
            <div className="absolute left-6 top-12 w-0.5 h-16 bg-gray-700"></div>
          </div>

          <div className="flex items-start gap-6">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
                <Rocket className="h-6 w-6 text-white" />
              </div>
            </div>
            <div className="flex-1 pt-2">
              <h3 className="text-2xl font-bold mb-2">
                Step 3 <span className="font-normal">Launch Your Stack</span>
              </h3>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="bg-gray-800 rounded-lg p-12 max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold mb-4">
            Ready to Launch Your Agent?
          </h2>
          <p className="text-xl text-gray-300 mb-8">
            Join developers who are shipping faster without managing infrastructure. Get started for free, no credit card required.
          </p>
          <Button 
            asChild
            size="lg"
            className="bg-blue-600 hover:bg-blue-700 text-white text-lg px-8 py-6"
          >
            <Link href="/login">Deploy Your First Agent</Link>
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-8 border-t border-gray-800">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-gray-400">
            <Rocket className="h-4 w-4 text-blue-500" />
            <span>© 2024 Launch Stack, Inc.</span>
          </div>
          <div className="flex items-center gap-6 text-gray-400">
            <Link href="#" className="hover:text-white transition-colors">
              Terms of Service
            </Link>
            <Link href="#" className="hover:text-white transition-colors">
              Privacy Policy
            </Link>
          </div>
        </div>
      </footer>
    </div>
  )
}

