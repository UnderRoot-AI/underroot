import { useEffect, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import {
  LogOut, Plus, RefreshCw, Trash2, Pencil,
  Users, Activity, FlaskConical, BookOpen, BarChart2, TrendingUp,
  Cpu, FileText, Download, CheckCircle2, XCircle, Wifi, WifiOff,
  LayoutDashboard, Sprout, Smartphone,
} from "lucide-react";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/ui/Card";
import StatCard from "../../components/ui/StatCard";
import Button from "../../components/ui/Button";
import Loading from "../../components/common/Loading";
import {
  developerApi,
  type DeveloperStats,
  type DeveloperUser,
  type AdminSoilTest,
  type AdminDevice,
  type AdminReport,
  type Scheme,
  type SchemePayload,
} from "../../services/developer.api";
import { ROUTES } from "../../constants/routes";
import { useT } from "../../i18n/useT";

// ─── Tiny SVG bar chart (login buckets) ───────────────────────────────────
function BarChart({
  data,
  labels,
  color = "#166534",
  height = 80,
}: {
  data: number[];
  labels: string[];
  color?: string;
  height?: number;
}) {
  const max = Math.max(...data, 1);
  const W = 100;
  const barW = W / data.length - 2;
  return (
    <svg viewBox={`0 0 ${W * data.length} ${height + 20}`} style={{ width: "100%", height: height + 20 }}>
      {data.map((v, i) => {
        const bh = (v / max) * height;
        const x = i * (W + 2) + 1;
        const y = height - bh;
        return (
          <g key={i}>
            <rect x={x} y={y} width={barW} height={bh} rx={3} fill={color} opacity={0.85} />
            <text x={x + barW / 2} y={height + 15} textAnchor="middle" fontSize={9} fill="#859188">{labels[i]}</text>
            <text x={x + barW / 2} y={y - 3} textAnchor="middle" fontSize={9} fill={color} fontWeight={700}>{v}</text>
          </g>
        );
      })}
    </svg>
  );
}

// ─── Donut chart ──────────────────────────────────────────────────────────
function DonutChart({
  value,
  total,
  color = "#166534",
  size = 80,
  label,
}: {
  value: number;
  total: number;
  color?: string;
  size?: number;
  label: string;
}) {
  const r = 32;
  const circ = 2 * Math.PI * r;
  const pct = total > 0 ? value / total : 0;
  const dash = pct * circ;
  return (
    <div style={{ textAlign: "center", flex: 1 }}>
      <svg viewBox="0 0 80 80" style={{ width: size, height: size }}>
        <circle cx={40} cy={40} r={r} fill="none" stroke="#edf1ed" strokeWidth={9} />
        <circle cx={40} cy={40} r={r} fill="none" stroke={color} strokeWidth={9}
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round" transform="rotate(-90 40 40)" />
        <text x={40} y={44} textAnchor="middle" fontSize={12} fontWeight={700} fill={color}>
          {Math.round(pct * 100)}%
        </text>
      </svg>
      <div style={{ fontSize: 10, color: "#859188", marginTop: 3 }}>{label}</div>
      <div style={{ fontSize: 12, fontWeight: 700 }}>{value} / {total}</div>
    </div>
  );
}

// ─── Horizontal bar (distribution) ───────────────────────────────────────
function HorizBar({ label, value, max, color = "#166534" }: { label: string; value: number; max: number; color?: string }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 3 }}>
        <span>{label}</span><b>{value}</b>
      </div>
      <div style={{ background: "#edf1ed", borderRadius: 5, height: 6 }}>
        <div style={{ width: `${pct}%`, height: 6, background: color, borderRadius: 5, transition: ".3s" }} />
      </div>
    </div>
  );
}

// ─── Status badge ─────────────────────────────────────────────────────────
function StatusBadge({ value, map }: { value: string; map: Record<string, string> }) {
  const cls = map[value] ?? "badge-blue";
  return <span className={`badge ${cls}`}>{value}</span>;
}

const HEALTH_BADGE: Record<string, string> = {
  Excellent: "badge-green", Good: "badge-green",
  Fair: "badge-yellow", Poor: "badge-red", Critical: "badge-red", Unknown: "badge-blue",
};
const STATUS_BADGE: Record<string, string> = {
  online: "badge-green", offline: "badge-yellow", unknown: "badge-blue",
};
const REPORT_BADGE: Record<string, string> = {
  verified: "badge-green", generated: "badge-green", uploaded: "badge-blue",
};

