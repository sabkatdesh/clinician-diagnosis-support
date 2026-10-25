import os
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from app.llm.clients import LLAMA_4_SCOUT

load_dotenv()


# ----------------------------
# OUTPUT MODELS
# ----------------------------

class ChapterCandidate(BaseModel):
    chapter_number: Optional[int] = Field(None, description="Matched chapter number")
    chapter_title: Optional[str] = Field(None, description="Matched chapter title")
    match_reason: Optional[str] = Field(
        None,
        description="Why this chapter is relevant, such as exact disease title, overview, subtype, disease-dominant chapter"
    )


class DiseaseChapterMatches(BaseModel):
    disease_name: str = Field(..., description="Input disease name")
    matched_chapters: List[ChapterCandidate] = Field(
        default_factory=list,
        description="All relevant chapter candidates for this disease"
    )


class AllDiseaseChapterMatches(BaseModel):
    primary_disease: DiseaseChapterMatches
    alternative_disease_1: DiseaseChapterMatches
    alternative_disease_2: DiseaseChapterMatches


parser = PydanticOutputParser(pydantic_object=AllDiseaseChapterMatches)


# ----------------------------
# YOUR FULL CHAPTER LIST HERE
# ----------------------------
final_chapters = """
===== FINAL CHAPTER LIST =====
1 | Approach to Medicine, the Patient, and the Medical Profession
2 | Bioethics in the Practice of Medicine
3 | Palliative Care
4 | Disparities in Health and Health Care
5 | Global Health
6 | History And Physical Examination Abdomen
7 | Approach To The Patient With Abnormal Vital Signs
8 | Statistical Interpretation Of Data For Clinical Decision Making
9 | Measuring Health And Health Care
10 | Quality, Safety, And Value
11 | Population Health Population Health Kirsten Bibbins-Domingo
12 | The Preventive Health Visit
13 | Diet and Nutrition
14 | Physical Activity
15 | Immunization
16 | Principles of Occupational and Environmental Medicine
17 | Effects of Climate Change on Health
18 | Radiation Injury
19 | Bioterrorism
20 | Chronic Poisoning: Trace Metals and Others
21 | Adolescent Medicine
22 | Epidemiology of Aging
23 | Geriatric Assessment (
24 | Common Clinical Sequelae of Aging
25 | Principles of Drug Therapy
26 | Pain
27 | Biology of Addiction
28 | Immunomodulatory Drugs
29 | Biologic Agents And Signaling Inhibitors
30 | Complementary And Integrative Medicine
31 | Principles of Genetics
32 | Clinical Genomics-Genome Structure and Variation
33 | Applications of Molecular Technologies to Clinical Medicine
34 | Regenerative Medicine, Cell Therapy, And Gene Therapy
35 | The Innate and Adaptive Immune Systems
36 | Tissue Injury And Repair
37 | Complement System in Disease
38 | Transplantation Immunology
39 | Approach to the Patient with Possible Cardiovascular Disease
40 | Epidemiology of Cardiovascular Disease
41 | Cardiac and Circulatory Function
42 | Electrocardiography
43 | Echocardiography
44 | Noninvasive Cardiac Imaging
45 | Heart Failure: Epidemiology, Pathobiology, and Diagnosis
46 | Heart Failure: Treatment and Prognosis
47 | Diseases of the Myocardium and Endocardium
48 | Principles Of Electrophysiology
49 | Approach to the Patient with Suspected Arrhythmia
50 | Cardiac Arrest and Life-Threatening Arrhythmias
51 | Bradycardias and Conduction System Delays
52 | Supraventricular Ectopy And Tachyarrhythmias
53 | Ventricular Arrhythmias
54 | Electrophysiologic Procedures and Surgery
55 | Congenital Heart Disease in Adults
56 | Angina Pectoris and Chronic Ischemic Heart Disease
57 | Acute Coronary Syndrome
58 | ST-Elevation Acute Myocardial Infarction
59 | Interventional Diagnosis And Treatment Of Coronary Artery Disease
60 | Valvular Heart Disease
61 | Infective Endocarditis
62 | Pericardial Diseases
63 | Diseases of the Aorta
64 | Arterial Hypertension
65 | Atherosclerotic Peripheral Arterial Disease
66 | Other Peripheral Arterial Diseases
67 | Thrombotic Disorders
68 | Venous Thrombosis And Embolism
69 | Pulmonary Hypertension
70 | Antithrombotic and Antiplatelet Therapy
71 | Approach to the Patient with Respiratory Disease
72 | Imaging in Pulmonary Disease
73 | Respiratory Testing and Function
74 | Disorders of Ventilatory Control
75 | Asthma
76 | Chronic Obstructive Pulmonary Disease
77 | Cystic Fibrosis
78 | Bronchiectasis, Atelectasis, and Cavitary or Cystic Lung Diseases
79 | Alveolar Filling Disorders
80 | Interstitial Lung Disease
81 | Occupational Lung Disease
82 | Physical and Chemical Injuries of the Lung
83 | Sarcoidosis
84 | Acute Bronchitis and Tracheitis
85 | Overview of Pneumonia
86 | Diseases of the Diaphragm, Chest Wall, Pleura, and Mediastinum
87 | Interventional and Surgical Approaches to Lung Disease
88 | Approach to the Patient in a Critical Care Setting
89 | Respiratory Monitoring in Critical Care
90 | Acute Respiratory Failure
91 | Mechanical Ventilation
92 | Approach to the Patient with Shock
93 | Cardiogenic Shock
94 | Shock Syndromes Related to Sepsis
95 | Disorders Due to Heat and Cold
96 | Acute Poisoning
97 | Medical Aspects of Trauma and Burns
98 | Envenomation, Bites, And Stings
99 | Rhabdomyolysis
100 | Approach to the Patient with Renal Disease
101 | Structure and Function of the Kidneys
102 | Disorders of Sodium and Water
103 | Potassium Disorders
104 | Acid-Base Disorders
105 | Disorders of Magnesium and Phosphorus
106 | Acute Kidney Injury
107 | Glomerular Disorders and Nephrotic Syndromes
108 | Interstitial Nephritis
109 | Diabetes and the Kidney
110 | Vascular Disorders of the Kidney
111 | Nephrolithiasis
112 | Cystic Kidney Diseases
113 | Developmental Renal/Urinary Abnormalities
114 | Benign Prostatic Hyperplasia and Prostatitis
115 | Urinary Incontinence
116 | Chronic Kidney Disease
117 | Treatment of Irreversible Renal Failure
118 | Approach to the Patient with Gastrointestinal Disease
119 | Diagnostic Imaging Procedures in Gastroenterology
120 | Gastrointestinal Endoscopy
121 | Gastrointestinal Hemorrhage
122 | Disorders Of Gastrointestinal Motility
123 | Irritable Bowel and Functional Upper Gastrointestinal Syndromes
124 | Diseases of the Esophagus
125 | Acid Peptic Disease
126 | Approach to the Patient with Diarrhea and Malabsorption
127 | Inflammatory Bowel Disease
128 | Inflammatory And Anatomic Diseases Of The Intestine
129 | Vascular Diseases of the Gastrointestinal Tract
130 | Pancreatitis
131 | Diseases of the Rectum and Anus
132 | Approach to the Patient with Liver Disease
133 | Approach To The Patient With Jaundice Or Abnormal Liver Tests
134 | Acute Viral Hepatitis
135 | Chronic Viral And Autoimmune Hepatitis
136 | Drug-Induced Liver Injury
137 | Bacterial, Parasitic, Fungal, and Granulomatous Liver Diseases
138 | Alcoholic and Nonalcoholic Steatohepatitis
139 | Cirrhosis and Its Sequelae
140 | Liver Failure and Transplantation
141 | Diseases of the Gallbladder and Bile Ducts
142 | Hematopoiesis and Hematopoietic Growth Factors
143 | The Peripheral Blood Smear
144 | Approach To The Anemias
145 | Microcytic and Hypochromic Anemias
146 | Autoimmune And Intravascular Hemolytic Anemias
147 | Hemolytic Anemias: Red Blood Cell Membrane and Metabolic Defects
148 | The Thalassemias
149 | Sickle Cell Disease And Other Hemoglobinopathies
150 | Megaloblastic Anemias
151 | Aplastic Anemia and Related Bone Marrow Failure States
152 | Polycythemia Vera, Essential Thrombocythemia
153 | Leukocytosis and Leukopenia
154 | Approach to the Patient with Lymphadenopathy or Splenomegaly
155 | Histiocytoses
156 | Eosinophilic Syndromes
157 | Approach to the Patient with Bleeding or Thrombosis
158 | Thrombocytopenia
159 | Von Willebrand Disease and Hemorrhagic Abnormalities
160 | Coagulation Factor Deficiencies
161 | Disseminated Intravascular Coagulation And Bleeding In Liver Failure
162 | Transfusion Medicine
163 | Hematopoietic Cell Transplantation
164 | Approach to the Patient with Cancer
165 | Epidemiology of Cancer
166 | Cancer Biology and Genetics
167 | Myelodysplastic Syndromes
168 | The Acute Leukemias
169 | Chronic Lymphocytic Leukemia
170 | Chronic
171 | Non-Hodgkin Lymphomas
172 | Hodgkin Lymphoma
173 | Plasma Cell Disorders
174 | Amyloidosis
175 | Tumors of the Central Nervous System
176 | Head and Neck Cancer
177 | Lung Cancer and Other Pulmonary Neoplasms
178 | Neoplasms of the Esophagus and Stomach
179 | Neoplasms of the Small and Large Intestine
180 | Pancreatic Cancer
181 | Liver And Biliary Tract Tumors
182 | Tumors of the Kidney, Bladder, Ureters, and Renal Pelvis
183 | Breast Cancer and Benign Breast Disorders
184 | Gynecologic Cancers
185 | Testicular Cancer Uterine Fibroids
186 | Prostate Cancer
187 | Malignant Bone Tumors, Sarcomas, and Other Soft Tissue Neoplasms
188 | Melanoma and Nonmelanoma Skin Cancers
189 | Approach to Inborn Errors of Metabolism
190 | Disorders of Lipid Metabolism
191 | Glycogen Storage Diseases
192 | Lysosomal Storage Diseases
193 | Homocystinuria and Hyperhomocysteinemia
194 | The Porphyrias
195 | Wilson Disease
196 | Iron Overload (Hemochromatosis)
197 | Severe Malnutrition
198 | Malnutrition
199 | Vitamins, Trace Minerals, and Other Micronutrients
200 | Eating Disorders
201 | Obesity
202 | Approach to the Patient with Endocrine Disease
203 | Principles of Endocrinology
204 | Neuroendocrinology and the Neuroendocrine System
205 | Anterior Pituitary
206 | Posterior Pituitary
207 | Thyroid
208 | Adrenal Cortex
209 | Adrenal Medulla, Catecholamines, and Pheochromocytoma
210 | Diabetes Mellitus
211 | Hypoglycemia
212 | Polyglandular Disorders
213 | Neuroendocrine Neoplasms
214 | Sexual Development
215 | Transgender Medicine
216 | The Testis and Male Hypogonadism, Infertility, and Sexual Dysfunction
217 | Ovaries and Pubertal Development
218 | Reproductive Endocrinology and Infertility
219 | Approach to Women's Health
220 | Contraception
221 | Medical Issues in Pregnancy
222 | Menopause Diagnosis
223 | Intimate Partner Violence General References
224 | Approach to the Patient with Metabolic Bone Disease
225 | Osteoporosis
226 | Osteomalacia And Rickets A13
227 | The Parathyroid Glands, Hypercalcemia, and Hypocalcemia
228 | Paget Disease of Bone
229 | Osteonecrosis, Osteosclerosis/ Hyperostosis
230 | Approach to the Patient with Allergic or Immunologic Disease
231 | Primary Immunodeficiency Diseases
232 | Urticaria And Angioedema Bradykinin-Mediated Hereditary Angioedema And Related
233 | Anaphylaxis
234 | Drug Allergy
235 | Mastocytosis
236 | Approach to the Patient with Rheumatic Disease
237 | Laboratory Testing in the Rheumatic Diseases
238 | Imaging Studies in the Rheumatic Diseases
239 | Inherited Diseases of Connective Tissue
240 | The Systemic Autoinflammatory Diseases
241 | Osteoarthritis Cd2Bp1
242 | Bursitis, Tendinopathy, Other Periarticular Disorders
243 | Rheumatoid Arthritis
244 | Spondyloarthritis
245 | Systemic Lupus Erythematosus
246 | Systemic Sclerosis (Scleroderma)
247 | Sjögren Syndrome
248 | Inflammatory Myopathies
249 | The Systemic Vasculitides
250 | Giant Cell Arteritis and Polymyalgia Rheumatica
251 | Infections of Bursae, Joints, and Bones
252 | Crystal Deposition Diseases
253 | Fibromyalgia
254 | Systemic Diseases in Which Arthritis Is a Feature
255 | Surgical Treatment of Joint Diseases
256 | Introduction To Microbial Disease
257 | The Human Microbiome
258 | Principles of Anti-Infective Therapy
259 | Approach To Fever Or Suspected Infection In The Normal Host
260 | Suspected Infection in the Immunocompromised Host
261 | Prevention and Control of Health Care-Associated Infections
262 | Approach to the Patient with Suspected Enteric Infection
263 | Approach to the Patient with Urinary Tract Infection
264 | Approach to the Patient with a Sexually Transmitted Infection
265 | Approach to the Patient Before and After Travel
266 | Antibacterial Chemotherapy
267 | Staphylococcal Infections
268 | Streptococcus Pneumoniae Pulmonary Infections
269 | Nonpneumococcal Streptococcal Infections and Rheumatic Fever
270 | Enterococcal Infections
271 | Clostridial And Clostridioides Infections
272 | Gram-Positive Rod Infections
273 | Diseases Caused By Non-Spore-Forming Anaerobic Bacteria
274 | Neisseria Meningitidis Infections Bacteria Penicillin
275 | Neisseria Gonorrhoeae Infections
276 | Chancroid Diagnosis
277 | Haemophilus And Moraxella Infections
278 | Cholera And Other Vibrio Infections
279 | Campylobacter Infections
280 | Escherichia Coli Enteric Infections
281 | Enterobacterales: Non-Enteric Infections and Multidrug Resistance
282 | Pseudomonas And Burkholderia Infections
283 | Diseases Caused By Acinetobacter And Stenotrophomonas Species Species
284 | Salmonella Infections (Including Enteric Fever) Prognosis
285 | Shigellosis
286 | Brucellosis
287 | Tularemia And Other Francisella Infections Prevention
288 | Plague And Other Yersinia Infections Prevention
289 | Whooping Cough And Other Bordetella Infections
290 | Legionella Infections Prevention
291 | Bartonella Infections
292 | Granuloma Inguinale (Donovanosis)
293 | Mycoplasma Infections Prevention
294 | Diseases Caused by Chlamydiae
295 | Syphilis and Nonsyphilitic Treponematoses
296 | Lyme Disease
297 | Relapsing Fever And Other Borrelia Infections
298 | Leptospirosis
299 | Tuberculosis
300 | The Nontuberculous Mycobacteria
301 | Leprosy (Hansen Disease)
302 | Rickettsial Infections
303 | Zoonoses
304 | Actinomycosis
305 | Whipple Disease
306 | Nocardiosis
307 | Systemic Antifungal Agents
308 | Endemic Mycoses
309 | Cryptococcosis Clinical Manifestations
310 | Candidiasis
311 | Aspergillosis
312 | Mucormycosis
313 | Pneumocystis Pneumonia
314 | Mycetoma and Dematiaceous Fungal Infections
315 | Antiparasitic Therapy
316 | Malaria
317 | African Sleeping Sickness
318 | Chagas Disease
319 | Leishmaniasis
320 | Toxoplasmosis
321 | Cryptosporidiosis
322 | Giardiasis
323 | Amebiasis
324 | Babesiosis and Other Protozoan Diseases
325 | Cestodes
326 | Trematode Infections
327 | Nematode Infections
328 | Antiviral Therapy (Non-HIV)
329 | The Common Cold
330 | Respiratory Syncytial Virus and Human Metapneumovirus
331 | Parainfluenza Viral Disease
332 | Influenza
333 | Adenovirus Diseases
334 | Pre-2019 Coronaviruses
335 | Covid-19
336 | Covid-19
337 | Covid-19
338 | Measles
339 | Rubella (German Measles)
340 | Mumps Prevention
341 | Polyomaviruses
342 | Parvovirus A B
343 | Smallpox, Monkeypox, and Other Poxvirus Infections
344 | Papillomavirus
345 | Herpes Simplex Virus Infections
346 | Varicella-Zoster Virus (Chickenpox, Shingles)
347 | Cytomegalovirus
348 | Epstein-Barr Virus Infection
349 | Enteroviruses
350 | Rotaviruses, Noroviruses, and Other Gastrointestinal Viruses
351 | Viral Hemorrhagic Fevers
352 | Arboviruses Causing Fever, Rash, and Neurologic Syndromes
353 | Acquired Immunodeficiency Syndrome Keywords
354 | Pathobiology of Human Immunodeficiency Viruses
355 | Acute Clinical Manifestations and Diagnosis of HIV
356 | Prevention of Human Immunodeficiency Virus Infection
357 | Antiretroviral Treatment of Human Immunodeficiency Virus Infection
358 | Microbial Complications of HIV/AIDS
359 | Systemic Manifestations of HIV/AIDS
360 | Retroviruses Other Than Human Immunodeficiency Virus
361 | Delirium and Changes in Mental Status
362 | Psychiatric Disorders in Medical Practice
363 | Nicotine And Tobacco A12
364 | Alcohol Use Disorders
365 | Drug Use Disorders
366 | Approach to the Patient with Neurologic Disease
367 | Headaches and Other Head Pain
368 | Traumatic Brain Injury and Spinal Cord Injury
370 | Regional Cerebral Dysfunction
371 | Cognitive Impairment and Dementia
372 | The Epilepsies
373 | Coma, Disorders of Consciousness, and Brain Death
374 | Sleep Disorders
375 | Approach to Cerebrovascular Diseases
376 | Ischemic Cerebrovascular Disease
377 | Hemorrhagic Cerebrovascular Disease
378 | Parkinsonism
379 | Other Movement Disorders
380 | Multiple Sclerosis and Demyelinating Conditions
381 | Meningitis: Bacterial, Viral, and Other
382 | Brain Abscess and Parameningeal Infections
383 | Encephalitis
384 | Nutritional and Alcohol-Related Neurologic Disorders
385 | Developmental and Neurocutaneous Disorders
386 | Autonomic Disorders
387 | Amyotrophic Lateral Sclerosis and Other Motor Neuron Diseases
388 | Peripheral Neuropathies
389 | Muscle Diseases
390 | Disorders of Neuromuscular Transmission
391 | Diseases of the Visual System
392 | Neuro-Ophthalmology
393 | Diseases of the Mouth and Salivary Glands
394 | Approach to the Patient with Nose, Sinus, and Ear Disorders
395 | Smell and Taste
396 | Hearing and Equilibrium
397 | Throat Disorders
398 | Principles of Medical Consultation
399 | Preoperative Evaluation
400 | Overview of Anesthesia
401 | Postoperative Care and Complications
402 | Medical Care of Patients with Psychiatric Diseases
403 | Approach to Skin Diseases
404 | Principles of Therapy of Skin Diseases
405 | Eczemas, Photodermatoses, Papulosquamous Diseases
406 | Macular, Papular, Purpuric, Vesiculobullous, and Pustular Diseases
407 | Urticaria, Drug Hypersensitivity Rashes
408 | Infections, Pigmentation Disorders, Regional Dermatology
409 | Diseases of Hair and Nails
"""


