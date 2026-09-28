import { useEffect } from "react";
import { authApi } from "../services/auth.api";
import { useAuthStore } from "../store/authStore";

export function useAuth() {
  const { user, loading, setUser, setLoading, logout } = useAuthStore();

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token || user) return;
    setLoading(true);
    authApi.me()
      .then(setUser)
      .catch(() => logout())
      .finally(() => setLoading(false));
  }, [user, setUser, setLoading, logout]);

  return { user, loading, setUser, logout };
}
