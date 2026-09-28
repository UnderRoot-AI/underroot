import { api } from "./api";
export interface HardwarePort { device:string; description?:string; manufacturer?:string; }
export const hardwareApi = {
  async ports(){ const {data}=await api.get<{ports:HardwarePort[];baudrate:number}>("/hardware/ports"); return data; },
  async read(port:string){ const {data}=await api.get<{parameters:Record<string,number>}>("/hardware/read",{params:{port}}); return data.parameters; }
};
