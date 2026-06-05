from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from app.database import engine
from app.routers import kpis, churn, loyalty, satisfaction, nlp, customers
from app.services.ml_client import predict_churn, predict_recommendation

app = FastAPI(
    title="ME2026 Platform Backend",
    description="Unified backend API for the airline data platform. Connects React dashboard to PostgreSQL DW and ML services.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kpis.router)
app.include_router(churn.router)
app.include_router(loyalty.router)
app.include_router(satisfaction.router)
app.include_router(nlp.router)
app.include_router(customers.router)


@app.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    return {"status": "ok", "database": db_status}


class PredictionRequest(BaseModel):
    loyalty_number: int


@app.post("/api/predictions/churn")
def score_churn(req: PredictionRequest):
    result = predict_churn(req.loyalty_number)
    if result is None:
        raise HTTPException(status_code=404, detail="Loyalty number not found")
    return result


@app.post("/api/predictions/recommendation")
def score_loyalty(req: PredictionRequest):
    result = predict_recommendation(req.loyalty_number)
    if result is None:
        raise HTTPException(status_code=404, detail="Loyalty number not found")
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)