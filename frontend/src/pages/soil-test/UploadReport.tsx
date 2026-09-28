import { useState } from "react";
import { FileUp, UploadCloud, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import ErrorAlert from "../../components/common/ErrorAlert";
import { useReport } from "../../hooks/useReport";
import { ROUTES } from "../../constants/routes";
import { useT } from "../../i18n/useT";

const MAX_MB = 10;
const MAX_BYTES = MAX_MB * 1024 * 1024;

function fmt(bytes: number) {
  return bytes > 1_000_000
    ? `${(bytes / 1_000_000).toFixed(1)} MB`
    : `${Math.round(bytes / 1024)} KB`;
}

export default function UploadReport() {
  const [file, setFile] = useState<File | null>(null);
  const [sizeError, setSizeError] = useState("");
  const { upload, loading, error } = useReport();
  const navigate = useNavigate();
  const t = useT();

  function pickFile(f: File | null) {
    setSizeError("");
    if (!f) { setFile(null); return; }
    if (f.size > MAX_BYTES) {
      setSizeError(`File is too large (${fmt(f.size)}). Maximum allowed size is ${MAX_MB} MB.`);
      setFile(null);
      return;
    }
    setFile(f);
  }

  async function submit() {
    if (!file) return;
    try {
      const report = await upload(file);
      navigate(`${ROUTES.PROCESSING}?report=${report.id}`);
    } catch {
      // error is shown via the ErrorAlert below
    }
  }

  const displayError = sizeError || error;

  return (
    <>
      <PageHeader title={t("uploadReportTitle")} subtitle={t("uploadReportSubtitle")} />
      <Card>
        <div
          className="upload-zone"
          style={{ cursor: "pointer" }}
          onClick={() => !file && document.getElementById("soil-file")?.click()}
          onDragOver={e => e.preventDefault()}
          onDrop={e => { e.preventDefault(); pickFile(e.dataTransfer.files[0] ?? null); }}
        >
          <UploadCloud size={40} />
          {file ? (
            <>
              <h2 style={{ wordBreak: "break-all" }}>{file.name}</h2>
              <p style={{ color: "var(--green)" }}>{fmt(file.size)} · {t("selectedFile")}</p>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ marginTop: 10 }}
                onClick={e => { e.stopPropagation(); setFile(null); setSizeError(""); }}
              >
                <X size={14} /> {t("removeFile")}
              </button>
            </>
          ) : (
            <>
              <h2>{t("dragDropHere")}</h2>
              <p>{t("supportedFormats")}</p>
              <p style={{ fontSize: 11, marginTop: 4 }}>{t("orClickBrowse")}</p>
            </>
          )}
          <input
            id="soil-file"
            hidden
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={e => pickFile(e.target.files?.[0] ?? null)}
          />
        </div>

        <ErrorAlert message={displayError} />

        <div className="form-actions">
          <Button disabled={!file} loading={loading} onClick={submit}>
            <FileUp size={17} /> {t("uploadAndExtract")}
          </Button>
        </div>
      </Card>
    </>
  );
}