const COLORS = ["#166534", "#2563eb", "#d97706", "#7c3aed", "#0891b2", "#dc2626"];

// ─── Tab definitions ──────────────────────────────────────────────────────
type Tab = "dashboard" | "users" | "soil-tests" | "devices" | "reports" | "schemes";

const TABS: { id: Tab; label: string; icon: ReactNode }[] = [
  { id: "dashboard",  label: "Dashboard",   icon: <LayoutDashboard size={15} /> },
  { id: "users",      label: "Users",       icon: <Users size={15} /> },
  { id: "soil-tests", label: "Soil Tests",  icon: <Sprout size={15} /> },
  { id: "devices",    label: "Devices",     icon: <Smartphone size={15} /> },
  { id: "reports",    label: "Reports",     icon: <FileText size={15} /> },
  { id: "schemes",    label: "Schemes",     icon: <BookOpen size={15} /> },
];

const emptyScheme: SchemePayload = { name: "", state: "", description: "", url: "", active: true };

// ─── Main component ───────────────────────────────────────────────────────
export default function DeveloperDashboard() {
  const navigate = useNavigate();
  const t = useT();

  const [tab, setTab] = useState<Tab>("dashboard");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // data
  const [stats, setStats] = useState<DeveloperStats | null>(null);
  const [users, setUsers] = useState<DeveloperUser[]>([]);
  const [soilTests, setSoilTests] = useState<AdminSoilTest[]>([]);
  const [soilTestsTotal, setSoilTestsTotal] = useState(0);
  const [devices, setDevices] = useState<AdminDevice[]>([]);
  const [devicesTotal, setDevicesTotal] = useState(0);
  const [reports, setReports] = useState<AdminReport[]>([]);
  const [reportsTotal, setReportsTotal] = useState(0);
  const [schemes, setSchemes] = useState<Scheme[]>([]);

  // scheme form
  const [schemeForm, setSchemeForm] = useState<SchemePayload>(emptyScheme);
  const [editingSchemeId, setEditingSchemeId] = useState<number | null>(null);
  const [showSchemeForm, setShowSchemeForm] = useState(false);
  const [schemeMsg, setSchemeMsg] = useState("");

  // user search
  const [userSearch, setUserSearch] = useState("");
  // soil test search
  const [testSearch, setTestSearch] = useState("");
  // device search
  const [deviceSearch, setDeviceSearch] = useState("");
  // report search
  const [reportSearch, setReportSearch] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [s, u, sc] = await Promise.all([
        developerApi.stats(),
        developerApi.users(),
        developerApi.schemes(),
      ]);
      setStats(s);
      setUsers(u);
      setSchemes(sc);

      const [st, dv, rp] = await Promise.all([
        developerApi.soilTests(),
        developerApi.devices(),
        developerApi.reports(),
      ]);
      setSoilTests(st.items);
      setSoilTestsTotal(st.total);
      setDevices(dv.items);
      setDevicesTotal(dv.total);
      setReports(rp.items);
      setReportsTotal(rp.total);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to load admin data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  function logout() {
    localStorage.removeItem("developer_token");
    location.href = ROUTES.DEVELOPER_LOGIN;
  }

  // ── Scheme actions ───────────────────────────────────────────────────────
  function startEditScheme(s: Scheme) {
    setEditingSchemeId(s.id);
    setSchemeForm({ name: s.name, state: s.state || "", description: s.description, url: s.url, active: s.active });
    setShowSchemeForm(true);
  }

  async function saveScheme() {
    setSchemeMsg("");
    try {
      if (editingSchemeId) await developerApi.updateScheme(editingSchemeId, schemeForm);
      else await developerApi.createScheme(schemeForm);
      setSchemeForm(emptyScheme);
      setEditingSchemeId(null);
      setShowSchemeForm(false);
      const sc = await developerApi.schemes();
      setSchemes(sc);
      setSchemeMsg(t("schemeSaved"));
    } catch (e: any) {
      setSchemeMsg(e.response?.data?.detail || "Could not save scheme.");
    }
  }

  async function removeScheme(id: number) {
    if (!confirm(t("removeSchemeConfirm"))) return;
    await developerApi.deleteScheme(id);
    setSchemes(await developerApi.schemes());
  }

  async function downloadCsv() {
    const blob = await developerApi.usersCsv();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "smart-soil-users-by-location.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  // ── Filtered lists ────────────────────────────────────────────────────────
  const filteredUsers = users.filter(u => {
    const q = userSearch.toLowerCase();
    return !q || u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
      || (u.state || "").toLowerCase().includes(q);
  });

  const filteredTests = soilTests.filter(t => {
    const q = testSearch.toLowerCase();
    return !q || t.user_name.toLowerCase().includes(q) || (t.location || "").toLowerCase().includes(q)
      || t.health_status.toLowerCase().includes(q) || t.source.toLowerCase().includes(q);
  });

  const filteredDevices = devices.filter(d => {
    const q = deviceSearch.toLowerCase();
    return !q || d.name.toLowerCase().includes(q) || d.owner_name.toLowerCase().includes(q)
      || d.device_id.toLowerCase().includes(q) || (d.model || "").toLowerCase().includes(q);
  });

  const filteredReports = reports.filter(r => {
    const q = reportSearch.toLowerCase();
    return !q || r.owner_name.toLowerCase().includes(q) || r.status.toLowerCase().includes(q)
      || (r.file_name || "").toLowerCase().includes(q);
  });

  // ── Derived chart data ────────────────────────────────────────────────────
  const stateCounts: Record<string, number> = {};
  users.forEach(u => { const k = u.state || "Unknown"; stateCounts[k] = (stateCounts[k] || 0) + 1; });
  const stateEntries = Object.entries(stateCounts).sort((a, b) => b[1] - a[1]).slice(0, 6);
  const maxStateCount = stateEntries[0]?.[1] || 1;

  const loginBuckets = [
    { label: "0", count: users.filter(u => u.login_count === 0).length },
    { label: "1–5", count: users.filter(u => u.login_count >= 1 && u.login_count <= 5).length },
    { label: "6–20", count: users.filter(u => u.login_count >= 6 && u.login_count <= 20).length },
    { label: "21–50", count: users.filter(u => u.login_count >= 21 && u.login_count <= 50).length },
    { label: "50+", count: users.filter(u => u.login_count > 50).length },
  ];

  const activeSchemes = schemes.filter(s => s.active).length;
  const hiddenSchemes = schemes.length - activeSchemes;

  function fmtDate(d: string | undefined | null) {
    if (!d) return "—";
    return new Date(d).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
  }

  function fmtDateTime(d: string | undefined | null) {
    if (!d) return "—";
    return new Date(d).toLocaleString("en-IN", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
  }

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="page-content">
      <PageHeader
        title={t("devDashTitle")}
        subtitle={t("devDashSubtitle")}
        action={
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn btn-secondary" onClick={load} disabled={loading}>
              <RefreshCw size={14} /> {t("refresh")}
            </button>
            <button className="btn btn-danger" onClick={logout}>
              <LogOut size={14} /> {t("logout")}
            </button>
          </div>
        }
      />

      {/* ── Tab navigation ── */}
      <div className="admin-tabs">
        {TABS.map(tb => (
          <button
            key={tb.id}
            className={`admin-tab${tab === tb.id ? " admin-tab--active" : ""}`}
            onClick={() => setTab(tb.id)}
          >
            {tb.icon} {tb.label}
          </button>
        ))}
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {loading && <Loading />}

      {!loading && (
        <>
          {/* ══════════════════════════ DASHBOARD ══════════════════════════ */}
          {tab === "dashboard" && (
            <>
              <div className="stats-grid" style={{ gridTemplateColumns: "repeat(4,1fr)" }}>
                <StatCard label="Total Users" value={stats?.total_users ?? "—"} helper="All accounts" icon={<Users size={17} />} />
                <StatCard label="Verified" value={stats?.verified_users ?? "—"} helper="Email confirmed" icon={<CheckCircle2 size={17} />} />
                <StatCard label="Unverified" value={stats?.unverified_users ?? "—"} helper="Not yet confirmed" icon={<XCircle size={17} />} />
                <StatCard label="Active Logins" value={stats?.logged_in_users ?? "—"} helper="Have ever logged in" icon={<Activity size={17} />} />
              </div>
              <div className="stats-grid" style={{ gridTemplateColumns: "repeat(4,1fr)" }}>
                <StatCard label="Total Soil Tests" value={stats?.total_soil_tests ?? "—"} helper="All saved tests" icon={<FlaskConical size={17} />} />
                <StatCard label="Active Devices" value={stats?.total_devices ?? "—"} helper="Registered & active" icon={<Cpu size={17} />} />
                <StatCard label="Reports" value={stats?.total_reports ?? "—"} helper="Generated & uploaded" icon={<FileText size={17} />} />
                <StatCard label="Active Schemes" value={stats?.active_schemes ?? "—"} helper="Visible to farmers" icon={<BookOpen size={17} />} />
              </div>

              {/* Charts row */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, marginBottom: 20 }}>
                <Card>
                  <div style={{ marginBottom: 10 }}>
                    <h2 style={{ margin: "0 0 2px", fontSize: 13 }}>{t("loginActivity")}</h2>
                    <p style={{ margin: 0, color: "var(--muted)", fontSize: 11 }}>{t("loginActivityDesc")}</p>
                  </div>
                  {users.length
                    ? <BarChart data={loginBuckets.map(b => b.count)} labels={loginBuckets.map(b => b.label)} />
                    : <div style={{ textAlign: "center", padding: "20px 0", color: "var(--muted)", fontSize: 11 }}>No data</div>}
                </Card>

                <Card>
                  <div style={{ marginBottom: 10 }}>
                    <h2 style={{ margin: "0 0 2px", fontSize: 13 }}>{t("userEngagement")}</h2>
                    <p style={{ margin: 0, color: "var(--muted)", fontSize: 11 }}>{t("userEngagementDesc")}</p>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-around", paddingTop: 6 }}>
                    <DonutChart value={stats?.verified_users ?? 0} total={stats?.total_users ?? 0} color="#166534" label="Verified" />
                    <DonutChart value={stats?.logged_in_users ?? 0} total={stats?.total_users ?? 0} color="#2563eb" label={t("loggedIn")} />
                  </div>
                </Card>

                <Card>
                  <div style={{ marginBottom: 10 }}>
                    <h2 style={{ margin: "0 0 2px", fontSize: 13 }}>{t("schemeStatus")}</h2>
                    <p style={{ margin: 0, color: "var(--muted)", fontSize: 11 }}>{t("schemeStatusDesc")}</p>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-around", paddingTop: 6 }}>
                    <DonutChart value={activeSchemes} total={schemes.length || 1} color="#166534" label={t("activeLabel")} />
                    <DonutChart value={hiddenSchemes} total={schemes.length || 1} color="#d97706" label={t("hiddenLabel")} />
                  </div>
                </Card>
              </div>

              {stateEntries.length > 0 && (
                <Card>
                  <div className="card-heading">
                    <div>
                      <h2>{t("userDistribution")}</h2>
                      <p>{t("userDistributionDesc")}</p>
                    </div>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 40px" }}>
                    {stateEntries.map(([state, count], i) => (
                      <HorizBar key={state} label={state} value={count} max={maxStateCount} color={COLORS[i % COLORS.length]} />
                    ))}
                  </div>
                </Card>
              )}
            </>
          )}

          {/* ══════════════════════════ USERS ══════════════════════════════ */}
          {tab === "users" && (
            <Card>
              <div className="card-heading">
                <div>
                  <h2>{t("userListTitle")}</h2>
                  <p>{users.length} users registered</p>
                </div>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <input
                    className="admin-search"
                    placeholder="Search name, email or state…"
                    value={userSearch}
                    onChange={e => setUserSearch(e.target.value)}
                  />
                  <Button onClick={downloadCsv} variant="secondary">
                    <Download size={15} /> {t("downloadUserList")}
                  </Button>
                </div>
              </div>
              {filteredUsers.length === 0 ? (
                <p className="muted">{t("noUsersYet")}</p>
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>State</th>
                        <th>District</th>
                        <th>Verified</th>
                        <th>Logins</th>
                        <th>Registered</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredUsers.map(u => (
                        <tr key={u.id}>
                          <td><b style={{ fontSize: 12 }}>{u.name}</b></td>
                          <td style={{ color: "var(--muted)", fontSize: 11 }}>{u.email}</td>
                          <td>{u.state || "—"}</td>
                          <td>{u.district || "—"}</td>
                          <td>
                            {u.email_verified
                              ? <span className="badge badge-green">Verified</span>
                              : <span className="badge badge-yellow">Unverified</span>}
                          </td>
                          <td style={{ textAlign: "center" }}>{u.login_count}</td>
                          <td style={{ color: "var(--muted)", fontSize: 11, whiteSpace: "nowrap" }}>{fmtDate(u.created_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          )}

          {/* ══════════════════════════ SOIL TESTS ═════════════════════════ */}
          {tab === "soil-tests" && (
            <Card>
              <div className="card-heading">
                <div>
                  <h2>Soil Tests</h2>
                  <p>{soilTestsTotal} total — showing {soilTests.length}</p>
                </div>
                <input
                  className="admin-search"
                  placeholder="Search user, location or status…"
                  value={testSearch}
                  onChange={e => setTestSearch(e.target.value)}
                />
              </div>
              {filteredTests.length === 0 ? (
                <div className="empty-state">
                  <p>No soil tests yet.</p>
                </div>
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>User</th>
                        <th>Location</th>
                        <th>Source</th>
                        <th>pH</th>
                        <th>N (kg/ha)</th>
                        <th>Health</th>
                        <th>Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredTests.map(st => (
                        <tr key={st.id}>
                          <td style={{ color: "var(--muted)", fontSize: 11 }}>{st.id}</td>
                          <td><b style={{ fontSize: 12 }}>{st.user_name}</b></td>
                          <td style={{ color: "var(--muted)", fontSize: 11 }}>{st.location || "—"}</td>
                          <td><span className="badge badge-blue">{st.source}</span></td>
                          <td>{st.ph != null ? st.ph.toFixed(1) : "—"}</td>
                          <td>{st.nitrogen != null ? st.nitrogen.toFixed(0) : "—"}</td>
                          <td>
                            <StatusBadge value={st.health_status} map={HEALTH_BADGE} />
                            <span style={{ marginLeft: 5, fontSize: 10, color: "var(--muted)" }}>{st.health_score.toFixed(0)}</span>
                          </td>
                          <td style={{ color: "var(--muted)", fontSize: 11, whiteSpace: "nowrap" }}>{fmtDate(st.created_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          )}

          {/* ══════════════════════════ DEVICES ════════════════════════════ */}
          {tab === "devices" && (
            <Card>
              <div className="card-heading">
                <div>
                  <h2>Registered Devices</h2>
                  <p>{devicesTotal} active device{devicesTotal !== 1 ? "s" : ""}</p>
                </div>
                <input
                  className="admin-search"
                  placeholder="Search name, owner or device ID…"
                  value={deviceSearch}
                  onChange={e => setDeviceSearch(e.target.value)}
                />
              </div>
              {filteredDevices.length === 0 ? (
                <div className="empty-state">
                  <p>No devices registered.</p>
                </div>
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Device Name</th>
                        <th>Device ID</th>
                        <th>Model</th>
                        <th>Connection</th>
                        <th>Owner</th>
                        <th>Status</th>
                        <th>Readings</th>
                        <th>Last Seen</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredDevices.map(d => (
                        <tr key={d.id}>
                          <td><b style={{ fontSize: 12 }}>{d.name}</b></td>
                          <td style={{ color: "var(--muted)", fontSize: 11, fontFamily: "monospace" }}>{d.device_id}</td>
                          <td style={{ fontSize: 11 }}>{[d.manufacturer, d.model].filter(Boolean).join(" ") || "—"}</td>
                          <td><span className="badge badge-blue">{d.connection_type}</span></td>
                          <td>{d.owner_name}</td>
                          <td><StatusBadge value={d.status} map={STATUS_BADGE} /></td>
                          <td style={{ textAlign: "center" }}>{d.reading_count}</td>
                          <td style={{ color: "var(--muted)", fontSize: 11, whiteSpace: "nowrap" }}>{fmtDateTime(d.last_seen_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          )}

          {/* ══════════════════════════ REPORTS ════════════════════════════ */}
          {tab === "reports" && (
            <Card>
              <div className="card-heading">
                <div>
                  <h2>Reports</h2>
                  <p>{reportsTotal} total — showing {reports.length}</p>
                </div>
                <input
                  className="admin-search"
                  placeholder="Search owner, filename or status…"
                  value={reportSearch}
                  onChange={e => setReportSearch(e.target.value)}
                />
              </div>
              {filteredReports.length === 0 ? (
                <div className="empty-state">
                  <p>No reports yet.</p>
                </div>
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Owner</th>
                        <th>File</th>
                        <th>Soil Test</th>
                        <th>Status</th>
                        <th>Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredReports.map(r => (
                        <tr key={r.id}>
                          <td style={{ color: "var(--muted)", fontSize: 11 }}>{r.id}</td>
                          <td><b style={{ fontSize: 12 }}>{r.owner_name}</b></td>
                          <td style={{ color: "var(--muted)", fontSize: 11 }}>{r.file_name || "—"}</td>
                          <td style={{ color: "var(--muted)", fontSize: 11 }}>{r.soil_test_id ?? "—"}</td>
                          <td><StatusBadge value={r.status} map={REPORT_BADGE} /></td>
                          <td style={{ color: "var(--muted)", fontSize: 11, whiteSpace: "nowrap" }}>{fmtDate(r.created_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          )}

          {/* ══════════════════════════ SCHEMES ════════════════════════════ */}
          {tab === "schemes" && (
            <Card>
              <div className="card-heading">
                <div>
                  <h2>{t("govSchemesTitle")}</h2>
                  <p>{t("govSchemesDesc")}</p>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <Button onClick={() => navigate(ROUTES.DEVELOPER_ADD_SCHEME)}>
                    <Plus size={14} /> {t("addNewScheme")}
                  </Button>
                </div>
              </div>

              {schemeMsg && (
                <div className={`alert ${schemeMsg.startsWith("Could") ? "alert-error" : "alert-success"}`}>
                  {schemeMsg}
                </div>
              )}

              {showSchemeForm && (
                <div className="admin-scheme-form">
                  <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 14 }}>
                    {editingSchemeId ? t("editScheme") : t("quickAddScheme")}
                  </div>
                  <div className="form-grid">
                    <label>{t("schemeNameLabel")}<input value={schemeForm.name} onChange={e => setSchemeForm({ ...schemeForm, name: e.target.value })} /></label>
                    <label>{t("schemeStateLabel")}<input value={schemeForm.state || ""} onChange={e => setSchemeForm({ ...schemeForm, state: e.target.value })} /></label>
                    <label>{t("schemeUrlLabel")}<input value={schemeForm.url} onChange={e => setSchemeForm({ ...schemeForm, url: e.target.value })} /></label>
                    <label>{t("schemeActiveLabel")}
                      <select value={schemeForm.active ? "yes" : "no"} onChange={e => setSchemeForm({ ...schemeForm, active: e.target.value === "yes" })}>
                        <option value="yes">{t("visibleToUsersOption")}</option>
                        <option value="no">{t("hiddenOption")}</option>
                      </select>
                    </label>
                  </div>
                  <label style={{ display: "flex", flexDirection: "column", gap: 7, fontSize: 11, fontWeight: 700, color: "#4e5d53", marginTop: 12 }}>
                    {t("descriptionLabel")}
                    <textarea value={schemeForm.description} onChange={e => setSchemeForm({ ...schemeForm, description: e.target.value })} />
                  </label>
                  <div className="form-actions">
                    <button className="btn btn-secondary" onClick={() => { setEditingSchemeId(null); setSchemeForm(emptyScheme); setShowSchemeForm(false); }}>
                      {t("cancel")}
                    </button>
                    <Button onClick={saveScheme}>
                      {editingSchemeId ? <><Pencil size={14} /> {t("updateScheme")}</> : <><Plus size={14} /> {t("saveScheme")}</>}
                    </Button>
                  </div>
                </div>
              )}

              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>{t("schemeCol")}</th>
                      <th>{t("stateColLabel")}</th>
                      <th>{t("statusCol")}</th>
                      <th>{t("updatedCol")}</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {schemes.length === 0 && (
                      <tr><td colSpan={5} style={{ textAlign: "center", color: "var(--muted)", padding: 24 }}>{t("noSchemesYet")}</td></tr>
                    )}
                    {schemes.map(s => (
                      <tr key={s.id}>
                        <td>
                          <b>{s.name}</b>
                          <div className="muted">{s.description?.slice(0, 80)}{(s.description?.length ?? 0) > 80 ? "…" : ""}</div>
                        </td>
                        <td>{s.state || t("allIndia")}</td>
                        <td>
                          <span className={`badge ${s.active ? "badge-green" : "badge-yellow"}`}>
                            {s.active ? t("activeLabel") : t("hiddenLabel")}
                          </span>
                        </td>
                        <td style={{ color: "var(--muted)", fontSize: 11 }}>{fmtDate(s.updated_at)}</td>
                        <td style={{ whiteSpace: "nowrap" }}>
                          <button className="icon-btn" title={t("edit")} onClick={() => startEditScheme(s)}><Pencil size={15} /></button>
                          <button className="icon-btn" title={t("delete")} onClick={() => removeScheme(s.id)}><Trash2 size={15} /></button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
