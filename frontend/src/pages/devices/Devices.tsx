import { useState, useEffect, useCallback } from "react";
import {
  Cpu, Plus, Trash2, RefreshCw, Wifi, WifiOff, Clock, AlertCircle, ChevronDown, ChevronUp
} from "lucide-react";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Loading from "../../components/common/Loading";
import EmptyState from "../../components/common/EmptyState";
import { devicesApi } from "../../services/devices.api";
import type { Device, HardwareReading } from "../../types/hardware";
import { formatDate } from "../../utils/formatDate";

// ── Core parameter labels ─────────────────────────────────────────────────────
const PARAM_LABELS: Record<string, string> = {
  ph: "pH", ec: "EC", nitrogen: "N", phosphorus: "P", potassium: "K",
  moisture: "Moisture", temperature: "Temp", organic_carbon: "OC",
  sulphur: "S", zinc: "Zn", iron: "Fe", manganese: "Mn", copper: "Cu", boron: "B",
};

const CONNECTION_TYPE_LABELS: Record<string, string> = {
  http: "HTTP", mqtt: "MQTT", ble: "BLE", modbus: "Modbus",
  lorawan: "LoRaWAN", manual: "Manual", generic: "Generic",
};

const STATUS_COLOR: Record<string, string> = {
  online: "#22c55e", offline: "#ef4444", unknown: "#94a3b8",
};

// ── Sub-components ────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLOR[status] ?? "#94a3b8";
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 12,
      fontWeight: 600, color, background: `${color}18`, borderRadius: 99,
      padding: "2px 10px", border: `1px solid ${color}44` }}>
      {status === "online" ? <Wifi size={11} /> : <WifiOff size={11} />}
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

function MeasurementGrid({ measurements }: { measurements: Record<string, { value: number; unit: string }> }) {
  const entries = Object.entries(measurements);
  if (!entries.length) return <p style={{ fontSize: 13, color: "var(--text-muted)" }}>No measurements</p>;
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(80px, 1fr))", gap: 8, marginTop: 8 }}>
      {entries.map(([key, mv]) => (
        <div key={key} style={{ background: "var(--surface)", borderRadius: 8, padding: "8px 10px",
          border: "1px solid var(--border)", textAlign: "center" }}>
          <div style={{ fontSize: 10, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>
            {PARAM_LABELS[key] ?? key}
          </div>
          <div style={{ fontSize: 15, fontWeight: 700, color: "var(--text)", marginTop: 2 }}>
            {mv.value}
          </div>
          {mv.unit && <div style={{ fontSize: 9, color: "var(--text-muted)", marginTop: 1 }}>{mv.unit}</div>}
        </div>
      ))}
    </div>
  );
}

