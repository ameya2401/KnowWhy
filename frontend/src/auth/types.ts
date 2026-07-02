export type AuthProviderName = "google" | "github";

export interface User {
  id: string;
  email: string;
  full_name: string;
  profile_picture_url: string | null;
  provider: AuthProviderName;
  is_active: boolean;
  last_login_at: string | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: User;
}
