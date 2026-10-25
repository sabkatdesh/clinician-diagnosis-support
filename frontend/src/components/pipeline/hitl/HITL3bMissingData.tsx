import { useState } from 'react'
import { Loader2, HelpCircle } from 'lucide-react'
import type { PipelineStateResponse } from '@/api/pipeline'
import { pipelineApi } from '@/api/pipeline'
import { useInvalidatePipeline } from '@/hooks/usePipelineState'

interface MissingDataItem {
  category: string
  description: string
  why_needed: string
  question_for_doctor: string
}

interface CRAGValues {
  crag_output: {
    verdict: 'confirmed' | 'uncertain' | 'incorrect'
    confidence_score: number
    final_diagnosis: string
  } | null
  crag_missing_data: MissingDataItem[] | null
  crag_attempt: number | null
}

const CATEGORY_COLORS: Record<string, string> = {
  symptom:     'bg-violet-50 text-violet-700',
  sign:        'bg-sky-50 text-sky-700',
  test_result: 'bg-amber-50 text-amber-700',
  history:     'bg-emerald-50 text-emerald-700',
  pattern:     'bg-slate-50 text-slate-600',
}

const MAX_ATTEMPTS = 3

export default function HITL3bMissingData({ state }: { state: PipelineStateResponse }) {
  const invalidate   = useInvalidatePipeline()
  const [answers, setAnswers]     = useState<Record<number, string>>({})
  const [freeText, setFreeText]   = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError]         = useState('')

  const vals = state.values as unknown as CRAGValues
  const crag    = vals.crag_output
  const missing = vals.crag_missing_data ?? []
  const attempt = vals.crag_attempt ?? 1

  if (!crag) {
    return (
      <div className="max-w-md mx-auto px-4 py-12 text-center">
        <p className="text-sm text-slate-500">CRAG data not yet available.</p>
      </div>
    )
  }

  const pct = Math.round(crag.confidence_score * 100)

  function buildAdditionalData(): string {
    const parts: string[] = []
    missing.forEach((item, i) => {
      const answer = (answers[i] ?? '').trim()
      if (answer) {
        parts.push(`Q: ${item.question_for_doctor}\nA: ${answer}`)
      }
    })
    if (freeText.trim()) {
      parts.push(`Additional information: ${freeText.trim()}`)
    }
    return parts.join('\n\n')
  }

  async function submit() {
    const text = buildAdditionalData()
    if (!text.trim()) {
      setError('Please answer at least one question or provide additional information.')
      return
    }
    setError('')
    setSubmitting(true)
    try {
      await pipelineApi.resume(state.thread_id, 'hitl_3b_crag_missing_data', { additional_data: text })
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
        <div className="inline-flex items-center gap-2 bg-amber-50 text-amber-700 text-xs font-medium px-3 py-1.5 rounded-full mb-3">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
          More information needed
        </div>
        <h1 className="text-lg font-semibold text-slate-800 mb-1">Answer clinical questions</h1>
        <p className="text-sm text-slate-500">
          The AI needs additional clinical data to reach sufficient confidence. Answer as many as possible.
        </p>
      </div>

      {/* Current CRAG status */}
      <div className="bg-slate-50 border border-slate-100 rounded-xl px-4 py-3 mb-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs text-slate-500 mb-0.5">Working diagnosis</p>
            <p className="text-sm font-medium text-slate-800">{crag.final_diagnosis}</p>
          </div>
          <div className="text-right flex-shrink-0">
            <p className="text-xs text-slate-500 mb-0.5">Confidence</p>
            <p className={`text-sm font-semibold ${
              pct >= 80 ? 'text-emerald-600' : pct >= 60 ? 'text-amber-600' : 'text-red-500'
            }`}>{pct}%</p>
          </div>
        </div>
        <div className="mt-2 h-1.5 bg-slate-200 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full ${pct >= 80 ? 'bg-emerald-500' : pct >= 60 ? 'bg-amber-400' : 'bg-red-400'}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className="mt-2 text-xs text-slate-400">
          Attempt {attempt} of {MAX_ATTEMPTS} · Verdict: {crag.verdict}
        </p>
      </div>

      {/* Missing data questions */}
      {missing.length > 0 ? (
        <div className="space-y-4 mb-5">
          {missing.map((item, i) => (
            <div key={i} className="bg-white border border-slate-100 rounded-2xl p-4">
              <div className="flex items-start gap-2 mb-2">
                <HelpCircle className="w-4 h-4 text-brand-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${
                    CATEGORY_COLORS[item.category] ?? 'bg-slate-50 text-slate-600'
                  }`}>
                    {item.category.replace('_', ' ')}
                  </span>
                  <p className="mt-2 text-sm font-medium text-slate-700">{item.question_for_doctor}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{item.why_needed}</p>
                </div>
              </div>
              <textarea
                rows={2}
                value={answers[i] ?? ''}
                onChange={e => setAnswers(prev => ({ ...prev, [i]: e.target.value }))}
                placeholder="Your answer…"
                className="input-field resize-none mt-1"
              />
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-amber-50 border border-amber-100 rounded-xl px-4 py-3 mb-5">
          <p className="text-sm text-amber-700">
            The AI's confidence is below threshold. Please provide any additional clinical findings,
            test results, or history that may help confirm or rule out the diagnosis.
          </p>
        </div>
      )}

      {/* Free-text fallback */}
      <div className="mb-5">
        <label className="text-sm font-medium text-slate-700 block mb-1.5">
          Additional information
          <span className="text-slate-400 font-normal ml-1">(optional)</span>
        </label>
        <textarea
          rows={3}
          value={freeText}
          onChange={e => setFreeText(e.target.value)}
          placeholder="Any other relevant findings, test results, or clinical context…"
          className="input-field resize-none"
        />
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 rounded-xl px-4 py-3 text-sm mb-4">{error}</div>
      )}

      <button type="button" onClick={submit} disabled={submitting}
        className="w-full flex items-center justify-center gap-2 bg-brand-700 hover:bg-brand-800 text-white font-medium rounded-xl py-3 text-sm transition-colors disabled:opacity-60">
        {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
        {submitting ? 'Submitting…' : 'Submit additional data'}
      </button>

      <p className="text-center text-xs text-slate-400 mt-6">
        Decision support only. The final judgement is yours.
      </p>
    </div>
  )
}
