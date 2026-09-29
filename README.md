# UnderRoot

> **Know Your Soil. Grow Smarter.**

UnderRoot is an AI-powered soil health intelligence platform designed to turn soil measurements into clear, actionable insights for better agricultural decisions.

It combines soil analysis, health scoring, crop and fertilizer recommendations, connected-device data ingestion, digital soil reports, and an AI assistant into one platform.

---

## 🌱 What is UnderRoot?

Soil testing often produces numbers without making it easy to understand what those numbers mean or what action should be taken next.

UnderRoot addresses this by providing a complete soil intelligence workflow:

**Soil Data → Analysis → Health Score → Recommendations → Report → Decision Support**

The platform can work with manually entered soil-test data as well as readings ingested from supported hardware/software integrations.

---

## ✨ Core Features

### 🧪 Soil Health Analysis

Analyze important soil parameters including:

- pH
- Electrical Conductivity (EC)
- Nitrogen (N)
- Phosphorus (P)
- Potassium (K)
- Organic Carbon (OC)
- Moisture
- Temperature
- Sulphur (S)
- Zinc (Zn)
- Iron (Fe)
- Manganese (Mn)
- Copper (Cu)
- Boron (B)

The analyzer identifies:

- Optimal values
- Low values
- High values
- Critical conditions
- Missing parameters
- Deficiencies
- Excesses
- Warnings

A deterministic soil-health score from **0–100** is generated along with a health status such as:

- Excellent
- Good
- Needs Attention
- Poor
- Awaiting Data

---

### 🌾 Crop Recommendations

UnderRoot evaluates soil conditions and provides crop recommendations based on available soil parameters.

Recommendations include:

- Crop name
- Suitability
- Reasoning
- Season
- Expected duration
- Relevant soil conditions

The system is designed to make recommendations understandable rather than simply displaying a crop name.

---

### 🧴 Fertilizer Recommendations

The fertilizer recommendation system considers soil deficiencies and other available parameters.

Recommendations can include:

- Fertilizer/product type
- Application rate
- Frequency
- Reasoning
- Precautions
- Important notes

The recommendation interface separates the explanation into clear sections so users can understand **why** a recommendation was generated.

> Recommendations are decision-support information and should be validated against local agronomic conditions and professional guidance before application.

---

## 🤖 AI Soil Assistant

UnderRoot includes a context-aware AI assistant designed around soil-health information.

The assistant can use:

- Latest soil-test data
- Soil health score
- Soil health status
- Detected deficiencies
- Detected excesses
- Crop recommendations
- Fertilizer recommendations
- Recent conversation history
- Local soil-health knowledge

The assistant supports multiple languages, including:

- English
- Hindi
- Gujarati
- Marathi

The assistant is designed to ground responses in available UnderRoot soil data rather than acting as a general-purpose chatbot.

---

## 📡 Connected Hardware

UnderRoot includes a device-ingestion architecture for receiving soil readings from connected hardware.

The current software architecture supports:

```text
Soil Device
     │
     ▼
Device / Gateway / Integration
     │
     ▼
UnderRoot Ingestion API
     │
     ├── Raw Hardware Reading
     │
     └── Soil Test
             │
             ▼
       Soil Analysis
             │
             ├── Health Score
             ├── Deficiencies
             ├── Recommendations
             └── Reports
```
The platform is designed to support integrations such as:

BLE gateways
RS485 / Modbus gateways
LoRaWAN systems
MQTT systems
HTTP integrations
Other supported device adapters
SoilX Integration

The project has been designed with commercial soil-sensing hardware such as the REVE Nano-Science SoilX ecosystem in mind.

However, UnderRoot does not claim direct proprietary SoilX BLE communication unless an official/public integration interface is available.

The current implementation provides an HTTP-based hardware ingestion pipeline and simulator so the complete software workflow can be developed and tested without depending on proprietary communication protocols.

🔌 Device Management

Authenticated users can manage connected devices through the platform.

Available device functionality includes:

Register a device
View devices
View device details
Delete devices
Submit hardware readings
View device readings
View the latest device reading
Generate soil-test records from hardware readings
Device API
GET    /api/devices
POST   /api/devices
GET    /api/devices/{device_id}
DELETE /api/devices/{device_id}

POST   /api/devices/{device_id}/readings
GET    /api/devices/{device_id}/readings
GET    /api/devices/{device_id}/readings/latest

Hardware-generated soil tests preserve their source as:

source = hardware

and maintain the relationship with the originating device.

🧪 Hardware Simulator

UnderRoot includes a device simulator for testing the complete ingestion pipeline.

Example:

cd backend

