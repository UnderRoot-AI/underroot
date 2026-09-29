import { api } from "./api";
import type {
  Device,
  HardwareReading,
  DeviceCreatePayload,
  ReadingIngestionPayload,
  DeviceProfile,
} from "../types/hardware";

export const devicesApi = {
  async listDevices(): Promise<Device[]> {
    const { data } = await api.get<Device[]>("/devices");
    return data;
  },

  async createDevice(payload: DeviceCreatePayload): Promise<Device> {
    const { data } = await api.post<Device>("/devices", payload);
    return data;
  },

  async getDevice(devicePk: number): Promise<Device> {
    const { data } = await api.get<Device>(`/devices/${devicePk}`);
    return data;
  },

  async deleteDevice(devicePk: number): Promise<void> {
    await api.delete(`/devices/${devicePk}`);
  },

  async ingestReading(devicePk: number, payload: ReadingIngestionPayload): Promise<{
    reading: HardwareReading;
    soil_test: { id: number; health_score: number; health_status: string; source: string; device_id: string; created_at: string };
    message: string;
  }> {
    const { data } = await api.post(`/devices/${devicePk}/readings`, payload);
    return data;
  },

  async listReadings(devicePk: number, limit = 50): Promise<HardwareReading[]> {
    const { data } = await api.get<HardwareReading[]>(`/devices/${devicePk}/readings`, { params: { limit } });
    return data;
  },

  async getLatestReading(devicePk: number): Promise<HardwareReading> {
    const { data } = await api.get<HardwareReading>(`/devices/${devicePk}/readings/latest`);
    return data;
  },

  async getConnectionTypes(): Promise<{ connection_types: string[] }> {
    const { data } = await api.get<{ connection_types: string[] }>("/devices/meta/connection-types");
    return data;
  },

  async getDeviceProfiles(): Promise<{ profiles: DeviceProfile[] }> {
    const { data } = await api.get<{ profiles: DeviceProfile[] }>("/devices/meta/profiles");
    return data;
  },
};
