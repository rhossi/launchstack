"use client"

import { useState } from "react"
import { useRouter, useParams } from "next/navigation"
import Link from "next/link"
import { ProtectedRoute } from "@/components/layout/protected-route"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { agentsApi, ApiError } from "@/lib/api"

export default function CreateAgentPage() {
  const router = useRouter()
  const params = useParams()
  const stackId = params.id as string
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    
    if (!file) {
      setError("Please select a zip file to upload")
      return
    }
    
    if (!file.name.endsWith('.zip')) {
      setError("File must be a .zip file")
      return
    }
    
    setLoading(true)

    try {
      await agentsApi.create(stackId, { 
        name, 
        description: description || undefined,
        file: file
      })
      router.push(`/stacks/${stackId}`)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail || "Failed to create agent")
      } else {
        setError("An unexpected error occurred")
      }
    } finally {
      setLoading(false)
    }
  }
  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.zip')) {
        setError("File must be a .zip file")
        setFile(null)
        return
      }
      setFile(selectedFile)
      setError("")
    }
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
            <CardTitle>Create Agent</CardTitle>
            <CardDescription>Create a new agent in this stack</CardDescription>
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
              <div className="space-y-2">
                <Label htmlFor="file">Agent Code (ZIP file) *</Label>
                <Input
                  id="file"
                  type="file"
                  accept=".zip"
                  onChange={handleFileChange}
                  required
                />
                <p className="text-sm text-muted-foreground">
                  Upload a zip file containing your agent code (graph.py, config.yaml, etc.)
                </p>
                {file && (
                  <p className="text-sm text-green-600">
                    Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                  </p>
                )}
              </div>
            </CardContent>
            <CardFooter className="flex justify-end gap-2">
              <Link href={`/stacks/${stackId}`}>
                <Button type="button" variant="outline">Cancel</Button>
              </Link>
              <Button type="submit" disabled={loading}>
                {loading ? "Creating..." : "Create Agent"}
              </Button>
            </CardFooter>
          </form>
        </Card>
      </div>
    </ProtectedRoute>
  )
}

