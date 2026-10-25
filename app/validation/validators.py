from typing import List, Tuple
from app.schemas.clinical import AIIntegration1Output, SystemicExaminationCoT


# ─────────────────────────────────────────────
# AI INTEGRATION 1 VALIDATOR
# ─────────────────────────────────────────────

def validate_ai_integration_output(output: AIIntegration1Output) -> Tuple[bool, List[str]]:
    """
    Validate AI Integration 1 output for completeness.
    Returns: (is_valid, list_of_errors)
    """
    errors = []

    # Check all 6 steps
    steps = [output.step_1, output.step_2, output.step_3, output.step_4, output.step_5, output.step_6]
    for i, step in enumerate(steps, 1):
        if step is None:
            errors.append(f"Step {i} is None - reasoning incomplete")
        elif step.step_number is None or step.reasoning is None or step.conclusion is None:
            errors.append(f"Step {i} is incomplete - missing required fields")

    # Check recommendations
    if output.primary_recommendation is None:
        errors.append("Primary recommendation is missing")
    elif output.primary_recommendation.exam_types is None or len(output.primary_recommendation.exam_types) == 0:
        errors.append("Primary recommendation has no exam types")

    if output.alternative_1 is None:
        errors.append("Alternative 1 recommendation is missing")
    elif output.alternative_1.exam_types is None or len(output.alternative_1.exam_types) == 0:
        errors.append("Alternative 1 has no exam types")

    if output.alternative_2 is None:
        errors.append("Alternative 2 recommendation is missing")
    elif output.alternative_2.exam_types is None or len(output.alternative_2.exam_types) == 0:
        errors.append("Alternative 2 has no exam types")

    # Check overall assessment
    if output.overall_confidence is None:
        errors.append("Overall confidence is missing")

    if output.clinical_summary is None:
        errors.append("Clinical summary is missing")

    # Check HITL flag
    if output.requires_hitl is None:
        errors.append("HITL requirement flag is missing")

    is_valid = len(errors) == 0
    return is_valid, errors


def handle_incomplete_output(output: AIIntegration1Output, errors: List[str]) -> AIIntegration1Output:
    """
    If output is incomplete, flag for HITL immediately.
    """
    output.requires_hitl = True
    output.hitl_reason = f"AI output validation failed with errors: {', '.join(errors)}. Human review required to complete analysis."
    return output


# ─────────────────────────────────────────────
# SYSTEMIC EXAMINATION COT VALIDATOR
# ─────────────────────────────────────────────

