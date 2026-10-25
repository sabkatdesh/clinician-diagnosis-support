"""
celery_app.py — Celery worker and task definitions.

Uses Upstash Redis as both broker and result backend.
The pipeline runs inside a Celery task so it executes in the background
even if the doctor closes the dashboard.
"""

import os
from celery import Celery
from dotenv import load_dotenv
import ssl
load_dotenv()

from app.config import UPSTASH_REDIS_URL

# ─────────────────────────────────────────────
# CELERY APP
# Broker  = Upstash Redis (task queue)
# Backend = Upstash Redis (task results)
# ─────────────────────────────────────────────

celery_app = Celery(
   "clinical_ai",
    broker=UPSTASH_REDIS_URL,
    backend=UPSTASH_REDIS_URL,
)



celery_app.conf.update(
    # Serialisation
    task_serializer          = "json",
    result_serializer        = "json",
    accept_content           = ["json"],

    # Reliability
    task_acks_late           = True,        # ack only after task completes
    task_reject_on_worker_lost = True,      # requeue if worker dies mid-task
    worker_prefetch_multiplier = 1,         # one task at a time per worker (long-running LLM calls)

    # Results
    result_expires           = 60 * 60 * 24,   # keep results for 24 hours

    # Timezone
    timezone                 = "UTC",
    enable_utc               = True,

    # Retry defaults
    task_max_retries         = 3,
    task_default_retry_delay = 5,           # seconds between retries
    # SSL fix for Upstash rediss://
    broker_use_ssl           = {"ssl_cert_reqs": ssl.CERT_NONE},
    redis_backend_use_ssl    = {"ssl_cert_reqs": ssl.CERT_NONE},
)


# ─────────────────────────────────────────────
# TASKS
# ─────────────────────────────────────────────

@celery_app.task(
    bind=True,
    name="tasks.run_pipeline_task",
    max_retries=3,
    default_retry_delay=5,
)
def run_pipeline_task(self, thread_id: str, chief_complain: str, doctor_id: str, session_id: str, patient_id: str):
    """
    Background task: start and run the LangGraph pipeline.

    Runs automatically until the first HITL pause (or completion).
    After a HITL pause the workflow is frozen in Postgres —
    the task completes normally and the graph waits indefinitely.

    Resume is handled by resume_pipeline_task below.

    Args:
        thread_id:     LangGraph thread ID (also the Postgres checkpoint key)
        chief_complain: Raw text entered by the doctor
        doctor_id:     Supabase auth.uid() of the authenticated doctor
        session_id:    Supabase sessions.id for this pipeline run
        patient_id:    Supabase patients.id for this patient
    """
    from app.pipeline.graph import run_pipeline
    from app.db.supabase_db import update_session_stage, fail_session

    try:
        result = run_pipeline(
            thread_id      = thread_id,
            chief_complain = chief_complain,
            session_id     = session_id,
            doctor_id      = doctor_id,
            patient_id     = patient_id,
        )

        # Update session stage after pipeline pauses or completes
        paused_at = result.get("paused_at")
        update_session_stage(
            session_id    = session_id,
            current_stage = paused_at or "completed",
            paused_at     = paused_at,
        )

        return {
            "status":    result.get("status"),
            "paused_at": paused_at,
            "thread_id": thread_id,
        }

    except Exception as exc:
        fail_session(session_id, str(exc))
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="tasks.resume_pipeline_task",
    max_retries=3,
    default_retry_delay=5,
)
def resume_pipeline_task(
    self,
    thread_id:    str,
    resume_type:  str,
    payload:      dict,
    doctor_id:    str,
    session_id:   str,
    patient_id:   str,
    hitl_log_id:  str,
):
    """
    Background task: resume a paused pipeline after a HITL response.

    resume_type matches the HITL node:
        "hitl_1_recommendation_approval"
        "hitl_2_exam_input"
        "hitl_3_diagnosis_approval"
        "hitl_3b_crag_missing_data"
        "hitl_4_crag_confirmation"

    payload contains the doctor's response data for that HITL.

    Args:
        thread_id:    LangGraph thread ID
        resume_type:  Which HITL is being resumed
        payload:      Doctor response data (dict)
        doctor_id:    Doctor's auth UID
        session_id:   Supabase session ID
        patient_id:   Supabase patient ID
        hitl_log_id:  HITL log row ID to update on resume
    """
    from app.pipeline.graph import (
        resume_after_approval,
        resume_after_exam_input,
        resume_after_diagnosis_approval,
        resume_after_crag_missing_data,
        resume_after_crag_confirmation,
    )
    from app.db.supabase_db import update_session_stage, complete_session, fail_session, log_hitl_resume

    try:
        # Log the doctor's response
        log_hitl_resume(hitl_log_id, payload)

        # Call the correct resume function
        if resume_type == "hitl_1_recommendation_approval":
            result = resume_after_approval(
                thread_id             = thread_id,
                approved              = payload["approved"],
                modified_recommendation = payload.get("modified_recommendation", ""),
            )

        elif resume_type == "hitl_2_exam_input":
            result = resume_after_exam_input(
                thread_id = thread_id,
                exam_text = payload["exam_text"],
            )

        elif resume_type == "hitl_3_diagnosis_approval":
            result = resume_after_diagnosis_approval(
                thread_id   = thread_id,
                approved    = payload["approved"],
                doctor_note = payload.get("doctor_note", ""),
            )

        elif resume_type == "hitl_3b_crag_missing_data":
            result = resume_after_crag_missing_data(
                thread_id       = thread_id,
                additional_data = payload["additional_data"],
            )

        elif resume_type == "hitl_4_crag_confirmation":
            result = resume_after_crag_confirmation(
                thread_id        = thread_id,
                confirmed        = payload["confirmed"],
                doctor_final_note = payload.get("doctor_final_note", ""),
            )

        else:
            raise ValueError(f"Unknown resume_type: {resume_type}")

        # Update session status
        paused_at = result.get("paused_at")
        status    = result.get("status")

        if status == "complete":
            complete_session(session_id)
        else:
            update_session_stage(
                session_id    = session_id,
                current_stage = paused_at or "running",
                paused_at     = paused_at,
            )

        return {
            "status":    status,
            "paused_at": paused_at,
            "thread_id": thread_id,
        }

    except Exception as exc:
        fail_session(session_id, str(exc))
        raise self.retry(exc=exc)
