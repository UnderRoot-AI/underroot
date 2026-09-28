import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Cpu, MapPin, RefreshCw, Save } from "lucide-react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import ErrorAlert from "../../components/common/ErrorAlert";
import { SOIL_PARAMETERS } from "../../constants/soilParameters";
import { useSoil } from "../../hooks/useSoil";
import { ROUTES } from "../../constants/routes";
import { hardwareApi, type HardwarePort } from "../../services/hardware.api";
import { useT } from "../../i18n/useT";

export default function SoilTest() {
  const navigate = useNavigate();
  const { create, loading, error } = useSoil();
  const t = useT();
  const [location, setLocation] = useState("");
  const [form, setForm] = useState<Record<string, string>>({});
  const [coords, setCoords] = useState({ latitude: "", longitude: "" });
  const [ports, setPorts] = useState<HardwarePort[]>([]);
  const [port, setPort] = useState("");
  const [hardwareError, setHardwareError] = useState("");
  const [reading, setReading] = useState(false);

  function setGeo() {
    navigator.geolocation?.getCurrentPosition(p =>
      setCoords({ latitude: String(p.coords.latitude), longitude: String(p.coords.longitude) })
    );
  }

  async function loadPorts() {
    setHardwareError("");
    try {
      const x = await hardwareApi.ports();
      setPorts(x.ports);
      if (!port && x.ports[0]) setPort(x.ports[0].device);
    } catch {
      setHardwareError(t("noHardwareConnected"));
    }
  }

  useEffect(() => { loadPorts(); }, []);

  async function readHardware() {
    if (!port) { setHardwareError(t("hardwareInstructions")); return; }
    setReading(true);
    setHardwareError("");
    try {
      const values = await hardwareApi.read(port);
      setForm(prev => ({ ...prev, ...Object.fromEntries(Object.entries(values).map(([k, v]) => [k, String(v)])) }));
    } catch (e: any) {
      setHardwareError(e.response?.data?.detail || "Hardware read failed.");
    } finally {
      setReading(false);
    }
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    try {
      const parameters = Object.fromEntries(
        Object.entries(form).filter(([k, v]) => k !== "notes" && v !== "").map(([k, v]) => [k, Number(v)])
      );
      const test = await create({
        location,
        latitude: coords.latitude ? Number(coords.latitude) : undefined,
        longitude: coords.longitude ? Number(coords.longitude) : undefined,
        parameters,
        notes: form.notes,
      });
      navigate(`${ROUTES.SOIL_ANALYZER}?test=${test.id}`);
    } catch { /* error already set by useSoil */ }
  }

  return (
    <>
      <PageHeader title={t("soilTestTitle")} subtitle={t("soilTestSubtitle")} />
      <form onSubmit={submit}>
        <Card>
          <div className="section-heading">
            <h2>{t("location")}</h2>
            <p>{t("soilTestSubtitle")}</p>
          </div>
          <div className="form-grid">
            <label>
              {t("location")}
              <input value={location} onChange={e => setLocation(e.target.value)} placeholder="e.g. North Field" />
            </label>
            <div className="geo-row">
              <label>Latitude<input value={coords.latitude} onChange={e => setCoords({ ...coords, latitude: e.target.value })} placeholder="23.15" /></label>
              <label>Longitude<input value={coords.longitude} onChange={e => setCoords({ ...coords, longitude: e.target.value })} placeholder="72.03" /></label>
              <button type="button" className="geo-btn" onClick={setGeo}><MapPin size={16} /> GPS</button>
            </div>
          </div>
        </Card>
        <Card>
          <div className="section-heading">
            <h2>{t("soilParameters")}</h2>
          </div>
          <div className="hardware-row">
            <select value={port} onChange={e => setPort(e.target.value)}>
              <option value="">{t("noHardwareConnected")}</option>
              {ports.map(p => <option key={p.device} value={p.device}>{p.device} — {p.description || "Serial device"}</option>)}
            </select>
            <button type="button" className="geo-btn" onClick={loadPorts}><RefreshCw size={15} /> {t("refresh")}</button>
            <Button type="button" loading={reading} onClick={readHardware}><Cpu size={16} /> {t("fetchingHardware")}</Button>
          </div>
          {hardwareError && <ErrorAlert message={hardwareError} />}
          <div className="parameter-input-grid">
            {SOIL_PARAMETERS.map(p => (
              <label key={p.key}>
                {p.label} {p.unit && <small>({p.unit})</small>}
                <input
                  type="number"
                  step="any"
                  min={p.min}
                  max={p.max}
                  value={form[p.key] || ""}
                  onChange={e => setForm({ ...form, [p.key]: e.target.value })}
                  placeholder={`0–${p.max}`}
                />
              </label>
            ))}
          </div>
          <label>
            Notes
            <textarea value={form.notes || ""} onChange={e => setForm({ ...form, notes: e.target.value })} placeholder="Notes…" />
          </label>
          <ErrorAlert message={error} />
          <div className="form-actions">
            <Button type="submit" loading={loading}><Save size={17} /> {t("save")}</Button>
          </div>
        </Card>
      </form>
    </>
  );
}
