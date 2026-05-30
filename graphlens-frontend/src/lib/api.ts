import axios from "axios";
import { clearToken, getToken } from "./token";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = axios.create({ baseURL: API_URL });

// Attach the JWT to every request.
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, drop the (stale) token so the app can redirect to login.
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error?.response?.status === 401 && typeof window !== "undefined") {
      clearToken();
    }
    return Promise.reject(error);
  },
);

export { API_URL };
