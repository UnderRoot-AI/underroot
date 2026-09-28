import axios from "axios";
import { ENV } from "../config/env";

const developerApiClient = axios.create({ baseURL: ENV.API_URL, timeout: 30000 });
developerApiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("developer_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export interface DeveloperStats { total_users:number; logged_in_users:number; total_logins:number; total_soil_tests:number; active_schemes:number; }
export interface DeveloperUser { id:number; name:string; email:string; phone?:string; state?:string; district?:string; village?:string; language:string; login_count:number; last_login_at?:string; created_at?:string; }
export interface Scheme { id:number; name:string; state?:string; description:string; url:string; active:boolean; updated_at?:string; created_at?:string; }
export interface SchemePayload { name:string; state?:string; description:string; url:string; active:boolean; }

export const developerApi = {
  async login(email:string,password:string){ const {data}=await developerApiClient.post("/developer/login",{email,password}); return data; },
  async stats(){ const {data}=await developerApiClient.get<DeveloperStats>("/developer/stats"); return data; },
  async users(){ const {data}=await developerApiClient.get<DeveloperUser[]>("/developer/users"); return data; },
  async usersCsv(){ const {data}=await developerApiClient.get("/developer/users/export",{responseType:"blob"}); return data as Blob; },
  async schemes(){ const {data}=await developerApiClient.get<Scheme[]>("/developer/schemes"); return data; },
  async createScheme(payload:SchemePayload){ const {data}=await developerApiClient.post<Scheme>("/developer/schemes",payload); return data; },
  async updateScheme(id:number,payload:SchemePayload){ const {data}=await developerApiClient.put<Scheme>(`/developer/schemes/${id}`,payload); return data; },
  async deleteScheme(id:number){ await developerApiClient.delete(`/developer/schemes/${id}`); },
};
