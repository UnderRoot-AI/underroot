import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Plus, Save, Globe, MapPin, FileText, Link2, ToggleLeft } from "lucide-react";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import { developerApi, type SchemePayload } from "../../services/developer.api";
import { ROUTES } from "../../constants/routes";
import { useT } from "../../i18n/useT";

const INDIAN_STATES = [
  "All India","Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh",
  "Goa","Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala",
  "Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland",
  "Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura",
  "Uttar Pradesh","Uttarakhand","West Bengal","Delhi","Jammu & Kashmir","Ladakh",
];

const CATEGORIES = [
  "Soil Health","Crop Insurance","Fertilizer Subsidy","Irrigation","Seed Distribution",
  "Farm Equipment","Credit & Loan","Market Support","Organic Farming","Other",
];

const empty: SchemePayload & { category: string } = {
  name: "", state: "", description: "", url: "", active: true, category: "Other",
};

export default function AddScheme() {
  const navigate = useNavigate();
  const t = useT();
  const [form, setForm] = useState({ ...empty });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  function set<K extends keyof typeof form>(k: K, v: (typeof form)[K]) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (!form.name.trim()) { setError(t("schemeNameRequired2")); return; }
    if (!form.description.trim()) { setError(t("descriptionRequired2")); return; }
    setSaving(true);
    try {
      await developerApi.createScheme({
        name: form.name.trim(),
        state: form.state === "All India" ? "" : form.state,
        description: form.description.trim(),
        url: form.url.trim(),
        active: form.active,
      });
      setSuccess(true);
      setTimeout(() => navigate(ROUTES.DEVELOPER), 1500);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Could not save scheme. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page-content">
      <PageHeader
        title={t("addSchemeTitle")}
        subtitle={t("addSchemeSubtitle")}
        action={
          <Button onClick={() => navigate(ROUTES.DEVELOPER)}>
            <ArrowLeft size={15} /> {t("backToDashboard")}
          </Button>
        }
      />

      {success && (
        <div className="alert alert-success" style={{ marginBottom: 20 }}>
          {t("schemeSavedSuccess")}
        </div>
      )}
      {error && (
        <div className="alert alert-error" style={{ marginBottom: 20 }}>
          {error}
        </div>
      )}

      <Card>
        <form onSubmit={submit}>
          <div style={{ marginBottom: 22 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
              <FileText size={16} color="var(--green)" />
              <span style={{ fontWeight: 700, fontSize: 14 }}>{t("schemeDetails")}</span>
            </div>
            <div className="form-grid">
              <label style={{ gridColumn: "1/-1" }}>
                {t("schemeNameRequired")}
                <input required value={form.name} onChange={e => set("name", e.target.value)} placeholder="e.g. PM Kisan Samman Nidhi" />
              </label>
              <label>
                {t("schemeCategoryLabel")}
                <select value={form.category} onChange={e => set("category", e.target.value)}>
                  {CATEGORIES.map(c => <option key={c}>{c}</option>)}
                </select>
              </label>
              <label>
                {t("schemeVisibilityLabel")}
                <select value={form.active ? "yes" : "no"} onChange={e => set("active", e.target.value === "yes")}>
                  <option value="yes">{t("visibleOption")}</option>
                  <option value="no">{t("hiddenDraftOption")}</option>
                </select>
              </label>
            </div>
          </div>

          <div style={{ marginBottom: 22 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
              <MapPin size={16} color="var(--green)" />
              <span style={{ fontWeight: 700, fontSize: 14 }}>{t("coverageLabel")}</span>
            </div>
            <div className="form-grid">
              <label>
                {t("stateRegionLabel")}
                <select value={form.state || "All India"} onChange={e => set("state", e.target.value === "All India" ? "" : e.target.value)}>
                  {INDIAN_STATES.map(s => <option key={s}>{s}</option>)}
                </select>
              </label>
              <label>
                {t("officialWebsite")}
                <div style={{ position: "relative" }}>
                  <input value={form.url} onChange={e => set("url", e.target.value)} placeholder="https://pmkisan.gov.in" style={{ paddingLeft: 32 }} />
                  <Link2 size={13} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "#93a097" }} />
                </div>
              </label>
            </div>
          </div>

          <div style={{ marginBottom: 22 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
              <Globe size={16} color="var(--green)" />
              <span style={{ fontWeight: 700, fontSize: 14 }}>{t("descriptionRequired")}</span>
            </div>
            <textarea
              required
              value={form.description}
              onChange={e => set("description", e.target.value)}
              placeholder={t("descriptionPlaceholder")}
              style={{ width: "100%", minHeight: 140, fontSize: 12, lineHeight: 1.6 }}
            />
            <div style={{ fontSize: 10, color: "var(--muted)", marginTop: 4 }}>
              {form.description.trim().length} {t("characters")}
            </div>
          </div>

          <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", borderTop: "1px solid var(--line)", paddingTop: 18 }}>
            <button type="button" className="btn btn-secondary" onClick={() => navigate(ROUTES.DEVELOPER)}>
              {t("cancel")}
            </button>
            <Button type="submit" loading={saving}>
              <Save size={15} /> {t("schemeSaveBtn")}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
