import { api } from "./api";
export interface ResourceItem { name:string; url:string; description:string; }
export const resourcesApi = { async government(){ const {data}=await api.get<{title:string;items:ResourceItem[];note:string}>("/resources/government"); return data; } };
