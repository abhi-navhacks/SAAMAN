# 🚀 Hosting SAMAAN on Vercel & Cloud Platforms

This guide walks you through deploying **SAMAAN ("One Nation, One Material Code")** to the cloud.

---

## ⚡ The Vercel Reality (Important Context)

* **Vercel** is an ultra-fast serverless platform designed for frontends and lightweight serverless functions.
* Vercel enforces a **strict 250 MB uncompressed limit** on serverless functions and a **10-15s timeout**.
* Heavy ML libraries like `torch` and `sentence-transformers` are **~800 MB - 1.5 GB**, which causes standard Python ML apps to fail during Vercel builds if deployed naively.

To solve this, we have set up **Two Simple & Foolproof Solutions**:

---

## 🏆 Option 1: Direct Vercel Deployment (Precomputed Mode) — 100% Free & Fast

In this mode, all 1,332 real materials, duplicate clusters, 2D t-SNE coordinates, and national statistics are served from the precomputed cache (`data/precomputed_samaan.json`, 2.3 MB).

* **CNMC AI Code Generator**: Fully operational in real-time using deterministic rule-based NER and canonical key hashing (`cnmc_generator.py`).
* **Bundle Size**: Only ~15 MB total! Builds in under 20 seconds.

### Step 1: Prepare Requirements
Copy `requirements-vercel.txt` to `requirements.txt`:
```powershell
cp requirements-vercel.txt requirements.txt
```
*(Keep your original ML dependencies backed up if you run heavy pipeline re-training locally)*

### Step 2: Deploy to Vercel via CLI
Install Vercel CLI (if not already installed) and deploy:
```powershell
npm install -g vercel
vercel
```
1. Follow the interactive prompts:
   - Set up and deploy? **Yes** (`Y`)
   - Which scope? Select your personal account
   - Link to existing project? **No** (`N`)
   - Project name? `samaan` (or press Enter)
   - Directory located? `./` (press Enter)
2. To deploy to production:
```powershell
vercel --prod
```

### Step 3: (Alternative) Deploy via GitHub
1. Push this folder to a GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "Deploy SAMAAN to Vercel"
   git remote add origin https://github.com/<your-username>/samaan.git
   git push -u origin main
   ```
2. Go to [vercel.com](https://vercel.com) → **Add New Project** → Import your GitHub repository.
3. Vercel automatically detects `vercel.json` and `api/index.py` and deploys your site to `https://samaan.vercel.app`.

---

## 🌐 Option 2: Render.com / Railway (Full 24/7 Python ML Server)

If you want the **entire heavy ML pipeline** (`sentence-transformers`, `torch`, live vector similarity search) running continuously in the cloud for free:

### On Render.com (Free Tier):
1. Push your code to GitHub.
2. Go to [render.com](https://render.com) → **New Web Service**.
3. Select your GitHub repository.
4. Settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python startup.py`
5. Click **Create Web Service**. Render gives you a free HTTPS URL: `https://samaan.onrender.com`.

---

## 📁 Pre-configured Files in this Directory

| File | Purpose |
| :--- | :--- |
| `vercel.json` | Tells Vercel how to route web traffic to `api/index.py` |
| `api/index.py` | Fast, lightweight Serverless FastAPI handler for Vercel |
| `requirements-vercel.txt` | Lightweight dependencies (FastAPI, Pandas, Jinja2, Uvicorn) without 1GB PyTorch |
| `data/precomputed_samaan.json` | 2.3 MB snapshot of all 1,332 records, 2D t-SNE points, matches, and stats |
| `export_for_vercel.py` | Script to re-export cache anytime you add new materials |
