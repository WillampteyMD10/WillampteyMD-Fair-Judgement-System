import os
import time
from uuid import UUID
from typing import Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

# Vercel explicitly looks for an object named 'app' inside the api/ folder
app = FastAPI(title="WillampteyMD Fair Judgment System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    try:
        connection = psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=RealDictCursor)
        return connection
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database connectivity failure.")

class HumanVerdictSubmission(BaseModel):
    incident_id: UUID
    analyst_id: UUID
    human_hypothesis: str
    opened_timestamp: float

@app.get("/")
def read_root():
    return {"status": "online", "system": "WillampteyMD Fair Judgment System", "engine": "SkepticOS"}

@app.post("/v1/verdicts/evaluate")
async def process_blinded_human_verdict(submission: HumanVerdictSubmission):
    execution_duration = time.time() - submission.opened_timestamp
    
    # Enforce the 45-second lock gate
    if execution_duration < 45.0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"Security Protocol Block: Analysis execution window too brief ({execution_duration:.1f}s)."
        )

    # Simplified mock metrics for verification pass
    detective_paranoia_score = 94.20
    is_compliant = (submission.human_hypothesis == "malicious")

    return {
        "incident_id": submission.incident_id,
        "velocity_check": "PASS",
        "elapsed_seconds": round(execution_duration, 2),
        "detective_ai_score": detective_paranoia_score,
        "is_compliant_match": is_compliant
    }