function DeviceCard({ device, onDelete }: { device: Device; onDelete: () => void }) {
  const [expanded, setExpanded] = useState(false);
  const [latestReading, setLatestReading] = useState<HardwareReading | null>(null);
  const [readingCount, setReadingCount] = useState<number>(0);
  const [loadingReading, setLoadingReading] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    let alive = true;
    setLoadingReading(true);
    Promise.all([
      devicesApi.getLatestReading(device.id).catch(() => null),
      devicesApi.listReadings(device.id, 1000).catch(() => []),
    ]).then(([latest, all]) => {
      if (!alive) return;
      setLatestReading(latest);
      setReadingCount(all.length);
    }).finally(() => { if (alive) setLoadingReading(false); });
    return () => { alive = false; };
  }, [device.id]);

  const handleDelete = async () => {
    if (!confirm(`Remove device "${device.name}"? This cannot be undone.`)) return;
    setDeleting(true);
    try { await devicesApi.deleteDevice(device.id); onDelete(); }
    catch { alert("Failed to remove device."); }
    finally { setDeleting(false); }
  };

  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, flexWrap: "wrap" }}>
        {/* Left: device info */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            <Cpu size={20} style={{ color: "var(--accent)", flexShrink: 0 }} />
            <strong style={{ fontSize: 16, color: "var(--text)" }}>{device.name}</strong>
            <StatusBadge status={device.status} />
            <span style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", background: "var(--surface)",
              border: "1px solid var(--border)", borderRadius: 99, padding: "2px 8px" }}>
              {CONNECTION_TYPE_LABELS[device.connection_type] ?? device.connection_type}
            </span>
          </div>
          <div style={{ marginTop: 8, display: "flex", gap: 20, flexWrap: "wrap" }}>
            {device.manufacturer && (
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                <b style={{ color: "var(--text)" }}>{device.manufacturer}</b>
                {device.model ? ` / ${device.model}` : ""}
              </span>
            )}
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
              ID: <code style={{ fontSize: 11, background: "var(--surface)", padding: "1px 6px", borderRadius: 4 }}>
                {device.device_id}
              </code>
            </span>
          </div>
          <div style={{ marginTop: 6, display: "flex", gap: 16, flexWrap: "wrap" }}>
            <span style={{ fontSize: 12, color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 4 }}>
              <Clock size={11} />
              {device.last_seen_at ? `Last seen: ${formatDate(device.last_seen_at)}` : "Never connected"}
            </span>
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
              {loadingReading ? "..." : `${readingCount} reading${readingCount !== 1 ? "s" : ""}`}
            </span>
          </div>
        </div>
        {/* Right: actions */}
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexShrink: 0 }}>
          <Button variant="ghost" onClick={() => setExpanded(e => !e)} style={{ padding: "6px 10px", fontSize: 12 }}>
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            {expanded ? "Hide" : "Latest"}
          </Button>
          <Button variant="danger" loading={deleting} onClick={handleDelete} style={{ padding: "6px 10px", fontSize: 12 }}>
            <Trash2 size={13} />
          </Button>
        </div>
      </div>

      {/* Latest reading panel */}
      {expanded && (
        <div style={{ marginTop: 16, borderTop: "1px solid var(--border)", paddingTop: 14 }}>
          <h4 style={{ fontSize: 13, color: "var(--text-muted)", fontWeight: 600, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Latest Measurements
          </h4>
          {loadingReading ? (
            <p style={{ fontSize: 13, color: "var(--text-muted)" }}>Loading...</p>
          ) : latestReading ? (
            <>
              <MeasurementGrid measurements={latestReading.measurements} />
              <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 8 }}>
                Recorded {formatDate(latestReading.created_at)}
                {latestReading.soil_test_id && (
                  <> · Soil test #{latestReading.soil_test_id} created</>
                )}
              </p>
            </>
          ) : (
            <p style={{ fontSize: 13, color: "var(--text-muted)" }}>No readings yet</p>
          )}
        </div>
      )}
    </Card>
  );
}

// ── Add device form ───────────────────────────────────────────────────────────

interface AddDeviceFormProps {
  onAdded: (device: Device) => void;
  onCancel: () => void;
}

const CONNECTION_TYPES = ["generic", "http", "ble", "mqtt", "modbus", "lorawan", "manual"];

function AddDeviceForm({ onAdded, onCancel }: AddDeviceFormProps) {
  const [form, setForm] = useState({
    name: "", device_id: "", manufacturer: "", model: "", connection_type: "generic",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!form.name.trim() || !form.device_id.trim()) {
      setError("Name and Device ID are required.");
      return;
    }
    setLoading(true);
    try {
      const device = await devicesApi.createDevice({
        name: form.name.trim(),
        device_id: form.device_id.trim(),
        manufacturer: form.manufacturer.trim() || undefined,
        model: form.model.trim() || undefined,
        connection_type: form.connection_type,
      });
      onAdded(device);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to register device.");
    } finally {
      setLoading(false);
    }
  };

  const field = (label: string, key: keyof typeof form, placeholder = "", required = false) => (
    <div style={{ marginBottom: 14 }}>
      <label style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", display: "block", marginBottom: 5 }}>
        {label}{required && " *"}
      </label>
      <input
        type="text"
        className="form-input"
        placeholder={placeholder}
        value={form[key]}
        onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
        required={required}
        style={{ width: "100%", boxSizing: "border-box" }}
      />
    </div>
  );

  return (
    <Card>
      <h3 style={{ marginBottom: 20, fontSize: 16, fontWeight: 700 }}>Register New Device</h3>
      <form onSubmit={handleSubmit}>
        {field("Device Name", "name", "e.g. Field-A Soil Sensor", true)}
        {field("Device ID", "device_id", "e.g. SOILX-001 or serial number", true)}
        {field("Manufacturer", "manufacturer", "e.g. REVE Nano-Science")}
        {field("Model", "model", "e.g. SoilX")}
        <div style={{ marginBottom: 14 }}>
          <label style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", display: "block", marginBottom: 5 }}>
            Connection Type
          </label>
          <select
            className="form-input"
            value={form.connection_type}
            onChange={e => setForm(f => ({ ...f, connection_type: e.target.value }))}
            style={{ width: "100%" }}
          >
            {CONNECTION_TYPES.map(t => (
              <option key={t} value={t}>{CONNECTION_TYPE_LABELS[t] ?? t}</option>
            ))}
          </select>
        </div>
        {/* SoilX note */}
        {(form.manufacturer.toLowerCase().includes("reve") || form.model.toLowerCase().includes("soilx")) && (
          <div style={{ background: "#3b82d418", border: "1px solid #3b82d444", borderRadius: 8,
            padding: "10px 14px", marginBottom: 14, fontSize: 12, color: "var(--text)" }}>
            <AlertCircle size={13} style={{ display: "inline", marginRight: 6, color: "#3b82d4" }} />
            <strong>Integration Ready</strong> — SoilX is a supported device profile.
            Send measurements via the HTTP ingestion endpoint once your device is connected.
          </div>
        )}
        {error && (
          <p style={{ color: "#ef4444", fontSize: 13, marginBottom: 12 }}>
            <AlertCircle size={12} style={{ display: "inline", marginRight: 4 }} />{error}
          </p>
        )}
        <div style={{ display: "flex", gap: 10 }}>
          <Button type="submit" loading={loading}>Register Device</Button>
          <Button type="button" variant="ghost" onClick={onCancel}>Cancel</Button>
        </div>
      </form>
    </Card>
  );
}

