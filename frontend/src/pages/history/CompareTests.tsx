import { useEffect, useState } from "react";
import { ArrowDown, ArrowUp, GitCompare, Minus } from "lucide-react";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/ui/Card";
import EmptyState from "../../components/common/EmptyState";
import { useSoil } from "../../hooks/useSoil";
import { SOIL_PARAMETERS } from "../../constants/soilParameters";
import { formatDate } from "../../utils/formatDate";
import { useT } from "../../i18n/useT";

function DeltaCell({ a, b, unit }: { a: number | undefined; b: number | undefined; unit: string }) {
  if (a == null || b == null) return <em className="">—</em>;
  const d = b - a;
  if (Math.abs(d) < 0.001) return <em><Minus size={12} /> 0</em>;
  return (
    <em className={d > 0 ? "up" : "down"}>
      {d > 0 ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
      {" "}{Math.abs(d).toFixed(2)} {unit}
    </em>
  );
}

export default function CompareTests() {
  const { tests, load, loading } = useSoil();
  const t = useT();
  const [a, setA] = useState<string>("");
  const [b, setB] = useState<string>("");
  useEffect(() => { load(); }, [load]);

  const one = tests.find(t2 => String(t2.id) === a);
  const two = tests.find(t2 => String(t2.id) === b);

  return (
    <>
      <PageHeader title={t("compareTitle")} subtitle={t("compareSubtitle")} />
      <Card>
        <div className="compare-selects">
          <label>
            {t("selectTest1")}
            <select value={a} onChange={e => setA(e.target.value)}>
              <option value="">{t("selectTest1")}</option>
              {tests.map(t2 => (
                <option key={t2.id} value={t2.id}>
                  #{t2.id} — {t2.location || "Field"} ({formatDate(t2.created_at)})
                </option>
              ))}
            </select>
          </label>
          <span className="vs-label">VS</span>
          <label>
            {t("selectTest2")}
            <select value={b} onChange={e => setB(e.target.value)}>
              <option value="">{t("selectTest2")}</option>
              {tests.map(t2 => (
                <option key={t2.id} value={t2.id}>
                  #{t2.id} — {t2.location || "Field"} ({formatDate(t2.created_at)})
                </option>
              ))}
            </select>
          </label>
        </div>
        {loading && <p className="muted" style={{ marginTop: 12 }}>Loading tests…</p>}
        {!loading && tests.length < 2 && (
          <EmptyState
            icon={<GitCompare />}
            title="Not enough tests"
            text="You need at least two soil tests to compare. Create another test first."
          />
        )}
      </Card>

      {one && two ? (
        <Card>
          <div className="card-heading">
            <div>
              <h2>{t("difference")}</h2>
              <p>
                Test #{one.id} ({formatDate(one.created_at)})
                {" "} → {" "}
                Test #{two.id} ({formatDate(two.created_at)})
              </p>
            </div>
            <GitCompare />
          </div>

          {/* Health score comparison */}
          <div className="compare-row" style={{ fontWeight: 600, borderBottom: "2px solid var(--border)", marginBottom: 8, paddingBottom: 8 }}>
            <span>Health Score</span>
            <b>{one.health_score ?? "—"} / 100</b>
            <b>{two.health_score ?? "—"} / 100</b>
            <DeltaCell a={one.health_score} b={two.health_score} unit="" />
          </div>

          <div className="compare-grid">
            {SOIL_PARAMETERS.map(p => {
              const x = one.parameters?.[p.key as keyof typeof one.parameters];
              const y = two.parameters?.[p.key as keyof typeof two.parameters];
              return (
                <div className="compare-row" key={p.key}>
                  <span>{p.label}</span>
                  <b>{x != null ? `${x} ${p.unit}` : "—"}</b>
                  <b>{y != null ? `${y} ${p.unit}` : "—"}</b>
                  <DeltaCell a={x as number | undefined} b={y as number | undefined} unit={p.unit} />
                </div>
              );
            })}
          </div>
        </Card>
      ) : a && b && a === b ? (
        <Card>
          <div className="alert alert-warning">Select two different tests to compare.</div>
        </Card>
      ) : null}
    </>
  );
}
