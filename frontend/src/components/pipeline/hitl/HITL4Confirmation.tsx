import { useState } from 'react'
import {
  CheckCircle, XCircle, AlertCircle, AlertTriangle,
  ChevronDown, ChevronUp, Loader2, FlaskConical,
} from 'lucide-react'
import type { PipelineStateResponse, CRAGOutput, RequiredTest } from '@/api/pipeline'
import { pipelineApi } from '@/api/pipeline'
import { useInvalidatePipeline } from '@/hooks/usePipelineState'

// ─── Shared sub-components ────────────────────────────────────────────────────

export function VerdictBadge({ verdict }: { verdict: CRAGOutput['verdict'] }) {
  const styles = {
    confirmed: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    uncertain:  'bg-amber-50 text-amber-700 border-amber-200',
    incorrect:  'bg-red-50 text-red-700 border-red-200',
  }
  const icons = {
    confirmed: <CheckCircle className="w-3.5 h-3.5" />,
    uncertain:  <AlertCircle className="w-3.5 h-3.5" />,
    incorrect:  <XCircle className="w-3.5 h-3.5" />,
  }
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full border capitalize ${styles[verdict]}`}>
      {icons[verdict]}{verdict}
    </span>
  )
}

function PriorityChip({ priority }: { priority: RequiredTest['priority'] }) {
  const styles = {
    urgent:   'bg-red-50 text-red-700',
    routine:  'bg-sky-50 text-sky-700',
    optional: 'bg-slate-50 text-slate-500',
  }
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${styles[priority]}`}>
      {priority}
    </span>
  )
}

