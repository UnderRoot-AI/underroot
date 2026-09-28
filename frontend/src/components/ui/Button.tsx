import type { ButtonHTMLAttributes, ReactNode } from "react";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: "primary" | "secondary" | "ghost" | "danger";
  loading?: boolean;
}

export default function Button({ children, variant = "primary", loading, disabled, ...props }: Props) {
  return (
    <button className={`btn btn-${variant}`} disabled={disabled || loading} {...props}>
      {loading ? "Please wait..." : children}
    </button>
  );
}
