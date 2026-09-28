import { useEffect, useState } from "react";
import { ArrowDown, ArrowUp, GitCompare } from "lucide-react";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/ui/Card";
import { useSoil } from "../../hooks/useSoil";
import { SOIL_PARAMETERS } from "../../constants/soilParameters";
import { useT } from "../../i18n/useT";

export default function CompareTests() {
  const { tests, load } = useSoil();
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
              {tests.map(t2 => <option key={t2.id} value={t2.id}>#{t2.id} — {t2.location || "Field"}</option>)}
            </select>
          </label>
          <span>VS</span>
          <label>
            {t("selectTest2")}
            <select value={b} onChange={e => setB(e.target.value)}>
              <option value="">{t("selectTest2")}</option>
              {tests.map(t2 => <option key={t2.id} value={t2.id}>#{t2.id} — {t2.location || "Field"}</option>)}
            </select>
          </label>
        </div>
      </Card>
      {one && two ? (
        <Card>
          <div className="card-heading">
            <div><h2>{t("difference")}</h2><p>{t("compareSubtitle")}</p></div>
            <GitCompare />
          </div>
          <div className="compare-grid">
            {SOIL_PARAMETERS.map(p => {
              const x = Number(one.parameters[p.key] ?? 0);
              const y = Number(two.parameters[p.key] ?? 0);
              const d = y - x;
              return (
                <div className="compare-row" key={p.key}>
                  <span>{p.label}</span>
                  <b>{x} {p.unit}</b>
                  <b>{y} {p.unit}</b>
                  <em className={d > 0 ? "up" : d < 0 ? "down" : ""}>
                    {d > 0 ? <ArrowUp /> : d < 0 ? <ArrowDown /> : "—"} {Math.abs(d).toFixed(2)}
                  </em>
                </div>
              );
            })}
          </div>
        </Card>
      ) : null}
    </>
  );
}
