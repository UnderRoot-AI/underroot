import type { ReactNode } from "react";

export default function StatCard({
  label,
  value,
  helper,
  icon
}: {
  label: string;
  value: string | number;
  helper?: string;
  icon?: ReactNode;
}) {
  return (
    <div className="stat-card">
      <div className="stat-icon">{icon}</div>
      <div>
        <p className="muted">{label}</p>
        <h3>{value}</h3>
        {helper && <small>{helper}</small>}
      </div>
    </div>
  );
}
