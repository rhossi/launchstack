"use client"

import { useEffect, useState } from "react"
import { useRouter, useParams } from "next/navigation"
import Link from "next/link"
import { ProtectedRoute } from "@/components/layout/protected-route"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { stacksApi, agentsApi, ApiError } from "@/lib/api"
import { StackDetailResponse } from "@/types/stack"
import { AgentResponse } from "@/types/agent"
import { format } from "date-fns"
import { MoreVertical, Trash2, Edit, Eye, ExternalLink } from "lucide-react"

export default function StackDetailPage() {
  const router = useRouter()
  const params = useParams()
  const stackId = params.id as string
  const [stack, setStack] = useState<StackDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    loadStack()
  }, [stackId])

  // Poll for status updates when agents are in "creating" status
  useEffect(() => {
    if (!stack) return

    const hasCreatingAgents = stack.agents.some(agent => agent.status === "creating")
    
    if (!hasCreatingAgents) return

    // Poll every 2 seconds while agents are creating
    const interval = setInterval(() => {
      loadStack()
    }, 2000)

    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stack])

  const loadStack = async () => {
    try {
      setLoading(true)
      const data = await stacksApi.get(stackId)
      setStack(data)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.push("/login")
      } else if (err instanceof ApiError && err.status === 404) {
        router.push("/stacks")
      }
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this stack? This will delete all agents in this stack.")) {
      return
    }

    try {
      setDeleting(true)
      await stacksApi.delete(stackId)
      // Redirect to stacks list to see deletion status
      router.push("/stacks")
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.push("/login")
      }
      alert("Failed to delete stack")
      setDeleting(false)
    }
  }

  const handleDeleteAgent = async (agentId: string) => {
    if (!confirm("Are you sure you want to delete this agent?")) {
      return
    }

    try {
      await agentsApi.delete(agentId)
      loadStack()
    } catch (err) {
      alert("Failed to delete agent")
    }
  }

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="container mx-auto px-4 py-8">
          <div>Loading...</div>
        </div>
      </ProtectedRoute>
    )
  }

  if (!stack) {
    return null
  }

  return (
    <ProtectedRoute>
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <Link href="/stacks">
            <Button variant="ghost">← Back to Stacks</Button>
          </Link>
        </div>

        <Card className="mb-6">
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle>{stack.name}</CardTitle>
                <CardDescription>{stack.description || "No description"}</CardDescription>
              </div>
              <div className="flex gap-2">
                <Link href={`/stacks/${stackId}/edit`}>
                  <Button variant="outline">
                    <Edit className="mr-2 h-4 w-4" />
                    Update Stack
                  </Button>
                </Link>
                <Button variant="destructive" onClick={handleDelete} disabled={deleting}>
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete Stack
                </Button>
                <Link href={`/stacks/${stackId}/agents/new`}>
                  <Button>Create Agent</Button>
                </Link>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <p className="text-sm font-medium">Created</p>
                <p className="text-sm text-muted-foreground">
                  {format(new Date(stack.created_at), "MMM d, yyyy 'at' h:mm a")}
                </p>
                <p className="text-sm text-muted-foreground">by {stack.created_by.full_name}</p>
              </div>
              <div>
                <p className="text-sm font-medium">Last Updated</p>
                <p className="text-sm text-muted-foreground">
                  {format(new Date(stack.updated_at), "MMM d, yyyy 'at' h:mm a")}
                </p>
                <p className="text-sm text-muted-foreground">by {stack.updated_by.full_name}</p>
              </div>
            </div>
            {stack.namespace && (
              <div className="mt-4 pt-4 border-t">
                <p className="text-sm font-medium">Namespace</p>
                <p className="text-sm text-muted-foreground font-mono">{stack.namespace}</p>
              </div>
            )}
          </CardContent>
        </Card>

        <div>
          <h2 className="text-2xl font-bold mb-4">Agents</h2>
          {stack.agents.length === 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>No agents</CardTitle>
                <CardDescription>Create your first agent for this stack</CardDescription>
              </CardHeader>
            </Card>
          ) : (
            <div className="space-y-4">
              {stack.agents.map((agent) => (
                <Card key={agent.id}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle>{agent.name}</CardTitle>
                        <CardDescription>{agent.description || "No description"}</CardDescription>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem asChild>
                            <Link href={`/agents/${agent.id}/edit`}>
                              <Edit className="mr-2 h-4 w-4" />
                              Update
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleDeleteAgent(agent.id)}>
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">Status:</span>
                        <span className={`text-sm px-2 py-1 rounded ${
                          agent.status === 'running' || agent.status === 'ready' ? 'bg-green-100 text-green-800' :
                          agent.status === 'deploying' || agent.status === 'creating' ? 'bg-yellow-100 text-yellow-800' :
                          agent.status === 'failed' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {agent.status}
                        </span>
                      </div>
                      <div>
                        <p className="text-sm font-medium mb-1">API URL</p>
                        {agent.api_url ? (
                          <a 
                            href={agent.api_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-sm text-blue-600 hover:underline flex items-center gap-1"
                          >
                            {agent.api_url}
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        ) : (
                          <span className="text-sm text-muted-foreground">Not available</span>
                        )}
                      </div>
                      <div>
                        <p className="text-sm font-medium mb-1">UI URL</p>
                        {agent.ui_url ? (
                          <a 
                            href={agent.ui_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-sm text-blue-600 hover:underline flex items-center gap-1"
                          >
                            {agent.ui_url}
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        ) : (
                          <span className="text-sm text-muted-foreground">Not available</span>
                        )}
                      </div>
                      <div className="grid gap-4 md:grid-cols-2 text-sm text-muted-foreground pt-2 border-t">
                      <div>
                        <p>Created: {format(new Date(agent.created_at), "MMM d, yyyy 'at' h:mm a")}</p>
                        <p>by {agent.created_by.full_name}</p>
                      </div>
                      <div>
                        <p>Updated: {format(new Date(agent.updated_at), "MMM d, yyyy 'at' h:mm a")}</p>
                        <p>by {agent.updated_by.full_name}</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  )
}

