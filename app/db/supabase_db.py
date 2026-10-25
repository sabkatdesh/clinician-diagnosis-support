"""
supabase_db.py — All Supabase operations for the Clinical AI Platform.

Uses the SERVICE ROLE key (bypasses RLS) so the backend can write
on behalf of any authenticated doctor without re-sending their JWT
on every internal call.

The doctor_id is always passed explicitly from the API layer,
which has already validated the JWT and extracted auth.uid().
"""

import os
import json
import time
from typing import Optional, Any
from datetime import datetime, timezone

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL         = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]   # service role key — bypasses RLS

# Single client reused across all calls
_client: Optional[Client] = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _safe_json(obj: Any) -> Any:
    """
    Convert Pydantic models, datetimes, and other non-serialisable objects
    to plain dicts/strings so they can be stored as JSONB.
    """
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):          # Pydantic v2
        return obj.model_dump(mode="json")
    if hasattr(obj, "dict"):                # Pydantic v1
        return obj.dict()
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, (list, tuple)):
        return [_safe_json(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _safe_json(v) for k, v in obj.items()}
    return obj


# ─────────────────────────────────────────────────────────────────────────────
# AUTH — Doctor signup helper
# ─────────────────────────────────────────────────────────────────────────────

def signup_doctor(email: str, password: str, full_name: str, hospital: str) -> dict:
    """
    Create a new doctor account via Supabase Auth.
    full_name and hospital are stored in raw_user_meta_data,
    which the DB trigger (handle_new_doctor) copies into doctor_profiles.
    """
    sb = get_client()
    response = sb.auth.sign_up({
        "email":    email,
        "password": password,
        "options": {
            "data": {
                "full_name": full_name,
                "hospital":  hospital,
            }
        }
    })
    return response


def login_doctor(email: str, password: str) -> dict:
    """Authenticate a doctor and return session + JWT."""
    sb = get_client()
    response = sb.auth.sign_in_with_password({
        "email":    email,
        "password": password,
    })
    return response


def get_doctor_profile(doctor_id: str) -> Optional[dict]:
    """Fetch a doctor's profile by their auth UID."""
    sb = get_client()
    res = sb.table("doctor_profiles").select("*").eq("id", doctor_id).single().execute()
    return res.data


# ─────────────────────────────────────────────────────────────────────────────
# PATIENTS
# ─────────────────────────────────────────────────────────────────────────────

def create_patient(doctor_id: str, chief_complain_raw: str) -> str:
    """
    Create a minimal patient row at pipeline start (before Stage 1A runs).
    Returns the new patient_id (UUID).
    Stage 1A will update this row with extracted demographics.
    """
    sb  = get_client()
    res = sb.table("patients").insert({
        "doctor_id":          doctor_id,
        "chief_complain_raw": chief_complain_raw,
    }).execute()
    return res.data[0]["id"]


def update_patient_from_stage_1a(patient_id: str, patient_info: Any) -> None:
    """
    After Stage 1A extracts structured PatientInfo, write demographics to DB.
    patient_info is a PatientInfo Pydantic object.
    """
    sb = get_client()

    gi = getattr(patient_info, "general_info", None)
    if gi is None:
        return

    update_data = {
        "name":                 getattr(gi, "name",            None),
        "age":                  getattr(gi, "age",             None),
        "gender":               getattr(gi, "gender",          None),
        "contact_number":       getattr(gi, "contact_number",  None),
        "address":              getattr(gi, "address",         None),
        "patient_id_external":  getattr(gi, "patient_id",      None),
        "admission_datetime":   (
            gi.admission_datetime.isoformat()
            if getattr(gi, "admission_datetime", None)
            else None
        ),
    }

    # Remove None values so we don't overwrite existing data with nulls
    update_data = {k: v for k, v in update_data.items() if v is not None}

    if update_data:
        sb.table("patients").update(update_data).eq("id", patient_id).execute()


def get_patient(patient_id: str) -> Optional[dict]:
    """Fetch a single patient record."""
    sb  = get_client()
    res = sb.table("patients").select("*").eq("id", patient_id).single().execute()
    return res.data


def delete_patient(patient_id: str) -> None:
    """Delete a patient and all associated data (sessions cascade via FK)."""
    sb = get_client()
    sb.table("patients").delete().eq("id", patient_id).execute()


def delete_session(thread_id: str) -> None:
    """Delete a single session by thread_id."""
    sb = get_client()
    sb.table("sessions").delete().eq("thread_id", thread_id).execute()


def get_doctor_patients(doctor_id: str) -> list:
    """All patients belonging to this doctor, newest first."""
    sb  = get_client()
    res = (
        sb.table("patients")
        .select("*, sessions(id, status, current_stage, created_at)")
        .eq("doctor_id", doctor_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


# ─────────────────────────────────────────────────────────────────────────────
# SESSIONS
# ─────────────────────────────────────────────────────────────────────────────

def create_session(thread_id: str, doctor_id: str, patient_id: str) -> str:
    """
    Create a new session row at pipeline start.
    Returns session_id (UUID).
    """
    sb  = get_client()
    res = sb.table("sessions").insert({
        "thread_id":  thread_id,
        "doctor_id":  doctor_id,
        "patient_id": patient_id,
        "status":     "starting",
    }).execute()
    return res.data[0]["id"]


def update_session_stage(session_id: str, current_stage: str, paused_at: Optional[str] = None) -> None:
    """Update which stage the session is currently at."""
    sb = get_client()
    sb.table("sessions").update({
        "current_stage": current_stage,
        "paused_at":     paused_at,
        "status":        "paused_hitl" if paused_at else "running",
    }).eq("id", session_id).execute()


def update_session_task_id(session_id: str, task_id: str) -> None:
    """Store the Celery task ID once the task is enqueued."""
    sb = get_client()
    sb.table("sessions").update({"task_id": task_id}).eq("id", session_id).execute()


def complete_session(session_id: str) -> None:
    """Mark session as completed."""
    sb = get_client()
    sb.table("sessions").update({
        "status":       "completed",
        "paused_at":    None,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", session_id).execute()


def fail_session(session_id: str, error: str) -> None:
    """Mark session as failed."""
    sb = get_client()
    sb.table("sessions").update({
        "status":        "failed",
        "current_stage": error[:500],
    }).eq("id", session_id).execute()


def get_session_by_thread(thread_id: str) -> Optional[dict]:
    """Fetch a session by its LangGraph thread_id."""
    sb  = get_client()
    res = (
        sb.table("sessions")
        .select("*")
        .eq("thread_id", thread_id)
        .single()
        .execute()
    )
    return res.data


def get_doctor_sessions(doctor_id: str) -> list:
    """All sessions for this doctor, newest first."""
    sb  = get_client()
    res = (
        sb.table("sessions")
        .select("*, patients(name, age, gender)")
        .eq("doctor_id", doctor_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


# ─────────────────────────────────────────────────────────────────────────────
# STAGE LOGS
# ─────────────────────────────────────────────────────────────────────────────

def log_stage_start(session_id: str, doctor_id: str, stage_name: str, stage_input: Any) -> str:
    """
    Insert a stage log row when a node begins.
    Returns the log row ID so we can update it on completion.
    """
    sb  = get_client()
    res = sb.table("stage_logs").insert({
        "session_id":  session_id,
        "doctor_id":   doctor_id,
        "stage_name":  stage_name,
        "stage_input": _safe_json(stage_input),
        "started_at":  datetime.now(timezone.utc).isoformat(),
    }).execute()
    return res.data[0]["id"]


def log_stage_complete(
    log_id:       str,
    stage_output: Any,
    started_at:   float,    # time.time() value from before the node ran
    success:      bool = True,
    error_message: Optional[str] = None,
) -> None:
    """Update a stage log row when a node finishes."""
    sb       = get_client()
    now      = datetime.now(timezone.utc)
    duration = int((time.time() - started_at) * 1000)   # milliseconds

    sb.table("stage_logs").update({
        "stage_output":  _safe_json(stage_output),
        "success":       success,
        "error_message": error_message,
        "completed_at":  now.isoformat(),
        "duration_ms":   duration,
    }).eq("id", log_id).execute()


def log_stage(
    session_id:   str,
    doctor_id:    str,
    stage_name:   str,
    stage_input:  Any,
    stage_output: Any,
    started_at:   float,
    success:      bool = True,
    error_message: Optional[str] = None,
) -> None:
    """
    Convenience: insert a complete stage log in one call.
    Use this when you have both input and output ready.
    """
    sb       = get_client()
    now      = datetime.now(timezone.utc)
    duration = int((time.time() - started_at) * 1000)

    sb.table("stage_logs").insert({
        "session_id":    session_id,
        "doctor_id":     doctor_id,
        "stage_name":    stage_name,
        "stage_input":   _safe_json(stage_input),
        "stage_output":  _safe_json(stage_output),
        "success":       success,
        "error_message": error_message,
        "started_at":    datetime.fromtimestamp(started_at, tz=timezone.utc).isoformat(),
        "completed_at":  now.isoformat(),
        "duration_ms":   duration,
    }).execute()


# ─────────────────────────────────────────────────────────────────────────────
# HITL LOGS
# ─────────────────────────────────────────────────────────────────────────────

def log_hitl_pause(
    session_id:     str,
    doctor_id:      str,
    hitl_number:    str,
    hitl_type:      str,
    displayed_data: Any,
) -> str:
    """
    Log when a HITL pause fires.
    Returns the hitl_log row ID so we can update it on resume.
    """
    sb  = get_client()
    res = sb.table("hitl_logs").insert({
        "session_id":     session_id,
        "doctor_id":      doctor_id,
        "hitl_number":    hitl_number,
        "hitl_type":      hitl_type,
        "displayed_data": _safe_json(displayed_data),
        "paused_at":      datetime.now(timezone.utc).isoformat(),
    }).execute()
    return res.data[0]["id"]


def log_hitl_resume(hitl_log_id: str, doctor_response: Any) -> None:
    """Update the HITL log when the doctor responds."""
    sb = get_client()
    sb.table("hitl_logs").update({
        "doctor_response": _safe_json(doctor_response),
        "resumed_at":      datetime.now(timezone.utc).isoformat(),
    }).eq("id", hitl_log_id).execute()


# ─────────────────────────────────────────────────────────────────────────────
# CRAG ATTEMPTS
# ─────────────────────────────────────────────────────────────────────────────

def log_crag_attempt(
    session_id:      str,
    doctor_id:       str,
    attempt_number:  int,
    crag_output:     Any,
    doctor_response: Optional[str] = None,
) -> str:
    """
    Log one CRAG attempt.
    crag_output is a CRAGOutput Pydantic object.
    Returns the row ID.
    """
    sb = get_client()

    required_tests      = _safe_json(getattr(crag_output, "required_tests",      None))
    red_flags           = _safe_json(getattr(crag_output, "red_flags",           None))
    supporting_evidence = _safe_json(getattr(crag_output, "supporting_evidence", []))
    against_evidence    = _safe_json(getattr(crag_output, "against_evidence",    []))
    missing_data        = _safe_json(getattr(crag_output, "missing_data",        None))

    res = sb.table("crag_attempts").insert({
        "session_id":           session_id,
        "doctor_id":            doctor_id,
        "attempt_number":       attempt_number,
        "verdict":              crag_output.verdict,
        "confidence_score":     crag_output.confidence_score,
        "retry_recommended":    crag_output.retry_recommended,
        "primary_diagnosis":    getattr(crag_output, "validated_primary_diagnosis", None),
        "final_diagnosis":      crag_output.final_diagnosis,
        "missing_data":         missing_data,
        "doctor_response":      doctor_response,
        "supporting_evidence":  supporting_evidence,
        "against_evidence":     against_evidence,
        "required_tests":       required_tests,
        "red_flags":            red_flags,
    }).execute()
    return res.data[0]["id"]


# ─────────────────────────────────────────────────────────────────────────────
# FINAL REPORTS
# ─────────────────────────────────────────────────────────────────────────────

def save_final_report(
    session_id:         str,
    patient_id:         str,
    doctor_id:          str,
    crag_output:        Any,
    doctor_confirmed:   bool,
    doctor_final_note:  Optional[str],
    total_crag_attempts: int,
) -> str:
    """
    Write the final report after HITL #4 confirmation.
    Returns the report row ID.
    """
    sb = get_client()

    res = sb.table("final_reports").insert({
        "session_id":                   session_id,
        "patient_id":                   patient_id,
        "doctor_id":                    doctor_id,
        "verdict":                      crag_output.verdict,
        "final_diagnosis":              crag_output.final_diagnosis,
        "final_diagnosis_confidence":   crag_output.final_diagnosis_confidence,
        "validated_primary_diagnosis":  getattr(crag_output, "validated_primary_diagnosis", None),
        "corrected_diagnosis":          getattr(crag_output, "corrected_diagnosis",          None),
        "clinical_reasoning_summary":   getattr(crag_output, "clinical_reasoning_summary",   None),
        "supporting_evidence":          _safe_json(getattr(crag_output, "supporting_evidence", [])),
        "against_evidence":             _safe_json(getattr(crag_output, "against_evidence",    [])),
        "required_tests":               _safe_json(getattr(crag_output, "required_tests",      None)),
        "red_flags":                    _safe_json(getattr(crag_output, "red_flags",           None)),
        "doctor_confirmed":             doctor_confirmed,
        "doctor_final_note":            doctor_final_note,
        "total_crag_attempts":          total_crag_attempts,
    }).execute()
    return res.data[0]["id"]


def get_final_report(session_id: str) -> Optional[dict]:
    """Fetch the final report for a session."""
    sb  = get_client()
    res = (
        sb.table("final_reports")
        .select("*")
        .eq("session_id", session_id)
        .single()
        .execute()
    )
    return res.data


def get_patient_reports(patient_id: str) -> list:
    """All final reports for a patient across all sessions."""
    sb  = get_client()
    res = (
        sb.table("final_reports")
        .select("*, sessions(thread_id, created_at)")
        .eq("patient_id", patient_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []
