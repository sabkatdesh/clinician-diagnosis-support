import { useState } from 'react'
import { CheckCircle, ChevronDown, ChevronUp, Loader2, AlertCircle } from 'lucide-react'
import type { PipelineStateResponse, ExaminationRecommendation, ExamSystem } from '@/api/pipeline'
import { pipelineApi } from '@/api/pipeline'
import { useInvalidatePipeline } from '@/hooks/usePipelineState'

const SYSTEM_FULL: Record<ExamSystem, string> = {
  CVS: 'Cardiovascular',
  RS:  'Respiratory',
  CNS: 'Nervous system',
  GIT: 'Gastrointestinal',
  GUS: 'Genitourinary',
  MSK: 'Musculoskeletal',
}

const SYSTEM_COLOR: Record<ExamSystem, string> = {
  CVS: 'bg-red-50 text-red-700 border-red-200',
  RS:  'bg-sky-50 text-sky-700 border-sky-200',
  CNS: 'bg-violet-50 text-violet-700 border-violet-200',
  GIT: 'bg-amber-50 text-amber-700 border-amber-200',
  GUS: 'bg-teal-50 text-teal-700 border-teal-200',
  MSK: 'bg-orange-50 text-orange-700 border-orange-200',
}

function ConfidenceBar({ value }: { value: number | null }) {
  if (value == null) return null
  const pct = Math.round(value * 100)
  const color = pct >= 80 ? 'bg-emerald-500' : pct >= 60 ? 'bg-amber-400' : 'bg-red-400'
  const label = pct >= 80 ? 'High' : pct >= 60 ? 'Moderate' : 'Low'
  return (
    <div className="flex items-center gap-2 mt-1">
      <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-500 w-20">{label} — {pct}%</span>
    </div>
  )
}

