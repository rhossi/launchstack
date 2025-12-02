"use client"

import { useEffect, useState } from "react"
import { useRouter, useParams } from "next/navigation"
import Link from "next/link"
import { ProtectedRoute } from "@/components/layout/protected-route"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { agentsApi, ApiError } from "@/lib/api"

export default function EditAgentPage() {
  const router = useRouter()
  const params = useParams()
  const agentId = params.id as string
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [stackId, setStackId] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [loadingData, setLoadingData] = useState(true)

  useEffect(() => {
    loadAgent()
  }, [agentId])

  const loadAgent = async () => {
    try {
      setLoadingData(true)
      const agent = await agentsApi.get(agentId)
      setName(agent.name)
      setDescription(agent.description || "")
      setStackId(agent.stack_id)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.push("/login")
      } else if (err instanceof ApiError && err.status === 404) {
        router.push("/stacks")
      }
    } finally {
      setLoadingData(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      await agentsApi.update(agentId, { name, description: description || undefined })
      router.push(`/stacks/${stackId}`)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail || "Failed to update agent")
      } else {
        setError("An unexpected error occurred")
      }
    } finally {
      setLoading(false)
    }
  }

  if (loadingData) {
    return (
      <ProtectedRoute>
        <div className="container mx-auto px-4 py-8">
          <div>Loading...</div>
        </div>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute>
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <Link href={`/stacks/${stackId}`}>
            <Button variant="ghost">← Back to Stack</Button>
          </Link>
        </div>

        <Card className="max-w-2xl">
          <CardHeader>
            <CardTitle>Update Agent</CardTitle>
            <CardDescription>Update agent information</CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {error && (
                <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
                  {error}
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="name">Name *</Label>
                <Input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  maxLength={255}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  maxLength={5000}
                  rows={4}
                />
              </div>
            </CardContent>
            <CardFooter className="flex justify-end gap-2">
              <Link href={`/stacks/${stackId}`}>
                <Button type="button" variant="outline">Cancel</Button>
              </Link>
              <Button type="submit" disabled={loading}>
                {loading ? "Updating..." : "Update Agent"}
              </Button>
            </CardFooter>
          </form>
        </Card>
      </div>
    </ProtectedRoute>
  )
}

