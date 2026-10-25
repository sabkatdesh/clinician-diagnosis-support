import { useState } from 'react'
import { Loader2, Eye, EyeOff } from 'lucide-react'
import type { PipelineStateResponse, ExamSystem } from '@/api/pipeline'
import { pipelineApi } from '@/api/pipeline'
import { useInvalidatePipeline } from '@/hooks/usePipelineState'
import {
  composeExamText, EMPTY_FINDINGS,
  type AllExamFindings, type BoolState,
  type CVSForm, type RSForm, type CNSForm,
  type GITForm, type GUSForm, type MSKForm,
} from '@/lib/composeExamText'

const SYSTEM_LABELS: Record<ExamSystem, string> = {
  CVS: 'CVS', RS: 'Resp', CNS: 'CNS', GIT: 'GIT', GUS: 'GUS', MSK: 'MSK',
}

type BtnProps = { val: BoolState; options?: string[]; onChange: (v: BoolState) => void }
function BoolRow({ label, val, onChange }: { label: string } & BtnProps) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-50">
      <span className="text-sm text-slate-700 flex-1">{label}</span>
      <div className="flex gap-1">
        {(['yes', 'no'] as const).map(v => (
          <button key={v} type="button" onClick={() => onChange(val === v ? null : v)}
            className={`px-3 py-1.5 rounded-lg text-xs border capitalize transition-colors ${
              val === v
                ? v === 'yes' ? 'bg-amber-500 text-white border-amber-500'
                              : 'bg-emerald-600 text-white border-emerald-600'
                : 'border-slate-200 text-slate-500 hover:border-slate-300'
            }`}>{v === 'yes' ? 'Yes' : 'No'}
          </button>
        ))}
      </div>
    </div>
  )
}

function ChipRow<T extends string>({
  label, options, val, onChange,
}: { label: string; options: T[]; val: T | null; onChange: (v: T | null) => void }) {
  return (
    <div className="py-2 border-b border-slate-50">
      <p className="text-xs text-slate-500 mb-1.5">{label}</p>
      <div className="flex flex-wrap gap-1.5">
        {options.map(o => (
          <button key={o} type="button" onClick={() => onChange(val === o ? null : o)}
            className={`px-2.5 py-1 rounded-full text-xs border capitalize transition-colors ${
              val === o ? 'bg-brand-700 text-white border-brand-700' : 'border-slate-200 text-slate-600 hover:border-brand-300'
            }`}>{o}
          </button>
        ))}
      </div>
    </div>
  )
}

function OtherText({ val, onChange }: { val: string; onChange: (v: string) => void }) {
  return (
    <div className="pt-2">
      <p className="text-xs text-slate-500 mb-1.5">Other findings (free text)</p>
      <textarea rows={2} value={val} onChange={e => onChange(e.target.value)}
        placeholder="Any additional findings…"
        className="input-field resize-none" />
    </div>
  )
}

// ─── System forms ────────────────────────────────────────────────────────────

function CVSSection({ f, onChange }: { f: CVSForm; onChange: (p: Partial<CVSForm>) => void }) {
  return (
    <div className="space-y-0">
      <BoolRow label="S1/S2 normal" val={f.s1_s2_normal} onChange={v => onChange({ s1_s2_normal: v })} />
      <BoolRow label="Murmur present" val={f.murmur_present} onChange={v => onChange({ murmur_present: v })} />
      {f.murmur_present === 'yes' && (
        <ChipRow label="Murmur type" options={['systolic', 'diastolic', 'continuous'] as const}
          val={f.murmur_type} onChange={v => onChange({ murmur_type: v })} />
      )}
      <BoolRow label="JVP elevated" val={f.jvp_elevation} onChange={v => onChange({ jvp_elevation: v })} />
      <ChipRow label="Pulse character" options={['normal', 'weak', 'bounding', 'irregular'] as const}
        val={f.pulse_character} onChange={v => onChange({ pulse_character: v })} />
      <BoolRow label="Peripheral oedema" val={f.edema_present} onChange={v => onChange({ edema_present: v })} />
      {f.edema_present === 'yes' && (
        <ChipRow label="Oedema grade" options={['+1', '+2', '+3', '+4'] as const}
          val={f.edema_grade} onChange={v => onChange({ edema_grade: v })} />
      )}
      <OtherText val={f.other} onChange={v => onChange({ other: v })} />
    </div>
  )
}

