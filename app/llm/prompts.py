import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from app.schemas.clinical import (
    PatientInfo,
    AIIntegration1Output,
    SystemicExaminationResults,
    SystemicExaminationCoT,
)
from app.validation.validators import normalize_exam_output
from app.llm.clients import (
    GPT_OSS_120B,
    GPT_OSS_20B,
    LLAMA_3_70B,
    LLAMA_4_SCOUT,
)

load_dotenv()

# ─────────────────────────────────────────────
# PARSERS
# ─────────────────────────────────────────────

structured_parser_step_1 = PydanticOutputParser(pydantic_object=PatientInfo)
structured_parser_step_2 = PydanticOutputParser(pydantic_object=AIIntegration1Output)
structured_parser_step_3 = PydanticOutputParser(pydantic_object=SystemicExaminationResults)
structured_parser_step_2_cot = PydanticOutputParser(pydantic_object=SystemicExaminationCoT)


# ─────────────────────────────────────────────
# PROMPT TEMPLATES
# ─────────────────────────────────────────────

template_structured_step_1 = PromptTemplate(
    template="""You are a medical professional extracting patient information from clinical notes.

INSTRUCTIONS:
- Extract ALL available information from the provided clinical notes
- If information is not mentioned, leave it as None
- Do NOT hallucinate or assume information
- For admission_datetime: if not explicitly mentioned, use current date/time
- Be precise and complete

Clinical Notes:
{info}

Extract and structure the information according to the following format:

{format_instructions}""",
    input_variables=["info"],
    partial_variables={"format_instructions": structured_parser_step_1.get_format_instructions()},
)


template_structured_step_2 = PromptTemplate(
    template="""You are an expert medical professional. Analyze the structured patient data and perform 6-step Chain of Thought reasoning to determine which systemic examinations are needed.

CRITICAL: You MUST complete ALL 6 steps. You MUST provide primary recommendation + 2 alternatives. Do NOT skip any steps.

Patient Data:
{structured_info}

INSTRUCTIONS - COMPLETE ALL 6 STEPS:

Step 1: Analyze Chief Complaints
- What are the main complaints?
- How long have they been present?
- What severity level?
- Provide: step_number=1, step_name, detailed reasoning, conclusion, confidence (0.0-1.0)

Step 2: Interpret Vital Signs
- Are vitals abnormal?
- What do abnormalities suggest?
- Signs of infection, dehydration, hemodynamic compromise?
- Provide: step_number=2, step_name, detailed reasoning, conclusion, confidence (0.0-1.0)

Step 3: Analyze Examination Findings
- What physical findings are significant?
- Do findings support the complaints?
- Any red flags or emergency signs?
- Provide: step_number=3, step_name, detailed reasoning, conclusion, confidence (0.0-1.0)

Step 4: Identify Clinical Context
- Which body systems are involved?
- What are possible diagnoses?
- Are there risk factors or comorbidities?
- Provide: step_number=4, step_name, detailed reasoning, conclusion, confidence (0.0-1.0)

Step 5: Pattern Recognition
- How do all findings connect together?
- What clinical syndrome does this suggest?
- Are there multiple system involvements?
- Provide: step_number=5, step_name, detailed reasoning, conclusion, confidence (0.0-1.0)

Step 6: Generate Examination Recommendations
- Which systemic exams are NEEDED? (Can be multiple: CVS, RS, CNS, GIT, GUS, MSK)
- Rank them by priority/importance
- Provide reasoning for each recommendation
- Provide: step_number=6, step_name, detailed reasoning, conclusion, confidence (0.0-1.0)

MANDATORY RECOMMENDATIONS (ALL THREE REQUIRED):
Provide EXACTLY 3 exam recommendations ranked by priority:
1. Primary recommendation (rank=1): Most important exam(s) needed
2. Alternative 1 (rank=2): Second most important exam(s)
3. Alternative 2 (rank=3): Third most important exam(s)

Each recommendation MUST include:
- rank: 1, 2, or 3
- exam_types: List of exam types (CVS, RS, CNS, GIT, GUS, MSK)
- confidence_score: 0.0-1.0
- why_recommended: Detailed explanation
- supporting_findings: List of findings supporting this recommendation

FINAL OUTPUT REQUIREMENTS:
- step_1: MUST be complete
- step_2: MUST be complete
- step_3: MUST be complete
- step_4: MUST be complete
- step_5: MUST be complete
- step_6: MUST be complete
- primary_recommendation: MUST be present
- alternative_1: MUST be present
- alternative_2: MUST be present
- overall_confidence: Average of all step confidences
- clinical_summary: MUST summarize the clinical picture
- knowledge_gaps: List any missing information
- requires_hitl: Boolean indicating if human review needed
- hitl_reason: Explanation if HITL required

Do NOT leave any step as None. Do NOT skip recommendations. Complete everything.

{format_instructions}""",
    input_variables=["structured_info"],
    partial_variables={"format_instructions": structured_parser_step_2.get_format_instructions()},
)