def validate_systemic_examination_cot(output: SystemicExaminationCoT) -> Tuple[bool, List[str]]:
    """
    Validate SystemicExaminationCoT output for completeness.
    Extracts diagnoses from step 6 conclusion if needed.
    Returns: (is_valid, list_of_errors)
    """
    errors = []

    # Normalize diagnosis fields: LLM sometimes returns dicts like
    # {"diagnosis": "...", "confidence": 0.88, "reasoning": "..."} instead of flat strings.
    def _extract_diag(field_val):
        if isinstance(field_val, dict):
            return field_val.get("diagnosis") or field_val.get("diagnosis_name")
        return field_val

    def _extract_conf(diag_field, conf_field):
        if conf_field is not None:
            return conf_field
        if isinstance(diag_field, dict):
            return diag_field.get("confidence")
        return conf_field

    if isinstance(output.primary_diagnosis, dict):
        output.primary_diagnosis_confidence = _extract_conf(output.primary_diagnosis, output.primary_diagnosis_confidence)
        if output.primary_diagnosis_reasoning is None:
            output.primary_diagnosis_reasoning = output.primary_diagnosis.get("reasoning")
        output.primary_diagnosis = _extract_diag(output.primary_diagnosis)

    if isinstance(output.alternative_diagnosis_1, dict):
        output.alternative_diagnosis_1_confidence = _extract_conf(output.alternative_diagnosis_1, output.alternative_diagnosis_1_confidence)
        output.alternative_diagnosis_1 = _extract_diag(output.alternative_diagnosis_1)

    if isinstance(output.alternative_diagnosis_2, dict):
        output.alternative_diagnosis_2_confidence = _extract_conf(output.alternative_diagnosis_2, output.alternative_diagnosis_2_confidence)
        output.alternative_diagnosis_2 = _extract_diag(output.alternative_diagnosis_2)

    # Extract diagnoses from step 6 conclusion if still missing
    if output.step_6_generate_provisional_diagnosis:
        step6_conclusion = output.step_6_generate_provisional_diagnosis.conclusion
        if isinstance(step6_conclusion, dict):
            if output.primary_diagnosis is None:
                output.primary_diagnosis = step6_conclusion.get('primary_diagnosis')
            if output.primary_diagnosis_confidence is None:
                output.primary_diagnosis_confidence = step6_conclusion.get('primary_diagnosis_confidence')
            if output.primary_diagnosis_reasoning is None:
                output.primary_diagnosis_reasoning = step6_conclusion.get('primary_diagnosis_reasoning')
            if output.alternative_diagnosis_1 is None:
                output.alternative_diagnosis_1 = step6_conclusion.get('alternative_diagnosis_1')
            if output.alternative_diagnosis_1_confidence is None:
                output.alternative_diagnosis_1_confidence = step6_conclusion.get('alternative_diagnosis_1_confidence')
            if output.alternative_diagnosis_2 is None:
                output.alternative_diagnosis_2 = step6_conclusion.get('alternative_diagnosis_2')
            if output.alternative_diagnosis_2_confidence is None:
                output.alternative_diagnosis_2_confidence = step6_conclusion.get('alternative_diagnosis_2_confidence')

    # Check all 6 steps
    steps = [
        output.step_1_organize_findings,
        output.step_2_identify_abnormalities,
        output.step_3_correlate_with_complaints,
        output.step_4_system_analysis,
        output.step_5_differential_narrowing,
        output.step_6_generate_provisional_diagnosis,
    ]

    for i, step in enumerate(steps, 1):
        if step is None:
            errors.append(f"Step {i} is None - reasoning incomplete")
        elif step.step_number is None or step.reasoning is None or step.conclusion is None:
            errors.append(f"Step {i} is incomplete - missing required fields")

    # Check diagnoses
    if output.primary_diagnosis is None:
        errors.append("Primary diagnosis is missing")

    if output.primary_diagnosis_confidence is None:
        errors.append("Primary diagnosis confidence is missing")

    if output.alternative_diagnosis_1 is None:
        errors.append("Alternative diagnosis 1 is missing")

    if output.alternative_diagnosis_1_confidence is None:
        errors.append("Alternative diagnosis 1 confidence is missing")

    if output.alternative_diagnosis_2 is None:
        errors.append("Alternative diagnosis 2 is missing")

    if output.alternative_diagnosis_2_confidence is None:
        errors.append("Alternative diagnosis 2 confidence is missing")

    # Check overall assessment
    if output.overall_confidence is None:
        errors.append("Overall confidence is missing")

    if output.clinical_summary is None:
        errors.append("Clinical summary is missing")

    if output.further_investigations_needed is None or len(output.further_investigations_needed) == 0:
        errors.append("Further investigations list is missing or empty")

    if output.supportive_management_plan is None or len(output.supportive_management_plan) == 0:
        errors.append("Supportive management plan is missing or empty")

    # Check HITL flag
    if output.requires_hitl is None:
        errors.append("HITL requirement flag is missing")

    is_valid = len(errors) == 0
    return is_valid, errors


def handle_incomplete_systemic_exam_output(output: SystemicExaminationCoT, errors: List[str]) -> SystemicExaminationCoT:
    """
    If output is incomplete, flag for HITL immediately.
    """
    output.requires_hitl = True
    output.hitl_reason = f"Systemic examination analysis validation failed with errors: {', '.join(errors)}. Human review required to complete diagnosis."
    return output



def normalize_exam_output(data: dict) -> dict:
    def lower_if_str(val):
        return val.lower() if isinstance(val, str) else val

    # RS Examination
    rs = data.get("rs_examination", {})
    if rs:
        rs["wheeze_type"] = lower_if_str(rs.get("wheeze_type"))
        rs["breath_sounds_character"] = lower_if_str(rs.get("breath_sounds_character"))

    # CNS Examination
    cns = data.get("cns_examination", {})
    if cns:
        cns["consciousness_level"] = lower_if_str(cns.get("consciousness_level"))

    return data
