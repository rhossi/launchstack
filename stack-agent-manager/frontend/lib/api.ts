import { LoginRequest, LoginResponse, RegisterRequest, User } from "@/types/user";
import { StackListPaginated, StackDetailResponse, StackCreate, StackUpdate } from "@/types/stack";
import { AgentListPaginated, AgentResponse, AgentCreate, AgentUpdate } from "@/types/agent";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public code?: string
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, error.detail || response.statusText, error.code);
  }

  if (response.status === 204) {
    return null as T;
  }

  return response.json();
  } catch (error) {
    // Handle network errors (Failed to fetch)
    if (error instanceof TypeError && error.message === "Failed to fetch") {
      throw new ApiError(
        0,
        `Cannot connect to backend API at ${API_URL}. Please ensure the backend server is running.`,
        "NETWORK_ERROR"
      );
    }
    // Re-throw ApiError instances
    if (error instanceof ApiError) {
      throw error;
    }
    // Wrap other errors
    throw new ApiError(0, error instanceof Error ? error.message : "An unexpected error occurred");
  }
}

// Auth API
export const authApi = {
  register: (data: RegisterRequest) =>
    fetchApi<User>(`/api/auth/register`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data: LoginRequest) =>
    fetchApi<LoginResponse>(`/api/auth/login`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  logout: () =>
    fetchApi<void>(`/api/auth/logout`, {
      method: "POST",
    }),

  me: () => fetchApi<User>(`/api/auth/me`),

  refresh: () => fetchApi<{ access_token: string; token_type: string }>(`/api/auth/refresh`, {
    method: "POST",
  }),
};

// Stacks API
export const stacksApi = {
  list: (page: number = 1, limit: number = 20, search?: string) => {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    if (search) params.append("search", search);
    return fetchApi<StackListPaginated>(`/api/stacks?${params}`);
  },

  get: (stackId: string) =>
    fetchApi<StackDetailResponse>(`/api/stacks/${stackId}`),

  create: (data: StackCreate) =>
    fetchApi<StackDetailResponse>(`/api/stacks`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (stackId: string, data: StackUpdate) =>
    fetchApi<StackDetailResponse>(`/api/stacks/${stackId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (stackId: string) =>
    fetchApi<void>(`/api/stacks/${stackId}`, {
      method: "DELETE",
    }),
};

// Agents API
export const agentsApi = {
  list: (stackId: string) =>
    fetchApi<AgentListPaginated>(`/api/stacks/${stackId}/agents`),

  get: (agentId: string) =>
    fetchApi<AgentResponse>(`/api/agents/${agentId}`),

  create: (stackId: string, data: AgentCreate) => {
    const formData = new FormData();
    formData.append("name", data.name);
    if (data.description) {
      formData.append("description", data.description);
    }
    if (data.file) {
      formData.append("file", data.file);
    }
    
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    const headers: HeadersInit = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    // Don't set Content-Type - browser will set it with boundary for multipart/form-data
    
    return fetch(`${API_URL}/api/stacks/${stackId}/agents`, {
      method: "POST",
      headers,
      credentials: "include",
      body: formData,
    }).then(async (response) => {
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new ApiError(response.status, error.detail || response.statusText, error.code);
      }
      return response.json();
    });
  },

  update: (agentId: string, data: AgentUpdate) =>
    fetchApi<AgentResponse>(`/api/agents/${agentId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (agentId: string) =>
    fetchApi<void>(`/api/agents/${agentId}`, {
      method: "DELETE",
    }),
};

export { ApiError };

