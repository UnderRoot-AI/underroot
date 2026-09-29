# UnderRoot — Smart Soil Health Detection and Decision Support System

AI-powered soil health intelligence platform for smarter farming.

This project keeps the existing React UI structure/style and delivers:

- Soil-probe/hardware values → soil analyzer → parameter analysis → crop + fertilizer recommendations.
- OCR for uploaded PDF/image soil reports, followed by verification and analysis.
- Separate `soil_reports.db` for soil-report history.
- Working Random Forest crop and fertilizer recommendation models with retraining script.
- RAG assistant using the local agriculture knowledge base.
- Working English/Hindi/Gujarati language selector persisted to user profiles.
- Developer login with platform statistics, location-wise user table and CSV download.
- Developer CRUD for government schemes/information.
- State, district and village/city stored with user profiles and included in developer exports.

## Architecture

```text
                         +----------------------+
Hardware Soil Probe ---->|                      |
                         |   FastAPI Backend    |
OCR PDF/Image ---------->|                      |
                         +----------+-----------+
                                    |
          +-------------------------+--------------------------+
          |                         |                          |
          v                         v                          v
   Soil Analyzer              ML Models                    RAG
   pH/N/P/K/EC/...            Crop RF                       Local KB
   health + status            Fertilizer RF                 Assistant
          |                         |
          +------------+------------+
                       v
              Soil Report History
                       |
          +------------+-------------+
          |                          |
   smart_soil.db              soil_reports.db
   users/tests/etc.            report history/OCR/RAG

Developer Control Center
  ├─ User statistics
  ├─ User list by State/District/Village
  ├─ CSV export
  └─ Government scheme CRUD
```

## Local development

### Backend

Python 3.12 or 3.13 recommended. Python 3.14 is supported by the project code.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/train_models.py
uvicorn app.main:app --reload --port 8001
```

API docs: http://127.0.0.1:8001/docs
Health:   http://127.0.0.1:8001/health

Copy `backend/.env.example` to `backend/.env` and fill in your values before starting.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Copy `frontend/.env.example` to `frontend/.env` before starting.

If Vite uses port 5175, the backend CORS list already includes both localhost and 127.0.0.1 on 5175.

## OCR dependency

For image/scanned-PDF OCR, install Tesseract OCR on Windows and add `tesseract.exe` to PATH.
Text PDFs are processed through `pypdf` without Tesseract when the PDF contains selectable text.

---

## Deployment (Render + Vercel)

### Backend — Render Web Service

| Setting         | Value                                              |
|-----------------|---------------------------------------------------|
| Root Directory  | `backend`                                         |
| Runtime         | Python 3                                          |
| Build Command   | `pip install -r requirements.txt`                 |
| Start Command   | `uvicorn app.main:app --host 0.0.0.0 --port $PORT`|

#### SQLite persistence on Render

Render's default web-service filesystem is ephemeral. SQLite data is lost on redeploy or
restart unless the databases are stored on a Persistent Disk.

**Add a Persistent Disk to the Render Web Service:**

- Mount path: `/var/data`
- Size: choose according to your expected data volume (1 GB is sufficient to start)

SQLite is suitable for low-to-medium traffic loads. It is not designed for high-concurrency
write-heavy production workloads. For large scale consider migrating to PostgreSQL in the future.

#### Render environment variables

Set all of the following in the Render dashboard under **Environment → Environment Variables**.

| Variable                       | Example production value                                  | Notes                                               |
|-------------------------------|----------------------------------------------------------|-----------------------------------------------------|
| `DATABASE_URL`                 | `sqlite:////var/data/smart_soil.db`                       | Four slashes = absolute path on the Persistent Disk |
| `SOIL_REPORT_DATABASE_URL`     | `sqlite:////var/data/soil_reports.db`                     | Four slashes = absolute path on the Persistent Disk |
| `UPLOAD_DIR`                   | `/var/data/uploads`                                       | Uploaded files — must be on the Persistent Disk     |
| `JWT_SECRET`                   | *(long random string — generate with `openssl rand -hex 32`)* | Never commit this value                         |
| `CORS_ORIGINS`                 | `https://your-app.vercel.app`                             | Comma-separated; add localhost for hybrid testing   |
| `FRONTEND_URL`                 | `https://your-app.vercel.app`                             | Used in password-reset email links                  |
| `SMTP_HOST`                    | `smtp.gmail.com`                                          |                                                     |
| `SMTP_PORT`                    | `587`                                                     |                                                     |
| `SMTP_USER`                    | `your-gmail@gmail.com`                                    |                                                     |
| `SMTP_PASSWORD`                | *(Gmail App Password — 16 chars, no spaces)*              | See `.env.example` for setup instructions           |
| `SMTP_FROM`                    | `your-gmail@gmail.com`                                    |                                                     |
| `EMAIL_FROM_NAME`              | `UnderRoot`                                               |                                                     |
| `DEVELOPER_EMAIL`              | *(your admin email)*                                      |                                                     |
| `DEVELOPER_PASSWORD_HASH`      | *(bcrypt hash — generate with the provided seed utility)* | Prefer this over `DEVELOPER_PASSWORD` in production |
| `HARDWARE_MODE`                | `mock`                                                    | No physical device on Render                        |
| `SMS_PROVIDER`                 | `console` or `twilio`                                     |                                                     |
| `TWILIO_ACCOUNT_SID`           | *(from Twilio dashboard)*                                 | Required only when `SMS_PROVIDER=twilio`            |
| `TWILIO_AUTH_TOKEN`            | *(from Twilio dashboard)*                                 | Required only when `SMS_PROVIDER=twilio`            |
| `TWILIO_FROM_NUMBER`           | `+1XXXXXXXXXX`                                            | Required only when `SMS_PROVIDER=twilio`            |

