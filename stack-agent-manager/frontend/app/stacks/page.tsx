"use client"

import { useEffect, useState, useRef } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { ProtectedRoute } from "@/components/layout/protected-route"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { stacksApi, ApiError } from "@/lib/api"
import { StackListResponse } from "@/types/stack"
import { format } from "date-fns"

function getStatusBadge(status: string) {
  const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
  switch (status) {
    case "creating":
      return <span className={`${baseClasses} bg-yellow-100 text-yellow-800`}>Creating</span>
    case "ready":
      return <span className={`${baseClasses} bg-green-100 text-green-800`}>Ready</span>
    case "deleting":
      return <span className={`${baseClasses} bg-orange-100 text-orange-800`}>Deleting</span>
    case "failed":
      return <span className={`${baseClasses} bg-red-100 text-red-800`}>Failed</span>
    default:
      return <span className={`${baseClasses} bg-gray-100 text-gray-800`}>{status}</span>
  }
}

export default function StacksPage() {
  const router = useRouter()
  const [stacks, setStacks] = useState<StackListResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    loadStacks()
  }, [page, search])

  // Poll for status updates if any stack is in "creating" status
  useEffect(() => {
    const hasActiveStacks = stacks.some(s => s.status === "creating" || s.status === "deleting")
    
    if (hasActiveStacks && !pollingIntervalRef.current) {
      pollingIntervalRef.current = setInterval(() => {
        loadStacks()
      }, 2000) // Poll every 2 seconds
    } else if (!hasActiveStacks && pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }
    
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
        pollingIntervalRef.current = null
      }
    }
  }, [stacks])

  const loadStacks = async () => {
    try {
      setLoading(true)
      const response = await stacksApi.list(page, 20, search || undefined)
      setStacks(response.items)
      setTotalPages(response.pages)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.push("/login")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <ProtectedRoute>
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">Stacks</h1>
          <Link href="/stacks/new">
            <Button>Create Stack</Button>
          </Link>
        </div>

        <div className="mb-6">
          <Input
            placeholder="Search stacks..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
            className="max-w-md"
          />
        </div>

        {loading ? (
          <div>Loading...</div>
        ) : stacks.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>No stacks found</CardTitle>
              <CardDescription>Create your first stack to get started</CardDescription>
            </CardHeader>
          </Card>
        ) : (
          <>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {stacks.map((stack) => (
                <Card key={stack.id} className="cursor-pointer hover:shadow-lg transition-shadow">
                  <Link href={`/stacks/${stack.id}`}>
                    <CardHeader>
                      <CardTitle>{stack.name}</CardTitle>
                      <CardDescription>
                        {stack.description || "No description"}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="text-sm text-muted-foreground space-y-2">
                        <div className="flex items-center justify-between">
                          <span>Status:</span>
                          {getStatusBadge(stack.status)}
                        </div>
                        <p>Created: {format(new Date(stack.created_at), "MMM d, yyyy 'at' h:mm a")}</p>
                        <p>Created by: {stack.created_by.full_name}</p>
                        <p>Agents: {stack.agent_count}</p>
                      </div>
                    </CardContent>
                  </Link>
                </Card>
              ))}
            </div>

            {totalPages > 1 && (
              <div className="mt-6 flex justify-center gap-2">
                <Button
                  variant="outline"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <span className="flex items-center px-4">
                  Page {page} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Next
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </ProtectedRoute>
  )
}

