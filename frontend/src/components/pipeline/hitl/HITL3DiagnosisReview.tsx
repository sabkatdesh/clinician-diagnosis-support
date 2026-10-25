import { useState } from 'react'
import { CheckCircle, ChevronDown, ChevronUp, Loader2, AlertTriangle } from 'lucide-react'
import type { PipelineStateResponse } from '@/api/pipeline'
import { pipelineApi } from '@/api/pipeline'
import { useInvalidatePipeline } from '@/hooks/usePipelineState'

interface DiagnosisEntry {
  name: string | null
  confidence: number | null
  reasoning?: string | null
}

interface ProvisionalDiagnosis {
  primary_diagnosis: string | null
  primary_diagnosis_confidence: number | null
  primary_diagnosis_reasoning: string | null
  alternative_diagnosis_1: string | null
  alternative_diagnosis_1_confidence: number | null
  alternative_diagnosis_2: string | null
  alternative_diagnosis_2_confidence: number | null
  overall_confidence: number | null
  clinical_summary: string | null
  knowledge_gaps: string[] | null
  safety_concerns: string[] | null
  further_investigations_needed: string[] | null
  supportive_management_plan: string[] | null
  step_1_organize_findings: { step_name: string | null; reasoning: string | null } | null
  step_2_identify_abnormalities: { step_name: string | null; reasoning: string | null } | null
  step_3_correlate_with_complaints: { step_name: string | null; reasoning: string | null } | null
  step_4_system_analysis: { step_name: string | null; reasoning: string | null } | null
  step_5_differential_narrowing: { step_name: string | null; reasoning: string | null } | null
  step_6_generate_provisional_diagnosis: { step_name: string | null; reasoning: string | null } | null
}

