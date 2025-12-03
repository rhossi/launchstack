import { withAuth } from "next-auth/middleware";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Check if authentication is enabled (default: false)
const ENABLE_AUTH = process.env.ENABLE_AUTH === "true";

// Create middleware based on whether auth is enabled
const middleware = ENABLE_AUTH
  ? withAuth({
      pages: {
        signIn: "/login",
      },
    })
  : function (request: NextRequest) {
      // If auth is disabled, pass through all requests
      return NextResponse.next();
    };

export default middleware;

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api/auth (authentication endpoints)
     * - login (login page)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    "/((?!api/auth|login|_next/static|_next/image|favicon.ico|logo.svg).*)",
  ],
};

