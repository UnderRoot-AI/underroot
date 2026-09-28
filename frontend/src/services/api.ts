import axios from "axios";
import { ENV } from "../config/env";

export const api = axios.create({
  baseURL: ENV.API_URL,
  timeout: 30000
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      // Only redirect if we are NOT already on an auth page to avoid redirect loops
      const path = window.location.pathname;
      const authPaths = ["/login", "/signup", "/verify-email", "/forgot-password", "/reset-password"];
      if (!authPaths.some(p => path.startsWith(p))) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);