#### Database initialisation on Render

Tables are created automatically on first startup via SQLAlchemy `create_all()` and the
`ensure_*` migration helpers in `app/database/migrations.py`. No manual migration command
is needed. Existing data is never overwritten; the startup routines only add missing tables
or columns.

#### Persistent Disk directory initialisation

On first deploy, create the uploads sub-directory inside the disk:

```bash
mkdir -p /var/data/uploads
```

You can do this via the Render Shell tab or the start command wrapper. The application will
also attempt to create `UPLOAD_DIR` automatically at startup via `Path(...).mkdir(parents=True, exist_ok=True)`.

### Frontend — Vercel

| Setting          | Value                                    |
|------------------|------------------------------------------|
| Root Directory   | `frontend`                               |
| Build Command    | `npm run build`                          |
| Output Directory | `dist`                                   |

#### Vercel environment variable

| Variable       | Value                                            |
|----------------|--------------------------------------------------|
| `VITE_API_URL` | `https://your-backend.onrender.com/api`          |

Set this in the Vercel dashboard under **Settings → Environment Variables** before your first deployment.

### Health check

```
GET https://your-backend.onrender.com/health
```

Returns `{"status": "ok"}`. Render uses this endpoint automatically if configured as the health-check path.

---

## Databases

### Main application database

```text
backend/smart_soil.db        (local)
/var/data/smart_soil.db      (Render Persistent Disk)
```

Stores users, login statistics, soil tests, application reports, conversations and government schemes.

### Separate soil-report database

```text
backend/soil_reports.db      (local)
/var/data/soil_reports.db    (Render Persistent Disk)
```

Stores soil-report history independently from the main application database.

---

## Developer access

Developer Control Center:
- Local URL: `http://localhost:5173/developer/login`
- Production URL: `https://your-app.vercel.app/developer/login`

Configure credentials in `backend/.env` via `DEVELOPER_EMAIL` and `DEVELOPER_PASSWORD_HASH`.
Restart the backend after changing credentials.

## Soil analyzer flow

```text
Soil Probe
   ↓
Read pH, N, P, K, EC, moisture, temperature, organic carbon
   ↓
Save Soil Test
   ↓
Soil Analyzer
   ├─ Data completeness
   ├─ Parameter-by-parameter status
   ├─ Soil screening score
   ├─ Graphical parameter profile
   ├─ Crop recommendation
   └─ Fertilizer recommendation
```

Analyzer endpoint: `GET /api/soil/tests/{test_id}/analysis`

Recommendation endpoints (also work independently):

```
GET /api/recommendations/crops?soil_test_id={id}
GET /api/recommendations/fertilizer?soil_test_id={id}
```

## OCR + RAG flow

```text
PDF / JPG / PNG → OCR / text extraction → Extract pH, N, P, K, EC, moisture, temperature, organic carbon
→ User verifies extracted values → Soil Test created → Soil Analyzer
```

RAG knowledge base: `backend/data/knowledge/`

## Machine-learning models

Training script:

```powershell
cd backend
python scripts/train_models.py
```

Generated model files:

```text
backend/ml_models/crop_model.joblib
backend/ml_models/fertilizer_model.joblib
backend/ml_models/training_metrics.json
```

These are development datasets. Replace with validated local agricultural/soil-laboratory data before field deployment.

## Hardware serial format

JSON:
```json
{"ph":6.8,"nitrogen":45,"phosphorus":30,"potassium":50,"ec":0.8,"moisture":42,"temperature":24,"organic_carbon":0.7}
```

Key/value:
```
pH=6.8,N=45,P=30,K=50,EC=0.8,moisture=42,temperature=24,OC=0.7
```

Frontend flow: `Soil Test → Select soil probe port → Read from probe → Save soil test → Soil Analyzer`

## Phone verification

Phone verification uses a 6-digit OTP. Configure Twilio in `backend/.env` for production SMS:

```env
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1XXXXXXXXXX
```

If `SMS_PROVIDER=console` (default), the API returns a development OTP — do not use this in production.

## Language switching

The language selector supports English, Hindi and Gujarati. The selected language is persisted locally
and to the signed-in user's profile.

## Safety note

Crop and fertilizer results are decision-support screening outputs. Fertilizer dose depends on crop,
field size, soil-test method/units, product formulation and local agricultural recommendations.
The system intentionally does not invent a universal numeric fertilizer dose from the ML model alone.
