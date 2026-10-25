import type { IntakeFormData, TriState } from '@/types/intake'

interface Props {
  form: IntakeFormData
  onChange: (patch: Partial<IntakeFormData>) => void
}

export default function Step4GenExam({ form, onChange }: Props) {
  return (
    <div className="space-y-5">
      {/* Appearance */}
      <div>
        <p className="text-sm font-medium text-slate-700 mb-2">General appearance</p>
        <div className="flex gap-2">
          {(['well', 'ill-looking', 'distressed'] as const).map(v => (
            <button
              key={v}
              type="button"
              onClick={() => onChange({ appearance: form.appearance === v ? '' : v })}
              className={`flex-1 py-2.5 rounded-xl text-sm border capitalize transition-colors ${
                form.appearance === v
                  ? 'bg-brand-700 text-white border-brand-700'
                  : 'border-slate-200 text-slate-600 hover:border-brand-300'
              }`}
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      {/* Signs — Present / Absent / Not checked */}
      <div>
        <p className="text-sm font-medium text-slate-700 mb-3">Signs</p>
        <div className="space-y-2">
          {([
            ['pallor', 'Pallor'],
            ['jaundice', 'Jaundice'],
            ['cyanosis', 'Cyanosis'],
            ['clubbing', 'Clubbing'],
            ['koilonychia', 'Koilonychia'],
            ['dehydration', 'Dehydration'],
            ['bonyTenderness', 'Bony tenderness'],
            ['meningealIrritation', 'Meningeal irritation signs'],
          ] as [keyof IntakeFormData, string][]).map(([field, label]) => (
            <TriStateRow
              key={field}
              label={label}
              value={form[field] as TriState}
              onChange={v => onChange({ [field]: v })}
            />
          ))}
        </div>
      </div>

      {/* Edema */}
      <div>
        <p className="text-sm font-medium text-slate-700 mb-2">Oedema</p>
        <div className="flex flex-wrap gap-2">
          {['none', 'pedal', 'facial', 'sacral', 'generalised'].map(v => (
            <button
              key={v}
              type="button"
              onClick={() => onChange({ edema: form.edema === v ? '' : v })}
              className={`px-4 py-2 rounded-full text-sm border capitalize transition-colors ${
                form.edema === v
                  ? 'bg-brand-700 text-white border-brand-700'
                  : 'border-slate-200 text-slate-600 hover:border-brand-300'
              }`}
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      {/* Lymph nodes */}
      <div>
        <p className="text-sm font-medium text-slate-700 mb-2">Lymph nodes</p>
        <div className="flex flex-wrap gap-2">
          {['none', 'cervical', 'axillary', 'inguinal', 'generalised'].map(v => (
            <button
              key={v}
              type="button"
              onClick={() => onChange({ lymphNodes: form.lymphNodes === v ? '' : v })}
              className={`px-4 py-2 rounded-full text-sm border capitalize transition-colors ${
                form.lymphNodes === v
                  ? 'bg-brand-700 text-white border-brand-700'
                  : 'border-slate-200 text-slate-600 hover:border-brand-300'
              }`}
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      {/* Tongue */}
      <div>
        <p className="text-sm font-medium text-slate-700 mb-2">Tongue</p>
        <div className="flex gap-2">
          {['normal', 'dry', 'coated', 'strawberry'].map(v => (
            <button
              key={v}
              type="button"
              onClick={() => onChange({ tongue: form.tongue === v ? '' : v })}
              className={`flex-1 py-2 rounded-xl text-sm border capitalize transition-colors ${
                form.tongue === v
                  ? 'bg-brand-700 text-white border-brand-700'
                  : 'border-slate-200 text-slate-600 hover:border-brand-300'
              }`}
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      {/* Throat / ENT */}
      <div>
        <p className="text-sm font-medium text-slate-700 mb-2">Throat / ENT</p>
        <div className="flex flex-wrap gap-2">
          {['normal', 'congested throat', 'enlarged tonsils', 'ear discharge'].map(v => (
            <button
              key={v}
              type="button"
              onClick={() => onChange({ throat: form.throat === v ? '' : v })}
              className={`px-3 py-2 rounded-full text-sm border capitalize transition-colors ${
                form.throat === v
                  ? 'bg-brand-700 text-white border-brand-700'
                  : 'border-slate-200 text-slate-600 hover:border-brand-300'
              }`}
            >
              {v}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

function TriStateRow({
  label, value, onChange,
}: {
  label: string
  value: TriState
  onChange: (v: TriState) => void
}) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-sm text-slate-700">{label}</span>
      <div className="flex gap-1">
        {(['present', 'absent', 'not checked'] as TriState[]).map(v => (
          <button
            key={v}
            type="button"
            onClick={() => onChange(v)}
            className={`px-3 py-1.5 rounded-lg text-xs border transition-colors ${
              value === v
                ? v === 'present'
                  ? 'bg-amber-500 text-white border-amber-500'
                  : v === 'absent'
                  ? 'bg-emerald-600 text-white border-emerald-600'
                  : 'bg-slate-200 text-slate-600 border-slate-200'
                : 'border-slate-200 text-slate-500 hover:border-slate-300'
            }`}
          >
            {v === 'not checked' ? '—' : v === 'present' ? 'Present' : 'Absent'}
          </button>
        ))}
      </div>
    </div>
  )
}
