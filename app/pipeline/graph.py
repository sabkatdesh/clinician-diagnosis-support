"""
graph.py — LangGraph pipeline with Supabase Postgres checkpointing and Supabase logging.

Changes from the original:
  - MemorySaver replaced with PostgresSaver checkpointer (Supabase)
  - Every node logs to Supabase via app.db.supabase_db
  - run_pipeline() and all resume_*() functions accept session_id, doctor_id, patient_id
  - Stage 1A updates patient demographics in Supabase after extraction
  - HITL nodes log pauses to hitl_logs
  - crag_node logs each attempt to crag_attempts
  - hitl_crag_node (HITL #4) writes the final_report on confirmation
  - Terminal runner (__main__) kept for local testing
"""

import json
import os
import re
import time
from typing import Optional, List, TypedDict

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

from app.llm.prompts import (
    structured_chief_complaints,
    systemic_examination_recommendation,
    systemic_exam_cot_recommendation,
    template_structured_step_3,
    LLAMA_3_70B,
)
from app.schemas.clinical import SystemicExaminationResults
from app.validation.validators import (
    validate_ai_integration_output,
    handle_incomplete_output,
    validate_systemic_examination_cot,
    handle_incomplete_systemic_exam_output,
    normalize_exam_output,
)
from app.pipeline.crag import crag_chain, CONFIDENCE_THRESHOLD, MAX_CRAG_ATTEMPTS, CRAGOutput
from app.retrieval.query_builder import build_query
from app.retrieval.chapters import get_chapter_matches
from app.retrieval.search import main as rag_search
import app.db.supabase_db as db

load_dotenv()

SUPABASE_DB_URL = os.environ.get("SUPABASE_DB_URL")

from langgraph.checkpoint.postgres import PostgresSaver
from contextlib import ExitStack
import atexit

_pg_stack = ExitStack()
checkpointer = _pg_stack.enter_context(
    PostgresSaver.from_conn_string(SUPABASE_DB_URL)
)
checkpointer.setup()
atexit.register(_pg_stack.close)


# ─────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────

class PipelineState(TypedDict):
    # ── Input ──
    chief_complain: str

    # ── Supabase IDs (injected by run_pipeline, carried through state) ──
    session_id:  Optional[str]
    doctor_id:   Optional[str]
    patient_id:  Optional[str]

    # ── Stage 1A ──
    patient_info: Optional[object]

    # ── Stage 1B ──
    exam_recommendation: Optional[object]

    # ── HITL #1 ──
    doctor_approved_recommendation: Optional[bool]
    doctor_modified_recommendation: Optional[str]

    # ── HITL #2 ──
    systemic_examination_text: Optional[str]

    # ── Stage 1C-i ──
    structured_exam_findings: Optional[object]

    # ── Stage 1C-ii ──
    provisional_diagnosis: Optional[object]

    # ── HITL #3 ──
    doctor_approved_diagnosis: Optional[bool]
    doctor_diagnosis_note: Optional[str]

    # ── RAG ──
    rag_results: Optional[dict]

    # ── CRAG loop ──
    crag_attempt:        int
    crag_output:         Optional[object]
    crag_history:        List[dict]
    crag_missing_data:   Optional[List[dict]]
    doctor_additional_data: Optional[str]

    # ── HITL #4 ──
    doctor_final_confirmed: Optional[bool]
    doctor_final_note:      Optional[str]


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _format_rag_results(results: list) -> str:
    if not results:
        return "No results retrieved."
    lines = []
    for i, r in enumerate(results, 1):
        content    = r.get("content") or r.get("page_content") or str(r)
        chapter    = r.get("chapter_title", "")
        subsection = r.get("subsection_title", "")
        lines.append(f"[{i}] {chapter} > {subsection}\n{content}")
    return "\n\n".join(lines)


def _format_attempt_history(history: list) -> str:
    if not history:
        return "No previous attempts."
    lines = []
    for h in history:
        lines.append(
            f"Attempt {h['attempt']}:\n"
            f"  Verdict          : {h['verdict']}\n"
            f"  Confidence       : {h['confidence']:.0%}\n"
            f"  Final Diagnosis  : {h['final_diagnosis']}\n"
            f"  Missing Data     : {h.get('missing_data_summary', 'None')}\n"
            f"  Doctor Response  : {h.get('doctor_response', 'None')}\n"
        )
    return "\n".join(lines)


def _ids(state: PipelineState) -> tuple:
    """Extract (session_id, doctor_id, patient_id) from state. Safe defaults for terminal runner."""
    return (
        state.get("session_id")  or "",
        state.get("doctor_id")   or "",
        state.get("patient_id")  or "",
    )




