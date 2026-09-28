export function isEmail(value: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

export function required(value: string, label: string) {
  return value.trim() ? "" : `${label} is required`;
}

export function passwordError(value: string) {
  if (value.length < 8) return "Password must contain at least 8 characters";
  return "";
}
