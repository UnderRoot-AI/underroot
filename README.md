# Smart Soil Health Detection and Decision Support System — Final

This final version keeps the existing React UI structure/style and adds the requested end-to-end workflow:

- Soil-probe/hardware values → soil analyzer → parameter analysis → crop + fertilizer recommendations.
- OCR for uploaded PDF/image soil reports, followed by verification and analysis.
- Separate `soil_reports.db` for soil-report history.
- Soil Report screen is now **history only**; the actual analysis is on **Soil Analyzer**.
- Working Random Forest crop and fertilizer recommendation models with retraining script and stored training-set medians for incomplete readings.
- RAG assistant using the local agriculture knowledge base.
- Working English/Hindi/Gujarati language selector; language is also saved to the user profile.
- Developer login with platform statistics, successful-login counts, location-wise user table and CSV download.
- Developer CRUD for government schemes/information so old entries can be removed and new entries can be continuously added/updated.
- State, district and village/city are stored with the user profile and included in developer exports.

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

## Final developer login

Use this account for the developer control center:

```text
Developer URL: http://localhost:5173/developer/login
Email:         underroot@gmail.com
Password:      underroot4
```

For production, change the developer credentials through environment variables and use a strong secret/password hash.

## Developer functionality

After developer login:

1. **Platform statistics**
   - Registered users.
   - Users who have successfully logged in at least once.
   - Total successful login count.
   - Total soil tests.
   - Active government schemes.

2. **User download**
   - Name
   - Email
   - Phone
   - State
   - District
   - Village/City
   - Language
   - Login count
   - Last login
   - Registration date
   - Download as CSV.

3. **Government scheme management**
   - Add a new scheme/information item.
   - Edit an existing item.
   - Hide an item without deleting it.
   - Permanently remove an old item.
   - User-facing Government Resources page reads the active entries from the database.

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

The analyzer endpoint is:

```text
GET /api/soil/tests/{test_id}/analysis
```

The existing recommendation endpoints also work independently:

```text
GET /api/recommendations/crops?soil_test_id={id}
GET /api/recommendations/fertilizer?soil_test_id={id}
```

## Soil Report history

The **Soil Report** page no longer mixes analysis with history. It displays stored report records from the separate database:

```text
backend/soil_reports.db
```

The report store contains uploaded/processed report metadata, OCR text, extracted parameters, OCR engine and RAG context.

## OCR + RAG flow

```text
PDF / JPG / PNG
      ↓
OCR / text extraction
      ↓
Extract pH, N, P, K, EC, moisture, temperature, organic carbon
      ↓
User verifies extracted values
      ↓
Soil Test created
      ↓
Soil Analyzer
```

RAG uses the files under:

```text
backend/data/knowledge/
```

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

Current development-model training data contains:

- Crop model: 3,000 generated development rows across 10 crop classes.
- Fertilizer model: 6,000 generated development rows across nutrient recommendation classes.

These are development datasets and should be replaced with validated local agricultural/soil-laboratory data before field deployment.

## Start backend

Python 3.14 is supported by the project code; if a third-party package has a Python-version-specific wheel issue on your machine, use a compatible Python 3.13/3.12 virtual environment.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/train_models.py
uvicorn app.main:app --reload --port 8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

## Start frontend

```powershell
cd frontend
npm install
npm run dev
```

If Vite uses port 5175, the backend CORS list already includes both localhost and 127.0.0.1 on 5175.

## OCR dependency

For image/scanned-PDF OCR, install Tesseract OCR on Windows and add `tesseract.exe` to PATH.

Text PDFs can still be processed through `pypdf` without Tesseract when the PDF contains selectable text.

## Hardware serial format

JSON:

```json
{"ph":6.8,"nitrogen":45,"phosphorus":30,"potassium":50,"ec":0.8,"moisture":42,"temperature":24,"organic_carbon":0.7}
```

Key/value:

```text
pH=6.8,N=45,P=30,K=50,EC=0.8,moisture=42,temperature=24,OC=0.7
```

Frontend flow:

```text
Soil Test → Select soil probe port → Read from probe → Save soil test → Soil Analyzer
```

## Databases

### Main application database

```text
backend/smart_soil.db
```

Stores users, login statistics, soil tests, application reports, conversations and government schemes.

### Separate soil-report database

```text
backend/soil_reports.db
```

Stores soil-report history independently from the main application database.

## Safety note

Crop and fertilizer results are decision-support screening outputs. Fertilizer dose depends on crop, field size, soil-test method/units, product formulation and local agricultural recommendations. The system intentionally does not invent a universal numeric fertilizer dose from the ML model alone.

## Developer access

Developer Control Center:
- URL: `http://localhost:5173/developer/login`
- Email: `underroot@gmail.com`
- Password: `underroot4`

The developer account is configured in `backend/.env` using `DEVELOPER_EMAIL` and `DEVELOPER_PASSWORD`. Restart the backend after changing credentials.

## Phone verification

Phone verification uses a 6-digit OTP. The project supports Twilio for real SMS delivery. Configure these values in `backend/.env` for production SMS:

```env
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1XXXXXXXXXX
PHONE_OTP_EXPIRE_MINUTES=10
```

If `SMS_PROVIDER=console` (the default local setting), the API returns a development OTP so the complete verification flow can be tested without a paid SMS provider. The development OTP must not be exposed this way in production.

Users who provide a phone number during signup are taken to the phone verification screen. Changing a verified phone number resets its verification state and requires a new OTP.

## Language switching

The language selector supports English, Hindi and Gujarati. The selected language is persisted locally and to the signed-in user's profile. A global translation layer also covers static labels, buttons, headings, placeholders and common page text that was previously hard-coded, so changing language updates the visible application UI without changing the existing visual design.