function RSSection({ f, onChange }: { f: RSForm; onChange: (p: Partial<RSForm>) => void }) {
  return (
    <div>
      <BoolRow label="Chest movement symmetric" val={f.chest_movement_symmetric} onChange={v => onChange({ chest_movement_symmetric: v })} />
      <ChipRow label="Percussion" options={['resonant', 'dull', 'hyperresonant'] as const}
        val={f.percussion} onChange={v => onChange({ percussion: v })} />
      <BoolRow label="Wheeze" val={f.wheeze_present} onChange={v => onChange({ wheeze_present: v })} />
      {f.wheeze_present === 'yes' && (
        <ChipRow label="Wheeze type" options={['expiratory', 'inspiratory', 'biphasic'] as const}
          val={f.wheeze_type} onChange={v => onChange({ wheeze_type: v })} />
      )}
      <BoolRow label="Crackles" val={f.crackles_present} onChange={v => onChange({ crackles_present: v })} />
      {f.crackles_present === 'yes' && (
        <ChipRow label="Crackle type" options={['fine', 'coarse'] as const}
          val={f.crackles_type} onChange={v => onChange({ crackles_type: v })} />
      )}
      <BoolRow label="Accessory muscle use" val={f.accessory_muscle_use} onChange={v => onChange({ accessory_muscle_use: v })} />
      <OtherText val={f.other} onChange={v => onChange({ other: v })} />
    </div>
  )
}

function CNSSection({ f, onChange }: { f: CNSForm; onChange: (p: Partial<CNSForm>) => void }) {
  return (
    <div>
      <ChipRow label="Consciousness" options={['alert', 'drowsy', 'lethargic', 'stuporous', 'comatose'] as const}
        val={f.consciousness} onChange={v => onChange({ consciousness: v })} />
      <BoolRow label="Fully oriented" val={f.oriented} onChange={v => onChange({ oriented: v })} />
      <div className="py-2 border-b border-slate-50">
        <label className="text-xs text-slate-500 mb-1 block">GCS score (3–15)</label>
        <input type="text" value={f.gcs} onChange={e => onChange({ gcs: e.target.value })}
          placeholder="e.g. 15" className="input-field" />
      </div>
      <ChipRow label="Pupils" options={['reactive', 'sluggish', 'fixed'] as const}
        val={f.pupils} onChange={v => onChange({ pupils: v })} />
      <BoolRow label="Motor power normal" val={f.motor_normal} onChange={v => onChange({ motor_normal: v })} />
      <BoolRow label="Neck stiffness" val={f.neck_stiffness} onChange={v => onChange({ neck_stiffness: v })} />
      <BoolRow label="Kernig sign" val={f.kernig} onChange={v => onChange({ kernig: v })} />
      <OtherText val={f.other} onChange={v => onChange({ other: v })} />
    </div>
  )
}