.\.venv\Scripts\python.exe scripts\simulate_device.py `
  --email your@email.com `
  --password YourPassword `
  --device-pk 1 `
  --count 3 `
  --interval 2 `
  --vary

The simulator can generate varying soil measurements and submit them through the same API workflow used by hardware integrations.

📄 Soil Reports

UnderRoot generates digital soil-health reports containing:

UnderRoot branding
Soil test information
Field information
Test date
Health score
Health status
Parameter values
Parameter statuses
Key findings
Crop recommendations
Fertilizer recommendations

Reports are generated as PDF documents.

The PDF system includes protected report access so users cannot retrieve another user's report through the API.

🔐 Authentication & Security

UnderRoot includes a complete authentication workflow.

Account Features
User registration
Email verification
Login
Logout
Forgot password
Reset password
Password validation
Resend verification email
Account deletion
Protected authenticated routes
Email Verification

Email verification is required before an account can be used for normal login.

Unverified accounts are blocked from login until verification is completed.

Password Reset

The password-reset workflow allows users to:

Request a password reset
Receive a reset link
Set a new password
Log in using the new password

The previous password is no longer accepted after a successful reset.

Account Deletion

Users can permanently delete their account after confirming their password.

User-owned application data is removed according to the platform's account-deletion workflow.

👨‍💻 Admin / Developer Panel

UnderRoot includes a protected developer/admin panel for platform administration.

The developer panel provides visibility into:

Dashboard statistics
Users
Email verification status
Soil tests
Devices
Reports
Schemes

It also provides search functionality across administrative sections.

Administrative endpoints are protected separately from normal user authentication.

Normal users cannot access developer-only endpoints.

🏗️ Architecture

High-level architecture:

                    ┌─────────────────────┐
                    │      Frontend       │
                    │   React + Vite      │
                    └──────────┬──────────┘
                               │
                               │ REST API
                               ▼
                    ┌─────────────────────┐
                    │       FastAPI       │
                    │      Backend        │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
       Authentication     Soil Services     Device Services
             │                 │                 │
             │                 ▼                 ▼
             │          Soil Analyzer      Hardware Readings
             │                 │
             │        ┌────────┴────────┐
             │        ▼                 ▼
             │   Recommendations     Reports
             │        │                 │
             └────────┴────────┬────────┘
                               │
                               ▼
                         Database Layer
🛠️ Technology Stack
Frontend
React
TypeScript
Vite
Tailwind CSS
React Router
Axios
Backend
Python
FastAPI
SQLAlchemy
Pydantic
Uvicorn
Database
Relational database architecture
SQLAlchemy ORM
Persistent soil-test, user, device, reading, report and application data
Testing
Pytest
FastAPI TestClient
Frontend production builds
Document Generation
ReportLab
📁 Project Structure
underroot/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── assets/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── scripts/
│   │   └── simulate_device.py
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── ...
│   ├── package.json
│   └── .env
│
├── README.md
└── .gitignore
🚀 Local Development
Prerequisites

Install:

Python 3.11+
Node.js 20+
npm
Git
A supported relational database
1. Clone the Repository
git clone https://github.com/UnderRoot-AI/underroot.git
cd underroot
2. Backend Setup

Open PowerShell:

cd backend

Create the virtual environment:

python -m venv .venv

Activate it:

.\.venv\Scripts\Activate.ps1

Install dependencies:

python -m pip install -r requirements.txt

Configure the backend .env file with the required application and database settings.

Start the backend:

uvicorn app.main:app --reload --port 8001

Backend:

http://127.0.0.1:8001

API:

http://127.0.0.1:8001/api

API documentation:

http://127.0.0.1:8001/docs
3. Frontend Setup

Open another PowerShell terminal:

cd frontend

Install dependencies:

npm install

Create/configure the frontend .env:

VITE_API_URL=http://127.0.0.1:8001/api

Start the development server:

npm run dev

The frontend will normally be available at:

http://localhost:5173
🔑 Environment Variables

Never commit secrets to GitHub.

Example frontend configuration:

VITE_API_URL=http://127.0.0.1:8001/api

Backend environment variables depend on the deployment configuration and should be stored in the backend .env file.

Typical configuration may include:

DATABASE_URL=...
SECRET_KEY=...

Email-service credentials, database credentials, API keys and other secrets must remain outside the repository.

🧪 Testing

Run backend tests from the backend directory:

pytest -q

The latest validated project state passed:

229 passed, 1 warning

The warning is related to a dependency deprecation and does not represent a failing test.

🏭 Frontend Production Build

From the frontend directory:

npm run build

The latest validated project state completed the production build successfully.