def normalize_crag_output(raw_output: dict) -> dict:
    """
    Extract missing top-level fields from step_6 if they're nested inside it.
    This handles cases where the LLM places verdict, confidence, etc. inside step_6_final_decision.
    """
    # If top-level fields are missing but step_6 exists, extract from there
    if 'verdict' not in raw_output and 'step_6_final_decision' in raw_output:
        step_6 = raw_output['step_6_final_decision']

        # Map fields from step_6 to root level
        raw_output['verdict'] = step_6.get('conclusion', 'uncertain')
        raw_output['confidence_score'] = step_6.get('confidence', 0.0)
        raw_output['retry_recommended'] = step_6.get('retry_recommended', False)
        raw_output['validated_primary_diagnosis'] = step_6.get('validated_primary_diagnosis', '')
        raw_output['final_diagnosis'] = step_6.get('final_diagnosis', '')
        raw_output['final_diagnosis_confidence'] = step_6.get('final_diagnosis_confidence', 0.0)
        raw_output['clinical_reasoning_summary'] = step_6.get('clinical_reasoning_summary', '')
        raw_output['requires_hitl'] = step_6.get('requires_hitl', True)
        raw_output['missing_data'] = step_6.get('missing_data', [])
        raw_output['required_tests'] = step_6.get('required_tests', [])
        raw_output['red_flags'] = step_6.get('red_flags', [])
        raw_output['hitl_reason'] = step_6.get('hitl_reason', '')
        raw_output['corrected_diagnosis'] = step_6.get('corrected_diagnosis')
        raw_output['correction_reasoning'] = step_6.get('correction_reasoning')

    # Also handle case where these fields are missing entirely
    # Set sensible defaults
    raw_output.setdefault('verdict', 'uncertain')
    raw_output.setdefault('confidence_score', 0.0)
    raw_output.setdefault('retry_recommended', False)
    raw_output.setdefault('validated_primary_diagnosis', raw_output.get('final_diagnosis', ''))
    raw_output.setdefault('requires_hitl', True)

    return raw_output

# ─────────────────────────────────────────────
# NODES
# ─────────────────────────────────────────────

def stage_1a(state: PipelineState) -> dict:
    print("\n" + "=" * 60)
    print("STAGE 1A: Extracting structured patient info...")
    print("=" * 60)

    session_id, doctor_id, patient_id = _ids(state)
    t0 = time.time()

    result = structured_chief_complaints.invoke({"info": state["chief_complain"]})
    print(result)

    # Update patient demographics in Supabase
    if patient_id:
        db.update_patient_from_stage_1a(patient_id, result)

    if session_id:
        db.log_stage(
            session_id   = session_id,
            doctor_id    = doctor_id,
            stage_name   = "stage_1a",
            stage_input  = {"chief_complain": state["chief_complain"]},
            stage_output = result,
            started_at   = t0,
        )

    return {"patient_info": result}


def stage_1b(state: PipelineState) -> dict:
    print("\n" + "=" * 60)
    print("STAGE 1B: Generating systemic examination recommendation...")
    print("=" * 60)

    session_id, doctor_id, _ = _ids(state)
    t0 = time.time()

    recommendation = systemic_examination_recommendation.invoke({
        "structured_info": state["patient_info"]
    })

    is_valid, errors = validate_ai_integration_output(recommendation)
    if not is_valid:
        print("❌ Validation failed:")
        for e in errors:
            print(f"  - {e}")
        recommendation = handle_incomplete_output(recommendation, errors)
    else:
        print("✅ Validation passed")

    if session_id:
        db.log_stage(
            session_id   = session_id,
            doctor_id    = doctor_id,
            stage_name   = "stage_1b",
            stage_input  = state["patient_info"],
            stage_output = recommendation,
            started_at   = t0,
        )

    return {"exam_recommendation": recommendation}


def hitl_approval_node(state: PipelineState) -> dict:
    """HITL #1 — Doctor approves or modifies exam recommendation."""

    if state.get("doctor_approved_recommendation") is not None:
        print("[HITL #1] Doctor input already received, continuing...")
        return {}

    session_id, doctor_id, _ = _ids(state)
    rec     = state["exam_recommendation"]
    primary = rec.primary_recommendation
    alt1    = rec.alternative_1
    alt2    = rec.alternative_2

    display = (
        "\n" + "=" * 70 + "\n"
        "⏸️  HITL PAUSE #1 — EXAM RECOMMENDATION APPROVAL\n"
        + "=" * 70 + "\n\n"
        f"PRIMARY  (rank 1): {primary.exam_types}  |  Confidence: {primary.confidence_score:.0%}\n"
        f"  Why: {primary.why_recommended}\n\n"
        f"ALT 1    (rank 2): {alt1.exam_types}  |  Confidence: {alt1.confidence_score:.0%}\n"
        f"  Why: {alt1.why_recommended}\n\n"
        f"ALT 2    (rank 3): {alt2.exam_types}  |  Confidence: {alt2.confidence_score:.0%}\n"
        f"  Why: {alt2.why_recommended}\n\n"
        f"Clinical Summary:\n  {rec.clinical_summary}\n\n"
        + "=" * 70 + "\n"
        "Options:\n"
        "  [A] Approve and proceed\n"
        "  [M] Type a modified recommendation\n"
        + "=" * 70 + "\n"
    )
    print(display)

    interrupt_payload = {
        "type":                   "recommendation_approval",
        "recommendation_summary": display,
        "message":                "Doctor: approve [A] or type modified recommendation [M]",
    }

    # Log the HITL pause
    if session_id:
        db.update_session_stage(session_id, "hitl_1_recommendation_approval", "hitl_1_recommendation_approval")

    interrupt(interrupt_payload)
    return {}


