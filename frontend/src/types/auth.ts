export interface User {
  id: number;
  name: string;
  email: string;
  phone?: string;
  language: string;
  location?: string;
  state?: string;
  district?: string;
  city_village?: string;
  email_verified: boolean;
  phone_verified: boolean;
  created_at?: string;
}
export interface AuthResponse {
  access_token: string;
  user: User;
  verification_required?: boolean;
  verification_url?: string;
  development_otp?: string;
}
export interface LoginPayload { email: string; password: string; }
export interface SignupPayload { name: string; email: string; password: string; phone?: string; language?: string; state?: string; district?: string; city_village?: string; }
