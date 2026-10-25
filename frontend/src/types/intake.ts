export interface Complaint {
  name: string
  duration: string
  durationUnit: 'hours' | 'days' | 'weeks' | 'months'
  onset: 'sudden' | 'gradual' | ''
  severity: 'mild' | 'moderate' | 'severe' | 'critical' | ''
  progression: 'better' | 'same' | 'worse' | ''
}

export type TriState = 'present' | 'absent' | 'not checked'

export interface IntakeFormData {
  // Step 1 — Who
  name: string
  age: string
  gender: 'Male' | 'Female' | 'Other' | ''
  contact: string
  patientId: string

  // Step 2 — Complaints
  complaints: Complaint[]

  // Step 3 — Vitals
  temperature: string
  temperatureUnit: 'C' | 'F'
  bpSystolic: string
  bpDiastolic: string
  heartRate: string
  respiratoryRate: string
  spo2: string
  weight: string
  height: string
  bmi: string

  // Step 4 — General examination
  appearance: 'well' | 'ill-looking' | 'distressed' | ''
  pallor: TriState
  jaundice: TriState
  cyanosis: TriState
  clubbing: TriState
  koilonychia: TriState
  dehydration: TriState
  bonyTenderness: TriState
  meningealIrritation: TriState
  edema: string
  lymphNodes: string
  tongue: string
  throat: string

  // Step 5 — History & safety
  allergies: string[]
  medications: string[]
  pastIllnesses: string[]
  familyHistory: string[]
  adverseReactions: string[]

  // Optional background
  smoking: string
  alcohol: string
  occupation: string
}

export const EMPTY_FORM: IntakeFormData = {
  name: '', age: '', gender: '', contact: '', patientId: '',
  complaints: [],
  temperature: '', temperatureUnit: 'C',
  bpSystolic: '', bpDiastolic: '',
  heartRate: '', respiratoryRate: '', spo2: '',
  weight: '', height: '', bmi: '',
  appearance: '',
  pallor: 'not checked', jaundice: 'not checked', cyanosis: 'not checked',
  clubbing: 'not checked', koilonychia: 'not checked', dehydration: 'not checked',
  bonyTenderness: 'not checked', meningealIrritation: 'not checked',
  edema: '', lymphNodes: '', tongue: '', throat: '',
  allergies: [''], medications: [''],
  pastIllnesses: [], familyHistory: [], adverseReactions: [],
  smoking: '', alcohol: '', occupation: '',
}

// Common complaint groups from the design doc
export const COMPLAINT_GROUPS = [
  {
    group: 'General',
    items: ['Fever', 'Weakness', 'Weight loss', 'Loss of appetite', 'Swelling', 'Fatigue'],
  },
  {
    group: 'Respiratory',
    items: ['Cough', 'Breathlessness', 'Wheeze', 'Chest pain', 'Sore throat', 'Runny nose'],
  },
  {
    group: 'Heart',
    items: ['Palpitations', 'Chest pain', 'Leg swelling', 'Fainting'],
  },
  {
    group: 'Gut',
    items: ['Abdominal pain', 'Vomiting', 'Diarrhoea', 'Constipation', 'Jaundice', 'Blood in stool'],
  },
  {
    group: 'Nervous system',
    items: ['Headache', 'Convulsion', 'Dizziness', 'Altered consciousness', 'Limb weakness'],
  },
  {
    group: 'Urinary',
    items: ['Burning urination', 'Frequent urination', 'Reduced urine', 'Blood in urine'],
  },
  {
    group: 'Bones & joints',
    items: ['Joint pain', 'Joint swelling', 'Back pain'],
  },
  {
    group: 'Skin',
    items: ['Rash', 'Itching'],
  },
]

export const PAST_ILLNESS_OPTIONS = [
  'Diabetes', 'Hypertension', 'Asthma', 'Tuberculosis',
  'Heart disease', 'Kidney disease', 'Liver disease', 'Stroke',
]