def hitl_exam_input_node(state: PipelineState) -> dict:
    """HITL #2 — Doctor types raw systemic examination findings."""

    if state.get("systemic_examination_text"):
        print("[HITL #2] Exam text already provided, continuing...")
        return {}

    session_id, doctor_id, _ = _ids(state)
    approved   = state.get("doctor_approved_recommendation")
    modified   = state.get("doctor_modified_recommendation", "")
    rec        = state["exam_recommendation"]
    exam_types = (
        rec.primary_recommendation.exam_types
        if approved
        else (modified or rec.primary_recommendation.exam_types)
    )

    display = (
        "\n" + "=" * 70 + "\n"
        "⏸️  HITL PAUSE #2 — SYSTEMIC EXAMINATION INPUT\n"
        + "=" * 70 + "\n\n"
        f"Recommended examination systems: {exam_types}\n\n"
        "Please type the full systemic examination findings.\n"
        "Include: Inspection, Palpation, Percussion, Auscultation\n"
        "for each recommended system.\n\n"
        + "=" * 70 + "\n"
    )
    print(display)

    if session_id:
        db.update_session_stage(session_id, "hitl_2_exam_input", "hitl_2_exam_input")

    interrupt({
        "type":                "exam_input",
        "recommended_systems": exam_types,
        "message":             "Doctor: please enter systemic examination findings",
    })
    return {}


def stage_1c_i(state: PipelineState) -> dict:
    print("\n" + "=" * 60)
    print("STAGE 1C-i: Structuring systemic examination findings...")
    print("=" * 60)

    session_id, doctor_id, _ = _ids(state)
    t0 = time.time()

    raw_output = (template_structured_step_3 | LLAMA_3_70B).invoke({
        "systemic_examination": state["systemic_examination_text"],
    })

    raw_text = raw_output.content.strip()
    print("RAW OUTPUT:", repr(raw_text[:200]))

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, flags=re.DOTALL)
    if match:
        raw_text = match.group(1).strip()
    else:
        match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
        raw_text = match.group(0).strip() if match else raw_text

    parsed_json = json.loads(raw_text)
    normalized  = normalize_exam_output(parsed_json)
    structured  = SystemicExaminationResults.model_validate(normalized)
    print(structured)

    if session_id:
        db.log_stage(
            session_id   = session_id,
            doctor_id    = doctor_id,
            stage_name   = "stage_1c_i",
            stage_input  = {"systemic_examination_text": state["systemic_examination_text"]},
            stage_output = structured,
            started_at   = t0,
        )

    return {"structured_exam_findings": structured}


def stage_1c_ii(state: PipelineState) -> dict:
    print("\n" + "=" * 60)
    print("STAGE 1C-ii: Generating provisional diagnosis...")
    print("=" * 60)

    session_id, doctor_id, _ = _ids(state)
    t0 = time.time()

    cot_output = systemic_exam_cot_recommendation.invoke({
        "patient_info":         state["patient_info"],
        "ai_recommendations":   state["exam_recommendation"],
        "examination_findings": state["structured_exam_findings"],
    })

    is_valid, errors = validate_systemic_examination_cot(cot_output)
    if not is_valid:
        print("❌ Validation failed:")
        for e in errors:
            print(f"  - {e}")
        cot_output = handle_incomplete_systemic_exam_output(cot_output, errors)
    else:
        print("✅ Validation passed")

    print("\nPrimary Diagnosis :", cot_output.primary_diagnosis)
    print("Confidence        :", cot_output.primary_diagnosis_confidence)
    print("Alternative 1     :", cot_output.alternative_diagnosis_1)
    print("Alternative 2     :", cot_output.alternative_diagnosis_2)

    if session_id:
        db.log_stage(
            session_id   = session_id,
            doctor_id    = doctor_id,
            stage_name   = "stage_1c_ii",
            stage_input  = {
                "patient_info":         str(state["patient_info"]),
                "structured_exam_findings": str(state["structured_exam_findings"]),
            },
            stage_output = cot_output,
            started_at   = t0,
        )

    return {"provisional_diagnosis": cot_output}