template_structured_step_3 = PromptTemplate(
    template="""You are an experienced clinician performing systemic examinations. Based on the patient data and AI recommendations, extract and structure the examination findings.

INSTRUCTIONS:
- Extract examination findings for ONLY the recommended systemic exams
- For each exam type recommended, provide specific structured findings
- If a finding is not mentioned, leave it as None
- Be precise and do NOT hallucinate findings
- Use the exact field names and values as specified
- Return valid JSON only

CRITICAL ENUM RULES:
For fields with restricted values, you MUST return ONLY one of the allowed literals exactly as written.

Allowed literal values:
- rs_examination.breath_sounds_character: "normal", "diminished", "absent"
- rs_examination.wheeze_type: "expiratory", "inspiratory", "biphasic"
- cns_examination.consciousness_level: "alert", "drowsy", "lethargic", "stuporous", "comatose"

STRICT RULES:
- Use lowercase only for literal fields
- Do NOT paraphrase literal values
- Do NOT add extra descriptive words inside literal fields
- If the source text contains richer clinical wording that does not exactly fit a literal field, map it to the closest allowed literal if safe
- Put extra descriptive clinical details in other_findings
- If no safe mapping is possible, use None

Examples:
- "Expiratory" → "expiratory"
- "Alert" → "alert"
- "Vesicular with prolonged expiratory phase" → breath_sounds_character="normal", other_findings="Vesicular with prolonged expiratory phase"

the systemic examination : {systemic_examination}

{format_instructions}""",
    input_variables=["systemic_examination"],
    partial_variables={"format_instructions": structured_parser_step_3.get_format_instructions()},
)


template_structured_step_2_cot = PromptTemplate(
    template="""You are an expert clinician analyzing systemic examination findings. Perform 6-step Chain of Thought reasoning to generate a provisional diagnosis.

CRITICAL: You MUST complete ALL 6 steps. You MUST provide primary diagnosis + 2 alternatives. Do NOT skip any steps.

Patient Data:
{patient_info}

AI Recommendations from Step 1:
{ai_recommendations}

Systemic Examination Findings:
{examination_findings}

INSTRUCTIONS - COMPLETE ALL 6 STEPS:

Step 1: Organize Examination Findings
- Organize findings by each examined system (CVS, RS, CNS, GIT, GUS, MSK)
- List normal and abnormal findings for each system
- Provide: step_number=1, step_name, detailed reasoning, conclusion, confidence (0.0-1.0)

Step 2: Identify Abnormalities
- What findings are abnormal?
- How significant are these abnormalities?
- Do they point to specific pathologies?
- Provide: step_number=2, step_name, detailed reasoning, conclusion, confidence (0.0-1.0)

Step 3: Correlate with Chief Complaints
- How do examination findings relate to chief complaints?
- Do findings explain the patient's symptoms?
- Are there unexpected findings?
- Provide: step_number=3, step_name, detailed reasoning, conclusion, confidence (0.0-1.0)

Step 4: System Analysis
- Analyze involvement of each body system
- Which systems are affected?
- What is the pattern of involvement?
- Provide: step_number=4, step_name, detailed reasoning, conclusion, confidence (0.0-1.0)

Step 5: Differential Diagnosis Narrowing
- Based on findings, what diagnoses are likely?
- What diagnoses can be ruled out?
- What is the differential diagnosis list?
- Provide: step_number=5, step_name, detailed reasoning, conclusion, confidence (0.0-1.0)

Step 6: Generate Provisional Diagnosis
- What is the MOST likely diagnosis?
- What are 2 alternative diagnoses?
- Provide reasoning for each
- Provide: step_number=6, step_name, detailed reasoning, conclusion, confidence (0.0-1.0)

MANDATORY DIAGNOSES (ALL THREE REQUIRED):
1. primary_diagnosis: Most likely diagnosis with confidence score
2. alternative_diagnosis_1: Second most likely with confidence score
3. alternative_diagnosis_2: Third most likely with confidence score

Each diagnosis MUST include:
- Diagnosis name
- Confidence score (0.0-1.0)
- Reasoning for diagnosis

FINAL OUTPUT REQUIREMENTS:
- step_1_organize_findings: MUST be complete
- step_2_identify_abnormalities: MUST be complete
- step_3_correlate_with_complaints: MUST be complete
- step_4_system_analysis: MUST be complete
- step_5_differential_narrowing: MUST be complete
- step_6_generate_provisional_diagnosis: MUST be complete
- primary_diagnosis: MUST be present with confidence
- alternative_diagnosis_1: MUST be present with confidence
- alternative_diagnosis_2: MUST be present with confidence
- overall_confidence: Average of all step confidences
- clinical_summary: MUST summarize findings and diagnosis
- further_investigations_needed: List tests/imaging needed
- supportive_management_plan: List supportive care measures
- safety_concerns: Any red flags identified
- requires_hitl: Boolean for human review
- hitl_reason: Explanation if needed

Do NOT leave any step as None. Do NOT skip diagnoses. Complete everything.

{format_instructions}""",
    input_variables=["patient_info", "ai_recommendations", "examination_findings"],
    partial_variables={"format_instructions": structured_parser_step_2_cot.get_format_instructions()},
)




# ─────────────────────────────────────────────
# CHAINS
# ─────────────────────────────────────────────

# Step 1: Clinical notes → structured PatientInfo
structured_chief_complaints = template_structured_step_1 | GPT_OSS_20B | structured_parser_step_1

# Step 2: PatientInfo → examination recommendation (6-step CoT)
systemic_examination_recommendation = template_structured_step_2 | GPT_OSS_120B | structured_parser_step_2

# Step 3a: Raw systemic exam text → structured SystemicExaminationResults
systemic_examination_structured = template_structured_step_3 | GPT_OSS_20B | structured_parser_step_3

# Step 3b: All inputs → provisional diagnosis (6-step CoT)
systemic_exam_cot_recommendation = template_structured_step_2_cot | LLAMA_4_SCOUT | structured_parser_step_2_cot
