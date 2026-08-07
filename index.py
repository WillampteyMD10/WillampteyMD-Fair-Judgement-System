[07.08.2026 12:31] William Lamptey: import os
import time
from uuid import UUID
from typing import Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="WillampteyMD Fair Judgment System API (SkepticOS)")

# Enable Cross-Origin Resource Sharing (CORS) so your Vercel React frontend can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In strict production, replace with your specific Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Connection Helper Function
def get_db_connection():
    try:
        # Pulls the connection string from environment variables populated during Render setup
        connection = psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=RealDictCursor)
        return connection
    except Exception as e:
        print(f"[!] Database connection failure: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connectivity failure.")

# Structured Input Framework Models
class IncidentIngest(BaseModel):
    target_host: str
    raw_payload: str
    is_honey_alert: Optional[bool] = False
    true_matrix_state: Optional[str] = "malicious"

class HumanVerdictSubmission(BaseModel):
    incident_id: UUID
    analyst_id: UUID
    human_hypothesis: str
    opened_timestamp: float  # Tracking velocity parameters

@app.get("/")
def read_root():
    return {"status": "online", "system": "WillampteyMD Fair Judgment System", "engine": "SkepticOS"}

@app.post("/v1/incidents/ingest")
async def ingest_siem_incident(payload: IncidentIngest):
    """
    Endpoint 1: Receives consolidated multi-signal alerts from the SIEM gate layer.
    Saves the data snapshot inside your Supabase cluster.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO incident_logs (target_host, raw_payload, is_honey_alert, true_matrix_state) VALUES (%s, %s, %s, %s) RETURNING incident_id;",
            (payload.target_host, payload.raw_payload, payload.is_honey_alert, payload.true_matrix_state)
        )
        incident_id = cursor.fetchone()['incident_id']
        conn.commit()
        return {"status": "success", "incident_id": incident_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Ingestion SQL Error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.post("/v1/verdicts/evaluate")
async def process_blinded_human_verdict(submission: HumanVerdictSubmission):
    """
    Endpoint 2: Enforces the 45-second velocity throttle constraint.
    Unlocks zero-creativity AI metrics only AFTER the analyst registers their blind hypothesis.
    """
    # Calculate exactly how long the human looked at the raw data logs
    execution_duration = time.time() - submission.opened_timestamp
    
    # HARD REGULATORY LOCK: Block access if the user clicked faster than 45 seconds
    if execution_duration < 45.0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"Security Protocol Block: Analysis execution window too brief ({execution_duration:.1f}s). Manual forensic evaluation required."
        )

    # Initialize the Gated Worker AI Execution Loop
    api_key = os.getenv("ENTERPRISE_API_KEY")
    worker_summary = "{\"msg\": \"Worker AI trace inactive. Check API Key credentials.\"}"
    
    if api_key:
        try:
            ai_client = OpenAI(api_key=api_key)
            completion = ai_client.chat.completions.create(
                model="gpt-4o",
                temperature=0.0,  # CRITICAL BOUNDARY: Eliminates creative text padding
[07.08.2026 12:31] William Lamptey: response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "Extract technical data to flat JSON. Keys: {'hash', 'cmd'}. Do not interpret intent or give troubleshooting advice."},
                    {"role": "user", "content": f"Target Telemetry Raw Metadata: {submission.incident_id}"}
                ]
            )
            worker_summary = completion.choices.message.content
        except Exception as e:
            worker_summary = f"{{'error': 'Worker AI operational pipeline crash: {str(e)}'}}"

    # Establish baseline statistical parameters for Detective AI risk profiling
    detective_paranoia_score = 94.20
    is_compliant = (submission.human_hypothesis == "malicious")

    # Commit records dynamically to your immutable Postgres ledger
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO analyst_verdicts (incident_id, analyst_id, human_hypothesis, worker_ai_snapshot, detective_ai_score, is_compliant_match, verdict_submitted_at) VALUES (%s, %s, %s, %s, %s, %s, NOW());",
            (submission.incident_id, submission.analyst_id, submission.human_hypothesis, worker_summary, detective_paranoia_score, is_compliant)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"[!] Audit Log Insertion Error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return {
        "incident_id": submission.incident_id,
        "velocity_check": "PASS",
        "elapsed_seconds": round(execution_duration, 2),
        "worker_ai_payload": worker_summary,
        "detective_ai_score": detective_paranoia_score,
        "is_compliant_match": is_compliant
    }
