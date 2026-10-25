import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft, ChevronRight, Check, Loader2 } from 'lucide-react'
import { EMPTY_FORM, type IntakeFormData } from '@/types/intake'
import { composeIntakeText } from '@/lib/compose'
import { pipelineApi } from '@/api/pipeline'
import Step1Who from '@/components/intake/Step1Who'
import Step2Complaints from '@/components/intake/Step2Complaints'
import Step3Vitals from '@/components/intake/Step3Vitals'
import Step4GenExam from '@/components/intake/Step4GenExam'
import Step5History from '@/components/intake/Step5History'

const STEPS = [
  { label: 'Patient',     title: 'Who is this patient?' },
  { label: 'Complaints',  title: 'Chief complaints' },
  { label: 'Vitals',      title: 'Vital signs' },
  { label: 'Examination', title: 'General examination' },
  { label: 'History',     title: 'History & safety' },
  { label: 'Review',      title: 'Review and start' },
]

export default function NewPatientPage() {
  const [step, setStep]   = useState(0)
  const [form, setForm]   = useState<IntakeFormData>(EMPTY_FORM)
  const [loading, setLoading] = useState(false)
  const [error, setError]  = useState('')
  const navigate = useNavigate()

  function patch(p: Partial<IntakeFormData>) {
    setForm(prev => ({ ...prev, ...p }))
  }

  function canAdvance(): boolean {
    if (step === 0) return !!form.gender    // age is optional, gender is quick to tap
    if (step === 1) return form.complaints.length > 0
    if (step === 4) {
      const hasAllergy = form.allergies.some(a => a.trim().length > 0)
      const hasMed     = form.medications.some(m => m.trim().length > 0)
      return hasAllergy && hasMed
    }
    return true
  }

  async function startAnalysis() {
    setError('')
    setLoading(true)
    try {
      const text = composeIntakeText(form)
      const res  = await pipelineApi.start(text)
      navigate(`/session/${res.thread_id}`)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? 'Failed to start analysis. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const isLast = step === STEPS.length - 1

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      {/* Progress bar */}
      <div className="flex items-center gap-1 mb-6">
        {STEPS.map((s, i) => (
          <div key={i} className="flex-1 flex flex-col items-center gap-1">
            <div className={`h-1.5 w-full rounded-full transition-colors ${
              i < step  ? 'bg-brand-700' :
              i === step ? 'bg-brand-400' : 'bg-slate-200'
            }`} />
          </div>
        ))}
      </div>
      <p className="text-xs text-slate-400 mb-1">Step {step + 1} of {STEPS.length} — {STEPS[step].label}</p>
      <h1 className="text-xl font-semibold text-slate-800 mb-6">{STEPS[step].title}</h1>

      {/* Step content */}
      <div className="bg-white rounded-2xl border border-slate-100 p-5 mb-6">
        {step === 0 && <Step1Who form={form} onChange={patch} />}
        {step === 1 && <Step2Complaints form={form} onChange={patch} />}
        {step === 2 && <Step3Vitals form={form} onChange={patch} />}
        {step === 3 && <Step4GenExam form={form} onChange={patch} />}
        {step === 4 && <Step5History form={form} onChange={patch} />}
        {step === 5 && <IntakeSummary form={form} onEdit={setStep} />}
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 rounded-xl px-4 py-3 text-sm mb-4">{error}</div>
      )}

      {/* Navigation */}
      <div className="flex gap-3">
        <button
          type="button"
          onClick={() => step > 0 ? setStep(s => s - 1) : navigate('/worklist')}
          className="flex items-center gap-2 px-4 py-3 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 text-sm font-medium transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          {step === 0 ? 'Cancel' : 'Back'}
        </button>

        {isLast ? (
          <button
            type="button"
            onClick={startAnalysis}
            disabled={loading}
            className="flex-1 flex items-center justify-center gap-2 bg-brand-700 hover:bg-brand-800 text-white font-medium rounded-xl py-3 text-sm transition-colors disabled:opacity-60"
          >
            {loading ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Starting analysis…</>
            ) : (
              <><Check className="w-4 h-4" /> Start analysis</>
            )}
          </button>
        ) : (
          <button
            type="button"
            onClick={() => setStep(s => s + 1)}
            disabled={!canAdvance()}
            className="flex-1 flex items-center justify-center gap-2 bg-brand-700 hover:bg-brand-800 text-white font-medium rounded-xl py-3 text-sm transition-colors disabled:opacity-50"
          >
            Next <ChevronRight className="w-4 h-4" />
          </button>
        )}
      </div>

      <p className="text-center text-xs text-slate-400 mt-6">
        Decision support only. The final judgement is yours.
      </p>
    </div>
  )
}

function IntakeSummary({
  form, onEdit,
}: {
  form: IntakeFormData
  onEdit: (step: number) => void
}) {
  const rows: { label: string; value: string; step: number }[] = [
    {
      label: 'Patient',
      value: [form.name || 'No name', form.age ? `${form.age}y` : '', form.gender].filter(Boolean).join(', ') || '—',
      step: 0,
    },
    {
      label: 'Complaints',
      value: form.complaints.length
        ? form.complaints.map(c => {
            const dur = c.duration ? ` (${c.duration}${c.durationUnit[0]})` : ''
            return c.name + dur
          }).join(', ')
        : '—',
      step: 1,
    },
    {
      label: 'Vitals',
      value: [
        form.temperature ? `Temp ${form.temperature}°${form.temperatureUnit}` : '',
        form.bpSystolic  ? `BP ${form.bpSystolic}/${form.bpDiastolic}` : '',
        form.heartRate   ? `HR ${form.heartRate}` : '',
        form.spo2        ? `SpO2 ${form.spo2}%` : '',
      ].filter(Boolean).join(' · ') || '—',
      step: 2,
    },
    {
      label: 'Allergies',
      value: form.allergies.filter(Boolean).join(', ') || '—',
      step: 4,
    },
    {
      label: 'Medications',
      value: form.medications.filter(Boolean).join(', ') || '—',
      step: 4,
    },
  ]

  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-500 mb-4">
        Review what will be sent to the AI for analysis. Tap any row to edit.
      </p>
      {rows.map(({ label, value, step }) => (
        <div
          key={label}
          className="flex items-start justify-between gap-4 py-3 border-b border-slate-100 last:border-0"
        >
          <div className="min-w-0">
            <p className="text-xs text-slate-400 mb-0.5">{label}</p>
            <p className="text-sm text-slate-800">{value}</p>
          </div>
          <button
            type="button"
            onClick={() => onEdit(step)}
            className="text-xs text-brand-700 hover:underline flex-shrink-0 mt-1"
          >
            Edit
          </button>
        </div>
      ))}
    </div>
  )
}
