import type { IntakeFormData } from '@/types/intake'
import { calcBMI } from '@/lib/compose'

interface Props {
  form: IntakeFormData
  onChange: (patch: Partial<IntakeFormData>) => void
}

function isOutOfRange(field: string, value: string): boolean {
  const n = parseFloat(value)
  if (isNaN(n)) return false
  const ranges: Record<string, [number, number]> = {
    heartRate: [40, 200],
    respiratoryRate: [8, 60],
    spo2: [70, 100],
    bpSystolic: [70, 220],
    bpDiastolic: [40, 140],
  }
  const r = ranges[field]
  if (!r) return false
  return n < r[0] || n > r[1]
}

export default function Step3Vitals({ form, onChange }: Props) {
  function handleVital(field: keyof IntakeFormData, value: string) {
    const patch: Partial<IntakeFormData> = { [field]: value }
    if (field === 'weight' || field === 'height') {
      const w = field === 'weight' ? value : form.weight
      const h = field === 'height' ? value : form.height
      patch.bmi = calcBMI(w, h)
    }
    onChange(patch)
  }

  return (
    <div className="space-y-5">
      {/* Temperature */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">Temperature</label>
        <div className="flex gap-2">
          <input
            type="number"
            value={form.temperature}
            onChange={e => onChange({ temperature: e.target.value })}
            placeholder="36.8"
            step="0.1"
            className="input-field flex-1"
          />
          <div className="flex rounded-xl border border-slate-200 overflow-hidden">
            {(['C', 'F'] as const).map(u => (
              <button
                key={u}
                type="button"
                onClick={() => onChange({ temperatureUnit: u })}
                className={`px-4 py-2.5 text-sm font-medium transition-colors ${
                  form.temperatureUnit === u
                    ? 'bg-brand-700 text-white'
                    : 'text-slate-500 hover:bg-slate-50'
                }`}
              >
                °{u}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Blood pressure */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">
          Blood pressure <span className="text-slate-400 font-normal">mmHg</span>
        </label>
        <div className="flex items-center gap-2">
          <VitalInput
            value={form.bpSystolic}
            onChange={v => handleVital('bpSystolic', v)}
            placeholder="120"
            warn={isOutOfRange('bpSystolic', form.bpSystolic)}
          />
          <span className="text-slate-400 text-lg">/</span>
          <VitalInput
            value={form.bpDiastolic}
            onChange={v => handleVital('bpDiastolic', v)}
            placeholder="80"
            warn={isOutOfRange('bpDiastolic', form.bpDiastolic)}
          />
        </div>
      </div>

      {/* Row: HR + RR */}
      <div className="grid grid-cols-2 gap-4">
        <LabeledVital
          label="Heart rate"
          unit="/min"
          value={form.heartRate}
          onChange={v => handleVital('heartRate', v)}
          placeholder="72"
          warn={isOutOfRange('heartRate', form.heartRate)}
        />
        <LabeledVital
          label="Respiratory rate"
          unit="/min"
          value={form.respiratoryRate}
          onChange={v => handleVital('respiratoryRate', v)}
          placeholder="16"
          warn={isOutOfRange('respiratoryRate', form.respiratoryRate)}
        />
      </div>

      {/* SpO2 */}
      <LabeledVital
        label="Oxygen saturation"
        unit="%"
        value={form.spo2}
        onChange={v => handleVital('spo2', v)}
        placeholder="98"
        warn={isOutOfRange('spo2', form.spo2)}
      />

      {/* Row: Weight + Height */}
      <div className="grid grid-cols-2 gap-4">
        <LabeledVital
          label="Weight"
          unit="kg"
          value={form.weight}
          onChange={v => handleVital('weight', v)}
          placeholder="65"
        />
        <LabeledVital
          label="Height"
          unit="cm"
          value={form.height}
          onChange={v => handleVital('height', v)}
          placeholder="165"
        />
      </div>

      {/* Auto BMI */}
      {form.bmi && (
        <div className="flex items-center gap-2 bg-slate-50 rounded-xl px-4 py-3">
          <span className="text-sm text-slate-500">BMI</span>
          <span className="text-lg font-semibold text-slate-800">{form.bmi}</span>
          <span className="text-xs text-slate-400 ml-1">
            {(() => {
              const b = parseFloat(form.bmi)
              if (b < 18.5) return '— Underweight'
              if (b < 25)   return '— Normal'
              if (b < 30)   return '— Overweight'
              return '— Obese'
            })()}
          </span>
          <span className="ml-auto text-xs text-slate-400">Auto-calculated</span>
        </div>
      )}
    </div>
  )
}

function VitalInput({
  value, onChange, placeholder, warn,
}: {
  value: string; onChange: (v: string) => void; placeholder: string; warn?: boolean
}) {
  return (
    <input
      type="number"
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      className={`input-field flex-1 text-center text-lg font-semibold ${
        warn ? 'border-amber-400 bg-amber-50 focus:ring-amber-500' : ''
      }`}
    />
  )
}

function LabeledVital({
  label, unit, value, onChange, placeholder, warn,
}: {
  label: string; unit: string; value: string
  onChange: (v: string) => void; placeholder: string; warn?: boolean
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1.5">
        {label} <span className="text-slate-400 font-normal">{unit}</span>
      </label>
      <input
        type="number"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className={`input-field text-center text-lg font-semibold ${
          warn ? 'border-amber-400 bg-amber-50 focus:ring-amber-500' : ''
        }`}
      />
      {warn && <p className="text-xs text-amber-600 mt-1">Value outside usual range</p>}
    </div>
  )
}
