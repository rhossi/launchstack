import { UserInfo } from "./user";

export interface AgentResponse {
  id: string;
  stack_id: string;
  name: string;
  description: string | null;
  status: string;
  api_url: string | null;
  ui_url: string | null;
  disk_path: string | null;
  created_at: string;
  created_by: UserInfo;
  updated_at: string;
  updated_by: UserInfo;
}

export interface AgentCreate {
  name: string;
  description?: string;
  file?: File;
}

export interface AgentUpdate {
  name?: string;
  description?: string;
}

export interface AgentListPaginated {
  items: AgentResponse[];
  total: number;
}

