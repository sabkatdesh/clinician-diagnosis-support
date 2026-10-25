from typing import List, Optional, Literal, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# ─────────────────────────────────────────────
# PATIENT INFO MODELS
# ─────────────────────────────────────────────

class GeneralInfo(BaseModel):
    name: Optional[str] = Field(default=None, description="Name of the patient")
    age: Optional[int] = Field(default=None, ge=0, le=130, description="Age of the patient")
    gender: Optional[Literal["Male", "Female", "Other"]] = Field(default=None, description="Gender of the patient")
    admission_datetime: datetime = Field(default_factory=datetime.now, description="Date & time of admission")
    patient_id: Optional[str] = Field(default=None, description="Patient ID/MRN")
    contact_number: Optional[str] = Field(default=None, description="Contact number")
    address: Optional[str] = Field(default=None, description="Address of the patient")


class PastMedicalHistory(BaseModel):
    past_illnesses: Optional[List[str]] = Field(default=None, description="Past medical conditions, e.g. diabetes, hypertension")
    surgical_history: Optional[List[str]] = Field(default=None, description="Past surgeries and dates")
    family_history: Optional[List[str]] = Field(default=None, description="Family history of diseases")
    birth_history: Optional[str] = Field(default=None, description="Birth history, complications")
    immunization_status: Optional[str] = Field(default=None, description="Immunization status and vaccines")


class DrugHistory(BaseModel):
    current_medications: Optional[List[str]] = Field(default=None, description="Current medications with dosage")
    drug_allergies: Optional[List[str]] = Field(default=None, description="Drug allergies and reactions")
    previous_adverse_reactions: Optional[List[str]] = Field(default=None, description="Previous adverse drug reactions")
    duration_of_medication: Optional[str] = Field(default=None, description="Duration of current medications")


class SocioeconomicHistory(BaseModel):
    socioeconomic_status: Optional[Literal["low", "lower-middle", "middle", "upper-middle", "high"]] = Field(default=None, description="Socioeconomic status")
    occupation: Optional[str] = Field(default=None, description="Patient occupation")
    diet: Optional[str] = Field(default=None, description="Dietary habits")
    smoking: Optional[str] = Field(default=None, description="Smoking habits, cigarettes per day")
    alcohol: Optional[str] = Field(default=None, description="Alcohol consumption")
    water_source: Optional[str] = Field(default=None, description="Source of drinking water")
    sleep_pattern: Optional[str] = Field(default=None, description="Sleep pattern and quality")
    stress_level: Optional[str] = Field(default=None, description="Stress level")


class ChiefComplaints(BaseModel):
    chief_complaints: Optional[List[str]] = Field(default=None, description="List of chief complaints")
    duration_of_complaints: Optional[str] = Field(default=None, description="Duration of complaints, e.g. 5 days, 2 weeks")
    severity: Optional[Literal["mild", "moderate", "severe", "critical"]] = Field(default=None, description="Severity of complaints")
    onset: Optional[Literal["sudden", "gradual"]] = Field(default=None, description="Onset of complaints")
    progression: Optional[str] = Field(default=None, description="How complaints have progressed")


class VitalSigns(BaseModel):
    temperature: Optional[float] = Field(default=None, description="Temperature in Celsius or Fahrenheit")
    temperature_unit: Optional[Literal["Celsius", "Fahrenheit"]] = Field(default=None, description="Temperature unit")
    blood_pressure_systolic: Optional[int] = Field(default=None, description="Systolic BP in mmHg")
    blood_pressure_diastolic: Optional[int] = Field(default=None, description="Diastolic BP in mmHg")
    heart_rate: Optional[int] = Field(default=None, ge=20, le=300, description="Heart rate in bpm")
    respiratory_rate: Optional[int] = Field(default=None, ge=5, le=100, description="Respiratory rate per minute")
    spo2: Optional[float] = Field(default=None, ge=0, le=100, description="Oxygen saturation %")
    weight: Optional[float] = Field(default=None, gt=0, description="Weight in kg")
    height: Optional[float] = Field(default=None, gt=0, description="Height in cm")
    bmi: Optional[float] = Field(default=None, description="BMI")
    muac: Optional[float] = Field(default=None, description="Mid-upper arm circumference")


