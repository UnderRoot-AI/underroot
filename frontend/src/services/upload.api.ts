import { api } from "./api";

export const uploadApi = {
  async report(file: File) {
    const form = new FormData();
    form.append("file", file);
    const { data } = await api.post("/reports/upload", form, {
      headers: { "Content-Type": "multipart/form-data" }
    });
    return data;
  }
};
