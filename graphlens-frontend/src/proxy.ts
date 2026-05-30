import { auth } from "@/auth";

// Protect the dashboard: unauthenticated requests are redirected to /login.
// (Next 16 renamed the "middleware" file convention to "proxy".)
export default auth((req) => {
  if (!req.auth && req.nextUrl.pathname.startsWith("/dashboard")) {
    const loginUrl = new URL("/login", req.nextUrl.origin);
    return Response.redirect(loginUrl);
  }
});

export const config = {
  matcher: ["/dashboard/:path*"],
};