# ----------------------------
# PROMPT
# ----------------------------

template_to_find_the_chapters = PromptTemplate(
    template="""
You will look into the chapter index and return ALL relevant chapter candidates for each disease.

Diseases:
- Primary disease: {primary_disease}
- Alternative disease 1: {alternative_disease_1}
- Alternative disease 2: {alternative_disease_2}

Chapter index:
{final_chapters}

RULES:
- Return ALL relevant disease-related chapter candidates for each disease.
- Include:
  1. exact disease chapter titles
  2. "Overview of <disease>" chapters
  3. disease-dominant subtype or organism-specific chapters if clearly related
  4. chapters where the disease is clearly the main focus
- Do NOT include broad generic chapters like:
  - Approach to...
  - Imaging...
  - Testing...
  - Monitoring...
  - Principles of...
- If no relevant chapter exists for a disease, return an empty list for that disease.
- Do not explain outside the JSON.
- Output must strictly follow the required schema.

{format_instructions}
""",
    input_variables=[
        "final_chapters",
        "primary_disease",
        "alternative_disease_1",
        "alternative_disease_2",
    ],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)


result_chain = template_to_find_the_chapters | LLAMA_4_SCOUT | parser

def get_chapter_matches(primary_disease, alternative_disease_1, alternative_disease_2):
    result = result_chain.invoke({
        "final_chapters": final_chapters,
        "primary_disease": primary_disease,
        "alternative_disease_1": alternative_disease_1,
        "alternative_disease_2": alternative_disease_2,
    })

    return {
        "primary_disease": [
            {
                "chapter_number": ch.chapter_number,
                "chapter_title": ch.chapter_title,
            }
            for ch in result.primary_disease.matched_chapters
        ],
        "alternative_disease_1": [
            {
                "chapter_number": ch.chapter_number,
                "chapter_title": ch.chapter_title,
            }
            for ch in result.alternative_disease_1.matched_chapters
        ],
        "alternative_disease_2": [
            {
                "chapter_number": ch.chapter_number,
                "chapter_title": ch.chapter_title,
            }
            for ch in result.alternative_disease_2.matched_chapters
        ],
    }