def hitl_diagnosis_node(state: PipelineState) -> dict:
    """HITL #3 — Doctor approves provisional diagnosis before RAG is triggered."""

    if state.get("doctor_approved_diagnosis") is not None:
        print("[HITL #3] Diagnosis approval already received, continuing...")
        return {}

    session_id, doctor_id, _ = _ids(state)
    diag = state["provisional_diagnosis"]

    def _pct(val):
        return f"{val:.0%}" if val is not None else "N/A"

    display = (
        "\n" + "=" * 70 + "\n"
        "⏸️  HITL PAUSE #3 — PROVISIONAL DIAGNOSIS APPROVAL\n"
        + "=" * 70 + "\n\n"
        f"PRIMARY DIAGNOSIS  : {diag.primary_diagnosis}\n"
        f"  Confidence       : {_pct(diag.primary_diagnosis_confidence)}\n\n"
        f"ALTERNATIVE 1      : {diag.alternative_diagnosis_1}\n"
        f"  Confidence       : {_pct(diag.alternative_diagnosis_1_confidence)}\n\n"
        f"ALTERNATIVE 2      : {diag.alternative_diagnosis_2}\n"
        f"  Confidence       : {_pct(diag.alternative_diagnosis_2_confidence)}\n\n"
        f"Clinical Summary   : {diag.clinical_summary}\n\n"
        f"Safety Concerns    : {diag.safety_concerns}\n\n"
        + "=" * 70 + "\n"
        "Options:\n"
        "  [A] Approve — proceed to RAG + CRAG validation\n"
        "  [N] Add a note / correction before RAG\n"
        + "=" * 70 + "\n"
    )
    print(display)

    if session_id:
        db.update_session_stage(session_id, "hitl_3_diagnosis_approval", "hitl_3_diagnosis_approval")

    interrupt({
        "type":              "diagnosis_approval",
        "diagnosis_summary": display,
        "message":           "Doctor: approve [A] or add a note/correction [N]",
    })
    return {}


def rag_node(state: PipelineState) -> dict:
    """RAG retrieval for all 3 provisional diagnoses."""

    print("\n" + "=" * 60)
    print("RAG NODE: Retrieving medical knowledge for all diagnoses...")
    print("=" * 60)

    session_id, doctor_id, _ = _ids(state)
    t0   = time.time()
    diag = state["provisional_diagnosis"]

    primary = diag.primary_diagnosis
    alt1    = diag.alternative_diagnosis_1
    alt2    = diag.alternative_diagnosis_2

    print(f"  Primary : {primary}")
    print(f"  Alt 1   : {alt1}")
    print(f"  Alt 2   : {alt2}")

    chapter_matches  = get_chapter_matches(primary, alt1, alt2)

    primary_chapters = [str(x["chapter_number"]) for x in chapter_matches["primary_disease"]       if x["chapter_number"] is not None]
    alt1_chapters    = [str(x["chapter_number"]) for x in chapter_matches["alternative_disease_1"]  if x["chapter_number"] is not None]
    alt2_chapters    = [str(x["chapter_number"]) for x in chapter_matches["alternative_disease_2"]  if x["chapter_number"] is not None]

    print(f"\n  Primary chapters : {primary_chapters}")
    print(f"  Alt1 chapters    : {alt1_chapters}")
    print(f"  Alt2 chapters    : {alt2_chapters}")

    if session_id:
        db.update_session_stage(session_id, "rag_node")

    print("\n[RAG] Searching primary...")
    primary_results = rag_search(query=build_query(primary, "diagnosis"), target_chapter_numbers=primary_chapters, disease_term=primary)

    print("[RAG] Searching alt 1...")
    alt1_results    = rag_search(query=build_query(alt1, "diagnosis"),    target_chapter_numbers=alt1_chapters,    disease_term=alt1)

    print("[RAG] Searching alt 2...")
    alt2_results    = rag_search(query=build_query(alt2, "diagnosis"),    target_chapter_numbers=alt2_chapters,    disease_term=alt2)

    rag_results = {
        "primary_results": primary_results,
        "alt1_results":    alt1_results,
        "alt2_results":    alt2_results,
    }

    if session_id:
        db.log_stage(
            session_id   = session_id,
            doctor_id    = doctor_id,
            stage_name   = "rag_node",
            stage_input  = {"primary": primary, "alt1": alt1, "alt2": alt2},
            stage_output = {
                "primary_count": len(primary_results),
                "alt1_count":    len(alt1_results),
                "alt2_count":    len(alt2_results),
            },
            started_at   = t0,
        )

    return {"rag_results": rag_results}

