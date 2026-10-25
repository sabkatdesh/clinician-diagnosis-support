import type { ExamSystem } from '@/api/pipeline'

export type BoolState = 'yes' | 'no' | null

export interface CVSForm {
  s1_s2_normal: BoolState
  murmur_present: BoolState
  murmur_type: 'systolic' | 'diastolic' | 'continuous' | null
  jvp_elevation: BoolState
  edema_present: BoolState
  edema_grade: '+1' | '+2' | '+3' | '+4' | null
  pulse_character: 'normal' | 'weak' | 'bounding' | 'irregular' | null
  other: string
}

export interface RSForm {
  chest_movement_symmetric: BoolState
  wheeze_present: BoolState
  wheeze_type: 'expiratory' | 'inspiratory' | 'biphasic' | null
  crackles_present: BoolState
  crackles_type: 'fine' | 'coarse' | null
  accessory_muscle_use: BoolState
  percussion: 'resonant' | 'dull' | 'hyperresonant' | null
  other: string
}

export interface CNSForm {
  consciousness: 'alert' | 'drowsy' | 'lethargic' | 'stuporous' | 'comatose' | null
  oriented: BoolState
  gcs: string
  pupils: 'reactive' | 'sluggish' | 'fixed' | null
  neck_stiffness: BoolState
  kernig: BoolState
  motor_normal: BoolState
  other: string
}

export interface GITForm {
  distension: BoolState
  tenderness: BoolState
  tenderness_site: string
  guarding: BoolState
  hepatomegaly: BoolState
  hepatomegaly_cm: string
  splenomegaly: BoolState
  ascites: BoolState
  bowel_sounds: 'normal' | 'increased' | 'decreased' | 'absent' | null
  other: string
}

export interface GUSForm {
  cva_tenderness: 'none' | 'right' | 'left' | 'bilateral' | null
  suprapubic_tenderness: BoolState
  bladder_distension: BoolState
  other: string
}

export interface MSKForm {
  joints_involved: string
  swelling: BoolState
  erythema_warmth: BoolState
  tenderness: BoolState
  rom_limited: BoolState
  muscle_strength: '5' | '4' | '3' | '2' | '1' | '0' | null
  other: string
}

export interface AllExamFindings {
  CVS: CVSForm
  RS:  RSForm
  CNS: CNSForm
  GIT: GITForm
  GUS: GUSForm
  MSK: MSKForm
}

function b(val: BoolState, yes: string, no: string, unknown = 'Not assessed') {
  if (val === 'yes') return yes
  if (val === 'no')  return no
  return unknown
}