class GeneralExamination(BaseModel):
    appearance: Optional[str] = Field(default=None, description="Patient appearance, e.g. ill-looking, well")
    pallor: Optional[bool] = Field(default=None, description="Presence of pallor")
    jaundice: Optional[bool] = Field(default=None, description="Presence of jaundice")
    cyanosis: Optional[bool] = Field(default=None, description="Presence of cyanosis")
    clubbing: Optional[bool] = Field(default=None, description="Presence of clubbing")
    koilonychia: Optional[bool] = Field(default=None, description="Presence of koilonychia")
    leukonychia: Optional[bool] = Field(default=None, description="Presence of leukonychia")
    edema: Optional[str] = Field(default=None, description="Location and type of edema")
    dehydration: Optional[bool] = Field(default=None, description="Signs of dehydration")
    tongue: Optional[str] = Field(default=None, description="Tongue findings, e.g. dry, coated, strawberry")
    lips: Optional[str] = Field(default=None, description="Lip findings")
    eyes: Optional[str] = Field(default=None, description="Eye findings")
    lymph_nodes: Optional[str] = Field(default=None, description="Lymph node findings, location and size")
    bcg_mark: Optional[bool] = Field(default=None, description="BCG mark present")
    ear_nose_throat: Optional[str] = Field(default=None, description="ENT findings")
    oral_cavity: Optional[str] = Field(default=None, description="Oral cavity findings")
    bony_tenderness: Optional[bool] = Field(default=None, description="Bony tenderness present")
    meningeal_irritation: Optional[bool] = Field(default=None, description="Signs of meningeal irritation")
    bedside_urine_albumin: Optional[str] = Field(default=None, description="Bedside urine albumin test result")


class PatientInfo(BaseModel):
    general_info: GeneralInfo
    chief_complaints: ChiefComplaints
    general_examination: GeneralExamination
    vital_signs: VitalSigns
    past_medical_history: Optional[PastMedicalHistory] = Field(default=None, description="Patient's past medical history")
    drug_history: DrugHistory
    socioeconomic_history: Optional[SocioeconomicHistory] = Field(default=None, description="Patient's socioeconomic background")


# ─────────────────────────────────────────────
# CHAIN OF THOUGHT & AI INTEGRATION 1 MODELS
# ─────────────────────────────────────────────

class CoTStep(BaseModel):
    """Single step in Chain of Thought reasoning"""
    step_number: Optional[int] = Field(None, description="Step number 1-6")
    step_name: Optional[str] = Field(None, description="Name of this reasoning step")
    reasoning: Optional[str] = Field(None, description="Detailed reasoning at this step")
    conclusion: Optional[Union[str, List[str], dict]] = Field(None, description="Conclusion from this step")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence 0-1")
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ExaminationRecommendation(BaseModel):
    """Single examination recommendation"""
    rank: Optional[int] = Field(None, ge=1, le=3, description="Rank 1-3")
    exam_types: Optional[List[Literal["CVS", "RS", "CNS", "GIT", "GUS", "MSK"]]] = Field(
        None, description="Types of systemic examinations needed"
    )
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence 0-1")
    why_recommended: Optional[str] = Field(None, description="Why these exams are recommended")
    supporting_findings: Optional[List[str]] = Field(None, description="Clinical findings supporting this")


