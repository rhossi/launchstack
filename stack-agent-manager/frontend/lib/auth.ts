import { User } from "@/types/user";
import { authApi } from "./api";

export function setAccessToken(token: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem("access_token", token);
  }
}

export function getAccessToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("access_token");
  }
  return null;
}

export function removeAccessToken() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("access_token");
  }
}

export async function getCurrentUser(): Promise<User | null> {
  try {
    return await authApi.me();
  } catch {
    return null;
  }
}

export function isAuthenticated(): boolean {
  return getAccessToken() !== null;
}

