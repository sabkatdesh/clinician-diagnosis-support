import type { IntakeFormData } from '@/types/intake'

interface Props {
  form: IntakeFormData
  onChange: (patch: Partial<IntakeFormData>) => void
}

export default function Step1Who({ form, onChange }: Props) {
  return (
    <div className="space-y-5">
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">
          Patient name <span className="text-slate-400 font-normal">(or leave blank for anonymous)</span>
        </label>
        <input
          type="text"
          value={form.name}
          onChange={e => onChange({ name: e.target.value })}
          placeholder="Full name"
          className="input-field"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">Age</label>
          <input
            type="number"
            value={form.age}
            onChange={e => onChange({ age: e.target.value })}
            placeholder="Years"
            min={0}
            max={130}
            className="input-field"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">Sex</label>
          <div className="flex gap-2">
            {(['Male', 'Female', 'Other'] as const).map(g => (
              <button
                key={g}
                type="button"
                onClick={() => onChange({ gender: g })}
                className={`flex-1 py-2.5 rounded-xl text-sm font-medium border transition-colors ${
                  form.gender === g
                    ? 'bg-brand-700 text-white border-brand-700'
                    : 'border-slate-200 text-slate-600 hover:border-brand-300'
                }`}
              >
                {g}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            Contact number <span className="text-slate-400 font-normal">(optional)</span>
          </label>
          <input
            type="tel"
            value={form.contact}
            onChange={e => onChange({ contact: e.target.value })}
            placeholder="01XXXXXXXXX"
            className="input-field"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            MRN / Patient ID <span className="text-slate-400 font-normal">(optional)</span>
          </label>
          <input
            type="text"
            value={form.patientId}
            onChange={e => onChange({ patientId: e.target.value })}
            placeholder="Hospital ID"
            className="input-field"
          />
        </div>
      </div>
    </div>
  )
}
