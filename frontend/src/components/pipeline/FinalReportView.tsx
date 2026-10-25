import { useNavigate } from 'react-router-dom'
import { CheckCircle, ArrowRight } from 'lucide-react'
import type { PipelineStateResponse } from '@/api/pipeline'
import { CRAGReport, VerdictBadge } from './hitl/HITL4Confirmation'

interface Props {
  state: PipelineStateResponse
}

export default function FinalReportView({ state }: Props) {
  const navigate = useNavigate()
  const crag = state.values.crag_output
  const provisionalDx = (state.values.provisional_diagnosis as { primary_diagnosis?: string } | null)?.primary_diagnosis

  if (!crag) {
    return (
      <div className="max-w-md mx-auto px-4 py-12 text-center">
        <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto mb-4" />
        <h1 className="text-lg font-semibold text-slate-800 mb-2">Analysis complete</h1>
        <p className="text-sm text-slate-500 mb-6">Report saved to the patient profile.</p>
        <button onClick={() => navigate('/worklist')}
          className="bg-brand-700 text-white text-sm font-medium px-5 py-3 rounded-xl hover:bg-brand-800 transition-colors">
          Back to worklist
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-5">
        <div className="inline-flex items-center gap-2 bg-emerald-50 text-emerald-700 text-xs font-medium px-3 py-1.5 rounded-full mb-3">
          <CheckCircle className="w-3.5 h-3.5" />
          Report generated
        </div>
        <div className="flex items-start gap-3">
          <div className="flex-1">
            <h1 className="text-lg font-semibold text-slate-800 mb-1">Final diagnosis report</h1>
            <div className="flex items-center gap-2">
              <VerdictBadge verdict={crag.verdict} />
              <span className="text-xs text-slate-400">
                {Math.round(crag.final_diagnosis_confidence * 100)}% confidence
              </span>
            </div>
          </div>
        </div>
        <div className="mt-3 bg-brand-50 border border-brand-100 rounded-xl px-4 py-3">
          <p className="text-sm font-semibold text-brand-800">{crag.final_diagnosis}</p>
          {crag.corrected_diagnosis && (
            <p className="text-xs text-brand-600 mt-0.5">
              Corrected from: {provisionalDx}
            </p>
          )}
        </div>
      </div>

      {/* Full report */}
      <CRAGReport crag={crag} provisionalDx={provisionalDx} />

      {/* Navigation */}
      <div className="mt-6 flex gap-3">
        <button onClick={() => navigate(`/patients/${state.session.patient_id}`)}
          className="flex-1 flex items-center justify-center gap-2 bg-brand-700 hover:bg-brand-800 text-white font-medium rounded-xl py-3 text-sm transition-colors">
          View patient profile <ArrowRight className="w-4 h-4" />
        </button>
        <button onClick={() => navigate('/worklist')}
          className="flex-1 flex items-center justify-center border border-slate-200 text-slate-600 font-medium rounded-xl py-3 text-sm hover:bg-slate-50 transition-colors">
          Worklist
        </button>
      </div>

      <p className="text-center text-xs text-slate-400 mt-6">
        Decision support only. The final judgement is yours.
      </p>
    </div>
  )
}
