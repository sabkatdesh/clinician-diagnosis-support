from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from app.llm.clients import GPT_OSS_120B as CRAG_LLM

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

CONFIDENCE_THRESHOLD = 0.90   # 90% — below this, loop retries
MAX_CRAG_ATTEMPTS    = 3


# ─────────────────────────────────────────────
# PYDANTIC MODELS
# ─────────────────────────────────────────────

class CRAGCoTStep(BaseModel):
    step_number: int   = Field(..., description="Step number 1-6")
    step_name:   str   = Field(..., description="Name of this reasoning step")
    reasoning:   str   = Field(..., description="Detailed reasoning at this step")
    conclusion:  str   = Field(..., description="Conclusion from this step")
    confidence:  float = Field(..., ge=0.0, le=1.0, description="Confidence 0.0-1.0")


class RequiredTest(BaseModel):
    test_name:        str                              = Field(..., description="Name of the test or investigation")
    reason:           str                              = Field(..., description="Why this test is needed")
    priority:         Literal["urgent", "routine", "optional"] = Field(..., description="Priority of this test")
    expected_finding: str                              = Field(..., description="What finding would confirm or rule out the diagnosis")


class MissingDataItem(BaseModel):
    """Describes a specific piece of missing clinical information needed to raise confidence."""
    category:    Literal["symptom", "sign", "test_result", "history", "pattern"] = Field(
        ..., description="Category of missing data"
    )
    description: str  = Field(..., description="What specific data is missing")
    why_needed:  str  = Field(..., description="How this data would help confirm or rule out the diagnosis")
    question_for_doctor: str = Field(..., description="Exact question to ask the doctor to get this data")


class CRAGOutput(BaseModel):
    """
    CRAG: Contextual RAG Validation Output
    Validates provisional diagnosis against retrieved medical knowledge
    using 6-step Chain of Thought reasoning.
    """

    created_at: datetime = Field(default_factory=datetime.now)

    # ── Attempt tracking ──
    attempt_number: int = Field(..., description="Which attempt this is (1, 2, or 3)")

    # ── 6 CoT Steps ──
    step_1_summarize_rag:        CRAGCoTStep = Field(..., description="Step 1: Summarize key diagnostic criteria from RAG results")
    step_2_match_primary:        CRAGCoTStep = Field(..., description="Step 2: Match patient findings against primary diagnosis criteria")
    step_3_match_alternatives:   CRAGCoTStep = Field(..., description="Step 3: Match patient findings against alternative diagnoses")
    step_4_gap_analysis:         CRAGCoTStep = Field(..., description="Step 4: Identify gaps — missing criteria, conflicting findings")
    step_5_weigh_evidence:       CRAGCoTStep = Field(..., description="Step 5: Weigh evidence for and against each diagnosis")
    step_6_final_decision:       CRAGCoTStep = Field(..., description="Step 6: Reach final verdict and decide on required tests if needed")

    # ── Verdict ──
    verdict:          Literal["confirmed", "uncertain", "incorrect"] = Field(..., description="Verdict on the provisional diagnosis")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in the verdict (0.0-1.0)")

    # ── Loop control ──
    retry_recommended: bool = Field(
        ...,
        description="True if confidence < 0.90 AND attempt < 3 — signals the graph to loop"
    )
    missing_data: Optional[List[MissingDataItem]] = Field(
        None,
        description="List of specific missing data items that would raise confidence. Only populate if retry_recommended=True."
    )

    # ── Diagnosis Resolution ──
    validated_primary_diagnosis: str           = Field(..., description="The validated or corrected primary diagnosis")
    corrected_diagnosis:         Optional[str] = Field(None, description="Corrected diagnosis if verdict is incorrect")
    correction_reasoning:        Optional[str] = Field(None, description="Why the original diagnosis was incorrect")

    # ── Required Tests (if uncertain) ──
    required_tests: Optional[List[RequiredTest]] = Field(
        None, description="Tests needed to confirm diagnosis if verdict is uncertain"
    )

    # ── Final Output ──
    final_diagnosis:            str   = Field(..., description="The final diagnosis after CRAG validation")
    final_diagnosis_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the final diagnosis")
    clinical_reasoning_summary: str   = Field(..., description="Full narrative summary of how the final diagnosis was reached")

    # ── Evidence ──
    supporting_evidence: List[str] = Field(default_factory=list, description="Key findings that support the final diagnosis")
    against_evidence:    List[str] = Field(default_factory=list, description="Key findings that argue against or create uncertainty")

    # ── Safety ──
    red_flags:     Optional[List[str]] = Field(None, description="Any red flags or safety concerns identified")
    requires_hitl: bool                = Field(..., description="Whether human review is required")
    hitl_reason:   Optional[str]       = Field(None, description="Why human review is needed")


