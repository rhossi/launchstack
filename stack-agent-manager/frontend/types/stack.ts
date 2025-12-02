import { UserInfo } from "./user";
import { AgentResponse } from "./agent";

export interface Stack {
  id: string;
  name: string;
  namespace: string | null;
  status: string;
  description: string | null;
  created_at: string;
  created_by: UserInfo;
  updated_at: string;
  updated_by: UserInfo;
}

export interface StackListResponse extends Stack {
  agent_count: number;
}

export interface StackDetailResponse extends Stack {
  agents: AgentResponse[];
}

export interface StackCreate {
  name: string;
  description?: string;
}

export interface StackUpdate {
  name?: string;
  description?: string;
}

export interface StackListPaginated {
  items: StackListResponse[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

