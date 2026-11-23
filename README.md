# 🌸 SheRise — Empowering Women Entrepreneurs Platform

**SheRise** is a venture marketplace and acceleration platform designed specifically to bridge the gender venture gap. It connects visionary female founders with angel syndicates, venture funds, and provides AI-accelerated pitch advisory powered by Google Gemini.

---

## 🌟 Key Features

### 1. Premium Landing Page
- Modern lavender, white, and deep purple design palette with glassmorphism and subtle elevation.
- Hero headline, live syndicate metrics ($18.5M+ raised, 450+ startups, 190+ investors, 91/100 avg readiness).
- Gemini 4 Hydrogen feature banner, curated dealflow showcase, and investor spotlight.

### 2. Full Authentication & Role Management
- Dual-role registration: **Female Founder** or **Investor / Supporter**.
- Client & server validation with password hashing.
- **1-Click Instant Demo Login**:
  - `Maya Lin` (Founder of BioNova Health)
  - `Elena Rostova` (Partner at Purple Horizon Ventures)

### 3. Entrepreneur Dashboard
- Personal founder hub with real-time KPI metrics (Active Ventures, Impressions, Inquiries, AI Score).
- Venture management list with funding progress bars.
- Live investor inquiry feed.

### 4. Create & Submit Business Idea
- Multi-step venture publication form: Industry sector, stage, target funding, problem statement, solution, target market, traction milestones, deck link, and website.
- Form validation with error handling.
- **Inline "✨ Audit with SheRise AI Doctor"** button directly integrated into the form.

### 5. Explore Ventures
- Searchable and filterable venture directory.
- Filters for Category (HealthTech, FinTech, AI & SaaS, CleanTech, EdTech, E-commerce, BioTech) and Stage.
- Sort options: Newest, Highest AI Score, Funding Goal, Most Views.
- Interactive modal with complete pitch details and "Express Interest" action.

### 6. Investor Discovery
- Directory of verified angel investors and venture funds.
- Filter by focus sector and investment thesis.
- **"✨ Pitch with AI"**: Automatically crafts bespoke, high-converting outreach emails matching the founder's pitch to that specific investor's thesis.

### 7. User Profile
- Profile view and editor with avatar, bio, company, location, and social links.

### 8. SheRise AI Pitch Doctor (Gemini API Integration)
- Evaluates any startup pitch across:
  - Problem-Solution Fit & Market Urgency
  - Revenue Model & Unit Economics
  - Defensibility & Moat
  - 30-Second Executive Pitch Hook
  - Diligence Questions & Growth Areas
- Uses Google Gemini API (`gemini-4-hydrogen` / `gemini-2.5-flash`) with fallback heuristic intelligence.

---

## 🚀 Quick Start Instructions (Local Development)

### Running on Windows
Double-click `start.bat` or run in PowerShell / Command Prompt:

```powershell
# Using Python directly:
& "C:\Users\YASHI\AppData\Local\Programs\Python\Python313\python.exe" run.py
```

Open your browser and navigate to:
👉 **`http://127.0.0.1:8000`**

---

## 🌐 Deploying to Render

This project is fully configured for zero-friction deployment on [Render](https://render.com).

### Option A: Deploy with Render Blueprint (`render.yaml`)
1. Push your repository to GitHub.
2. In your Render Dashboard, click **New +** > **Blueprint**.
3. Select your GitHub repository.
4. Render will automatically detect `render.yaml` and configure the Web Service with the proper start command and environment variables.

### Option B: Manual Web Service Setup
1. In your Render Dashboard, click **New +** > **Web Service**.
2. Connect your GitHub repository.
3. Configure the settings:
   - **Name**: `sherise-platform`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python run.py`
4. Add Environment Variables (under **Advanced** or **Environment** tab):
   - `PORT`: `8000` (Render automatically assigns and overrides this)
   - `HOST`: `0.0.0.0`
   - `GEMINI_API_KEY`: *(Optional)* Your Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/)
   - `SHERISE_SALT`: *(Optional)* A random secret string for password hashing

---

## 🔒 Security & Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `PORT` | `8000` | Port for the HTTP server (automatically set by Render) |
| `HOST` | `0.0.0.0` | Host binding (`0.0.0.0` required for Render and Docker) |
| `GEMINI_API_KEY` | *(None)* | Google Gemini API key. If unset, uses built-in heuristic engine. |
| `SHERISE_SALT` | `sherise_secure_salt_2026` | Secret salt used for hashing user passwords |
| `SHERISE_DB_PATH`| `sherise.db` | Path to SQLite database file |

> [!NOTE]
> `.gitignore` is pre-configured to ensure no `.env` files, API keys, SQLite databases (`*.db`), or Python cache (`__pycache__`) are committed to GitHub.

---

## 📁 Project Architecture

```
c:\Users\YASHI\OneDrive\Dokumen\My first project\
├── .gitignore          # Excludes caches, secrets, local DBs from Git
├── .env.example        # Template for environment variables
├── Procfile            # Process file for cloud PaaS deployments
├── render.yaml         # Render Blueprint configuration
├── database.py         # SQLite database schema, connections, and seed data
├── gemini_service.py   # Google Gemini API client & pitch evaluator
├── server.py           # Multi-threaded HTTP REST API & static server (0.0.0.0:PORT)
├── run.py              # Application launcher script
├── start.bat           # 1-click Windows startup script
├── requirements.txt    # Deployment dependencies
├── README.md           # Documentation
└── public/
    ├── index.html      # Single-page application master layout
    ├── css/
    │   └── styles.css  # Lavender & deep purple design system
    └── js/
        ├── api.js      # REST API client
        ├── state.js    # Reactive global state management
        ├── components.js# UI component renderers
        └── app.js      # Main router and event handlers
```