function RecommendationCard({
  rec, label, isPrimary, onApprove, submitting,
}: {
  rec: ExaminationRecommendation
  label: string
  isPrimary: boolean
  onApprove: (rec: ExaminationRecommendation) => void
  submitting: boolean
}) {
  const [expanded, setExpanded] = useState(isPrimary)

  return (
    <div className={`rounded-2xl border p-4 ${isPrimary ? 'border-brand-200 bg-brand-50/40' : 'border-slate-100 bg-white'}`}>
      <div className="flex items-start justify-between gap-3 mb-2">
        <div>
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
            isPrimary ? 'bg-brand-700 text-white' : 'bg-slate-100 text-slate-600'
          }`}>{label}</span>
        </div>
        <button
          type="button"
          onClick={() => onApprove(rec)}
          disabled={submitting}
          className={`flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-xl transition-colors disabled:opacity-50 ${
            isPrimary
              ? 'bg-brand-700 text-white hover:bg-brand-800'
              : 'border border-brand-200 text-brand-700 hover:bg-brand-50'
          }`}
        >
          {submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}
          {isPrimary ? 'Approve' : 'Use this'}
        </button>
      </div>

      {/* System badges */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {(rec.exam_types ?? []).map(sys => (
          <span key={sys} className={`text-xs font-medium px-2.5 py-1 rounded-full border ${SYSTEM_COLOR[sys]}`}>
            {SYSTEM_FULL[sys]}
          </span>
        ))}
      </div>

      <ConfidenceBar value={rec.confidence_score} />

      {/* Expandable detail */}
      <button
        type="button"
        onClick={() => setExpanded(v => !v)}
        className="mt-3 flex items-center gap-1 text-xs text-slate-400 hover:text-slate-600"
      >
        {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        {expanded ? 'Less detail' : 'Why recommended'}
      </button>

      {expanded && (
        <div className="mt-3 space-y-2">
          {rec.why_recommended && (
            <p className="text-sm text-slate-600">{rec.why_recommended}</p>
          )}
          {(rec.supporting_findings ?? []).length > 0 && (
            <ul className="space-y-0.5">
              {rec.supporting_findings!.map((f, i) => (
                <li key={i} className="text-xs text-slate-500 flex gap-1.5">
                  <span className="text-brand-400 mt-0.5">·</span>{f}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}

export default function HITL1ExamApproval({ state }: { state: PipelineStateResponse }) {
  const invalidate    = useInvalidatePipeline()
  const [submitting, setSubmitting] = useState(false)
  const [error, setError]   = useState('')
  const [showModify, setShowModify] = useState(false)
  const [modifyText, setModifyText] = useState('')
  const [cotOpen, setCotOpen]       = useState(false)

  const rec = state.values.exam_recommendation
  if (!rec) {
    return (
      <div className="max-w-md mx-auto px-4 py-12 text-center">
        <AlertCircle className="w-8 h-8 text-amber-400 mx-auto mb-3" />
        <p className="text-sm text-slate-500">Exam recommendation not yet available.</p>
      </div>
    )
  }

  async function approve(chosen: ExaminationRecommendation, isPrimary: boolean) {
    setError('')
    setSubmitting(true)
    try {
      if (isPrimary) {
        await pipelineApi.resume(state.thread_id, 'hitl_1_recommendation_approval', { approved: true })
      } else {
        const systemText = (chosen.exam_types ?? []).join(', ')
        await pipelineApi.resume(state.thread_id, 'hitl_1_recommendation_approval', {
          approved: false,
          modified_recommendation: systemText,
        })
      }
      invalidate(state.thread_id)
    } catch {
      setError('Failed to submit. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  async function submitModified() {
    if (!modifyText.trim()) return
    setError('')
    setSubmitting(true)
    try {
      await pipelineApi.resume(state.thread_id, 'hitl_1_recommendation_approval', {
        approved: false,
        modified_recommendation: modifyText.trim(),
      })
      invalidate(state.thread_id)
    } catch {
      setError('Failed to submit. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const coTSteps = [rec.step_1, rec.step_2, rec.step_3, rec.step_4, rec.step_5, rec.step_6].filter(Boolean)

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      <div className="mb-6">
        <div className="inline-flex items-center gap-2 bg-ai-100 text-ai-700 text-xs font-medium px-3 py-1.5 rounded-full mb-3">
          <span className="w-1.5 h-1.5 rounded-full bg-ai-500" />
          AI recommendation ready
        </div>
        <h1 className="text-lg font-semibold text-slate-800 mb-1">Examination plan</h1>
        <p className="text-sm text-slate-500">
          Review the recommended systems to examine. Approve to continue, or type a custom plan.
        </p>
      </div>

      {/* Clinical summary */}
      {rec.clinical_summary && (
        <div className="bg-slate-50 border border-slate-100 rounded-xl px-4 py-3 mb-5 text-sm text-slate-600">
          {rec.clinical_summary}
        </div>
      )}

      {/* Knowledge gaps */}
      {(rec.knowledge_gaps ?? []).length > 0 && (
        <div className="bg-amber-50 border border-amber-100 rounded-xl px-4 py-3 mb-5">
          <p className="text-xs font-medium text-amber-700 mb-1">Missing information</p>
          <ul className="space-y-0.5">
            {rec.knowledge_gaps!.map((g, i) => (
              <li key={i} className="text-xs text-amber-600">· {g}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendation cards */}
      <div className="space-y-3 mb-4">
        {rec.primary_recommendation && (
          <RecommendationCard
            rec={rec.primary_recommendation}
            label="Primary recommendation"
            isPrimary
            onApprove={(r) => approve(r, true)}
            submitting={submitting}
          />
        )}
        {rec.alternative_1 && (
          <RecommendationCard
            rec={rec.alternative_1}
            label="Alternative 1"
            isPrimary={false}
            onApprove={(r) => approve(r, false)}
            submitting={submitting}
          />
        )}
        {rec.alternative_2 && (
          <RecommendationCard
            rec={rec.alternative_2}
            label="Alternative 2"
            isPrimary={false}
            onApprove={(r) => approve(r, false)}
            submitting={submitting}
          />
        )}
      </div>

      {/* Custom modification */}
      <div className="mb-4">
        <button
          type="button"
          onClick={() => setShowModify(v => !v)}
          className="text-sm text-brand-700 underline"
        >
          {showModify ? 'Cancel' : 'Specify a different plan instead'}
        </button>

        {showModify && (
          <div className="mt-3">
            <p className="text-xs text-slate-500 mb-1.5">
              List the systems to examine, e.g. "CVS, RS, GIT"
            </p>
            <textarea
              rows={3}
              value={modifyText}
              onChange={e => setModifyText(e.target.value)}
              placeholder="CVS, RS — explain any change if helpful"
              className="input-field resize-none"
            />
            <button
              type="button"
              onClick={submitModified}
              disabled={!modifyText.trim() || submitting}
              className="mt-2 bg-brand-700 text-white text-sm font-medium px-4 py-2.5 rounded-xl hover:bg-brand-800 transition-colors disabled:opacity-50"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin inline mr-1" /> : null}
              Use custom plan
            </button>
          </div>
        )}
      </div>

      {/* AI reasoning accordion */}
      {coTSteps.length > 0 && (
        <div className="border border-slate-100 rounded-2xl overflow-hidden">
          <button
            type="button"
            onClick={() => setCotOpen(v => !v)}
            className="w-full flex items-center justify-between px-4 py-3 text-sm text-slate-500 hover:bg-slate-50 transition-colors"
          >
            <span>AI reasoning ({coTSteps.length} steps)</span>
            {cotOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
          {cotOpen && (
            <div className="border-t border-slate-100 divide-y divide-slate-50">
              {coTSteps.map((step, i) => step && (
                <div key={i} className="px-4 py-3">
                  <p className="text-xs font-medium text-slate-500 mb-1">
                    Step {step.step_number}: {step.step_name}
                  </p>
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
