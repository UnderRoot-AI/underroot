from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path
from typing import Tuple

from pypdf import PdfReader

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

try:
    import pytesseract
    from PIL import Image, ImageOps, ImageFilter

    # ── Bundled Tesseract executable ──────────────────────────────────────
    # Path structure:  client.py
    #                  └── ocr/          (parents[0])
    #                  └── integrations/ (parents[1])
    #                  └── app/          (parents[2])
    #                  └── backend/      (parents[3])  ← project root
    #                      └── tools/tesseract/tesseract.exe
    TESSERACT_PATH = (
        Path(__file__).resolve().parents[3]
        / "tools"
        / "tesseract"
        / "tesseract.exe"
    )

    if not TESSERACT_PATH.exists():
        raise RuntimeError(
            f"Bundled Tesseract executable not found at: {TESSERACT_PATH}\n"
            "Expected location: <backend>/tools/tesseract/tesseract.exe\n"
            "Image OCR (JPG/PNG/scanned PDF) will not work until this is resolved."
        )

    pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_PATH)

    # ── Windows: prevent socket-handle inheritance ───────────────────────
    # pytesseract calls subprocess.Popen() directly by name inside its own
    # module scope, so replacing pytesseract.pytesseract.subprocess_args has
    # no effect — the Popen call still sees the original local binding.
    #
    # Root cause: when tesseract.exe exits on Windows it closes its inherited
    # copy of Uvicorn's listening socket, which triggers a TCP RST and causes
    # ECONNRESET in the browser.
    #
    # Fix: patch subprocess.Popen itself so every call made by pytesseract
    # (and only from this process) automatically gets CREATE_NO_WINDOW.
    # This prevents handle inheritance without touching pytesseract internals.
    if sys.platform == "win32":
        import pytesseract.pytesseract as _pt_module
        _OrigPopen = subprocess.Popen

        class _NoWindowPopen(_OrigPopen):  # type: ignore[misc]
            def __init__(self, *args, **kwargs):
                kwargs.setdefault("creationflags", 0)
                kwargs["creationflags"] |= subprocess.CREATE_NO_WINDOW
                super().__init__(*args, **kwargs)

        # Patch only the Popen reference inside pytesseract's own module so
        # the rest of the application is unaffected.
        _pt_module.subprocess.Popen = _NoWindowPopen  # type: ignore[attr-defined]

except RuntimeError:
    # Re-raise RuntimeError so the startup log makes the problem explicit.
    raise

except Exception:
    pytesseract = None  # type: ignore[assignment]
    Image = None        # type: ignore[assignment]


def _image_ocr(data: bytes) -> str:
    if not pytesseract or not Image:
        return ""

    image = Image.open(io.BytesIO(data)).convert("RGB")
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)

    scale = 2 if max(image.size) < 2200 else 1

    if scale > 1:
        image = image.resize(
            (image.width * scale, image.height * scale)
        )

    image = image.filter(ImageFilter.SHARPEN)

    return pytesseract.image_to_string(image, config="--psm 3")


def extract_text(path: str | Path) -> Tuple[str, str]:
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".pdf":
        reader = PdfReader(str(p))

        text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

        # If PDF already contains selectable text, use it directly.
        if text.strip():
            return text[:100000], "pypdf"

        # Otherwise render PDF pages as images and OCR them.
        if fitz:
            chunks: list[str] = []

            doc = fitz.open(str(p))

            for page in doc:
                pix = page.get_pixmap(
                    matrix=fitz.Matrix(1.6, 1.6),
                    alpha=False,
                )
                chunks.append(_image_ocr(pix.tobytes("png")))

                if sum(len(x) for x in chunks) > 100000:
                    break

            return "\n".join(chunks)[:100000], "pymupdf+pytesseract"

        return "", "pypdf-no-text"

    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}:
        return _image_ocr(p.read_bytes())[:100000], "pytesseract"

    if suffix in {".txt", ".csv"}:
        return p.read_text(errors="ignore")[:100000], "plain-text"

    return "", "unsupported"