export function composeExamText(findings: AllExamFindings, systems: ExamSystem[]): string {
  const sections: string[] = []

  if (systems.includes('CVS')) {
    const f = findings.CVS
    const lines = [
      `Heart sounds: ${b(f.s1_s2_normal, 'S1 S2 normal', 'S1/S2 abnormal')}`,
      f.murmur_present === 'yes'
        ? `Murmur: Present${f.murmur_type ? ` (${f.murmur_type})` : ''}`
        : f.murmur_present === 'no' ? 'Murmur: Absent' : null,
      f.jvp_elevation != null ? `JVP: ${b(f.jvp_elevation, 'Elevated', 'Not elevated')}` : null,
      f.pulse_character ? `Pulse character: ${f.pulse_character}` : null,
      f.edema_present === 'yes'
        ? `Peripheral oedema: Present${f.edema_grade ? ` (${f.edema_grade})` : ''}`
        : f.edema_present === 'no' ? 'Peripheral oedema: Absent' : null,
      f.other.trim() ? f.other.trim() : null,
    ].filter(Boolean)
    sections.push(`CARDIOVASCULAR SYSTEM:\n${lines.map(l => `- ${l}`).join('\n')}`)
  }

  if (systems.includes('RS')) {
    const f = findings.RS
    const lines = [
      f.chest_movement_symmetric != null
        ? `Chest movement: ${b(f.chest_movement_symmetric, 'Symmetric', 'Asymmetric')}`
        : null,
      f.percussion ? `Percussion: ${f.percussion}` : null,
      f.wheeze_present === 'yes'
        ? `Wheeze: Present${f.wheeze_type ? ` (${f.wheeze_type})` : ''}`
        : f.wheeze_present === 'no' ? 'Wheeze: Absent' : null,
      f.crackles_present === 'yes'
        ? `Crackles: Present${f.crackles_type ? ` (${f.crackles_type})` : ''}`
        : f.crackles_present === 'no' ? 'Crackles: Absent' : null,
      f.accessory_muscle_use != null
        ? `Accessory muscle use: ${b(f.accessory_muscle_use, 'Present', 'Absent')}`
        : null,
      f.other.trim() ? f.other.trim() : null,
    ].filter(Boolean)
    sections.push(`RESPIRATORY SYSTEM:\n${lines.map(l => `- ${l}`).join('\n')}`)
  }

  if (systems.includes('CNS')) {
    const f = findings.CNS
    const lines = [
      f.consciousness ? `Consciousness: ${f.consciousness}` : null,
      f.oriented != null ? `Orientation: ${b(f.oriented, 'Oriented to person, place, time', 'Disoriented')}` : null,
      f.gcs.trim() ? `GCS: ${f.gcs.trim()}` : null,
      f.pupils ? `Pupils: ${f.pupils}` : null,
      f.motor_normal != null ? `Motor power: ${b(f.motor_normal, 'Normal bilaterally', 'Reduced')}` : null,
      f.neck_stiffness != null ? `Neck stiffness: ${b(f.neck_stiffness, 'Present', 'Absent')}` : null,
      f.kernig != null ? `Kernig sign: ${b(f.kernig, 'Positive', 'Negative')}` : null,
      f.other.trim() ? f.other.trim() : null,
    ].filter(Boolean)
    sections.push(`CENTRAL NERVOUS SYSTEM:\n${lines.map(l => `- ${l}`).join('\n')}`)
  }

  if (systems.includes('GIT')) {
    const f = findings.GIT
    const lines = [
      f.distension != null ? `Abdomen: ${b(f.distension, 'Distended', 'Soft and flat')}` : null,
      f.tenderness === 'yes'
        ? `Tenderness: Present${f.tenderness_site.trim() ? ` (${f.tenderness_site.trim()})` : ''}`
        : f.tenderness === 'no' ? 'Tenderness: Absent' : null,
      f.guarding != null ? `Guarding: ${b(f.guarding, 'Present', 'Absent')}` : null,
      f.hepatomegaly === 'yes'
        ? `Hepatomegaly: Present${f.hepatomegaly_cm.trim() ? ` (${f.hepatomegaly_cm.trim()} cm below costal margin)` : ''}`
        : f.hepatomegaly === 'no' ? 'Hepatomegaly: Absent' : null,
      f.splenomegaly != null ? `Splenomegaly: ${b(f.splenomegaly, 'Present', 'Absent')}` : null,
      f.ascites != null ? `Ascites: ${b(f.ascites, 'Present', 'Absent')}` : null,
      f.bowel_sounds ? `Bowel sounds: ${f.bowel_sounds}` : null,
      f.other.trim() ? f.other.trim() : null,
    ].filter(Boolean)
    sections.push(`GASTROINTESTINAL SYSTEM:\n${lines.map(l => `- ${l}`).join('\n')}`)
  }

  if (systems.includes('GUS')) {
    const f = findings.GUS
    const lines = [
      f.cva_tenderness != null
        ? `CVA tenderness: ${f.cva_tenderness === 'none' ? 'Absent' : `Present (${f.cva_tenderness})`}`
        : null,
      f.suprapubic_tenderness != null
        ? `Suprapubic tenderness: ${b(f.suprapubic_tenderness, 'Present', 'Absent')}`
        : null,
      f.bladder_distension != null
        ? `Bladder distension: ${b(f.bladder_distension, 'Present', 'Absent')}`
        : null,
      f.other.trim() ? f.other.trim() : null,
    ].filter(Boolean)
    sections.push(`GENITOURINARY SYSTEM:\n${lines.map(l => `- ${l}`).join('\n')}`)
  }

  if (systems.includes('MSK')) {
    const f = findings.MSK
    const lines = [
      f.joints_involved.trim() ? `Joints examined: ${f.joints_involved.trim()}` : null,
      f.swelling != null ? `Swelling: ${b(f.swelling, 'Present', 'Absent')}` : null,
      f.erythema_warmth != null ? `Erythema/warmth: ${b(f.erythema_warmth, 'Present', 'Absent')}` : null,
      f.tenderness != null ? `Tenderness: ${b(f.tenderness, 'Present', 'Absent')}` : null,
      f.rom_limited != null ? `Range of motion: ${b(f.rom_limited, 'Limited', 'Full')}` : null,
      f.muscle_strength ? `Muscle strength: ${f.muscle_strength}/5` : null,
      f.other.trim() ? f.other.trim() : null,
    ].filter(Boolean)
    sections.push(`MUSCULOSKELETAL SYSTEM:\n${lines.map(l => `- ${l}`).join('\n')}`)
  }

  return sections.join('\n\n')
}

export const EMPTY_CVS: CVSForm = {
  s1_s2_normal: null, murmur_present: null, murmur_type: null,
  jvp_elevation: null, edema_present: null, edema_grade: null,
  pulse_character: null, other: '',
}
export const EMPTY_RS: RSForm = {
  chest_movement_symmetric: null, wheeze_present: null, wheeze_type: null,
  crackles_present: null, crackles_type: null, accessory_muscle_use: null,
  percussion: null, other: '',
}
export const EMPTY_CNS: CNSForm = {
  consciousness: null, oriented: null, gcs: '', pupils: null,
  neck_stiffness: null, kernig: null, motor_normal: null, other: '',
}
export const EMPTY_GIT: GITForm = {
  distension: null, tenderness: null, tenderness_site: '', guarding: null,
  hepatomegaly: null, hepatomegaly_cm: '', splenomegaly: null,
  ascites: null, bowel_sounds: null, other: '',
}
export const EMPTY_GUS: GUSForm = {
  cva_tenderness: null, suprapubic_tenderness: null, bladder_distension: null, other: '',
}
export const EMPTY_MSK: MSKForm = {
  joints_involved: '', swelling: null, erythema_warmth: null,
  tenderness: null, rom_limited: null, muscle_strength: null, other: '',
}
export const EMPTY_FINDINGS: AllExamFindings = {
  CVS: EMPTY_CVS, RS: EMPTY_RS, CNS: EMPTY_CNS,
  GIT: EMPTY_GIT, GUS: EMPTY_GUS, MSK: EMPTY_MSK,
}