🔒 Security Principles

UnderRoot follows several important security principles:

Passwords are not stored in plaintext.
Email verification is required for normal login.
Authentication-protected endpoints require valid authentication.
Developer endpoints require developer authorization.
User data is isolated between accounts.
Report access is protected by ownership checks.
Account deletion requires password confirmation.
Secrets are stored through environment configuration.
Administrative data is not exposed through normal user APIs.
📊 Data Flow
Manual Soil Test
User
 │
 ▼
Enter Soil Parameters
 │
 ▼
Soil Test API
 │
 ▼
Validation
 │
 ▼
Soil Analyzer
 │
 ├── Parameter Status
 ├── Health Score
 ├── Deficiencies
 └── Excesses
 │
 ▼
Recommendations
 │
 ├── Crops
 └── Fertilizers
 │
 ▼
Report / Dashboard / AI Assistant
Hardware Soil Test
Soil Device
 │
 ▼
Gateway / Integration
 │
 ▼
Device Reading API
 │
 ▼
Hardware Reading
 │
 ▼
Soil Test
 │
 ▼
Soil Analyzer
 │
 ▼
Health + Recommendations + Report
🧠 Soil Analysis Approach

UnderRoot currently uses deterministic rule-based analysis for its core soil-health calculations.

This provides:

Reproducible results
Transparent thresholds
Consistent scoring
Predictable recommendations
Easier testing and validation

The AI assistant operates as a decision-support layer over available soil information and knowledge sources.

The system does not claim that AI-generated output replaces agronomic expertise.

🌍 Localization

The platform is designed for agricultural users in India and supports multilingual interaction.

Current AI assistant language support includes:

English
Hindi
Gujarati
Marathi

The architecture can be extended to additional regional languages.

📱 Responsive Interface

The frontend is designed for:

Desktop
Laptop
Tablet
Mobile

The interface includes dedicated workflows for:

Authentication
Dashboard
Soil analysis
History
Recommendations
Reports
Devices
AI assistant
Developer/admin operations
🛡️ Data & Safety Considerations

UnderRoot is intended as a soil-health intelligence and decision-support platform.

Soil recommendations can depend on factors that may not be available in a single measurement, including:

Crop variety
Local climate
Soil type
Irrigation
Previous cultivation
Farm management practices
Geographic conditions
Application history

Therefore, platform recommendations should be treated as decision support and validated against local agricultural conditions and qualified agronomic guidance where appropriate.

📌 Current Project Status
Completed
 User registration
 Email verification
 Login protection for unverified users
 Resend verification
 Forgot password
 Password reset
 Account deletion
 Soil-test workflow
 Soil parameter validation
 Soil health scoring
 Parameter status detection
 Deficiency detection
 Excess detection
 Crop recommendations
 Fertilizer recommendations
 Soil-test history
 PDF soil reports
 Protected report downloads
 AI soil assistant
 Multilingual assistant support
 Device management
 Hardware reading ingestion
 Hardware simulator
 Hardware-to-soil-test pipeline
 Developer/admin panel
 User administration
 Soil-test administration
 Device administration
 Report administration
 Responsive frontend
 Backend automated tests
 Production frontend build
🔮 Future Development

Potential future work includes:

Official hardware SDK integrations
Direct supported BLE integrations
Additional sensor protocols
Real-time device synchronization
Offline device synchronization
More soil parameters
More regional languages
Advanced farm analytics
Historical soil trend analysis
Field-level monitoring
Geospatial soil intelligence
Improved agronomic knowledge retrieval
Production deployment infrastructure
Notifications and alerts
Large-scale agricultural analytics
🚀 Deployment Considerations

Before production deployment, configure:

Production database
Secure HTTPS
Production frontend hosting
Production backend hosting
Environment secrets
Email delivery service
Database backups
Logging and monitoring
CORS configuration
Rate limiting
Secure authentication configuration
Production domain configuration

Development credentials and secrets must never be committed to the repository.

📈 Project Vision

UnderRoot aims to become a practical soil-intelligence platform that connects:

Sensors + Soil Data + AI + Agronomic Knowledge + Farmers

into a single decision-support ecosystem.

The long-term goal is to move beyond simply reporting soil values and help users understand:

What is happening in the soil, why it matters, and what action can be considered next.

📜 License

This project is currently under active development.

License terms should be added here before public distribution or commercial release.

👥 UnderRoot-AI

UnderRoot is developed by the UnderRoot-AI team.

GitHub Organization:

https://github.com/UnderRoot-AI

Repository:

https://github.com/UnderRoot-AI/underroot

UnderRoot — Know Your Soil. Grow Smarter.
