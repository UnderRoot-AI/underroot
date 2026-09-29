export default function SoilHealthGauge({ score = 0, status }: { score?: number; status?: string }) {
  const safe = Math.max(0, Math.min(100, score));
  const displayStatus = status || (safe >= 80 ? "Excellent" : safe >= 60 ? "Good" : safe >= 30 ? "Needs Attention" : safe > 0 ? "Poor" : "Awaiting Data");
  const color = safe >= 80 ? "#166534" : safe >= 60 ? "#15803d" : safe >= 30 ? "#d97706" : "#dc2626";
  return (
    <div className="health-gauge">
      <div className="gauge-ring" style={{ "--score": `${safe * 3.6}deg`, "--gauge-color": color } as React.CSSProperties}>
        <div><strong style={{ color }}>{Math.round(safe)}</strong><span>/ 100</span></div>
      </div>
      <div><b style={{ color }}>{displayStatus}</b><span>Overall soil health</span></div>
    </div>
  );
}
