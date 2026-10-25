"""
server.py — FastAPI application.

Endpoints:
  Auth
    POST /auth/signup          — register a new doctor
    POST /auth/login           — login, returns JWT
    GET  /auth/me              — current doctor profile

  Pipeline
    POST /pipeline/start       — start a new pipeline run
    POST /pipeline/resume/{thread_id} — resume a paused HITL
    GET  /pipeline/state/{thread_id}  — current state + pause point

  Sessions
    GET  /sessions             — all sessions for authenticated doctor
    GET  /sessions/{thread_id} — single session detail

  Patients
    GET  /patients             — all patients for authenticated doctor
    GET  /patients/{patient_id} — single patient + session history
    GET  /patients/{patient_id}/reports — all final reports for a patient
"""

import os
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client, Client
from app.db.supabase_db import (
    signup_doctor,
    login_doctor,
    get_doctor_profile,
    create_patient,
    get_patient,
    get_doctor_patients,
    delete_patient,
    create_session,
    get_session_by_thread,
    get_doctor_sessions,
    update_session_task_id,
    log_hitl_pause,
    get_final_report,
    get_patient_reports,
    delete_session,
)
from app.worker.celery_app import run_pipeline_task, resume_pipeline_task
from app.pipeline.graph import get_pipeline_state
from app.config import SUPABASE_URL, SUPABASE_ANON_KEY

app = FastAPI(
    title       = "Clinical AI Platform",
    description = "Multi-doctor clinical decision support system",
    version     = "1.0.0",
)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _get_anon_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


