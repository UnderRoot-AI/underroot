import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Download, LogOut, Plus, RefreshCw, Trash2, Pencil,
  Users, Activity, FlaskConical, BookOpen, BarChart2, TrendingUp,
} from "lucide-react";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/ui/Card";
import StatCard from "../../components/ui/StatCard";
import Button from "../../components/ui/Button";
import {
  developerApi,
  type DeveloperStats,
  type DeveloperUser,
  type Scheme,
  type SchemePayload,
} from "../../services/developer.api";
import { ROUTES } from "../../constants/routes";
import { useT } from "../../i18n/useT";

// ─── tiny SVG bar chart ────────────────────────────────────────────────────
function BarChart({
  data,
  labels,
  color = "#166534",
  height = 90,
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
            <rect x={x} y={y} width={barW} height={bh} rx={4} fill={color} opacity={0.85} />
            <text x={x + barW / 2} y={height + 15} textAnchor="middle" fontSize={9} fill="#859188">
              {labels[i]}
            </text>
            <text x={x + barW / 2} y={y - 3} textAnchor="middle" fontSize={9} fill={color} fontWeight={700}>
              {v}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// ─── tiny SVG donut ────────────────────────────────────────────────────────
function DonutChart({
  value,
  total,
  color = "#166534",
  size = 90,
  label,
}: {
  value: number;
  total: number;
  color?: string;
  size?: number;
  label: string;
}) {
  const r = 36;
  const circ = 2 * Math.PI * r;
  const pct = total > 0 ? value / total : 0;
  const dash = pct * circ;
  return (
    <div style={{ textAlign: "center", flex: 1 }}>
      <svg viewBox="0 0 90 90" style={{ width: size, height: size }}>
        <circle cx={45} cy={45} r={r} fill="none" stroke="#edf1ed" strokeWidth={10} />
        <circle
          cx={45} cy={45} r={r} fill="none"
          stroke={color} strokeWidth={10}
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
          transform="rotate(-90 45 45)"
        />
        <text x={45} y={48} textAnchor="middle" fontSize={13} fontWeight={700} fill={color}>
          {Math.round(pct * 100)}%
        </text>
      </svg>
      <div style={{ fontSize: 10, color: "#859188", marginTop: 4 }}>{label}</div>
      <div style={{ fontSize: 13, fontWeight: 700 }}>{value} / {total}</div>
    </div>
  );
}

// ─── horizontal bar (state distribution) ─────────────────────────────────
function HorizBar({ label, value, max, color = "#166534" }: { label: string; value: number; max: number; color?: string }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 4 }}>
        <span>{label}</span><b>{value}</b>
      </div>
      <div style={{ background: "#edf1ed", borderRadius: 6, height: 7 }}>
        <div style={{ width: `${pct}%`, height: 7, background: color, borderRadius: 6, transition: ".3s" }} />
      </div>
    </div>
  );
}

// ─── colour palette for multiple series ───────────────────────────────────
const COLORS = ["#166534", "#2563eb", "#d97706", "#7c3aed", "#0891b2", "#dc2626"];

const empty: SchemePayload = { name: "", state: "", description: "", url: "", active: true };