# ─────────────────────────────────────────────
# PARSER
# ─────────────────────────────────────────────

crag_parser = PydanticOutputParser(pydantic_object=CRAGOutput)


# ─────────────────────────────────────────────
# PROMPT
# ─────────────────────────────────────────────

crag_prompt = PromptTemplate(
    template="""You are a senior clinical decision support expert and medical knowledge validator.

Your task is to validate the provisional diagnosis by comparing:
1. The patient's full clinical data (complaints, examination, any test results provided)
2. The retrieved medical knowledge (RAG results) for each candidate diagnosis

This is attempt {attempt_number} of {max_attempts}.
Confidence threshold required to pass: {confidence_threshold_pct}%

You MUST complete ALL 6 reasoning steps. Do NOT skip any step.

=========================
PATIENT DATA
=========================

Chief Complaints & History:
{chief_complain}

Systemic Examination Findings:
{systemic_examination_text}

Structured Examination Findings:
{structured_exam_findings}

Additional Data Provided by Doctor (from previous attempt gaps):
{additional_data}

=========================
PROVISIONAL DIAGNOSES
=========================

Primary Diagnosis    : {primary_diagnosis} (Confidence: {primary_confidence})
Alternative 1        : {alt_diagnosis_1}   (Confidence: {alt1_confidence})
Alternative 2        : {alt_diagnosis_2}   (Confidence: {alt2_confidence})

Doctor's Note        : {doctor_note}

=========================
RAG RETRIEVED KNOWLEDGE
=========================

--- Knowledge for PRIMARY: {primary_diagnosis} ---
{primary_rag_results}

--- Knowledge for ALTERNATIVE 1: {alt_diagnosis_1} ---
{alt1_rag_results}

--- Knowledge for ALTERNATIVE 2: {alt_diagnosis_2} ---
{alt2_rag_results}

=========================
PREVIOUS ATTEMPT HISTORY (if any)
=========================
{attempt_history}

=========================
INSTRUCTIONS — COMPLETE ALL 6 STEPS
=========================

Step 1: Summarize RAG Knowledge
- What are the canonical diagnostic criteria for each of the 3 diagnoses per retrieved knowledge?
- What are the classic symptoms, signs, examination findings, and confirmatory tests for each?
- Provide: step_number=1, step_name, detailed reasoning, conclusion, confidence (0.0-1.0)

Step 2: Match Patient vs Primary Diagnosis
- How well does the patient's presentation match the PRIMARY diagnosis criteria from RAG?
- List criteria MET, criteria ABSENT, and any CONTRADICTING findings.
- Include any test results from additional_data if provided.
- Provide: step_number=2, step_name, detailed reasoning, conclusion, confidence (0.0-1.0)

Step 3: Match Patient vs Alternative Diagnoses
- How well does the patient match ALTERNATIVE 1 and ALTERNATIVE 2?
- Could either alternative explain the presentation better than the primary?
- Provide: step_number=3, step_name, detailed reasoning, conclusion, confidence (0.0-1.0)

Step 4: Gap Analysis
- What key diagnostic criteria are MISSING from the patient data?
- What specific symptoms, signs, patterns, or test results are needed to reach {confidence_threshold_pct}% confidence?
- Are there any findings that CONFLICT with the primary diagnosis?
- Provide: step_number=4, step_name, detailed reasoning, conclusion, confidence (0.0-1.0)

Step 5: Weigh All Evidence
- Summarize evidence FOR and AGAINST each diagnosis
- Which diagnosis has the strongest evidence match?
- What is the current confidence level and what is preventing it from reaching {confidence_threshold_pct}%?
- Provide: step_number=5, step_name, detailed reasoning, conclusion, confidence (0.0-1.0)

Step 6: Final Decision
- What is the final verdict: confirmed / uncertain / incorrect?
- State the confidence_score (0.0-1.0).
- If confidence_score < {confidence_threshold} AND attempt_number < {max_attempts}:
    → set retry_recommended = true
    → populate missing_data list with SPECIFIC items needed (category, description, why_needed, question_for_doctor)
- If confidence_score >= {confidence_threshold} OR attempt_number == {max_attempts}:
    → set retry_recommended = false
- If confirmed: state the final diagnosis with confidence score
- If uncertain: list the required_tests (name, reason, priority, expected_finding)
- If incorrect: state the corrected_diagnosis and correction_reasoning
- Provide: step_number=6, step_name, detailed reasoning, conclusion, confidence (0.0-1.0)

⚠️ CRITICAL JSON STRUCTURE REQUIREMENT ⚠️
The following fields MUST be at the TOP LEVEL of your JSON output:
- verdict (top-level, string: "confirmed"/"uncertain"/"incorrect")
- confidence_score (top-level, float: 0.0-1.0)
- retry_recommended (top-level, boolean)
- validated_primary_diagnosis (top-level, string)
- final_diagnosis (top-level, string)
- final_diagnosis_confidence (top-level, float: 0.0-1.0)
- clinical_reasoning_summary (top-level, string)
- requires_hitl (top-level, boolean)

Do NOT nest these fields inside step_6_final_decision or any other object.
They must be at the root level of your JSON.

=========================
VERDICT RULES
=========================

- "confirmed"  → Patient clearly meets the primary diagnosis criteria from RAG. Confidence >= 0.75.
- "uncertain"  → Patient partially meets criteria OR key confirmatory tests are missing.
- "incorrect"  → Patient clearly does NOT meet primary criteria but clearly meets an alternative.

=========================
RETRY RULES
=========================

- If confidence_score < {confidence_threshold} AND attempt_number < {max_attempts}:
    → retry_recommended = true
    → missing_data MUST be populated with specific actionable items
    → Each missing_data item must have a clear question_for_doctor
- If confidence_score >= {confidence_threshold} OR attempt_number == {max_attempts}:
    → retry_recommended = false
    → missing_data = null
    → Provide final_diagnosis regardless of confidence (best available answer)

=========================
OUTPUT REQUIREMENTS
=========================

OUTPUT REQUIREMENTS
⚠️ CRITICAL: ALL top-level fields must be at the root of your JSON, NOT nested!
⚠️ The parser will FAIL if verdict, confidence_score, retry_recommended, validated_primary_diagnosis, final_diagnosis, final_diagnosis_confidence, clinical_reasoning_summary, or requires_hitl are nested inside step_6.

- attempt_number           : MUST match the attempt number provided above
- All 6 steps              : MUST be complete
- verdict                  : TOP-LEVEL, MUST be confirmed / uncertain / incorrect
- confidence_score         : TOP-LEVEL, 0.0-1.0
- retry_recommended        : TOP-LEVEL, MUST be set per retry rules above
- missing_data             : TOP-LEVEL, ONLY if retry_recommended=true, list specific items
- validated_primary_diagnosis : TOP-LEVEL, MUST be present
- final_diagnosis          : TOP-LEVEL, MUST be present
- final_diagnosis_confidence  : TOP-LEVEL, MUST be present
- supporting_evidence      : TOP-LEVEL, list of key supporting findings
- against_evidence         : TOP-LEVEL, list of conflicting or missing findings
- required_tests           : TOP-LEVEL, ONLY if verdict is uncertain
- corrected_diagnosis      : TOP-LEVEL, ONLY if verdict is incorrect
- requires_hitl            : TOP-LEVEL, true if uncertain or incorrect or low confidence
- red_flags                : TOP-LEVEL, any safety concerns
- hitl_reason              : TOP-LEVEL, explanation if HITL required
- clinical_reasoning_summary : TOP-LEVEL, MUST be present

{format_instructions}
""",
    input_variables=[
        "attempt_number",
        "max_attempts",
        "confidence_threshold",
        "confidence_threshold_pct",
        "chief_complain",
        "systemic_examination_text",
        "structured_exam_findings",
        "additional_data",
        "primary_diagnosis",
        "primary_confidence",
        "alt_diagnosis_1",
        "alt1_confidence",
        "alt_diagnosis_2",
        "alt2_confidence",
        "doctor_note",
        "primary_rag_results",
        "alt1_rag_results",
        "alt2_rag_results",
        "attempt_history",
    ],
    partial_variables={"format_instructions": crag_parser.get_format_instructions()},
)


# ─────────────────────────────────────────────
# CHAIN
# ─────────────────────────────────────────────

crag_chain = crag_prompt | CRAG_LLM | crag_parser
