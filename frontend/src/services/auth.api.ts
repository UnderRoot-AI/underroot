import { api } from "./api";
import type { AuthResponse, LoginPayload, SignupPayload, User } from "../types/auth";
export const authApi = {
  async login(payload: LoginPayload) { const { data } = await api.post<AuthResponse>("/auth/login", payload); return data; },
  async signup(payload: SignupPayload) { const { data } = await api.post<AuthResponse>("/auth/signup", payload); return data; },
  async me() { const { data } = await api.get<User>("/auth/me"); return data; },
  async verifyEmail(token: string) { const { data } = await api.get("/auth/verify-email", { params: { token } }); return data; },
  async resendVerification() { const { data } = await api.post<AuthResponse>("/auth/resend-verification"); return data; },
  async resendVerificationByEmail(email: string) { const { data } = await api.post<{ message: string }>("/auth/resend-verification-unauthenticated", { email }); return data; },
  async requestPhoneOtp(phone:string) { const { data } = await api.post("/auth/request-phone-otp", {phone}); return data as {message:string;phone_verified:boolean;development_otp?:string}; },
  async verifyPhoneOtp(otp:string) { const { data } = await api.post("/auth/verify-phone-otp", {otp}); return data as {message:string;phone_verified:boolean}; },
  async forgotPassword(email:string) { const { data } = await api.post<{message:string}>("/auth/forgot-password", {email}); return data; },
  async resetPassword(token:string, new_password:string) { const { data } = await api.post<{message:string}>("/auth/reset-password", {token, new_password}); return data; },
  async deleteAccount(password: string) { const { data } = await api.delete<{message:string}>("/auth/account", { data: { password } }); return data; },
};
export interface ProfileUpdatePayload { name?: string; state?: string; phone?: string; language?: string; location?: string; district?: string; city_village?: string; }
export const updateProfile = async (payload: ProfileUpdatePayload) => { const { data } = await api.put<User>("/auth/me", payload); return data; };