// ── Main Devices page ─────────────────────────────────────────────────────────

export default function Devices() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const loadDevices = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    else setRefreshing(true);
    try {
      const data = await devicesApi.listDevices();
      setDevices(data);
    } catch {
      // silently fail on refresh
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { loadDevices(); }, [loadDevices]);

  const handleAdded = (device: Device) => {
    setDevices(prev => [device, ...prev]);
    setShowForm(false);
  };

  const handleDeleted = (id: number) => {
    setDevices(prev => prev.filter(d => d.id !== id));
  };

  if (loading) return <Loading label="Loading devices..." />;

  return (
    <>
      <PageHeader
        title="Soil Devices"
        subtitle="Manage your connected soil-sensing hardware"
        action={
          <div style={{ display: "flex", gap: 10 }}>
            <Button variant="ghost" onClick={() => loadDevices(true)} loading={refreshing} style={{ padding: "8px 14px" }}>
              <RefreshCw size={14} /> Refresh
            </Button>
            {!showForm && (
              <Button onClick={() => setShowForm(true)}>
                <Plus size={17} /> Add Device
              </Button>
            )}
          </div>
        }
      />

      {showForm && (
        <div style={{ marginBottom: 24 }}>
          <AddDeviceForm onAdded={handleAdded} onCancel={() => setShowForm(false)} />
        </div>
      )}

      {devices.length === 0 && !showForm ? (
        <Card>
          <EmptyState
            icon={<Cpu size={36} style={{ color: "var(--text-muted)" }} />}
            title="No soil device connected yet"
            text="Register your first soil-sensing device to start receiving automated measurements and soil tests."
          />
          <div style={{ textAlign: "center", marginTop: 16 }}>
            <Button onClick={() => setShowForm(true)}><Plus size={17} /> Add Device</Button>
          </div>
        </Card>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {devices.map(device => (
            <DeviceCard
              key={device.id}
              device={device}
              onDelete={() => handleDeleted(device.id)}
            />
          ))}
        </div>
      )}

      {/* Architecture note */}
      <div style={{ marginTop: 24 }}>
      <Card>
        <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 10, color: "var(--text)" }}>
          <Cpu size={14} style={{ display: "inline", marginRight: 6, color: "var(--accent)" }} />
          Hardware Integration Architecture
        </h4>
        <div style={{ fontSize: 12, color: "var(--text-muted)", lineHeight: 1.7 }}>
          <p>UnderRoot is hardware-agnostic. Any device that can send HTTP POST requests can integrate automatically.</p>
          <p style={{ marginTop: 6 }}>
            <strong style={{ color: "var(--text)" }}>REVE Nano-Science SoilX</strong> —
            Register as a device above, then use an HTTP bridge to forward BLE readings to the ingestion endpoint.
            Direct BLE connectivity will be added once the official SoilX API is published.
          </p>
          <p style={{ marginTop: 6 }}>
            Ingestion endpoint: <code style={{ fontSize: 11, background: "var(--surface)", padding: "1px 6px", borderRadius: 4 }}>
              POST /api/devices/&#123;device_pk&#125;/readings
            </code>
          </p>
        </div>
      </Card>
      </div>
    </>
  );
}
