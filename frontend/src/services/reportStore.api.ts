import { api } from "./api";
export interface StoredSoilReport { id:number; app_report_id?:number; soil_test_id?:number; file_name?:string; status:string; extracted_parameters?:Record<string,number>; ocr_engine?:string; created_at:string; updated_at:string; }
export const reportStoreApi = { async list(){ const {data}=await api.get<StoredSoilReport[]>("/soil-reports"); return data; } };