export default function DeveloperDashboard() {
  const navigate = useNavigate();
  const t = useT();
  const [stats, setStats] = useState<DeveloperStats | null>(null);
  const [users, setUsers] = useState<DeveloperUser[]>([]);
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [form, setForm] = useState<SchemePayload>(empty);
  const [editing, setEditing] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [showForm, setShowForm] = useState(false);

  async function load() {
    const [a, b, c] = await Promise.all([developerApi.stats(), developerApi.users(), developerApi.schemes()]);
    setStats(a); setUsers(b); setSchemes(c);
  }
  useEffect(() => { load().catch(() => {}); }, []);

  function edit(x: Scheme) {
    setEditing(x.id);
    setForm({ name: x.name, state: x.state || "", description: x.description, url: x.url, active: x.active });
    setShowForm(true);
    window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
  }
  async function save() {
    setMessage("");
    try {
      if (editing) await developerApi.updateScheme(editing, form);
      else await developerApi.createScheme(form);
      setForm(empty); setEditing(null); setShowForm(false);
      await load();
      setMessage("Government scheme saved.");
    } catch (e: any) { setMessage(e.response?.data?.detail || "Could not save scheme."); }
  }
  async function remove(id: number) {
    if (!confirm("Remove this government scheme from the platform?")) return;
    await developerApi.deleteScheme(id); await load();
  }
  async function download() {
    const blob = await developerApi.usersCsv();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "smart-soil-users-by-location.csv"; a.click();
    URL.revokeObjectURL(url);
  }
  function logout() { localStorage.removeItem("developer_token"); location.href = ROUTES.DEVELOPER_LOGIN; }

  // ── derived chart data ─────────────────────────────────────────────────
  const stateCounts: Record<string, number> = {};
  users.forEach(u => { const k = u.state || "Unknown"; stateCounts[k] = (stateCounts[k] || 0) + 1; });
  const stateEntries = Object.entries(stateCounts).sort((a, b) => b[1] - a[1]).slice(0, 6);
  const maxStateCount = stateEntries[0]?.[1] || 1;

  // login activity: bucket users by login_count ranges
  const loginBuckets = [
    { label: "0", count: users.filter(u => u.login_count === 0).length },
    { label: "1–5", count: users.filter(u => u.login_count >= 1 && u.login_count <= 5).length },
    { label: "6–20", count: users.filter(u => u.login_count >= 6 && u.login_count <= 20).length },
    { label: "21–50", count: users.filter(u => u.login_count >= 21 && u.login_count <= 50).length },
    { label: "50+", count: users.filter(u => u.login_count > 50).length },
  ];

  // scheme activity: active vs hidden
  const activeSchemes = schemes.filter(s => s.active).length;
  const hiddenSchemes = schemes.length - activeSchemes;

  return (
    <div className="page-content">
      <PageHeader
        title={t("devDashTitle")}
        subtitle={t("devDashSubtitle")}
        action={
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn btn-secondary" onClick={() => load()}>
              <RefreshCw size={15} /> {t("refresh")}
            </button>
            <button className="btn btn-danger" onClick={logout}>
              <LogOut size={15} /> {t("logout")}
            </button>
          </div>
        }
      />

      <div className="stats-grid">
        <StatCard label={t("registeredUsers")} value={stats?.total_users ?? "—"} helper={t("allAccounts")} icon={<Users size={18} />} />
        <StatCard label={t("usersLoggedIn")} value={stats?.logged_in_users ?? "—"} helper={t("atLeastOneLogin")} icon={<Activity size={18} />} />
        <StatCard label={t("totalLoginsLabel")} value={stats?.total_logins ?? "—"} helper={t("recordedSessions")} icon={<TrendingUp size={18} />} />
      </div>
      <div className="stats-grid">
        <StatCard label={t("soilTestsSaved")} value={stats?.total_soil_tests ?? "—"} helper={t("allSavedTests")} icon={<FlaskConical size={18} />} />
        <StatCard label={t("activeSchemesLabel")} value={stats?.active_schemes ?? "—"} helper={t("visibleToFarmers")} icon={<BookOpen size={18} />} />
        <StatCard label={t("totalSchemesLabel")} value={schemes.length || "—"} helper={t("activeAndHidden")} icon={<BarChart2 size={18} />} />
      </div>

      {/* ── Charts row ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, marginBottom: 20 }}>
        <Card>
          <div style={{ marginBottom: 12 }}>
            <h2 style={{ margin: "0 0 3px", fontSize: 14 }}>{t("loginActivity")}</h2>
            <p style={{ margin: 0, color: "var(--muted)", fontSize: 11 }}>{t("loginActivityDesc")}</p>
          </div>
          {users.length ? (
            <BarChart data={loginBuckets.map(b => b.count)} labels={loginBuckets.map(b => b.label)} color="#166534" />
          ) : (
            <div style={{ textAlign: "center", padding: "30px 0", color: "var(--muted)", fontSize: 11 }}>{t("noData")}</div>
          )}
        </Card>

        <Card>
          <div style={{ marginBottom: 12 }}>
            <h2 style={{ margin: "0 0 3px", fontSize: 14 }}>{t("userEngagement")}</h2>
            <p style={{ margin: 0, color: "var(--muted)", fontSize: 11 }}>{t("userEngagementDesc")}</p>
          </div>
          <div style={{ display: "flex", justifyContent: "space-around", alignItems: "center", paddingTop: 8 }}>
            <DonutChart value={stats?.logged_in_users ?? 0} total={stats?.total_users ?? 0} color="#166534" label={t("loggedIn")} />
            <DonutChart value={stats?.total_soil_tests ?? 0} total={stats?.total_users ?? 0} color="#2563eb" label={t("ranSoilTest")} />
          </div>
        </Card>

        <Card>
          <div style={{ marginBottom: 12 }}>
            <h2 style={{ margin: "0 0 3px", fontSize: 14 }}>{t("schemeStatus")}</h2>
            <p style={{ margin: 0, color: "var(--muted)", fontSize: 11 }}>{t("schemeStatusDesc")}</p>
          </div>
          <div style={{ display: "flex", justifyContent: "space-around", alignItems: "center", paddingTop: 8 }}>
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

      <Card>
        <div className="card-heading">
          <div>
            <h2>{t("userListTitle")}</h2>
            <p>{t("userListDesc")}</p>
          </div>
          <Button onClick={download}>
            <Download size={16} /> {t("downloadUserList")}
          </Button>
        </div>
        {users.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>{t("nameCol")}</th><th>{t("emailCol")}</th><th>{t("stateCol")}</th>
                  <th>{t("districtCol")}</th><th>{t("villageCol")}</th><th>{t("loginsCol")}</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id}>
                    <td>{u.name}</td><td>{u.email}</td>
                    <td>{u.state || "—"}</td><td>{u.district || "—"}</td>
                    <td>{u.village || "—"}</td><td>{u.login_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="muted">{t("noUsersYet")}</p>
        )}
      </Card>

      <Card>
        <div className="card-heading">
          <div>
            <h2>{t("govSchemesTitle")}</h2>
            <p>{t("govSchemesDesc")}</p>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <Button onClick={() => navigate(ROUTES.DEVELOPER_ADD_SCHEME)}>
              <Plus size={16} /> {t("addNewScheme")}
            </Button>
          </div>
        </div>

        {message && <div className="alert alert-success">{message}</div>}

        {showForm && (
          <div style={{ background: "#f8faf8", border: "1px solid var(--line)", borderRadius: 12, padding: 18, marginBottom: 20 }}>
            <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 14 }}>
              {editing ? t("editScheme") : t("quickAddScheme")}
            </div>
            <div className="form-grid">
              <label>{t("schemeNameLabel")}<input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></label>
              <label>{t("schemeStateLabel")}<input value={form.state || ""} onChange={e => setForm({ ...form, state: e.target.value })} /></label>
              <label>{t("schemeUrlLabel")}<input value={form.url} onChange={e => setForm({ ...form, url: e.target.value })} /></label>
              <label>{t("schemeActiveLabel")}
                <select value={form.active ? "yes" : "no"} onChange={e => setForm({ ...form, active: e.target.value === "yes" })}>
                  <option value="yes">{t("visibleToUsersOption")}</option>
                  <option value="no">{t("hiddenOption")}</option>
                </select>
              </label>
            </div>
            <label style={{ display: "flex", flexDirection: "column", gap: 7, fontSize: 11, fontWeight: 700, color: "#4e5d53", marginTop: 12 }}>
              {t("descriptionLabel")}
              <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
            </label>
            <div className="form-actions">
              <button className="btn btn-secondary" onClick={() => { setEditing(null); setForm(empty); setShowForm(false); }}>
                {t("cancel")}
              </button>
              <Button onClick={save}>
                {editing ? <><Pencil size={15} /> {t("updateScheme")}</> : <><Plus size={15} /> {t("saveScheme")}</>}
              </Button>
            </div>
          </div>
        )}

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>{t("schemeCol")}</th><th>{t("stateColLabel")}</th><th>{t("statusCol")}</th><th>{t("updatedCol")}</th><th></th>
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
                    <div className="muted">{s.description?.slice(0, 80)}{s.description?.length > 80 ? "…" : ""}</div>
                  </td>
                  <td>{s.state || t("allIndia")}</td>
                  <td>
                    <span className={`badge ${s.active ? "badge-green" : "badge-yellow"}`}>
                      {s.active ? t("activeLabel") : t("hiddenLabel")}
                    </span>
                  </td>
                  <td>{s.updated_at ? new Date(s.updated_at).toLocaleDateString() : "—"}</td>
                  <td style={{ whiteSpace: "nowrap" }}>
                    <button className="icon-btn" title={t("edit")} onClick={() => edit(s)}><Pencil size={16} /></button>
                    <button className="icon-btn" title={t("delete")} onClick={() => remove(s.id)}><Trash2 size={16} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