class AIIntegration1Output(BaseModel):
    """
    AI System Integration 1: Stage 1 Problem Identification
    6-Step Chain of Thought with Structured Recommendations
    """
    # 6 CoT Steps
    step_1: Optional[CoTStep] = Field(None, description="Step 1: Analyze Chief Complaints")
    step_2: Optional[CoTStep] = Field(None, description="Step 2: Interpret Vital Signs")
    step_3: Optional[CoTStep] = Field(None, description="Step 3: Analyze Examination Findings")
    step_4: Optional[CoTStep] = Field(None, description="Step 4: Identify Clinical Context")
    step_5: Optional[CoTStep] = Field(None, description="Step 5: Pattern Recognition")
    step_6: Optional[CoTStep] = Field(None, description="Step 6: Generate Recommendations")

    # Recommendations (3 options)
    primary_recommendation: Optional[ExaminationRecommendation] = Field(
        None, description="Primary recommended examination"
    )
    alternative_1: Optional[ExaminationRecommendation] = Field(
        None, description="Alternative recommendation 1"
    )
    alternative_2: Optional[ExaminationRecommendation] = Field(
        None, description="Alternative recommendation 2"
    )

    # Overall Assessment
    overall_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Overall confidence in recommendations"
    )
    clinical_summary: Optional[str] = Field(
        None, description="Summary of clinical assessment"
    )
    knowledge_gaps: Optional[List[str]] = Field(
        None, description="Missing information"
    )
    requires_hitl: Optional[bool] = Field(
        None, description="Does this require human review?"
    )
    hitl_reason: Optional[str] = Field(
        None, description="Why HITL is needed (if applicable)"
    )


# ─────────────────────────────────────────────
# SYSTEMIC EXAMINATION MODELS
# ─────────────────────────────────────────────

class CVSExamination(BaseModel):
    """Cardiovascular System Examination"""
    inspection_findings: Optional[str] = Field(None, description="Inspection findings (scars, deformities, chest shape)")
    apex_beat_location: Optional[str] = Field(None, description="Location of apex beat (normal/displaced)")
    apex_beat_character: Optional[str] = Field(None, description="Character of apex beat (normal/hyperdynamic/weak)")

    s1_normal: Optional[bool] = Field(None, description="S1 sound normal")
    s2_normal: Optional[bool] = Field(None, description="S2 sound normal")

    murmur_present: Optional[bool] = Field(None, description="Murmur present")
    murmur_type: Optional[Literal["systolic", "diastolic", "continuous"]] = Field(None, description="Type of murmur")
    murmur_location: Optional[str] = Field(None, description="Location of murmur (aortic area, mitral area, etc)")
    murmur_intensity: Optional[Literal["1/6", "2/6", "3/6", "4/6", "5/6", "6/6"]] = Field(None, description="Murmur intensity")
    murmur_description: Optional[str] = Field(None, description="Additional murmur characteristics")

    additional_heart_sounds: Optional[str] = Field(None, description="S3, S4, or other sounds")

    radial_pulse_present: Optional[bool] = Field(None, description="Radial pulse palpable")
    radial_pulse_rate: Optional[int] = Field(None, ge=20, le=300, description="Radial pulse rate")
    radial_pulse_character: Optional[Literal["normal", "weak", "bounding", "irregular"]] = Field(None, description="Pulse character")

    femoral_pulse_present: Optional[bool] = Field(None, description="Femoral pulse palpable")
    pedal_pulse_present: Optional[bool] = Field(None, description="Dorsalis pedis pulse palpable")

    blood_pressure_systolic: Optional[int] = Field(None, description="Systolic BP in mmHg")
    blood_pressure_diastolic: Optional[int] = Field(None, description="Diastolic BP in mmHg")

    jvp_elevation: Optional[bool] = Field(None, description="JVP elevated")
    jvp_height: Optional[str] = Field(None, description="JVP height measurement")

    edema_present: Optional[bool] = Field(None, description="Peripheral edema present")
    edema_location: Optional[str] = Field(None, description="Location of edema (ankles, feet, sacral)")
    edema_grade: Optional[Literal["+1", "+2", "+3", "+4"]] = Field(None, description="Edema grading")

    capillary_refill: Optional[str] = Field(None, description="Capillary refill time (normal/delayed)")

    other_findings: Optional[str] = Field(None, description="Other CVS findings")


