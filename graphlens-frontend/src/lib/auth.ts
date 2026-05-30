import { api } from "./api";

export interface User {
  id: string;
  email: string;
  role: string;
}

/** Sign up a new account (login itself goes through NextAuth's signIn). */
export async function signup(email: string, password: string): Promise<void> {
  await api.post("/auth/signup", { email, password });
}

/** Pull a readable message out of an axios error. */
export function errorMessage(err: unknown, fallback = "Something went wrong"): string {
  if (typeof err === "object" && err !== null && "response" in err) {
    const detail = (err as { response?: { data?: { detail?: string } } }).response
      ?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}
