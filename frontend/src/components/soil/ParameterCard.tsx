import { Activity } from "lucide-react";

export default function ParameterCard({
  label, value, unit, status
}: { label: string; value?: number; unit?: string; status?: string }) {
  return (
    <div className="parameter-card">
      <div className="parameter-icon"><Activity size={17}/></div>
      <div>
        <span>{label}</span>
        <strong>{value ?? "—"} <small>{unit}</small></strong>
        {status && <em>{status}</em>}
      </div>
    </div>
  );
}