class RSExamination(BaseModel):
    """Respiratory System Examination"""
    chest_movement_symmetry: Optional[bool] = Field(None, description="Chest movement symmetric")
    chest_expansion_normal: Optional[bool] = Field(None, description="Chest expansion normal")

    percussion_findings: Optional[str] = Field(None, description="Percussion findings (resonant/dull/hyperresonant)")
    percussion_location: Optional[str] = Field(None, description="Location of abnormal percussion")

    breath_sounds_bilateral: Optional[bool] = Field(None, description="Breath sounds bilateral and equal")
    breath_sounds_character: Optional[str] = Field(None, description="Character of breath sounds")
    breath_sounds_location: Optional[str] = Field(None, description="Location of abnormal breath sounds")

    wheeze_present: Optional[bool] = Field(None, description="Wheeze present")
    wheeze_type: Optional[Literal["expiratory", "inspiratory", "biphasic"]] = Field(None, description="Type of wheeze")
    wheeze_location: Optional[str] = Field(None, description="Location of wheeze")

    crackles_present: Optional[bool] = Field(None, description="Crackles/rales present")
    crackles_type: Optional[Literal["fine", "coarse"]] = Field(None, description="Type of crackles")
    crackles_location: Optional[str] = Field(None, description="Location of crackles")

    rhonchi_present: Optional[bool] = Field(None, description="Rhonchi present")

    stridor_present: Optional[bool] = Field(None, description="Stridor present")
    stridor_type: Optional[Literal["inspiratory", "expiratory"]] = Field(None, description="Type of stridor")

    friction_rub_present: Optional[bool] = Field(None, description="Pleural friction rub present")

    accessory_muscle_use: Optional[bool] = Field(None, description="Accessory muscle use present")

    other_findings: Optional[str] = Field(None, description="Other RS findings")


