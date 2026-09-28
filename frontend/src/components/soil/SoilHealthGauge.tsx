export default function SoilHealthGauge({ score = 0 }: { score?: number }) {
  const safe = Math.max(0, Math.min(100, score));
  const status = safe >= 75 ? "Healthy" : safe >= 50 ? "Needs Attention" : "Poor";
  return (
    <div className="health-gauge">
      <div className="gauge-ring" style={{ "--score": `${safe * 3.6}deg` } as React.CSSProperties}>
        <div><strong>{Math.round(safe)}</strong><span>/ 100</span></div>
      </div>
      <div><b>{status}</b><span>Overall soil health</span></div>
    </div>
  );
}
