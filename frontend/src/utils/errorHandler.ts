import axios from "axios";

export function getErrorMessage(error: unknown, fallback = "Something went wrong") {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((x) => x?.msg || x).join(", ");
    if (error.message) return error.message;
  }
  return fallback;
}