class CNSExamination(BaseModel):
    """Central Nervous System Examination"""
    consciousness_level: Optional[Literal["alert", "drowsy", "lethargic", "stuporous", "comatose"]] = Field(None, description="Level of consciousness")

    orientation_person: Optional[bool] = Field(None, description="Oriented to person")
    orientation_place: Optional[bool] = Field(None, description="Oriented to place")
    orientation_time: Optional[bool] = Field(None, description="Oriented to time")

    gcs_score: Optional[int] = Field(None, ge=3, le=15, description="Glasgow Coma Scale score")

    pupil_size_right: Optional[str] = Field(None, description="Right pupil size (mm)")
    pupil_size_left: Optional[str] = Field(None, description="Left pupil size (mm)")
    pupil_reaction_right: Optional[Literal["reactive", "sluggish", "fixed"]] = Field(None, description="Right pupil reaction to light")
    pupil_reaction_left: Optional[Literal["reactive", "sluggish", "fixed"]] = Field(None, description="Left pupil reaction to light")

    cranial_nerve_2: Optional[str] = Field(None, description="CN II - Vision and visual fields")
    cranial_nerve_3: Optional[str] = Field(None, description="CN III - Oculomotor")
    cranial_nerve_4: Optional[str] = Field(None, description="CN IV - Trochlear")
    cranial_nerve_5: Optional[str] = Field(None, description="CN V - Trigeminal")
    cranial_nerve_6: Optional[str] = Field(None, description="CN VI - Abducens")
    cranial_nerve_7: Optional[str] = Field(None, description="CN VII - Facial")
    cranial_nerve_8: Optional[str] = Field(None, description="CN VIII - Vestibulocochlear")
    cranial_nerve_9: Optional[str] = Field(None, description="CN IX - Glossopharyngeal")
    cranial_nerve_10: Optional[str] = Field(None, description="CN X - Vagus")
    cranial_nerve_11: Optional[str] = Field(None, description="CN XI - Accessory")
    cranial_nerve_12: Optional[str] = Field(None, description="CN XII - Hypoglossal")

    motor_power_right_upper: Optional[Literal["0", "1", "2", "3", "4", "5"]] = Field(None, description="Motor power right upper limb (0-5)")
    motor_power_right_lower: Optional[Literal["0", "1", "2", "3", "4", "5"]] = Field(None, description="Motor power right lower limb (0-5)")
    motor_power_left_upper: Optional[Literal["0", "1", "2", "3", "4", "5"]] = Field(None, description="Motor power left upper limb (0-5)")
    motor_power_left_lower: Optional[Literal["0", "1", "2", "3", "4", "5"]] = Field(None, description="Motor power left lower limb (0-5)")

    muscle_tone: Optional[Literal["normal", "hypotonic", "hypertonic", "rigid"]] = Field(None, description="Muscle tone")

    reflexes_biceps: Optional[Literal["normal", "brisk", "absent", "exaggerated"]] = Field(None, description="Biceps reflex")
    reflexes_triceps: Optional[Literal["normal", "brisk", "absent", "exaggerated"]] = Field(None, description="Triceps reflex")
    reflexes_knee: Optional[Literal["normal", "brisk", "absent", "exaggerated"]] = Field(None, description="Knee reflex")
    reflexes_ankle: Optional[Literal["normal", "brisk", "absent", "exaggerated"]] = Field(None, description="Ankle reflex")

    plantar_response_right: Optional[Literal["flexor", "extensor", "equivocal"]] = Field(None, description="Right plantar response")
    plantar_response_left: Optional[Literal["flexor", "extensor", "equivocal"]] = Field(None, description="Left plantar response")

    sensory_light_touch: Optional[str] = Field(None, description="Light touch sensation findings")
    sensory_pain: Optional[str] = Field(None, description="Pain sensation findings")
    sensory_vibration: Optional[str] = Field(None, description="Vibration sense findings")
    sensory_proprioception: Optional[str] = Field(None, description="Proprioception findings")

    coordination_finger_nose: Optional[str] = Field(None, description="Finger-nose test findings")
    coordination_heel_shin: Optional[str] = Field(None, description="Heel-shin test findings")
    coordination_dysdiadochokinesia: Optional[bool] = Field(None, description="Dysdiadochokinesia present")

    gait: Optional[str] = Field(None, description="Gait findings (normal/ataxic/spastic/etc)")
    romberg_test: Optional[str] = Field(None, description="Romberg test findings")

    meningeal_irritation_neck_stiffness: Optional[bool] = Field(None, description="Neck stiffness present")
    meningeal_irritation_kernig_sign: Optional[bool] = Field(None, description="Kernig sign positive")
    meningeal_irritation_brudzinski_sign: Optional[bool] = Field(None, description="Brudzinski sign positive")

    other_findings: Optional[str] = Field(None, description="Other CNS findings")


class GITExamination(BaseModel):
    """Gastrointestinal System Examination"""
    general_appearance: Optional[str] = Field(None, description="General appearance of abdomen")
    distension_present: Optional[bool] = Field(None, description="Abdominal distension present")
    scars_present: Optional[bool] = Field(None, description="Surgical scars present")
    scars_location: Optional[str] = Field(None, description="Location and description of scars")

    inspection_findings: Optional[str] = Field(None, description="Other inspection findings")

    palpation_tenderness: Optional[bool] = Field(None, description="Abdominal tenderness present")
    palpation_tenderness_location: Optional[str] = Field(None, description="Location of tenderness (epigastric, RUQ, etc)")

    guarding_present: Optional[bool] = Field(None, description="Muscle guarding present")
    rigidity_present: Optional[bool] = Field(None, description="Abdominal rigidity present")

    rebound_tenderness: Optional[bool] = Field(None, description="Rebound tenderness present")

    hepatomegaly: Optional[bool] = Field(None, description="Hepatomegaly present")
    liver_edge_cm: Optional[float] = Field(None, description="Liver edge palpable (cm below costal margin)")
    liver_consistency: Optional[Literal["normal", "hard", "soft"]] = Field(None, description="Liver consistency")

    splenomegaly: Optional[bool] = Field(None, description="Splenomegaly present")
    spleen_size: Optional[str] = Field(None, description="Spleen size/palpability")

    kidney_palpable: Optional[bool] = Field(None, description="Kidney palpable")
    cvat_tenderness: Optional[bool] = Field(None, description="CVA tenderness present")

    masses_present: Optional[bool] = Field(None, description="Abdominal masses present")
    masses_description: Optional[str] = Field(None, description="Description of masses")

    percussion_findings: Optional[str] = Field(None, description="Percussion findings (tympany/dullness)")
    ascites_present: Optional[bool] = Field(None, description="Ascites present")

    bowel_sounds_present: Optional[bool] = Field(None, description="Bowel sounds present")
    bowel_sounds_character: Optional[str] = Field(None, description="Character of bowel sounds (normal/increased/decreased/absent)")

    other_findings: Optional[str] = Field(None, description="Other GIT findings")


