import { useState } from "react";
import type { FormEvent } from "react";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import { useAuthStore } from "../../store/authStore";
import { ROUTES } from "../../constants/routes";
import { updateProfile } from "../../services/auth.api";
import { getErrorMessage } from "../../utils/errorHandler";
import ErrorAlert from "../../components/common/ErrorAlert";
import { useNavigate } from "react-router-dom";
import { useLanguageStore } from "../../store/languageStore";
import { useT } from "../../i18n/useT";

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
    </>
  );
}
