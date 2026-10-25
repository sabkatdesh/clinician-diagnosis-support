import { Plus, X } from 'lucide-react'
import type { IntakeFormData } from '@/types/intake'
import { PAST_ILLNESS_OPTIONS } from '@/types/intake'

interface Props {
  form: IntakeFormData
  onChange: (patch: Partial<IntakeFormData>) => void
}

export default function Step5History({ form, onChange }: Props) {
  function updateList(field: 'allergies' | 'medications' | 'adverseReactions', idx: number, val: string) {
    const arr = [...form[field]]
    arr[idx] = val
    onChange({ [field]: arr })
  }

  function addRow(field: 'allergies' | 'medications' | 'adverseReactions') {
    onChange({ [field]: [...form[field], ''] })
  }

  function removeRow(field: 'allergies' | 'medications' | 'adverseReactions', idx: number) {
    const arr = form[field].filter((_, i) => i !== idx)
    onChange({ [field]: arr.length ? arr : [''] })
  }

  function toggleIllness(illness: string) {
    const current = form.pastIllnesses
    if (current.includes(illness)) {
      onChange({ pastIllnesses: current.filter(i => i !== illness) })
    } else {
      onChange({ pastIllnesses: [...current, illness] })
    }
  }

  function toggleFamily(illness: string) {
    const current = form.familyHistory
    if (current.includes(illness)) {
      onChange({ familyHistory: current.filter(i => i !== illness) })
    } else {
      onChange({ familyHistory: [...current, illness] })
    }
  }

  return (
    <div className="space-y-6">
      {/* Allergies — required */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <p className="text-sm font-medium text-slate-700">Drug allergies</p>
          <span className="text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded-full">Required</span>
        </div>
        <p className="text-xs text-slate-400 mb-2">Enter each allergy and reaction, or write "None known"</p>
        {form.allergies.map((a, i) => (
          <div key={i} className="flex gap-2 mb-2">
            <input
              type="text"
              value={a}
              onChange={e => updateList('allergies', i, e.target.value)}
              placeholder={i === 0 ? 'e.g. Penicillin — anaphylaxis, or None known' : 'Drug name and reaction'}
              className="input-field flex-1"
            />
            {form.allergies.length > 1 && (
              <button type="button" onClick={() => removeRow('allergies', i)}
                className="p-2.5 rounded-xl text-slate-400 hover:text-red-500 hover:bg-red-50 transition-colors">
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        ))}
        <button type="button" onClick={() => addRow('allergies')}
          className="flex items-center gap-1.5 text-sm text-brand-700 hover:text-brand-800 mt-1">
          <Plus className="w-3.5 h-3.5" /> Add another allergy
        </button>
      </div>

      {/* Medications — required */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <p className="text-sm font-medium text-slate-700">Current medications</p>
          <span className="text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded-full">Required</span>
        </div>
        {form.medications.map((m, i) => (
          <div key={i} className="flex gap-2 mb-2">
            <input
              type="text"
              value={m}
              onChange={e => updateList('medications', i, e.target.value)}
              placeholder={i === 0 ? 'e.g. Metformin 500mg twice daily, or None' : 'Drug name and dose'}
              className="input-field flex-1"
            />
            {form.medications.length > 1 && (
              <button type="button" onClick={() => removeRow('medications', i)}
                className="p-2.5 rounded-xl text-slate-400 hover:text-red-500 hover:bg-red-50 transition-colors">
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        ))}
        <button type="button" onClick={() => addRow('medications')}
          className="flex items-center gap-1.5 text-sm text-brand-700 hover:text-brand-800 mt-1">
          <Plus className="w-3.5 h-3.5" /> Add another medication
        </button>
      </div>

      {/* Past illnesses */}
      <div>
        <p className="text-sm font-medium text-slate-700 mb-2">Past illnesses</p>
        <div className="flex flex-wrap gap-2">
          {PAST_ILLNESS_OPTIONS.map(ill => (
            <button
              key={ill}
              type="button"
              onClick={() => toggleIllness(ill)}
              className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                form.pastIllnesses.includes(ill)
                  ? 'bg-brand-700 text-white border-brand-700'
                  : 'border-slate-200 text-slate-600 hover:border-brand-300'
              }`}
            >
              {ill}
            </button>
          ))}
        </div>
      </div>

      {/* Family history */}
      <div>
        <p className="text-sm font-medium text-slate-700 mb-2">Family history</p>
        <div className="flex flex-wrap gap-2">
          {PAST_ILLNESS_OPTIONS.map(ill => (
            <button
              key={ill}
              type="button"
              onClick={() => toggleFamily(ill)}
              className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                form.familyHistory.includes(ill)
                  ? 'bg-brand-700 text-white border-brand-700'
                  : 'border-slate-200 text-slate-600 hover:border-brand-300'
              }`}
            >
              {ill}
            </button>
          ))}
        </div>
      </div>

      {/* Adverse reactions (optional) */}
      <div>
        <p className="text-sm font-medium text-slate-700 mb-1">
          Previous adverse drug reactions <span className="text-slate-400 font-normal">(optional)</span>
        </p>
        {form.adverseReactions.map((r, i) => (
          <div key={i} className="flex gap-2 mb-2">
            <input
              type="text"
              value={r}
              onChange={e => updateList('adverseReactions', i, e.target.value)}
              placeholder="Drug and reaction"
              className="input-field flex-1"
            />
            {form.adverseReactions.length > 1 && (
              <button type="button" onClick={() => removeRow('adverseReactions', i)}
                className="p-2.5 rounded-xl text-slate-400 hover:text-red-500 hover:bg-red-50 transition-colors">
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        ))}
        <button type="button" onClick={() => addRow('adverseReactions')}
          className="flex items-center gap-1.5 text-sm text-brand-700 hover:text-brand-800 mt-1">
          <Plus className="w-3.5 h-3.5" /> Add
        </button>
      </div>

      {/* Background — social history (collapsed summary row) */}
      <div className="border-t border-slate-100 pt-4">
        <p className="text-sm font-medium text-slate-700 mb-3">Social history <span className="text-slate-400 font-normal">(optional)</span></p>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-slate-500 mb-1.5">Smoking</p>
            <div className="flex gap-1">
              {['never', 'former', 'current'].map(v => (
                <button key={v} type="button"
                  onClick={() => onChange({ smoking: form.smoking === v ? '' : v })}
                  className={`flex-1 py-2 rounded-xl text-xs border capitalize transition-colors ${
                    form.smoking === v ? 'bg-brand-700 text-white border-brand-700'
                      : 'border-slate-200 text-slate-600 hover:border-brand-300'
                  }`}>
                  {v}
                </button>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1.5">Alcohol</p>
            <div className="flex gap-1">
              {['none', 'occasional', 'regular'].map(v => (
                <button key={v} type="button"
                  onClick={() => onChange({ alcohol: form.alcohol === v ? '' : v })}
                  className={`flex-1 py-2 rounded-xl text-xs border capitalize transition-colors ${
                    form.alcohol === v ? 'bg-brand-700 text-white border-brand-700'
                      : 'border-slate-200 text-slate-600 hover:border-brand-300'
                  }`}>
                  {v}
                </button>
              ))}
            </div>
          </div>
        </div>
        <div className="mt-3">
          <p className="text-xs text-slate-500 mb-1.5">Occupation</p>
          <input type="text" value={form.occupation}
            onChange={e => onChange({ occupation: e.target.value })}
            placeholder="e.g. Farmer, teacher, student"
            className="input-field" />
        </div>
      </div>
    </div>
  )
}