class GUSExamination(BaseModel):
    """Genitourinary System Examination"""
    kidney_palpation_right: Optional[str] = Field(None, description="Right kidney palpation findings")
    kidney_palpation_left: Optional[str] = Field(None, description="Left kidney palpation findings")

    cvat_right: Optional[bool] = Field(None, description="Right CVA tenderness present")
    cvat_left: Optional[bool] = Field(None, description="Left CVA tenderness present")

    suprapubic_tenderness: Optional[bool] = Field(None, description="Suprapubic tenderness present")

    bladder_distension: Optional[bool] = Field(None, description="Bladder distension present")
    bladder_palpable: Optional[bool] = Field(None, description="Bladder palpable")

    genitalia_inspection: Optional[str] = Field(None, description="External genitalia inspection findings")

    urethral_discharge: Optional[bool] = Field(None, description="Urethral discharge present")
    discharge_description: Optional[str] = Field(None, description="Description of discharge")

    testicular_examination: Optional[str] = Field(None, description="Testicular examination findings (males)")
    testicular_size: Optional[str] = Field(None, description="Testicular size")
    testicular_consistency: Optional[str] = Field(None, description="Testicular consistency")

    prostate_examination: Optional[str] = Field(None, description="Prostate examination findings (males)")
    prostate_size: Optional[Literal["normal", "enlarged"]] = Field(None, description="Prostate size")

    inguinal_lymph_nodes: Optional[str] = Field(None, description="Inguinal lymph node findings")

    other_findings: Optional[str] = Field(None, description="Other GUS findings")


class MSKExamination(BaseModel):
    """Musculoskeletal System Examination"""
    general_inspection: Optional[str] = Field(None, description="General inspection (deformities, swelling, etc)")

    joint_examined: Optional[List[str]] = Field(None, description="Joints examined")

    joint_swelling: Optional[bool] = Field(None, description="Joint swelling present")
    swelling_location: Optional[str] = Field(None, description="Location of swelling")
    swelling_type: Optional[Literal["soft tissue", "bony", "effusion"]] = Field(None, description="Type of swelling")

    joint_deformity: Optional[bool] = Field(None, description="Joint deformity present")
    deformity_description: Optional[str] = Field(None, description="Description of deformity")

    erythema_present: Optional[bool] = Field(None, description="Joint erythema present")

    warmth_present: Optional[bool] = Field(None, description="Joint warmth present")

    range_of_motion_right: Optional[str] = Field(None, description="Right side ROM findings")
    range_of_motion_left: Optional[str] = Field(None, description="Left side ROM findings")

    tenderness_present: Optional[bool] = Field(None, description="Joint tenderness present")
    tenderness_location: Optional[str] = Field(None, description="Location of tenderness")

    muscle_strength_right: Optional[Literal["0", "1", "2", "3", "4", "5"]] = Field(None, description="Right side muscle strength (0-5)")
    muscle_strength_left: Optional[Literal["0", "1", "2", "3", "4", "5"]] = Field(None, description="Left side muscle strength (0-5)")

    muscle_atrophy: Optional[bool] = Field(None, description="Muscle atrophy present")
    atrophy_location: Optional[str] = Field(None, description="Location of atrophy")

    special_tests: Optional[str] = Field(None, description="Special tests performed (McMurray, Lachman, etc)")
    special_tests_findings: Optional[str] = Field(None, description="Findings of special tests")

    other_findings: Optional[str] = Field(None, description="Other MSK findings")


