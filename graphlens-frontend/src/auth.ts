import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";

// Server-side calls (this file runs on the server) prefer the internal URL so
// that inside Docker we reach the backend at http://backend:8000, while the
// browser still uses NEXT_PUBLIC_API_URL (http://localhost:8000).
const API =
  process.env.API_INTERNAL_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

export const { handlers, auth, signIn, signOut } = NextAuth({
  session: { strategy: "jwt" },
  pages: { signIn: "/login" },
  providers: [
    Credentials({
      credentials: { email: {}, password: {} },
      // Delegate credential checking to FastAPI — it remains the single
      // source of truth. We store the backend JWT in the NextAuth token.
      authorize: async (creds) => {
        if (!creds?.email || !creds?.password) return null;

        const body = new URLSearchParams();
        body.set("username", String(creds.email));
        body.set("password", String(creds.password));

        const res = await fetch(`${API}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body,
        });
        if (!res.ok) return null;
        const { access_token } = await res.json();

        const meRes = await fetch(`${API}/auth/me`, {
          headers: { Authorization: `Bearer ${access_token}` },
        });
        if (!meRes.ok) return null;
        const me = await meRes.json();

        return {
          id: me.id,
          email: me.email,
          role: me.role,
          accessToken: access_token,
        };
      },
    }),
  ],
  callbacks: {
    jwt({ token, user }) {
      if (user) {
        token.accessToken = user.accessToken;
        token.role = user.role;
      }
      return token;
    },
    session({ session, token }) {
      // JWT has an index signature (values typed `unknown`), so cast on read.
      session.accessToken = token.accessToken as string | undefined;
      if (session.user) session.user.role = token.role as string | undefined;
      return session;
    },
  },
});
