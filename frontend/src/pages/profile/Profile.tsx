import { useState } from "react";
import type { FormEvent } from "react";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import { useAuthStore } from "../../store/authStore";
import { useSoilStore } from "../../store/soilStore";
import { ROUTES } from "../../constants/routes";
import { authApi, updateProfile } from "../../services/auth.api";
import { getErrorMessage } from "../../utils/errorHandler";
import ErrorAlert from "../../components/common/ErrorAlert";
import { useNavigate } from "react-router-dom";
import { useLanguageStore } from "../../store/languageStore";
import { useT } from "../../i18n/useT";

// ── Delete Account dialog state ───────────────────────────────────────────────
interface DeleteDialogState {
  open: boolean;
  password: string;
  loading: boolean;
  error: string;
}

export default function Profile() {
  const { user, logout } = useAuthStore();
  const setLanguage = useLanguageStore((s) => s.setLanguage);
  const navigate = useNavigate();
  const t = useT();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState({
    name: user?.name || "",
    phone: user?.phone || "",
    location: user?.location || "",
    state: user?.state || "",
    district: user?.district || "",
    city_village: user?.city_village || "",
    language: user?.language || "en",
  });
  const [deleteDialog, setDeleteDialog] = useState<DeleteDialogState>({
    open: false,
    password: "",
    loading: false,
    error: "",
  });

  async function save(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSaved(false);
    try {
      const updated = await updateProfile(form);
      useAuthStore.getState().setUser(updated);
      setLanguage((updated.language || "en") as any);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      setError(getErrorMessage(e, "Could not save profile"));
    } finally {
      setSaving(false);
    }
  }

  function signout() { logout(); navigate(ROUTES.LOGIN); }

  function openDeleteDialog() {
    setDeleteDialog({ open: true, password: "", loading: false, error: "" });
  }

  function closeDeleteDialog() {
    if (deleteDialog.loading) return;
    setDeleteDialog({ open: false, password: "", loading: false, error: "" });
  }

  async function confirmDelete() {
    if (!deleteDialog.password) {
      setDeleteDialog(s => ({ ...s, error: "Please enter your password to confirm." }));
      return;
    }
    setDeleteDialog(s => ({ ...s, loading: true, error: "" }));
    try {
      await authApi.deleteAccount(deleteDialog.password);
      // Clear all user-specific state
      logout();
      useSoilStore.getState().setCurrentTest(null);
      useSoilStore.getState().setTests([]);
      navigate(ROUTES.LOGIN + "?deleted=1");
    } catch (e: any) {
      const msg =
        e.response?.data?.detail ||
        e.response?.statusText ||
        e.message ||
        "Could not delete account. Please try again.";
      setDeleteDialog(s => ({ ...s, loading: false, error: msg }));
    }
  }

  return (
    <>
      <PageHeader title={t("profileTitle")} subtitle={t("profileSubtitle")} />
      <Card>
        <form onSubmit={save}>
          <ErrorAlert message={error} />
          {saved && <div className="alert alert-success">✓ {t("profileSaved")}</div>}
          <div className="profile-head">
            <div className="profile-avatar">{user?.name?.charAt(0) || "U"}</div>
            <div>
              <h2>{user?.name || "Farmer"}</h2>
              <p>{user?.email} · {user?.email_verified ? `✓ ${t("emailVerifiedStatus")}` : `⚠ ${t("emailNotVerified")}`}</p>
            </div>
          </div>
          <div className="form-grid">
            <label>{t("name")}<input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></label>
            <label>{t("phone")}<input value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} /></label>
            <label>{t("stateLabel")}<input value={form.state} onChange={e => setForm({ ...form, state: e.target.value })} /></label>
            <label>{t("location")}<input value={form.location} onChange={e => setForm({ ...form, location: e.target.value })} /></label>
            <label>{t("districtLabel")}<input value={form.district} onChange={e => setForm({ ...form, district: e.target.value })} /></label>
            <label>{t("villageLabel")}<input value={form.city_village} onChange={e => setForm({ ...form, city_village: e.target.value })} /></label>
            <label>
              Language
              <select value={form.language} onChange={e => setForm({ ...form, language: e.target.value })}>
                <option value="en">English</option>
                <option value="hi">हिन्दी</option>
                <option value="gu">ગુજરાતી</option>
                <option value="mr">मराठी</option>
              </select>
            </label>
          </div>
          <div className="form-actions">
            <Button type="submit" loading={saving}>{t("saveChanges")}</Button>
            <button type="button" className="btn btn-danger" onClick={signout}>{t("logout")}</button>
          </div>
        </form>
      </Card>

      {/* ── Delete Account ─────────────────────────────────────────────── */}
      <Card>
        <div className="card-heading">
          <div>
            <h2 style={{ color: "#b42318" }}>Delete Account</h2>
            <p>Permanently remove your account and all associated data. This cannot be undone.</p>
          </div>
        </div>
        <div className="form-actions">
          <button
            type="button"
            className="btn btn-danger"
            onClick={openDeleteDialog}
          >
            Delete My Account
          </button>
        </div>
      </Card>

      {/* ── Confirmation dialog ────────────────────────────────────────── */}
      {deleteDialog.open && (
        <div
          style={{
            position: "fixed", inset: 0, zIndex: 1000,
            background: "rgba(0,0,0,0.45)",
            display: "flex", alignItems: "center", justifyContent: "center",
            padding: 20,
          }}
          onClick={closeDeleteDialog}
        >
          <div
            style={{
              background: "#fff", borderRadius: 16, padding: 28,
              width: "min(440px, 100%)", boxShadow: "0 20px 60px rgba(0,0,0,0.2)",
            }}
            onClick={e => e.stopPropagation()}
          >
            <h2 style={{ margin: "0 0 8px", fontSize: 18, color: "#b42318" }}>
              Delete Account
            </h2>
            <p style={{ margin: "0 0 16px", fontSize: 13, color: "var(--muted)", lineHeight: 1.6 }}>
              This will <strong>permanently delete</strong> your account, all soil tests,
              devices, reports, recommendations, and assistant history.
              <br /><br />
              <strong>This action cannot be undone.</strong>
            </p>

            {deleteDialog.error && (
              <div className="alert alert-error" style={{ marginBottom: 14, fontSize: 13 }}>
                {deleteDialog.error}
              </div>
            )}

            <label style={{ display: "flex", flexDirection: "column", gap: 7, fontSize: 12, fontWeight: 700, color: "#4e5d53", marginBottom: 20 }}>
              Confirm your password
              <input
                type="password"
                value={deleteDialog.password}
                onChange={e => setDeleteDialog(s => ({ ...s, password: e.target.value, error: "" }))}
                placeholder="Enter your current password"
                disabled={deleteDialog.loading}
                style={{ borderRadius: 9, border: "1px solid #d7e1d9", padding: "11px 12px", fontSize: 12 }}
                autoFocus
              />
            </label>

            <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={closeDeleteDialog}
                disabled={deleteDialog.loading}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-danger"
                onClick={confirmDelete}
                disabled={deleteDialog.loading || !deleteDialog.password}
              >
                {deleteDialog.loading ? "Deleting…" : "Yes, delete my account"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