def crag_node(state: PipelineState) -> dict:
    """CRAG — 6-step CoT validation with confidence loop."""

    attempt     = state.get("crag_attempt", 1)
    history     = state.get("crag_history", [])
    extra_data  = state.get("doctor_additional_data") or "None provided."
    doctor_note = state.get("doctor_diagnosis_note") or "None."

    session_id, doctor_id, _ = _ids(state)
    t0 = time.time()

    print("\n" + "=" * 60)
    print(f"CRAG NODE: Attempt {attempt} of {MAX_CRAG_ATTEMPTS}...")
    print("=" * 60)

    diag = state["provisional_diagnosis"]
    rag  = state["rag_results"]

    if session_id:
        db.update_session_stage(session_id, f"crag_node_attempt_{attempt}")

    # ── Get raw output from LLM ──
    raw_crag_output = crag_chain.invoke({
        "attempt_number":           attempt,
        "max_attempts":             MAX_CRAG_ATTEMPTS,
        "confidence_threshold":     CONFIDENCE_THRESHOLD,
        "confidence_threshold_pct": int(CONFIDENCE_THRESHOLD * 100),
        "chief_complain":           state["chief_complain"],
        "systemic_examination_text": state.get("systemic_examination_text", ""),
        "structured_exam_findings": str(state["structured_exam_findings"]),
        "additional_data":          extra_data,
        "primary_diagnosis":        diag.primary_diagnosis,
        "primary_confidence":       f"{diag.primary_diagnosis_confidence:.0%}" if diag.primary_diagnosis_confidence is not None else "N/A",
        "alt_diagnosis_1":          diag.alternative_diagnosis_1,
        "alt1_confidence":          f"{diag.alternative_diagnosis_1_confidence:.0%}" if diag.alternative_diagnosis_1_confidence is not None else "N/A",
        "alt_diagnosis_2":          diag.alternative_diagnosis_2,
        "alt2_confidence":          f"{diag.alternative_diagnosis_2_confidence:.0%}" if diag.alternative_diagnosis_2_confidence is not None else "N/A",
        "doctor_note":              doctor_note,
        "primary_rag_results":      _format_rag_results(rag.get("primary_results", [])),
        "alt1_rag_results":         _format_rag_results(rag.get("alt1_results",    [])),
        "alt2_rag_results":         _format_rag_results(rag.get("alt2_results",    [])),
        "attempt_history":          _format_attempt_history(history),
    })

    # ── Normalize: extract nested fields from step_6 if needed ──
    raw_output = raw_crag_output.dict() if hasattr(raw_crag_output, 'dict') else raw_crag_output
    normalized_output = normalize_crag_output(raw_output)

    # ── Parse into CRAGOutput with fallback ──
    try:
        crag_output = CRAGOutput.model_validate(normalized_output)
    except Exception as e:
        print(f"CRAG parsing failed even after normalization: {e}")
        # Fallback: create a minimal valid CRAGOutput
        crag_output = CRAGOutput(
            attempt_number=attempt,
            step_1_summarize_rag=normalized_output.get('step_1_summarize_rag', {}),
            step_2_match_primary=normalized_output.get('step_2_match_primary', {}),
            step_3_match_alternatives=normalized_output.get('step_3_match_alternatives', {}),
            step_4_gap_analysis=normalized_output.get('step_4_gap_analysis', {}),
            step_5_weigh_evidence=normalized_output.get('step_5_weigh_evidence', {}),
            step_6_final_decision=normalized_output.get('step_6_final_decision', {}),
            verdict=normalized_output.get('verdict', 'uncertain'),
            confidence_score=normalized_output.get('confidence_score', 0.0),
            retry_recommended=normalized_output.get('retry_recommended', False),
            validated_primary_diagnosis=normalized_output.get('validated_primary_diagnosis', ''),
            final_diagnosis=normalized_output.get('final_diagnosis', ''),
            final_diagnosis_confidence=normalized_output.get('final_diagnosis_confidence', 0.0),
            clinical_reasoning_summary=normalized_output.get('clinical_reasoning_summary', ''),
            requires_hitl=normalized_output.get('requires_hitl', True),
            missing_data=normalized_output.get('missing_data', []),
            required_tests=normalized_output.get('required_tests', []),
            red_flags=normalized_output.get('red_flags', []),
            hitl_reason=normalized_output.get('hitl_reason', ''),
            corrected_diagnosis=normalized_output.get('corrected_diagnosis'),
            correction_reasoning=normalized_output.get('correction_reasoning'),
            supporting_evidence=normalized_output.get('supporting_evidence', []),
            against_evidence=normalized_output.get('against_evidence', []),
        )

    print(f"\n  Verdict          : {crag_output.verdict}")
    print(f"  Confidence       : {crag_output.confidence_score:.0%}")
    print(f"  Final Diagnosis  : {crag_output.final_diagnosis}")
    print(f"  Retry Recommended: {crag_output.retry_recommended}")

    # ── Build history entry ──
    missing_summary = ""
    if crag_output.missing_data:
        missing_summary = "; ".join(
            f"{m.category}: {m.description}" for m in crag_output.missing_data
        )

    new_history_entry = {
        "attempt":              attempt,
        "verdict":              crag_output.verdict,
        "confidence":           crag_output.confidence_score,
        "final_diagnosis":      crag_output.final_diagnosis,
        "missing_data_summary": missing_summary,
        "doctor_response":      extra_data,
    }
    updated_history = history + [new_history_entry]

    missing_dicts = None
    if crag_output.missing_data:
        missing_dicts = [m.dict() for m in crag_output.missing_data]

    # ── Log to Supabase ──
    if session_id:
        db.log_crag_attempt(
            session_id      = session_id,
            doctor_id       = doctor_id,
            attempt_number  = attempt,
            crag_output     = crag_output,
            doctor_response = extra_data if extra_data != "None provided." else None,
        )
        db.log_stage(
            session_id   = session_id,
            doctor_id    = doctor_id,
            stage_name   = f"crag_node_attempt_{attempt}",
            stage_input  = {"attempt": attempt, "extra_data": extra_data},
            stage_output = crag_output,
            started_at   = t0,
        )

    return {
        "crag_output":            crag_output,
        "crag_attempt":           attempt,
        "crag_history":           updated_history,
        "crag_missing_data":      missing_dicts,
        "doctor_additional_data": None,
    }