export function CRAGReport({ crag, provisionalDx }: {
  crag: CRAGOutput
  provisionalDx?: string | null
}) {
  const [cotOpen, setCotOpen] = useState(false)
  const finalPct = Math.round(crag.final_diagnosis_confidence * 100)

  return (
    <div className="space-y-4">
      {/* Verdict + final diagnosis */}
      <div className={`rounded-2xl border p-4 ${
        crag.verdict === 'confirmed' ? 'border-emerald-200 bg-emerald-50/30'
          : crag.verdict === 'uncertain' ? 'border-amber-200 bg-amber-50/20'
          : 'border-red-200 bg-red-50/20'
      }`}>
        <div className="flex items-center justify-between mb-2">
          <VerdictBadge verdict={crag.verdict} />
          <span className={`text-sm font-semibold ${
            finalPct >= 80 ? 'text-emerald-600' : finalPct >= 60 ? 'text-amber-600' : 'text-red-500'
          }`}>{finalPct}% confidence</span>
        </div>
        <p className="text-base font-semibold text-slate-800 mt-1">{crag.final_diagnosis}</p>

        {/* Corrected diagnosis */}
        {crag.corrected_diagnosis && (
          <div className="mt-3 border-t border-red-200 pt-3">
            <p className="text-xs text-red-600 font-medium mb-0.5">Diagnosis corrected</p>
            {provisionalDx && (
              <p className="text-xs text-slate-400 line-through mb-0.5">{provisionalDx}</p>
            )}
            <p className="text-sm text-red-700 font-medium">{crag.corrected_diagnosis}</p>
            {crag.correction_reasoning && (
              <p className="text-xs text-slate-500 mt-1">{crag.correction_reasoning}</p>
            )}
          </div>
        )}
      </div>

      {/* Clinical reasoning */}
      {crag.clinical_reasoning_summary && (
        <div className="bg-slate-50 border border-slate-100 rounded-xl px-4 py-3 text-sm text-slate-600">
          {crag.clinical_reasoning_summary}
        </div>
      )}

      {/* Red flags */}
      {(crag.red_flags ?? []).length > 0 && (
        <div className="bg-red-50 border border-red-100 rounded-xl px-4 py-3">
          <div className="flex items-center gap-1.5 mb-1.5">
            <AlertTriangle className="w-4 h-4 text-red-500" />
            <p className="text-xs font-semibold text-red-700">Red flags</p>
          </div>
          <ul className="space-y-0.5">
            {crag.red_flags!.map((f, i) => (
              <li key={i} className="text-xs text-red-600">· {f}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Supporting vs against evidence */}
      <div className="grid grid-cols-2 gap-3">
        {crag.supporting_evidence.length > 0 && (
          <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-3">
            <p className="text-xs font-semibold text-emerald-700 mb-1.5">Supporting</p>
            <ul className="space-y-1">
              {crag.supporting_evidence.map((e, i) => (
                <li key={i} className="text-xs text-emerald-700 flex gap-1">
                  <span className="flex-shrink-0">✓</span>{e}
                </li>
              ))}
            </ul>
          </div>
        )}
        {crag.against_evidence.length > 0 && (
          <div className="bg-amber-50 border border-amber-100 rounded-xl p-3">
            <p className="text-xs font-semibold text-amber-700 mb-1.5">Against</p>
            <ul className="space-y-1">
              {crag.against_evidence.map((e, i) => (
                <li key={i} className="text-xs text-amber-700 flex gap-1">
                  <span className="flex-shrink-0">✗</span>{e}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Required tests */}
      {(crag.required_tests ?? []).length > 0 && (
        <div className="border border-slate-100 rounded-2xl overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-3 bg-slate-50 border-b border-slate-100">
            <FlaskConical className="w-4 h-4 text-slate-400" />
            <p className="text-xs font-semibold text-slate-600">Required investigations</p>
          </div>
          <div className="divide-y divide-slate-50">
            {crag.required_tests!.map((t, i) => (
              <div key={i} className="px-4 py-3">
                <div className="flex items-center gap-2 mb-0.5">
                  <p className="text-sm font-medium text-slate-800 flex-1">{t.test_name}</p>
                  <PriorityChip priority={t.priority} />
                </div>
                <p className="text-xs text-slate-500">{t.reason}</p>
                <p className="text-xs text-slate-400 mt-0.5">Expected: {t.expected_finding}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* CoT reasoning */}
      <div className="border border-slate-100 rounded-2xl overflow-hidden">
        <button type="button" onClick={() => setCotOpen(v => !v)}
          className="w-full flex items-center justify-between px-4 py-3 text-sm text-slate-500 hover:bg-slate-50 transition-colors">
          <span>Evidence review reasoning</span>
          {cotOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
        {cotOpen && (
          <div className="border-t border-slate-100 divide-y divide-slate-50">
            {[
              { n: 1, step: (crag as unknown as Record<string, { step_name?: string; reasoning?: string }>)['step_1_summarize_rag'] },
              { n: 2, step: (crag as unknown as Record<string, { step_name?: string; reasoning?: string }>)['step_2_match_primary'] },
              { n: 3, step: (crag as unknown as Record<string, { step_name?: string; reasoning?: string }>)['step_3_match_alternatives'] },
              { n: 4, step: (crag as unknown as Record<string, { step_name?: string; reasoning?: string }>)['step_4_gap_analysis'] },
              { n: 5, step: (crag as unknown as Record<string, { step_name?: string; reasoning?: string }>)['step_5_weigh_evidence'] },
              { n: 6, step: (crag as unknown as Record<string, { step_name?: string; reasoning?: string }>)['step_6_final_decision'] },
            ].filter(s => s.step?.reasoning).map(({ n, step }) => (
              <div key={n} className="px-4 py-3">
                <p className="text-xs font-medium text-slate-500 mb-1">Step {n}: {step?.step_name}</p>
                <p className="text-xs text-slate-600">{step?.reasoning}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Main HITL 4 component ────────────────────────────────────────────────────

export default function HITL4Confirmation({ state }: { state: PipelineStateResponse }) {
  const invalidate  = useInvalidatePipeline()
  const [submitting, setSubmitting] = useState(false)
  const [error, setError]       = useState('')
  const [showNote, setShowNote] = useState(false)
  const [note, setNote]         = useState('')

  const crag = state.values.crag_output
  const provisionalDx = (state.values.provisional_diagnosis as { primary_diagnosis?: string } | null)?.primary_diagnosis

  if (!crag) {
    return (
      <div className="max-w-md mx-auto px-4 py-12 text-center">
        <p className="text-sm text-slate-500">CRAG results not yet available.</p>
      </div>
    )
  }

  const attempts = (state.values as unknown as { crag_history?: unknown[] }).crag_history?.length ?? 1

  async function confirm(confirmed: boolean) {
    setError('')
    setSubmitting(true)
    try {
      const payload: Record<string, unknown> = { confirmed }
      if (note.trim()) payload.doctor_final_note = note.trim()
      await pipelineApi.resume(state.thread_id, 'hitl_4_crag_confirmation', payload)
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
          Evidence validation complete
        </div>
        <h1 className="text-lg font-semibold text-slate-800 mb-1">Confirm final diagnosis</h1>
        <p className="text-sm text-slate-500">
          Review the evidence-validated result and confirm to generate the final report.
          {attempts > 1 && ` (${attempts} CRAG attempts)`}
        </p>
      </div>

      <CRAGReport crag={crag} provisionalDx={provisionalDx} />

      {/* Note */}
      <div className="mt-5 mb-4">
        <button type="button" onClick={() => setShowNote(v => !v)}
          className="text-sm text-brand-700 underline">
          {showNote ? 'Cancel note' : 'Add a note or override to the report'}
        </button>
        {showNote && (
          <div className="mt-3">
            <textarea rows={3} value={note} onChange={e => setNote(e.target.value)}
              placeholder="E.g. 'Patient has additional context not captured…'"
              className="input-field resize-none" />
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button type="button" onClick={() => confirm(true)} disabled={submitting}
          className="flex-1 flex items-center justify-center gap-2 bg-brand-700 hover:bg-brand-800 text-white font-medium rounded-xl py-3 text-sm transition-colors disabled:opacity-60">
          {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
          Confirm and generate report
        </button>
      </div>
      {showNote && note.trim() && (
        <button type="button" onClick={() => confirm(false)} disabled={submitting}
          className="w-full mt-2 flex items-center justify-center gap-2 border border-brand-200 text-brand-700 font-medium rounded-xl py-3 text-sm hover:bg-brand-50 transition-colors disabled:opacity-60">
          {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
          Confirm with note
        </button>
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
