import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { AuthContext } from "@/auth/AuthContext";
import { apiClient } from "@/services/apiClient";
import type { AuthProviderName, AuthResponse, User } from "@/auth/types";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const persistSession = useCallback((authResponse: AuthResponse) => {
    setAccessToken(authResponse.access_token);
    setUser(authResponse.user);
  }, []);

  useEffect(() => {
    let isMounted = true;

    async function restoreSession() {
      try {
        const response = await apiClient.post<AuthResponse>("/auth/refresh", {});
        if (isMounted) {
          persistSession(response.data);
        }
      } catch {
        if (isMounted) {
          setAccessToken(null);
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void restoreSession();

    return () => {
      isMounted = false;
    };
  }, [persistSession]);

  const loginWithProviderToken = useCallback(
    async (provider: AuthProviderName, providerToken: string) => {
      const response = await apiClient.post<AuthResponse>(`/auth/${provider}`, {
        access_token: providerToken,
      });
      persistSession(response.data);
    },
    [persistSession],
  );

  const logout = useCallback(async () => {
    await apiClient.post("/auth/logout", {});
    setAccessToken(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      accessToken,
      user,
      isAuthenticated: Boolean(accessToken),
      isLoading,
      loginWithProviderToken,
      logout,
    }),
    [accessToken, isLoading, loginWithProviderToken, logout, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
