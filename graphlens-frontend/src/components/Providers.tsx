"use client";

import { SessionProvider, useSession } from "next-auth/react";
import { useEffect } from "react";

import { clearToken, setToken } from "@/lib/token";

/** Keeps the in-memory backend JWT in sync with the NextAuth session so the
 * axios client / streaming fetch can authenticate backend calls. */
function TokenSync() {
  const { data } = useSession();
  useEffect(() => {
    if (data?.accessToken) setToken(data.accessToken);
    else clearToken();
  }, [data]);
  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <TokenSync />
      {children}
    </SessionProvider>
  );
}