class SystemicExaminationResults(BaseModel):
    """Container for all systemic examination results"""
    examination_datetime: datetime = Field(default_factory=datetime.now, description="Date/time of examination")
    examining_physician_id: Optional[str] = Field(None, description="ID of physician performing examination")

    cvs_examination: Optional[CVSExamination] = Field(None, description="Cardiovascular examination if performed")
    rs_examination: Optional[RSExamination] = Field(None, description="Respiratory examination if performed")
    cns_examination: Optional[CNSExamination] = Field(None, description="CNS examination if performed")
    git_examination: Optional[GITExamination] = Field(None, description="GIT examination if performed")
    gus_examination: Optional[GUSExamination] = Field(None, description="GUS examination if performed")
    msk_examination: Optional[MSKExamination] = Field(None, description="MSK examination if performed")

    overall_findings_summary: Optional[str] = Field(None, description="Overall summary of systemic examination findings")


# ─────────────────────────────────────────────
# AI INTEGRATION 2: SYSTEMIC EXAMINATION COT
# ─────────────────────────────────────────────

class SystemicExaminationCoT(BaseModel):
    """
    AI System Integration 2: Systemic Examination Analysis
    6-Step Chain of Thought reasoning for examination findings
    """
    # Metadata
    integration_id: str
    session_id: str
    ai_model: str
    created_at: datetime

    # 6 CoT Steps for Systemic Examination Analysis
    step_1_organize_findings: Optional[CoTStep] = Field(None, description="Step 1: Organize examination findings by system")
    step_2_identify_abnormalities: Optional[CoTStep] = Field(None, description="Step 2: Identify abnormal findings")
    step_3_correlate_with_complaints: Optional[CoTStep] = Field(None, description="Step 3: Correlate findings with chief complaints")
    step_4_system_analysis: Optional[CoTStep] = Field(None, description="Step 4: Analyze each system's involvement")
    step_5_differential_narrowing: Optional[CoTStep] = Field(None, description="Step 5: Narrow differential diagnosis")
    step_6_generate_provisional_diagnosis: Optional[CoTStep] = Field(None, description="Step 6: Generate provisional diagnosis options")

    # Examination Results
    systemic_examination_results: Optional[SystemicExaminationResults] = Field(
        None, description="Systemic examination results"
    )

    # Provisional Diagnoses
    primary_diagnosis: Optional[str] = Field(None, description="Primary provisional diagnosis")
    primary_diagnosis_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence in primary diagnosis")
    primary_diagnosis_reasoning: Optional[str] = Field(None, description="Reasoning for primary diagnosis")

    alternative_diagnosis_1: Optional[str] = Field(None, description="Alternative diagnosis 1")
    alternative_diagnosis_1_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence in alternative 1")

    alternative_diagnosis_2: Optional[str] = Field(None, description="Alternative diagnosis 2")
    alternative_diagnosis_2_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence in alternative 2")

    # Overall Assessment
    overall_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Overall confidence in diagnosis")
    clinical_summary: Optional[str] = Field(None, description="Summary of clinical findings and diagnosis")
    knowledge_gaps: Optional[List[str]] = Field(None, description="Missing information for better diagnosis")

    # Next Steps
    further_investigations_needed: Optional[List[str]] = Field(None, description="Lab tests, imaging, or other investigations needed")
    supportive_management_plan: Optional[List[str]] = Field(None, description="Supportive care recommendations")

    # Safety & HITL
    safety_concerns: Optional[List[str]] = Field(None, description="Any safety concerns or red flags")
    requires_hitl: Optional[bool] = Field(None, description="Does this require human review?")
    hitl_reason: Optional[str] = Field(None, description="Why HITL is needed (if applicable)")
