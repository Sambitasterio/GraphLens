/** In-memory backend JWT, kept in sync with the NextAuth session by
 * <TokenSync>. Not persisted — the httpOnly session cookie is the source of
 * truth, so a refresh re-hydrates the token from the session. */
let memToken: string | null = null;

export function getToken(): string | null {
  return memToken;
}

export function setToken(token: string): void {
  memToken = token;
}

export function clearToken(): void {
  memToken = null;
}
