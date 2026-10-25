import { api } from './client'
import type { RequiredTest } from './pipeline'

export interface Session {
  id: string
  thread_id: string
  task_id: string | null
  doctor_id: string
  patient_id: string
  patients?: { name: string | null; age: number | null; gender: string | null } | null
  status: 'starting' | 'running' | 'paused_hitl' | 'completed' | 'failed'
  current_stage: string | null
  paused_at: string | null
  created_at: string
  updated_at: string
  completed_at: string | null
}

export interface Patient {
  id: string
  doctor_id: string
  name: string | null
  age: number | null
  gender: string | null
  chief_complain_raw: string
  created_at: string
}

export interface FinalReport {
  id: string
  session_id: string
  patient_id: string
  doctor_id: string
  verdict: 'confirmed' | 'uncertain' | 'incorrect'
  final_diagnosis: string
  final_diagnosis_confidence: number
  validated_primary_diagnosis: string | null
  corrected_diagnosis: string | null
  clinical_reasoning_summary: string | null
  supporting_evidence: string[] | null
  against_evidence: string[] | null
  required_tests: RequiredTest[] | null
  red_flags: string[] | null
  doctor_confirmed: boolean
  doctor_final_note: string | null
  total_crag_attempts: number
  created_at: string
  sessions: { thread_id: string; created_at: string } | null
}

export const sessionsApi = {
  list: () =>
    api.get<Session[]>('/sessions').then(r => r.data),

  get: (threadId: string) =>
    api.get<{ session: Session; graph_state: unknown }>(`/sessions/${threadId}`).then(r => r.data),

  delete: (threadId: string) =>
    api.delete(`/sessions/${threadId}`),
}

export const patientsApi = {
  list: () =>
    api.get<Patient[]>('/patients').then(r => r.data),

  get: (patientId: string) =>
    api.get<Patient>(`/patients/${patientId}`).then(r => r.data),

  reports: (patientId: string) =>
    api.get<FinalReport[]>(`/patients/${patientId}/reports`).then(r => r.data),

  delete: (patientId: string) =>
    api.delete(`/patients/${patientId}`),
}
