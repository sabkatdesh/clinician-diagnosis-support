import { api } from './client'

export type ExamSystem = 'CVS' | 'RS' | 'CNS' | 'GIT' | 'GUS' | 'MSK'

export interface ExaminationRecommendation {
  rank: number | null
  exam_types: ExamSystem[] | null
  confidence_score: number | null
  why_recommended: string | null
  supporting_findings: string[] | null
}

export interface CoTStep {
  step_number: number | null
  step_name: string | null
  reasoning: string | null
  conclusion: unknown
  confidence: number | null
}

export interface AIIntegration1Output {
  step_1: CoTStep | null
  step_2: CoTStep | null
  step_3: CoTStep | null
  step_4: CoTStep | null
  step_5: CoTStep | null
  step_6: CoTStep | null
  primary_recommendation: ExaminationRecommendation | null
  alternative_1: ExaminationRecommendation | null
  alternative_2: ExaminationRecommendation | null
  overall_confidence: number | null
  clinical_summary: string | null
  knowledge_gaps: string[] | null
  requires_hitl: boolean | null
  hitl_reason: string | null
}

export interface MissingDataItem {
  category: 'symptom' | 'sign' | 'test_result' | 'history' | 'pattern'
  description: string
  why_needed: string
  question_for_doctor: string
}

export interface RequiredTest {
  test_name: string
  reason: string
  priority: 'urgent' | 'routine' | 'optional'
  expected_finding: string
}

export interface CRAGOutput {
  verdict: 'confirmed' | 'uncertain' | 'incorrect'
  confidence_score: number
  retry_recommended: boolean
  missing_data: MissingDataItem[] | null
  validated_primary_diagnosis: string
  corrected_diagnosis: string | null
  correction_reasoning: string | null
  required_tests: RequiredTest[] | null
  final_diagnosis: string
  final_diagnosis_confidence: number
  clinical_reasoning_summary: string
  supporting_evidence: string[]
  against_evidence: string[]
  red_flags: string[] | null
  requires_hitl: boolean
  hitl_reason: string | null
}

export interface PipelineValues {
  patient_info: unknown
  exam_recommendation: AIIntegration1Output | null
  doctor_approved_recommendation: boolean | null
  doctor_modified_recommendation: string | null
  systemic_examination_text: string | null
  provisional_diagnosis: unknown
  doctor_approved_diagnosis: boolean | null
  doctor_diagnosis_note: string | null
  crag_output: CRAGOutput | null
  crag_attempt: number | null
  crag_missing_data: MissingDataItem[] | null
  doctor_additional_data: string | null
  doctor_final_confirmed: boolean | null
  doctor_final_note: string | null
}

export interface StartPipelineResponse {
  thread_id: string
  session_id: string
  patient_id: string
  task_id: string
  message: string
}

export interface PipelineStateResponse {
  thread_id: string
  status: 'running' | 'paused' | 'complete' | 'not_found'
  paused_at: string | null
  session: {
    id: string
    thread_id: string
    status: string
    current_stage: string | null
    paused_at: string | null
    created_at: string
    updated_at: string
    patient_id: string
  }
  values: PipelineValues
}

export const pipelineApi = {
  start: (chiefComplain: string) =>
    api.post<StartPipelineResponse>('/pipeline/start', { chief_complain: chiefComplain }).then(r => r.data),

  resume: (threadId: string, resumeType: string, payload: Record<string, unknown>) =>
    api.post(`/pipeline/resume/${threadId}`, { resume_type: resumeType, payload }).then(r => r.data),

  getState: (threadId: string) =>
    api.get<PipelineStateResponse>(`/pipeline/state/${threadId}`).then(r => r.data),
}
