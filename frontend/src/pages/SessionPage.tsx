import { useParams, useNavigate } from 'react-router-dom'
import { Loader2, AlertCircle } from 'lucide-react'
import { usePipelineState } from '@/hooks/usePipelineState'
import ProcessingScreen from '@/components/pipeline/ProcessingScreen'
import FinalReportView from '@/components/pipeline/FinalReportView'
import HITL1ExamApproval from '@/components/pipeline/hitl/HITL1ExamApproval'
import HITL2ExamFindings from '@/components/pipeline/hitl/HITL2ExamFindings'
import HITL3DiagnosisReview from '@/components/pipeline/hitl/HITL3DiagnosisReview'
import HITL3bMissingData from '@/components/pipeline/hitl/HITL3bMissingData'
import HITL4Confirmation from '@/components/pipeline/hitl/HITL4Confirmation'

export default function SessionPage() {
  const { threadId } = useParams<{ threadId: string }>()
  const navigate     = useNavigate()
  const { data, isLoading, isError, refetch } = usePipelineState(threadId)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 text-brand-600 animate-spin" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="max-w-md mx-auto px-4 py-12 text-center">
        <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
        <p className="text-slate-700 font-medium mb-1">Could not load session</p>
        <p className="text-sm text-slate-400 mb-5">Your work is safe. Check your connection and try again.</p>
        <button onClick={() => refetch()}
          className="text-sm text-brand-700 border border-brand-200 px-4 py-2 rounded-xl hover:bg-brand-50 transition-colors">
          Try again
        </button>
      </div>
    )
  }

  if (!data || data.status === 'not_found') {
    return (
      <div className="max-w-md mx-auto px-4 py-12 text-center">
        <p className="text-slate-600">Session not found.</p>
        <button onClick={() => navigate('/worklist')} className="mt-4 text-sm text-brand-700 underline">
          Back to worklist
        </button>
      </div>
    )
  }

  // Pipeline complete — show the final report
  if (data.status === 'complete') {
    return <FinalReportView state={data} />
  }

  // HITL gates — paused and waiting for the doctor
  if (data.status === 'paused' && data.paused_at) {
    switch (data.paused_at) {
      case 'hitl_1_recommendation_approval':
        return <HITL1ExamApproval state={data} />
      case 'hitl_2_exam_input':
        return <HITL2ExamFindings state={data} />
      case 'hitl_3_diagnosis_approval':
        return <HITL3DiagnosisReview state={data} />
      case 'hitl_3b_crag_missing_data':
        return <HITL3bMissingData state={data} />
      case 'hitl_4_crag_confirmation':
        return <HITL4Confirmation state={data} />
      default:
        return <HITLPlaceholder label="Your input needed" detail={data.paused_at} />
    }
  }

  // Running (either status='running' or status='paused' with no paused_at — pipeline between stages)
  return <ProcessingScreen state={data} />
}

function HITLPlaceholder({ label, detail }: { label: string; detail: string }) {
  return (
    <div className="max-w-md mx-auto px-4 py-12 text-center">
      <div className="w-14 h-14 rounded-full bg-amber-50 flex items-center justify-center mx-auto mb-4">
        <span className="text-2xl">⏸</span>
      </div>
      <h1 className="text-lg font-semibold text-slate-800 mb-2">{label}</h1>
      <div className="bg-amber-50 rounded-xl px-4 py-3 text-xs text-amber-700">
        Coming in {detail}
      </div>
    </div>
  )
}
