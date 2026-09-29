import axios from "axios";
import { ENV } from "../config/env";

const developerApiClient = axios.create({ baseURL: ENV.API_URL, timeout: 30000 });
developerApiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("developer_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Types ──────────────────────────────────────────────────────────────────

export interface DeveloperStats {
  total_users: number;
  verified_users: number;
  unverified_users: number;
  logged_in_users: number;
  total_logins: number;
  total_soil_tests: number;
  total_devices: number;
  total_reports: number;
  active_schemes: number;
}

export interface DeveloperUser {
  id: number;
  name: string;
  email: string;
  phone?: string;
  state?: string;
  district?: string;
  village?: string;
  language: string;
  login_count: number;
  email_verified: boolean;
  last_login_at?: string;
  created_at?: string;
}

export interface AdminSoilTest {
  id: number;
  user_id: number;
  user_name: string;
  location?: string;
  source: string;
  health_score: number;
  health_status: string;
  ph?: number;
  nitrogen?: number;
  phosphorus?: number;
  potassium?: number;
  created_at: string;
}

export interface AdminDevice {
  id: number;
  device_id: string;
  name: string;
  manufacturer?: string;
  model?: string;
  connection_type: string;
  status: string;
  user_id: number;
  owner_name: string;
  last_seen_at?: string;
  reading_count: number;
  created_at: string;
}

export interface AdminReport {
  id: number;
  user_id: number;
  owner_name: string;
  soil_test_id?: number;
  file_name?: string;
  status: string;
  created_at: string;
}

export interface PaginatedResult<T> {
  total: number;
  items: T[];
}

export interface Scheme {
  id: number;
  name: string;
  state?: string;
  description: string;
  url: string;
  active: boolean;
  updated_at?: string;
  created_at?: string;
}

export interface SchemePayload {
  name: string;
  state?: string;
  description: string;
  url: string;
  active: boolean;
}

// ── API ────────────────────────────────────────────────────────────────────

export const developerApi = {
  async login(email: string, password: string) {
    const { data } = await developerApiClient.post("/developer/login", { email, password });
    return data;
  },

  async stats(): Promise<DeveloperStats> {
    const { data } = await developerApiClient.get<DeveloperStats>("/developer/stats");
    return data;
  },

  async users(): Promise<DeveloperUser[]> {
    const { data } = await developerApiClient.get<DeveloperUser[]>("/developer/users");
    return data;
  },

  async usersCsv(): Promise<Blob> {
    const { data } = await developerApiClient.get("/developer/users/export", { responseType: "blob" });
    return data as Blob;
  },

  async soilTests(limit = 100, offset = 0): Promise<PaginatedResult<AdminSoilTest>> {
    const { data } = await developerApiClient.get<PaginatedResult<AdminSoilTest>>(
      `/developer/soil-tests?limit=${limit}&offset=${offset}`
    );
    return data;
  },

  async devices(limit = 100, offset = 0): Promise<PaginatedResult<AdminDevice>> {
    const { data } = await developerApiClient.get<PaginatedResult<AdminDevice>>(
      `/developer/devices?limit=${limit}&offset=${offset}`
    );
    return data;
  },

  async reports(limit = 100, offset = 0): Promise<PaginatedResult<AdminReport>> {
    const { data } = await developerApiClient.get<PaginatedResult<AdminReport>>(
      `/developer/reports?limit=${limit}&offset=${offset}`
    );
    return data;
  },

  async schemes(): Promise<Scheme[]> {
    const { data } = await developerApiClient.get<Scheme[]>("/developer/schemes");
    return data;
  },

  async createScheme(payload: SchemePayload): Promise<Scheme> {
    const { data } = await developerApiClient.post<Scheme>("/developer/schemes", payload);
    return data;
  },

  async updateScheme(id: number, payload: SchemePayload): Promise<Scheme> {
    const { data } = await developerApiClient.put<Scheme>(`/developer/schemes/${id}`, payload);
    return data;
  },

  async deleteScheme(id: number): Promise<void> {
    await developerApiClient.delete(`/developer/schemes/${id}`);
  },
};