def hitl_crag_missing_node(state: PipelineState) -> dict:
    """HITL #3b — CRAG needs more data from doctor."""

    if state.get("doctor_additional_data") is not None:
        print("[HITL #3b] Additional data already provided, continuing...")
        return {}

    session_id, doctor_id, _ = _ids(state)
    crag    = state["crag_output"]
    attempt = state.get("crag_attempt", 1)
    missing = state.get("crag_missing_data", [])

    missing_display = ""
    questions = []
    if missing:
        for i, m in enumerate(missing, 1):
            missing_display += (
                f"\n  {i}. [{m.get('category', 'data').upper()}] {m.get('description', '')}\n"
                f"     Why needed     : {m.get('why_needed', '')}\n"
                f"     Question       : {m.get('question_for_doctor', '')}\n"
            )
            questions.append(m.get("question_for_doctor", ""))
    else:
        missing_display = "\n  No specific items listed — general confidence too low.\n"

    display = (
        "\n" + "=" * 70 + "\n"
        f"⏸️  HITL PAUSE #3b — CRAG NEEDS MORE DATA (Attempt {attempt}/{MAX_CRAG_ATTEMPTS})\n"
        + "=" * 70 + "\n\n"
        f"Current Verdict    : {crag.verdict.upper()}\n"
        f"Current Confidence : {crag.confidence_score:.0%}  (threshold: {int(CONFIDENCE_THRESHOLD*100)}%)\n"
        f"Current Diagnosis  : {crag.final_diagnosis}\n\n"
        "The following data is MISSING to reach sufficient confidence:\n"
        + missing_display
        + "\nPlease provide the missing clinical data / test results below.\n"
        + "=" * 70 + "\n"
    )
    print(display)

    interrupt_payload = {
        "type":              "crag_missing_data",
        "attempt":           attempt,
        "max_attempts":      MAX_CRAG_ATTEMPTS,
        "confidence":        crag.confidence_score,
        "threshold":         CONFIDENCE_THRESHOLD,
        "missing_items":     missing,
        "questions":         questions,
        "current_diagnosis": crag.final_diagnosis,
        "message":           "Doctor: please provide the missing clinical data",
    }

    if session_id:
        db.update_session_stage(session_id, "hitl_3b_crag_missing_data", "hitl_3b_crag_missing_data")

    interrupt(interrupt_payload)
    return {}


def hitl_crag_node(state: PipelineState) -> dict:
    """HITL #4 — Doctor reviews final CRAG verdict and confirms."""

    if state.get("doctor_final_confirmed") is not None:
        print("[HITL #4] Final confirmation already received, continuing...")

        # Write final report on the way through
        session_id, doctor_id, patient_id = _ids(state)
        if session_id and state.get("crag_output"):
            db.save_final_report(
                session_id          = session_id,
                patient_id          = patient_id,
                doctor_id           = doctor_id,
                crag_output         = state["crag_output"],
                doctor_confirmed    = state.get("doctor_final_confirmed", False),
                doctor_final_note   = state.get("doctor_final_note"),
                total_crag_attempts = len(state.get("crag_history", [])),
            )
            db.complete_session(session_id)
        return {}

    session_id, doctor_id, _ = _ids(state)
    crag    = state["crag_output"]
    history = state.get("crag_history", [])

    tests_display = ""
    if crag.required_tests:
        tests_display = "\nREQUIRED TESTS:\n"
        for t in crag.required_tests:
            tests_display += (
                f"  • {t.test_name} [{t.priority.upper()}]\n"
                f"    Reason          : {t.reason}\n"
                f"    Expected Finding: {t.expected_finding}\n"
            )
    else:
        tests_display = "\n  No additional tests required.\n"

    supporting = "\n".join(f"  ✓ {e}" for e in crag.supporting_evidence) or "  None listed"
    against    = "\n".join(f"  ✗ {e}" for e in crag.against_evidence)    or "  None listed"

    attempts_summary = f"\n(Reached after {len(history)} CRAG attempts)\n" if len(history) > 1 else ""

    display = (
        "\n" + "=" * 70 + "\n"
        "⏸️  HITL PAUSE #4 — FINAL CRAG VALIDATION RESULT\n"
        + "=" * 70
        + attempts_summary + "\n"
        f"VERDICT             : {crag.verdict.upper()}\n"
        f"CONFIDENCE          : {crag.confidence_score:.0%}\n\n"
        f"PROVISIONAL DX      : {state['provisional_diagnosis'].primary_diagnosis}\n"
        f"VALIDATED DX        : {crag.validated_primary_diagnosis}\n"
        + (f"CORRECTED DX        : {crag.corrected_diagnosis}\n"   if crag.corrected_diagnosis   else "")
        + (f"CORRECTION REASON   : {crag.correction_reasoning}\n"  if crag.correction_reasoning  else "")
        + f"\nFINAL DIAGNOSIS     : {crag.final_diagnosis}\n"
        f"FINAL CONFIDENCE    : {crag.final_diagnosis_confidence:.0%}\n\n"
        f"CLINICAL SUMMARY:\n  {crag.clinical_reasoning_summary}\n\n"
        f"SUPPORTING EVIDENCE:\n{supporting}\n\n"
        f"AGAINST EVIDENCE:\n{against}\n"
        + tests_display
        + (f"\nRED FLAGS:\n" + "\n".join(f"  ⚠ {r}" for r in crag.red_flags) + "\n" if crag.red_flags else "")
        + "\n" + "=" * 70 + "\n"
        "Options:\n"
        "  [C] Confirm final diagnosis\n"
        "  [N] Add a note / override\n"
        + "=" * 70 + "\n"
    )
    print(display)

    if session_id:
        db.update_session_stage(session_id, "hitl_4_crag_confirmation", "hitl_4_crag_confirmation")

    interrupt({
        "type":            "crag_confirmation",
        "crag_summary":    display,
        "verdict":         crag.verdict,
        "final_diagnosis": crag.final_diagnosis,
        "confidence":      crag.confidence_score,
        "required_tests":  [t.dict() for t in crag.required_tests] if crag.required_tests else [],
        "attempts_taken":  len(history),
        "message":         "Doctor: confirm [C] or add note/override [N]",
    })
    return {}