function GITSection({ f, onChange }: { f: GITForm; onChange: (p: Partial<GITForm>) => void }) {
  return (
    <div>
      <BoolRow label="Abdominal distension" val={f.distension} onChange={v => onChange({ distension: v })} />
      <BoolRow label="Tenderness" val={f.tenderness} onChange={v => onChange({ tenderness: v })} />
      {f.tenderness === 'yes' && (
        <div className="py-2 border-b border-slate-50">
          <label className="text-xs text-slate-500 mb-1 block">Tenderness site</label>
          <input type="text" value={f.tenderness_site} onChange={e => onChange({ tenderness_site: e.target.value })}
            placeholder="e.g. epigastric, RUQ, periumbilical" className="input-field" />
        </div>
      )}
      <BoolRow label="Guarding / rigidity" val={f.guarding} onChange={v => onChange({ guarding: v })} />
      <BoolRow label="Hepatomegaly" val={f.hepatomegaly} onChange={v => onChange({ hepatomegaly: v })} />
      {f.hepatomegaly === 'yes' && (
        <div className="py-2 border-b border-slate-50">
          <label className="text-xs text-slate-500 mb-1 block">Liver edge (cm below costal margin)</label>
          <input type="text" value={f.hepatomegaly_cm} onChange={e => onChange({ hepatomegaly_cm: e.target.value })}
            placeholder="e.g. 3" className="input-field" />
        </div>
      )}
      <BoolRow label="Splenomegaly" val={f.splenomegaly} onChange={v => onChange({ splenomegaly: v })} />
      <BoolRow label="Ascites" val={f.ascites} onChange={v => onChange({ ascites: v })} />
      <ChipRow label="Bowel sounds" options={['normal', 'increased', 'decreased', 'absent'] as const}
        val={f.bowel_sounds} onChange={v => onChange({ bowel_sounds: v })} />
      <OtherText val={f.other} onChange={v => onChange({ other: v })} />
    </div>
  )
}

function GUSSection({ f, onChange }: { f: GUSForm; onChange: (p: Partial<GUSForm>) => void }) {
  return (
    <div>
      <ChipRow label="CVA tenderness" options={['none', 'right', 'left', 'bilateral'] as const}
        val={f.cva_tenderness} onChange={v => onChange({ cva_tenderness: v })} />
      <BoolRow label="Suprapubic tenderness" val={f.suprapubic_tenderness} onChange={v => onChange({ suprapubic_tenderness: v })} />
      <BoolRow label="Bladder distension" val={f.bladder_distension} onChange={v => onChange({ bladder_distension: v })} />
      <OtherText val={f.other} onChange={v => onChange({ other: v })} />
    </div>
  )
}

function MSKSection({ f, onChange }: { f: MSKForm; onChange: (p: Partial<MSKForm>) => void }) {
  return (
    <div>
      <div className="py-2 border-b border-slate-50">
        <label className="text-xs text-slate-500 mb-1 block">Joints examined</label>
        <input type="text" value={f.joints_involved} onChange={e => onChange({ joints_involved: e.target.value })}
          placeholder="e.g. bilateral knees, right hip" className="input-field" />
      </div>
      <BoolRow label="Swelling" val={f.swelling} onChange={v => onChange({ swelling: v })} />
      <BoolRow label="Erythema / warmth" val={f.erythema_warmth} onChange={v => onChange({ erythema_warmth: v })} />
      <BoolRow label="Tenderness" val={f.tenderness} onChange={v => onChange({ tenderness: v })} />
      <BoolRow label="Range of motion limited" val={f.rom_limited} onChange={v => onChange({ rom_limited: v })} />
      <ChipRow label="Muscle strength" options={['5', '4', '3', '2', '1', '0'] as const}
        val={f.muscle_strength} onChange={v => onChange({ muscle_strength: v })} />
      <OtherText val={f.other} onChange={v => onChange({ other: v })} />
    </div>
  )
}

// ─── Determine systems from state ────────────────────────────────────────────

const ALL_SYSTEMS: ExamSystem[] = ['CVS', 'RS', 'CNS', 'GIT', 'GUS', 'MSK']
const KNOWN_CODES = new Set(ALL_SYSTEMS)

function resolveSystemsFromState(state: PipelineStateResponse): ExamSystem[] {
  const vals = state.values
  const approved = vals.doctor_approved_recommendation
  const rec = vals.exam_recommendation
  const modified = vals.doctor_modified_recommendation

  if (approved === true && rec?.primary_recommendation?.exam_types) {
    return rec.primary_recommendation.exam_types
  }
  if (approved === false && modified) {
    // Parse "CVS, RS" style text
    const parsed = modified.toUpperCase().split(/[,\s]+/).filter(t => KNOWN_CODES.has(t as ExamSystem)) as ExamSystem[]
    if (parsed.length > 0) return parsed
  }
  // Fallback to primary recommendation or all systems
  return rec?.primary_recommendation?.exam_types ?? ALL_SYSTEMS
}

// ─── Main component ────────────────────────────────────────────────────────

