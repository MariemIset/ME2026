# Customer review sentiment (NLP dashboard)

Part of the **ME2026** project: sentiment analysis UI and API for `fact_satisfaction_survey.comment_text` (and live client comments).

## Layout

- `backend/` — FastAPI + Hugging Face RoBERTa sentiment
- `frontend/` — React (Vite) dashboard + client comment form

## Run locally

### Backend

```powershell
cd ME2026\backend
python -m pip install --user -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Uses PostgreSQL by default (`postgres` / `password123` / `data_warehouse`). Start the warehouse first:

```powershell
cd ME2026\docker
docker compose up -d
```

### Frontend

```powershell
cd ME2026\frontend
npm install
npm run dev
```

Open **http://localhost:5173** — use **Dashboard** or **Submit feedback** to add comments.

## Git (this repo)

Work **inside** `ME2026` (this folder has its own `.git` → GitHub `MariemIset/ME2026`):

```powershell
cd c:\NLP\ME2026
git status
git add backend frontend SENTIMENT_APP.md .gitignore
git commit -m "Add NLP sentiment dashboard and API"
git push origin master
```

Do **not** push from `c:\NLP` unless that parent folder is your intended repo — use **`ME2026`** for this project.

Remote: `https://github.com/MariemIset/ME2026.git`
