import { CheckCircle, Circle, Loader2 } from 'lucide-react'
import type { PipelineStateResponse } from '@/api/pipeline'

const STAGE_LABELS: Record<string, string> = {
  stage_1a:    'Reading patient notes',
  stage_1b:    'Identifying which systems to examine',
  hitl_1:      'Waiting for your exam plan approval',
  hitl_2:      'Waiting for your examination findings',
  stage_1c_i:  'Processing examination findings',
  stage_1c_ii: 'Forming a provisional diagnosis',
  hitl_3:      'Waiting for your diagnosis review',
  rag_node:    'Searching the medical textbook',
  crag_node:   'Checking evidence quality',
  hitl_3b:     'Waiting for your answers to questions',
  hitl_4:      'Waiting for your final confirmation',
}

const STAGE_ORDER = [
  'stage_1a', 'stage_1b', 'hitl_1', 'hitl_2',
  'stage_1c_i', 'stage_1c_ii', 'hitl_3',
  'rag_node', 'crag_node', 'hitl_3b', 'hitl_4',
]

interface Props {
  state: PipelineStateResponse
}

export default function ProcessingScreen({ state }: Props) {
  const currentStage = state.session.current_stage ?? ''
  const currentIdx   = STAGE_ORDER.indexOf(currentStage)

  return (
    <div className="max-w-md mx-auto px-4 py-8">
      <div className="text-center mb-8">
        <div className="w-14 h-14 rounded-full bg-brand-50 flex items-center justify-center mx-auto mb-4">
          <Loader2 className="w-7 h-7 text-brand-700 animate-spin" />
        </div>
        <h1 className="text-lg font-semibold text-slate-800">Analysis in progress</h1>
        <p className="text-sm text-slate-500 mt-1">
          You can leave this page. We will show you when it needs you.
        </p>
      </div>

      {/* Stage list */}
      <div className="bg-white rounded-2xl border border-slate-100 divide-y divide-slate-50">
        {STAGE_ORDER.filter(s => !s.startsWith('hitl')).map((stage, idx) => {
          const done    = currentIdx > idx
          const active  = currentIdx === idx
          const label   = STAGE_LABELS[stage] ?? stage

          return (
            <div key={stage} className="flex items-center gap-3 px-4 py-3.5">
              {done ? (
                <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
              ) : active ? (
                <Loader2 className="w-5 h-5 text-brand-600 animate-spin flex-shrink-0" />
              ) : (
                <Circle className="w-5 h-5 text-slate-200 flex-shrink-0" />
              )}
              <span className={`text-sm ${
                done   ? 'text-slate-400 line-through' :
                active ? 'text-slate-800 font-medium'  : 'text-slate-400'
              }`}>
                {label}
              </span>
            </div>
          )
        })}
      </div>

      <p className="text-center text-xs text-slate-400 mt-8">
        Decision support only. The final judgement is yours.
      </p>
    </div>
  )
}
