import { api } from "./api";
import { clearToken, setToken } from "./token";

export interface User {
  id: string;
  email: string;
  role: string;
}

/** Log in via the OAuth2 password form, store the JWT. */
export async function login(email: string, password: string): Promise<void> {
  const body = new URLSearchParams();
  body.append("username", email); // backend treats username as email
  body.append("password", password);
  const { data } = await api.post("/auth/login", body, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  setToken(data.access_token);
}

export async function signup(email: string, password: string): Promise<void> {
  await api.post("/auth/signup", { email, password });
}

export async function fetchMe(): Promise<User> {
  const { data } = await api.get<User>("/auth/me");
  return data;
}

export function logout(): void {
  clearToken();
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
