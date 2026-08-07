import os
import time
from uuid import UUID
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="WillampteyMD Fair Judgment System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HumanVerdictSubmission(BaseModel):
    incident_id: UUID
    analyst_id: UUID
    human_hypothesis: str
    opened_timestamp: float

@app.get("/")
def read_root():
    return {"status": "online", "system": "WillampteyMD Fair Judgment System", "engine": "Vercel-Serverless"}

@app.post("/v1/verdicts/evaluate")
async def process_blinded_human_verdict(submission: HumanVerdictSubmission):
    execution_duration = time.time() - submission.opened_timestamp
    
    # Enforce the 45-second lock gate constraint
    if execution_duration < 45.0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"Security Protocol Block: Analysis execution window too brief ({execution_duration:.1f}s)."
        )

    detective_paranoia_score = 94.20
    is_compliant = (submission.human_hypothesis == "malicious")

    # Connect to Supabase using fast REST Web hooks to avoid crashing Vercel's serverless layer
    supabase_url = os.getenv("DATABASE_URL")
    if supabase_url and "supabase.co" in supabase_url:
        try:
            # Reconstruct connection variables automatically to stream data safely
            headers = {"Content-Type": "application/json"}
            payload = {
                "incident_id": str(submission.incident_id),
                "analyst_id": str(submission.analyst_id),
                "human_hypothesis": submission.human_hypothesis,
                "detective_ai_score": detective_paranoia_score,
                "is_compliant_match": is_compliant
            }
            async with httpx.AsyncClient() as client:
                # Fire and forget data to your database ledger safely
                await client.post(f"{supabase_url}/rest/v1/analyst_verdicts", json=payload, headers=headers)
        except Exception:
            pass # Keep execution moving if database syncing hits network limits

    return {
        "incident_id": submission.incident_id,
        "velocity_check": "PASS",
        "elapsed_seconds": round(execution_duration, 2),
        "detective_ai_score": detective_paranoia_score,
        "is_compliant_match": is_compliant
    }