# ─────────────────────────────────────────────
# ROUTING
# ─────────────────────────────────────────────

def route_after_crag(state: PipelineState) -> str:
    crag = state.get("crag_output")
    if crag and crag.retry_recommended:
        print(f"[CRAG ROUTER] Confidence {crag.confidence_score:.0%} < {CONFIDENCE_THRESHOLD:.0%} — routing to missing data HITL")
        return "hitl_crag_missing_node"
    print(f"[CRAG ROUTER] Confidence sufficient (or max attempts) — routing to final HITL")
    return "hitl_crag_node"


def increment_crag_attempt(state: PipelineState) -> dict:
    current = state.get("crag_attempt", 1)
    print(f"[CRAG] Incrementing attempt {current} → {current + 1}")
    return {"crag_attempt": current + 1}


# ─────────────────────────────────────────────
# GRAPH
# ─────────────────────────────────────────────

workflow = StateGraph(PipelineState)

workflow.add_node("stage_1a",               stage_1a)
workflow.add_node("stage_1b",               stage_1b)
workflow.add_node("hitl_approval_node",     hitl_approval_node)
workflow.add_node("hitl_exam_input_node",   hitl_exam_input_node)
workflow.add_node("stage_1c_i",             stage_1c_i)
workflow.add_node("stage_1c_ii",            stage_1c_ii)
workflow.add_node("hitl_diagnosis_node",    hitl_diagnosis_node)
workflow.add_node("rag_node",               rag_node)
workflow.add_node("crag_node",              crag_node)
workflow.add_node("hitl_crag_missing_node", hitl_crag_missing_node)
workflow.add_node("increment_crag_attempt", increment_crag_attempt)
workflow.add_node("hitl_crag_node",         hitl_crag_node)

workflow.add_edge(START,                    "stage_1a")
workflow.add_edge("stage_1a",               "stage_1b")
workflow.add_edge("stage_1b",               "hitl_approval_node")
workflow.add_edge("hitl_approval_node",     "hitl_exam_input_node")
workflow.add_edge("hitl_exam_input_node",   "stage_1c_i")
workflow.add_edge("stage_1c_i",             "stage_1c_ii")
workflow.add_edge("stage_1c_ii",            "hitl_diagnosis_node")
workflow.add_edge("hitl_diagnosis_node",    "rag_node")
workflow.add_edge("rag_node",               "crag_node")

workflow.add_conditional_edges(
    "crag_node",
    route_after_crag,
    {
        "hitl_crag_missing_node": "hitl_crag_missing_node",
        "hitl_crag_node":         "hitl_crag_node",
    }
)
workflow.add_edge("hitl_crag_missing_node", "increment_crag_attempt")
workflow.add_edge("increment_crag_attempt", "crag_node")
workflow.add_edge("hitl_crag_node",         END)

app = workflow.compile(checkpointer=checkpointer)


# ─────────────────────────────────────────────
# API FUNCTIONS — called by Celery tasks / FastAPI
# ─────────────────────────────────────────────

def run_pipeline(
    thread_id:      str,
    chief_complain: str,
    session_id:     str = "",
    doctor_id:      str = "",
    patient_id:     str = "",
) -> dict:
    """Start the pipeline. Runs until the first HITL pause."""
    config = {"configurable": {"thread_id": thread_id}}

    initial_state: PipelineState = {
        "chief_complain":                  chief_complain,
        "session_id":                      session_id,
        "doctor_id":                       doctor_id,
        "patient_id":                      patient_id,
        "patient_info":                    None,
        "exam_recommendation":             None,
        "doctor_approved_recommendation":  None,
        "doctor_modified_recommendation":  None,
        "systemic_examination_text":       None,
        "structured_exam_findings":        None,
        "provisional_diagnosis":           None,
        "doctor_approved_diagnosis":       None,
        "doctor_diagnosis_note":           None,
        "rag_results":                     None,
        "crag_attempt":                    1,
        "crag_output":                     None,
        "crag_history":                    [],
        "crag_missing_data":               None,
        "doctor_additional_data":          None,
        "doctor_final_confirmed":          None,
        "doctor_final_note":               None,
    }

    for event in app.stream(initial_state, config):
        pass

    return get_pipeline_state(thread_id)


