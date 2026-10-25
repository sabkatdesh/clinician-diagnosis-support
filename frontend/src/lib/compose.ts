import type { IntakeFormData } from '@/types/intake'

export function composeIntakeText(form: IntakeFormData): string {
  const lines: string[] = []

  // ── Patient identity ───────────────────────────────────────────────────
  const identityParts = [
    form.name || 'Unknown',
    form.age ? `${form.age}y` : null,
    form.gender || null,
  ].filter(Boolean).join(', ')

  const contactParts = [
    form.contact ? `Tel: ${form.contact}` : null,
    form.patientId ? `MRN: ${form.patientId}` : null,
  ].filter(Boolean).join(' | ')

  lines.push(`PATIENT: ${identityParts}${contactParts ? ' | ' + contactParts : ''}`)
  lines.push('')

  // ── Chief complaints ───────────────────────────────────────────────────
  if (form.complaints.length > 0) {
    const complaintSummary = form.complaints
      .map(c => {
        const dur = c.duration && c.durationUnit ? `${c.duration}${c.durationUnit[0]}` : ''
        return dur ? `${c.name} (${dur})` : c.name
      })
      .join(', ')
    lines.push(`CHIEF COMPLAINTS: ${complaintSummary}`)

    form.complaints.forEach(c => {
      const parts = [
        c.severity   ? `Severity: ${c.severity}`       : null,
        c.onset      ? `Onset: ${c.onset}`              : null,
        c.progression? `Progression: ${c.progression}`  : null,
      ].filter(Boolean)
      if (parts.length) {
        lines.push(`  ${c.name}: ${parts.join(' | ')}`)
      }
    })
    lines.push('')
  }

  // ── Vitals ─────────────────────────────────────────────────────────────
  const vitals: string[] = []
  if (form.temperature)    vitals.push(`Temp ${form.temperature}°${form.temperatureUnit}`)
  if (form.bpSystolic && form.bpDiastolic) vitals.push(`BP ${form.bpSystolic}/${form.bpDiastolic} mmHg`)
  if (form.heartRate)      vitals.push(`HR ${form.heartRate}/min`)
  if (form.respiratoryRate)vitals.push(`RR ${form.respiratoryRate}/min`)
  if (form.spo2)           vitals.push(`SpO2 ${form.spo2}%`)
  if (form.weight)         vitals.push(`Wt ${form.weight}kg`)
  if (form.height)         vitals.push(`Ht ${form.height}cm`)
  if (form.bmi)            vitals.push(`BMI ${form.bmi}`)
  if (vitals.length) {
    lines.push(`VITALS: ${vitals.join(' | ')}`)
    lines.push('')
  }

  // ── General examination ────────────────────────────────────────────────
  const genExamLines: string[] = []
  if (form.appearance) genExamLines.push(`Appearance: ${form.appearance}`)

  const signs: Array<[string, string]> = [
    ['Pallor', form.pallor],
    ['Jaundice', form.jaundice],
    ['Cyanosis', form.cyanosis],
    ['Clubbing', form.clubbing],
    ['Koilonychia', form.koilonychia],
    ['Dehydration', form.dehydration],
    ['Bony tenderness', form.bonyTenderness],
    ['Meningeal irritation', form.meningealIrritation],
  ]
  const signsSummary = signs
    .filter(([, v]) => v && v !== 'not checked')
    .map(([k, v]) => `${k}: ${v}`)
    .join(' | ')
  if (signsSummary) genExamLines.push(signsSummary)
  if (form.edema && form.edema !== 'none') genExamLines.push(`Edema: ${form.edema}`)
  if (form.lymphNodes && form.lymphNodes !== 'none') genExamLines.push(`Lymph nodes: ${form.lymphNodes}`)
  if (form.tongue)      genExamLines.push(`Tongue: ${form.tongue}`)
  if (form.throat)      genExamLines.push(`Throat/ENT: ${form.throat}`)

  if (genExamLines.length) {
    lines.push('GENERAL EXAMINATION:')
    genExamLines.forEach(l => lines.push(`  ${l}`))
    lines.push('')
  }

  // ── History & safety ───────────────────────────────────────────────────
  const allergies = form.allergies.filter(Boolean)
  lines.push(`ALLERGIES: ${allergies.length ? allergies.join(', ') : 'None known'}`)

  const meds = form.medications.filter(Boolean)
  lines.push(`MEDICATIONS: ${meds.length ? meds.join(', ') : 'None'}`)

  const pastIll = form.pastIllnesses.filter(Boolean)
  if (pastIll.length) lines.push(`PAST HISTORY: ${pastIll.join(', ')}`)

  const famHist = form.familyHistory.filter(Boolean)
  if (famHist.length) lines.push(`FAMILY HISTORY: ${famHist.join(', ')}`)

  const drugReactions = form.adverseReactions.filter(Boolean)
  if (drugReactions.length) lines.push(`DRUG REACTIONS: ${drugReactions.join(', ')}`)

  // ── Optional background ────────────────────────────────────────────────
  const bg: string[] = []
  if (form.smoking && form.smoking !== 'never') bg.push(`Smoking: ${form.smoking}`)
  if (form.alcohol && form.alcohol !== 'none')  bg.push(`Alcohol: ${form.alcohol}`)
  if (form.occupation) bg.push(`Occupation: ${form.occupation}`)
  if (bg.length) {
    lines.push('')
    lines.push(`SOCIAL HISTORY: ${bg.join(' | ')}`)
  }

  return lines.join('\n')
}

export function calcBMI(weight: string, height: string): string {
  const w = parseFloat(weight)
  const h = parseFloat(height) / 100
  if (!w || !h || h === 0) return ''
  return (w / (h * h)).toFixed(1)
}
