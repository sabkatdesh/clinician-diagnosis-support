import { useState } from 'react'
import { Plus, X } from 'lucide-react'
import type { IntakeFormData, Complaint } from '@/types/intake'
import { COMPLAINT_GROUPS } from '@/types/intake'

interface Props {
  form: IntakeFormData
  onChange: (patch: Partial<IntakeFormData>) => void
}

const EMPTY_COMPLAINT: Omit<Complaint, 'name'> = {
  duration: '', durationUnit: 'days', onset: '', severity: '', progression: '',
}

export default function Step2Complaints({ form, onChange }: Props) {
  const [customText, setCustomText] = useState('')
  const selected = new Set(form.complaints.map(c => c.name))

  function toggle(name: string) {
    if (selected.has(name)) {
      onChange({ complaints: form.complaints.filter(c => c.name !== name) })
    } else {
      onChange({ complaints: [...form.complaints, { name, ...EMPTY_COMPLAINT }] })
    }
  }

  function addCustom() {
    const trimmed = customText.trim()
    if (!trimmed || selected.has(trimmed)) return
    onChange({ complaints: [...form.complaints, { name: trimmed, ...EMPTY_COMPLAINT }] })
    setCustomText('')
  }

  function updateComplaint(name: string, patch: Partial<Complaint>) {
    onChange({
      complaints: form.complaints.map(c => c.name === name ? { ...c, ...patch } : c),
    })
  }

  return (
    <div className="space-y-6">
      {/* Complaint picker */}
      <div>
        <p className="text-sm font-medium text-slate-700 mb-3">Select all that apply</p>
        {COMPLAINT_GROUPS.map(({ group, items }) => (
          <div key={group} className="mb-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-2">{group}</p>
            <div className="flex flex-wrap gap-2">
              {items.map(item => (
                <button
                  key={item}
                  type="button"
                  onClick={() => toggle(item)}
                  className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                    selected.has(item)
                      ? 'bg-brand-700 text-white border-brand-700'
                      : 'border-slate-200 text-slate-600 hover:border-brand-300 hover:text-brand-700'
                  }`}
                >
                  {item}
                </button>
              ))}
            </div>
          </div>
        ))}

        {/* Custom complaint */}
        <div className="flex gap-2 mt-2">
          <input
            type="text"
            value={customText}
            onChange={e => setCustomText(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addCustom())}
            placeholder="Other complaint…"
            className="input-field flex-1"
          />
          <button
            type="button"
            onClick={addCustom}
            disabled={!customText.trim()}
            className="px-3 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 disabled:opacity-40 transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Per-complaint details */}
      {form.complaints.length > 0 && (
        <div className="space-y-4">
          <p className="text-sm font-medium text-slate-700">Details for each complaint</p>
          {form.complaints.map(c => (
            <ComplaintDetail
              key={c.name}
              complaint={c}
              onUpdate={patch => updateComplaint(c.name, patch)}
              onRemove={() => toggle(c.name)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function ComplaintDetail({
  complaint, onUpdate, onRemove,
}: {
  complaint: Complaint
  onUpdate: (patch: Partial<Complaint>) => void
  onRemove: () => void
}) {
  return (
    <div className="bg-slate-50 rounded-2xl p-4 space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-slate-800">{complaint.name}</p>
        <button type="button" onClick={onRemove} className="text-slate-400 hover:text-red-500 transition-colors">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Duration */}
      <div>
        <p className="text-xs text-slate-500 mb-2">How long?</p>
        <div className="flex gap-2">
          <input
            type="number"
            value={complaint.duration}
            onChange={e => onUpdate({ duration: e.target.value })}
            placeholder="0"
            min={1}
            className="input-field w-20 text-center"
          />
          <div className="flex gap-1 flex-1">
            {(['hours', 'days', 'weeks', 'months'] as const).map(u => (
              <button
                key={u}
                type="button"
                onClick={() => onUpdate({ durationUnit: u })}
                className={`flex-1 py-2 rounded-xl text-xs border transition-colors ${
                  complaint.durationUnit === u
                    ? 'bg-brand-700 text-white border-brand-700'
                    : 'border-slate-200 text-slate-600 hover:border-brand-300'
                }`}
              >
                {u}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Onset */}
      <TapRow
        label="Onset"
        value={complaint.onset}
        options={[{ v: 'sudden', label: 'Sudden' }, { v: 'gradual', label: 'Gradual' }]}
        onChange={v => onUpdate({ onset: v as Complaint['onset'] })}
      />

      {/* Severity */}
      <TapRow
        label="Severity"
        value={complaint.severity}
        options={[
          { v: 'mild', label: 'Mild' },
          { v: 'moderate', label: 'Moderate' },
          { v: 'severe', label: 'Severe' },
          { v: 'critical', label: 'Critical' },
        ]}
        onChange={v => onUpdate({ severity: v as Complaint['severity'] })}
      />

      {/* Progression */}
      <TapRow
        label="Getting"
        value={complaint.progression}
        options={[
          { v: 'better', label: 'Better' },
          { v: 'same', label: 'Same' },
          { v: 'worse', label: 'Worse' },
        ]}
        onChange={v => onUpdate({ progression: v as Complaint['progression'] })}
      />
    </div>
  )
}

function TapRow({
  label, value, options, onChange,
}: {
  label: string
  value: string
  options: { v: string; label: string }[]
  onChange: (v: string) => void
}) {
  return (
    <div>
      <p className="text-xs text-slate-500 mb-2">{label}</p>
      <div className="flex gap-2">
        {options.map(o => (
          <button
            key={o.v}
            type="button"
            onClick={() => onChange(value === o.v ? '' : o.v)}
            className={`flex-1 py-2 rounded-xl text-xs border transition-colors ${
              value === o.v
                ? 'bg-brand-700 text-white border-brand-700'
                : 'border-slate-200 text-slate-600 hover:border-brand-300'
            }`}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  )
}