async def get_current_doctor(authorization: str = Header(...)) -> dict:
    """
    FastAPI dependency — validates the Bearer JWT from Supabase Auth.
    Returns the decoded user dict with at least {"id": "<doctor_uid>"}.

    Usage:
        doctor = Depends(get_current_doctor)
        doctor["id"]  →  auth.uid()
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "Missing or malformed Authorization header.",
        )

    token = authorization.removeprefix("Bearer ").strip()

    try:
        sb   = _get_anon_client()
        user = sb.auth.get_user(token)
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token.")
        return {"id": user.user.id, "email": user.user.email}
    except Exception:
        raise HTTPException(status_code=401, detail="Token validation failed.")


# ─────────────────────────────────────────────────────────────────────────────
# REQUEST / RESPONSE SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email:     EmailStr
    password:  str
    full_name: str
    hospital:  str


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class StartPipelineRequest(BaseModel):
    chief_complain: str


class ResumeRequest(BaseModel):
    resume_type: str    # "hitl_1_recommendation_approval" | "hitl_2_exam_input" | ...
    payload:     dict   # HITL-specific response fields


# ─────────────────────────────────────────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
async def signup(req: SignupRequest):
    """Register a new doctor account."""
    try:
        response = signup_doctor(
            email     = req.email,
            password  = req.password,
            full_name = req.full_name,
            hospital  = req.hospital,
        )
        if not response.user:
            raise HTTPException(status_code=400, detail="Signup failed.")
        return {
            "message": "Account created. Check your email to confirm.",
            "user_id": response.user.id,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login")
async def login(req: LoginRequest):
    """Login and receive a JWT access token."""
    try:
        response = login_doctor(req.email, req.password)
        if not response.session:
            raise HTTPException(status_code=401, detail="Invalid credentials.")
        return {
            "access_token":  response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type":    "bearer",
            "doctor_id":     response.user.id,
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/auth/me")
async def me(doctor: dict = Depends(get_current_doctor)):
    """Return the current doctor's profile."""
    profile = get_doctor_profile(doctor["id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return profile


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/pipeline/start", status_code=status.HTTP_202_ACCEPTED)
async def start_pipeline(
    req:    StartPipelineRequest,
    doctor: dict = Depends(get_current_doctor),
):
    """
    Start a new pipeline run for a patient.

    1. Creates a patient row in Supabase.
    2. Creates a session row.
    3. Enqueues a Celery task to run the pipeline in the background.
    4. Returns thread_id so the dashboard can poll for state.
    """
    doctor_id = doctor["id"]
    thread_id = str(uuid.uuid4())

    # Create patient (demographics filled later by Stage 1A)
    patient_id = create_patient(
        doctor_id          = doctor_id,
        chief_complain_raw = req.chief_complain,
    )

    # Create session
    session_id = create_session(
        thread_id  = thread_id,
        doctor_id  = doctor_id,
        patient_id = patient_id,
    )

    # Enqueue background task
    task = run_pipeline_task.delay(
        thread_id     = thread_id,
        chief_complain = req.chief_complain,
        doctor_id     = doctor_id,
        session_id    = session_id,
        patient_id    = patient_id,
    )

    # Store Celery task ID in session
    update_session_task_id(session_id, task.id)

    return {
        "thread_id":  thread_id,
        "session_id": session_id,
        "patient_id": patient_id,
        "task_id":    task.id,
        "message":    "Pipeline started in background.",
    }


@app.post("/pipeline/resume/{thread_id}", status_code=status.HTTP_202_ACCEPTED)
async def resume_pipeline(
    thread_id: str,
    req:       ResumeRequest,
    doctor:    dict = Depends(get_current_doctor),
):
    """
    Resume a paused pipeline after a HITL response.

    req.resume_type — which HITL is being answered:
        "hitl_1_recommendation_approval"
        "hitl_2_exam_input"
        "hitl_3_diagnosis_approval"
        "hitl_3b_crag_missing_data"
        "hitl_4_crag_confirmation"

    req.payload — HITL-specific fields, e.g.:
        hitl_1: {"approved": true}
        hitl_1 modified: {"approved": false, "modified_recommendation": "..."}
        hitl_2: {"exam_text": "..."}
        hitl_3: {"approved": true}
        hitl_3 note: {"approved": false, "doctor_note": "..."}
        hitl_3b: {"additional_data": "..."}
        hitl_4: {"confirmed": true, "doctor_final_note": "..."}
    """
    doctor_id = doctor["id"]

    session = get_session_by_thread(thread_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session["doctor_id"] != doctor_id:
        raise HTTPException(status_code=403, detail="Not your session.")

    # Map resume_type → HITL label for logging
    hitl_label_map = {
        "hitl_1_recommendation_approval": "hitl_1",
        "hitl_2_exam_input":              "hitl_2",
        "hitl_3_diagnosis_approval":      "hitl_3",
        "hitl_3b_crag_missing_data":      "hitl_3b",
        "hitl_4_crag_confirmation":       "hitl_4",
    }
    hitl_label = hitl_label_map.get(req.resume_type)
    if not hitl_label:
        raise HTTPException(status_code=400, detail=f"Unknown resume_type: {req.resume_type}")

    # Log the HITL pause → will be updated with response by the Celery task
    hitl_log_id = log_hitl_pause(
        session_id     = session["id"],
        doctor_id      = doctor_id,
        hitl_number    = hitl_label,
        hitl_type      = req.resume_type,
        displayed_data = req.payload,
    )

    # Enqueue resume task
    task = resume_pipeline_task.delay(
        thread_id   = thread_id,
        resume_type = req.resume_type,
        payload     = req.payload,
        doctor_id   = doctor_id,
        session_id  = session["id"],
        patient_id  = session["patient_id"],
        hitl_log_id = hitl_log_id,
    )

    return {
        "thread_id": thread_id,
        "task_id":   task.id,
        "message":   f"Resuming from {req.resume_type} in background.",
    }


@app.get("/pipeline/state/{thread_id}")
async def pipeline_state(
    thread_id: str,
    doctor:    dict = Depends(get_current_doctor),
):
    """
    Return the current LangGraph state for a thread.

    Response includes:
      - paused_at: which HITL the graph is waiting at (or None)
      - status: "paused" | "complete" | "not_found"
      - values: full pipeline state dict
      - session: Supabase session metadata
    """
    doctor_id = doctor["id"]

    session = get_session_by_thread(thread_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session["doctor_id"] != doctor_id:
        raise HTTPException(status_code=403, detail="Not your session.")

    graph_state = get_pipeline_state(thread_id)

    return {
        "thread_id": thread_id,
        "session":   session,
        **graph_state,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SESSIONS ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/sessions")
async def list_sessions(doctor: dict = Depends(get_current_doctor)):
    """Return all sessions for the authenticated doctor, newest first."""
    return get_doctor_sessions(doctor["id"])


@app.get("/sessions/{thread_id}")
async def get_session(thread_id: str, doctor: dict = Depends(get_current_doctor)):
    """Return a single session and its current graph state."""
    session = get_session_by_thread(thread_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session["doctor_id"] != doctor["id"]:
        raise HTTPException(status_code=403, detail="Not your session.")

    graph_state = get_pipeline_state(thread_id)

    return {
        "session":    session,
        "graph_state": graph_state,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PATIENTS ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/patients")
async def list_patients(doctor: dict = Depends(get_current_doctor)):
    """Return all patients for the authenticated doctor, newest first."""
    return get_doctor_patients(doctor["id"])


@app.get("/patients/{patient_id}")
async def get_patient_detail(patient_id: str, doctor: dict = Depends(get_current_doctor)):
    """Return a patient record. Doctor-ownership enforced by RLS + explicit check."""
    patient = get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    if patient["doctor_id"] != doctor["id"]:
        raise HTTPException(status_code=403, detail="Not your patient.")
    return patient


@app.get("/patients/{patient_id}/reports")
async def get_reports(patient_id: str, doctor: dict = Depends(get_current_doctor)):
    """Return all final reports for a patient."""
    patient = get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    if patient["doctor_id"] != doctor["id"]:
        raise HTTPException(status_code=403, detail="Not your patient.")
    return get_patient_reports(patient_id)


@app.delete("/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient_route(patient_id: str, doctor: dict = Depends(get_current_doctor)):
    """Delete a patient and all associated sessions/reports."""
    patient = get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    if patient["doctor_id"] != doctor["id"]:
        raise HTTPException(status_code=403, detail="Not your patient.")
    delete_patient(patient_id)


@app.delete("/sessions/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session_route(thread_id: str, doctor: dict = Depends(get_current_doctor)):
    """Delete a single session by thread_id."""
    session = get_session_by_thread(thread_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session["doctor_id"] != doctor["id"]:
        raise HTTPException(status_code=403, detail="Not your session.")
    delete_session(thread_id)


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}