def get_pipeline_state(thread_id: str) -> dict:
    """Returns current LangGraph state + which HITL node it's paused at."""
    config     = {"configurable": {"thread_id": thread_id}}
    state      = app.get_state(config)

    if not state:
        return {"status": "not_found"}

    next_nodes = list(state.next) if state.next else []

    paused_at = None
    if   "hitl_approval_node"     in next_nodes: paused_at = "hitl_1_recommendation_approval"
    elif "hitl_exam_input_node"    in next_nodes: paused_at = "hitl_2_exam_input"
    elif "hitl_diagnosis_node"     in next_nodes: paused_at = "hitl_3_diagnosis_approval"
    elif "hitl_crag_missing_node"  in next_nodes: paused_at = "hitl_3b_crag_missing_data"
    elif "hitl_crag_node"          in next_nodes: paused_at = "hitl_4_crag_confirmation"

    return {
        "values":    state.values,
        "paused_at": paused_at,
        "next":      next_nodes,
        "status":    "complete" if not next_nodes else "paused",
    }


def resume_after_approval(thread_id: str, approved: bool, modified_recommendation: str = "") -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    app.update_state(config, {
        "doctor_approved_recommendation": approved,
        "doctor_modified_recommendation": modified_recommendation if not approved else "",
    })
    for event in app.stream(None, config): pass
    return get_pipeline_state(thread_id)


def resume_after_exam_input(thread_id: str, exam_text: str) -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    app.update_state(config, {"systemic_examination_text": exam_text})
    for event in app.stream(None, config): pass
    return get_pipeline_state(thread_id)


def resume_after_diagnosis_approval(thread_id: str, approved: bool, doctor_note: str = "") -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    app.update_state(config, {
        "doctor_approved_diagnosis": approved,
        "doctor_diagnosis_note":     doctor_note,
    })
    for event in app.stream(None, config): pass
    return get_pipeline_state(thread_id)


def resume_after_crag_missing_data(thread_id: str, additional_data: str) -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    app.update_state(config, {"doctor_additional_data": additional_data})
    for event in app.stream(None, config): pass
    return get_pipeline_state(thread_id)


def resume_after_crag_confirmation(thread_id: str, confirmed: bool, doctor_final_note: str = "") -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    app.update_state(config, {
        "doctor_final_confirmed": confirmed,
        "doctor_final_note":      doctor_final_note,
    })
    for event in app.stream(None, config): pass
    return get_pipeline_state(thread_id)


# ─────────────────────────────────────────────
# TERMINAL RUNNER — local testing without FastAPI
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uuid
    thread_id = str(uuid.uuid4())
    print(f"\nThread ID: {thread_id}\n")

    print("Enter chief complaints (type END on a new line to finish):")
    lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)
    chief_complain_input = "\n".join(lines)

    # Run without Supabase IDs for local testing
    state = run_pipeline(thread_id, chief_complain_input)
    print(f"\n[PAUSED AT]: {state['paused_at']}")

    choice = input("\nApprove recommendation? [A/M]: ").strip().upper()
    if choice == "A":
        state = resume_after_approval(thread_id, approved=True)
    else:
        modified = input("Type modified recommendation:\n> ").strip()
        state = resume_after_approval(thread_id, approved=False, modified_recommendation=modified)

    print(f"\n[PAUSED AT]: {state['paused_at']}")

    print("\nEnter systemic examination findings (type END on a new line to finish):")
    lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)
    state = resume_after_exam_input(thread_id, "\n".join(lines))

    print(f"\n[PAUSED AT]: {state['paused_at']}")

    choice = input("\nApprove provisional diagnosis? [A/N]: ").strip().upper()
    if choice == "A":
        state = resume_after_diagnosis_approval(thread_id, approved=True)
    else:
        note = input("Add your note/correction:\n> ").strip()
        state = resume_after_diagnosis_approval(thread_id, approved=False, doctor_note=note)

    while state.get("paused_at") == "hitl_3b_crag_missing_data":
        print(f"\n[PAUSED AT]: {state['paused_at']}")
        print("\nProvide missing clinical data (type END on a new line to finish):")
        lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        state = resume_after_crag_missing_data(thread_id, "\n".join(lines))

    print(f"\n[PAUSED AT]: {state['paused_at']}")

    choice = input("\nConfirm final diagnosis? [C/N]: ").strip().upper()
    if choice == "C":
        state = resume_after_crag_confirmation(thread_id, confirmed=True)
    else:
        note = input("Add your final note/override:\n> ").strip()
        state = resume_after_crag_confirmation(thread_id, confirmed=False, doctor_final_note=note)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    crag = state["values"].get("crag_output")
    if crag:
        print(f"Final Diagnosis  : {crag.final_diagnosis}")
        print(f"Verdict          : {crag.verdict}")
        print(f"Confidence       : {crag.final_diagnosis_confidence:.0%}")
        attempts = state["values"].get("crag_history", [])
        print(f"CRAG Attempts    : {len(attempts)}")
        if crag.required_tests:
            print("\nRequired Tests:")
            for t in crag.required_tests:
                print(f"  • {t.test_name} [{t.priority}] — {t.reason}")
