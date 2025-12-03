"use client";

import { useContext } from "react";
import { ThreadContext } from "./ThreadContext";

export function useThreads() {
  const context = useContext(ThreadContext);
  if (context === undefined) {
    throw new Error("useThreads must be used within a ThreadProvider");
  }
  return context;
}