function ConfidenceBar({ value }: { value: number | null }) {
  if (value == null) return null
  const pct   = Math.round(value * 100)
  const color = pct >= 80 ? 'bg-emerald-500' : pct >= 60 ? 'bg-amber-400' : 'bg-red-400'
  const label = pct >= 80 ? 'High' : pct >= 60 ? 'Moderate' : 'Low'
  return (
    <div className="flex items-center gap-2 mt-1.5">
      <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-xs w-24 ${
        pct >= 80 ? 'text-emerald-600' : pct >= 60 ? 'text-amber-600' : 'text-red-500'
      }`}>{label} — {pct}%</span>
    </div>
  )
}

function DiagnosisCard({ entry, isPrimary }: { entry: DiagnosisEntry; isPrimary: boolean }) {
  if (!entry.name) return null
  return (
    <div className={`rounded-2xl border p-4 ${
      isPrimary ? 'border-brand-200 bg-brand-50/40' : 'border-slate-100 bg-white'
    }`}>
      <div className="flex items-start gap-2 mb-1">
        {isPrimary && (
          <span className="text-xs font-semibold bg-brand-700 text-white px-2 py-0.5 rounded-full flex-shrink-0 mt-0.5">
            Primary
          </span>
        )}
        <p className={`text-sm font-medium ${isPrimary ? 'text-slate-800' : 'text-slate-600'}`}>
          {entry.name}
        </p>
      </div>
      <ConfidenceBar value={entry.confidence} />
      {entry.reasoning && isPrimary && (
        <p className="mt-2 text-xs text-slate-500">{entry.reasoning}</p>
      )}
    </div>
  )
}

export default function HITL3DiagnosisReview({ state }: { state: PipelineStateResponse }) {
  const invalidate  = useInvalidatePipeline()
  const [submitting, setSubmitting] = useState(false)
  const [error, setError]       = useState('')
  const [showNote, setShowNote] = useState(false)
  const [note, setNote]         = useState('')
  const [cotOpen, setCotOpen]   = useState(false)

  const diag = state.values.provisional_diagnosis as ProvisionalDiagnosis | null
  if (!diag) {
    return (
      <div className="max-w-md mx-auto px-4 py-12 text-center">
        <p className="text-sm text-slate-500">Provisional diagnosis not yet available.</p>
      </div>
    )
  }

  const diagnoses: DiagnosisEntry[] = [
    { name: diag.primary_diagnosis, confidence: diag.primary_diagnosis_confidence, reasoning: diag.primary_diagnosis_reasoning },
    { name: diag.alternative_diagnosis_1, confidence: diag.alternative_diagnosis_1_confidence },
    { name: diag.alternative_diagnosis_2, confidence: diag.alternative_diagnosis_2_confidence },
  ].filter(d => !!d.name)

  const cotSteps = [
    diag.step_1_organize_findings,
    diag.step_2_identify_abnormalities,
    diag.step_3_correlate_with_complaints,
    diag.step_4_system_analysis,
    diag.step_5_differential_narrowing,
    diag.step_6_generate_provisional_diagnosis,
  ].filter(Boolean)

  async function submit(approved: boolean) {
    setError('')
    setSubmitting(true)
    try {
      const payload: Record<string, unknown> = { approved }
      if (!approved && note.trim()) payload.doctor_note = note.trim()
      await pipelineApi.resume(state.thread_id, 'hitl_3_diagnosis_approval', payload)
      invalidate(state.thread_id)
    } catch {
      setError('Failed to submit. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      <div className="mb-5">
        <div className="inline-flex items-center gap-2 bg-ai-100 text-ai-700 text-xs font-medium px-3 py-1.5 rounded-full mb-3">
          <span className="w-1.5 h-1.5 rounded-full bg-ai-500" />
          AI analysis ready
        </div>
        <h1 className="text-lg font-semibold text-slate-800 mb-1">Review provisional diagnosis</h1>
        <p className="text-sm text-slate-500">
          The AI has formed a working diagnosis. Approve to continue to evidence validation, or add a correction note.
        </p>
      </div>

      {/* Clinical summary */}
      {diag.clinical_summary && (
        <div className="bg-slate-50 border border-slate-100 rounded-xl px-4 py-3 mb-5 text-sm text-slate-600">
          {diag.clinical_summary}
        </div>
      )}

      {/* Safety concerns */}
      {(diag.safety_concerns ?? []).length > 0 && (
        <div className="bg-red-50 border border-red-100 rounded-xl px-4 py-3 mb-4">
          <div className="flex items-center gap-1.5 mb-1.5">
            <AlertTriangle className="w-4 h-4 text-red-500" />
            <p className="text-xs font-semibold text-red-700">Safety concerns</p>
          </div>
          <ul className="space-y-0.5">
            {diag.safety_concerns!.map((c, i) => (
              <li key={i} className="text-xs text-red-600">· {c}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Diagnosis cards */}
      <div className="space-y-2.5 mb-5">
        {diagnoses.map((d, i) => (
          <DiagnosisCard key={i} entry={d} isPrimary={i === 0} />
        ))}
      </div>

      {/* Further investigations */}
      {(diag.further_investigations_needed ?? []).length > 0 && (
        <div className="border border-slate-100 rounded-2xl p-4 mb-4">
          <p className="text-xs font-semibold text-slate-500 mb-2">Suggested investigations</p>
          <ul className="space-y-1">
            {diag.further_investigations_needed!.map((inv, i) => (
              <li key={i} className="text-sm text-slate-600 flex gap-2">
                <span className="text-brand-400 mt-0.5">·</span>{inv}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Knowledge gaps */}
      {(diag.knowledge_gaps ?? []).length > 0 && (
        <div className="bg-amber-50 border border-amber-100 rounded-xl px-4 py-3 mb-4">
          <p className="text-xs font-medium text-amber-700 mb-1">Missing information</p>
          <ul className="space-y-0.5">
            {diag.knowledge_gaps!.map((g, i) => (
              <li key={i} className="text-xs text-amber-600">· {g}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Add note toggle */}
      <div className="mb-4">
        <button type="button" onClick={() => setShowNote(v => !v)}
          className="text-sm text-brand-700 underline">
          {showNote ? 'Cancel note' : 'Add a correction or note before proceeding'}
        </button>
        {showNote && (
          <div className="mt-3">
            <textarea rows={3} value={note} onChange={e => setNote(e.target.value)}
              placeholder="E.g. 'I think alternative 1 is more likely given the patient's travel history…'"
              className="input-field resize-none" />
          </div>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex gap-3 mb-4">
        <button type="button" onClick={() => submit(true)} disabled={submitting}
          className="flex-1 flex items-center justify-center gap-2 bg-brand-700 hover:bg-brand-800 text-white font-medium rounded-xl py-3 text-sm transition-colors disabled:opacity-60">
          {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
          Approve and continue
        </button>
        {showNote && note.trim() && (
          <button type="button" onClick={() => submit(false)} disabled={submitting}
            className="flex-1 flex items-center justify-center gap-2 border border-brand-200 text-brand-700 font-medium rounded-xl py-3 text-sm hover:bg-brand-50 transition-colors disabled:opacity-60">
            {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
            Submit with note
          </button>
        )}
      </div>

      {/* AI reasoning accordion */}
      {cotSteps.length > 0 && (
        <div className="border border-slate-100 rounded-2xl overflow-hidden">
          <button type="button" onClick={() => setCotOpen(v => !v)}
            className="w-full flex items-center justify-between px-4 py-3 text-sm text-slate-500 hover:bg-slate-50 transition-colors">
            <span>AI reasoning ({cotSteps.length} steps)</span>
            {cotOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
          {cotOpen && (
            <div className="border-t border-slate-100 divide-y divide-slate-50">
              {cotSteps.map((step, i) => step && (
                <div key={i} className="px-4 py-3">
                  <p className="text-xs font-medium text-slate-500 mb-1">Step {i + 1}: {step.step_name}</p>
                  <p className="text-xs text-slate-600">{step.reasoning}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="mt-4 bg-red-50 text-red-700 rounded-xl px-4 py-3 text-sm">{error}</div>
      )}

      <p className="text-center text-xs text-slate-400 mt-6">
        Decision support only. The final judgement is yours.
      </p>
    </div>
  )
}