export default function HITL2ExamFindings({ state }: { state: PipelineStateResponse }) {
  const invalidate = useInvalidatePipeline()
  const systems    = resolveSystemsFromState(state)

  const [activeTab, setActiveTab]   = useState<ExamSystem>(systems[0] ?? 'CVS')
  const [findings, setFindings]     = useState<AllExamFindings>(EMPTY_FINDINGS)
  const [showPreview, setShowPreview] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError]           = useState('')

  function patchSystem<K extends ExamSystem>(sys: K, patch: Partial<AllExamFindings[K]>) {
    setFindings(prev => ({ ...prev, [sys]: { ...prev[sys], ...patch } }))
  }

  const previewText = composeExamText(findings, systems)

  async function submit() {
    const text = previewText.trim()
    if (!text) { setError('Please enter at least one finding.'); return }
    setError('')
    setSubmitting(true)
    try {
      await pipelineApi.resume(state.thread_id, 'hitl_2_exam_input', { exam_text: text })
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
          Your input needed
        </div>
        <h1 className="text-lg font-semibold text-slate-800 mb-1">Enter examination findings</h1>
        <p className="text-sm text-slate-500">
          Fill in findings for each recommended system. Only assessed values will be included.
        </p>
      </div>

      {/* System tabs */}
      <div className="flex gap-1.5 mb-4 overflow-x-auto pb-1">
        {systems.map(sys => (
          <button key={sys} type="button" onClick={() => setActiveTab(sys)}
            className={`flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
              activeTab === sys
                ? 'bg-brand-700 text-white border-brand-700'
                : 'border-slate-200 text-slate-600 hover:border-brand-300'
            }`}>
            {SYSTEM_LABELS[sys]}
          </button>
        ))}
      </div>

      {/* Active system form */}
      <div className="bg-white rounded-2xl border border-slate-100 p-4 mb-4">
        {activeTab === 'CVS' && (
          <CVSSection f={findings.CVS} onChange={p => patchSystem('CVS', p)} />
        )}
        {activeTab === 'RS' && (
          <RSSection f={findings.RS} onChange={p => patchSystem('RS', p)} />
        )}
        {activeTab === 'CNS' && (
          <CNSSection f={findings.CNS} onChange={p => patchSystem('CNS', p)} />
        )}
        {activeTab === 'GIT' && (
          <GITSection f={findings.GIT} onChange={p => patchSystem('GIT', p)} />
        )}
        {activeTab === 'GUS' && (
          <GUSSection f={findings.GUS} onChange={p => patchSystem('GUS', p)} />
        )}
        {activeTab === 'MSK' && (
          <MSKSection f={findings.MSK} onChange={p => patchSystem('MSK', p)} />
        )}
      </div>

      {/* Preview toggle */}
      <button type="button" onClick={() => setShowPreview(v => !v)}
        className="flex items-center gap-1.5 text-sm text-brand-700 mb-4">
        {showPreview ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
        {showPreview ? 'Hide preview' : 'Preview clinical text'}
      </button>

      {showPreview && (
        <div className="bg-slate-50 border border-slate-100 rounded-2xl p-4 mb-4">
          <p className="text-xs font-medium text-slate-500 mb-2">Text that will be sent to the AI:</p>
          <pre className="text-xs text-slate-700 whitespace-pre-wrap font-mono leading-relaxed">
            {previewText || '(Nothing entered yet)'}
          </pre>
        </div>
      )}

      {error && (
        <div className="bg-red-50 text-red-700 rounded-xl px-4 py-3 text-sm mb-4">{error}</div>
      )}

      <button type="button" onClick={submit} disabled={submitting}
        className="w-full flex items-center justify-center gap-2 bg-brand-700 hover:bg-brand-800 text-white font-medium rounded-xl py-3 text-sm transition-colors disabled:opacity-60">
        {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
        {submitting ? 'Submitting…' : 'Submit examination findings'}
      </button>

      <p className="text-center text-xs text-slate-400 mt-6">
        Decision support only. The final judgement is yours.
      </p>
    </div>
  )
}
