"use client";

import { signIn, useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { KeyRound } from "lucide-react";

export default function LoginPage() {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (session) {
      router.push("/");
    }
  }, [session, router]);

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome</h1>
          <p className="text-gray-600">Sign in to access your account</p>
        </div>

        <button
          onClick={() => signIn("oci", { callbackUrl: "/" })}
          className="w-full bg-white hover:bg-red-600 text-gray-900 hover:text-white font-medium py-3 px-4 rounded-lg border border-gray-300 hover:border-red-600 transition-colors duration-200 flex items-center justify-center gap-3 shadow-sm"
        >
          <KeyRound className="w-5 h-5" />
          <span>OCI</span>
        </button>

        <p className="mt-6 text-center text-sm text-gray-500">
          Secure authentication powered by Oracle Cloud Infrastructure
        </p>
      </div>
    </div>
  );
}

