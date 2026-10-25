import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Loader2, AlertCircle, User, ChevronDown, ChevronUp,
  CheckCircle, XCircle, FlaskConical, AlertTriangle, ArrowLeft, Trash2,
} from 'lucide-react'
import { patientsApi, type FinalReport } from '@/api/sessions'
import { VerdictBadge } from '@/components/pipeline/hitl/HITL4Confirmation'

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.floor(diff / 60000)
  const h = Math.floor(m / 60)
  const d = Math.floor(h / 24)
  if (d > 30) return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
  if (d > 0) return `${d}d ago`
  if (h > 0) return `${h}h ago`
  return `${m}m ago`
}

// ─── Report card (expandable timeline item) ───────────────────────────────────

function ReportCard({ report }: { report: FinalReport }) {
  const [open, setOpen] = useState(false)
  const pct = Math.round(report.final_diagnosis_confidence * 100)

  return (
    <div className="bg-white border border-slate-100 rounded-2xl overflow-hidden">
      {/* Summary row */}
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-start gap-3 px-4 py-4 text-left hover:bg-slate-50/50 transition-colors"
      >
        <div className="w-2 h-2 rounded-full mt-1.5 flex-shrink-0 bg-brand-400" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <VerdictBadge verdict={report.verdict} />
            {report.doctor_confirmed
              ? <span className="text-xs text-emerald-600 flex items-center gap-1"><CheckCircle className="w-3 h-3" />Confirmed</span>
              : <span className="text-xs text-amber-600 flex items-center gap-1"><AlertCircle className="w-3 h-3" />Unconfirmed</span>
            }
          </div>
          <p className="text-sm font-semibold text-slate-800">{report.final_diagnosis}</p>
          <p className="text-xs text-slate-400 mt-0.5">
            {formatDate(report.created_at)}
            {report.total_crag_attempts > 1 && ` · ${report.total_crag_attempts} CRAG attempts`}
          </p>
        </div>
        <div className="flex-shrink-0 flex flex-col items-end gap-1 ml-2">
          <span className={`text-xs font-semibold ${
            pct >= 80 ? 'text-emerald-600' : pct >= 60 ? 'text-amber-600' : 'text-red-500'
          }`}>{pct}%</span>
          {open ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
        </div>
      </button>

      {/* Expanded detail */}
      {open && (
        <div className="border-t border-slate-100 px-4 py-4 space-y-4">
          {/* Corrected diagnosis */}
          {report.corrected_diagnosis && (
            <div className="flex items-start gap-2">
              <XCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-xs font-medium text-red-600">Diagnosis corrected</p>
                <p className="text-sm text-slate-700">{report.corrected_diagnosis}</p>
              </div>
            </div>
          )}

          {/* Clinical reasoning */}
          {report.clinical_reasoning_summary && (
            <p className="text-sm text-slate-600">{report.clinical_reasoning_summary}</p>
          )}

          {/* Evidence */}
          {((report.supporting_evidence ?? []).length > 0 || (report.against_evidence ?? []).length > 0) && (
            <div className="grid grid-cols-2 gap-2">
              {(report.supporting_evidence ?? []).length > 0 && (
                <div className="bg-emerald-50 rounded-xl p-3">
                  <p className="text-xs font-semibold text-emerald-700 mb-1">Supporting</p>
                  {report.supporting_evidence!.map((e, i) => (
                    <p key={i} className="text-xs text-emerald-700">✓ {e}</p>
                  ))}
                </div>
              )}
              {(report.against_evidence ?? []).length > 0 && (
                <div className="bg-amber-50 rounded-xl p-3">
                  <p className="text-xs font-semibold text-amber-700 mb-1">Against</p>
                  {report.against_evidence!.map((e, i) => (
                    <p key={i} className="text-xs text-amber-700">✗ {e}</p>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Red flags */}
          {(report.red_flags ?? []).length > 0 && (
            <div className="bg-red-50 border border-red-100 rounded-xl px-3 py-2.5">
              <div className="flex items-center gap-1.5 mb-1">
                <AlertTriangle className="w-3.5 h-3.5 text-red-500" />
                <p className="text-xs font-semibold text-red-700">Red flags</p>
              </div>
              {report.red_flags!.map((f, i) => (
                <p key={i} className="text-xs text-red-600">· {f}</p>
              ))}
            </div>
          )}

          {/* Required tests */}
          {(report.required_tests ?? []).length > 0 && (
            <div className="border border-slate-100 rounded-xl overflow-hidden">
              <div className="flex items-center gap-1.5 px-3 py-2 bg-slate-50 border-b border-slate-100">
                <FlaskConical className="w-3.5 h-3.5 text-slate-400" />
                <p className="text-xs font-semibold text-slate-600">Required investigations</p>
              </div>
              {report.required_tests!.map((t, i) => (
                <div key={i} className="px-3 py-2.5 border-b border-slate-50 last:border-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm text-slate-700 flex-1">{t.test_name}</p>
                    <span className={`text-xs px-2 py-0.5 rounded-full capitalize ${
                      t.priority === 'urgent' ? 'bg-red-50 text-red-600'
                        : t.priority === 'routine' ? 'bg-sky-50 text-sky-600'
                        : 'bg-slate-50 text-slate-500'
                    }`}>{t.priority}</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">{t.reason}</p>
                </div>
              ))}
            </div>
          )}

          {/* Doctor note */}
          {report.doctor_final_note && (
            <div className="border-l-2 border-brand-200 pl-3">
              <p className="text-xs text-slate-500 mb-0.5">Doctor's note</p>
              <p className="text-sm text-slate-600 italic">"{report.doctor_final_note}"</p>
            </div>
          )}

          {/* Session link */}
          {report.sessions?.thread_id && (
            <Link to={`/session/${report.sessions.thread_id}`}
              className="text-xs text-brand-700 hover:underline">
              View session →
            </Link>
          )}
        </div>
      )}
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function PatientProfilePage() {
  const { patientId } = useParams<{ patientId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [confirmDelete, setConfirmDelete] = useState(false)

  const patientQ = useQuery({
    queryKey: ['patient', patientId],
    queryFn:  () => patientsApi.get(patientId!),
    enabled:  !!patientId,
    staleTime: 60_000,
  })

  const reportsQ = useQuery({
    queryKey: ['patient-reports', patientId],
    queryFn:  () => patientsApi.reports(patientId!),
    enabled:  !!patientId,
    staleTime: 30_000,
  })

  const deleteMutation = useMutation({
    mutationFn: () => patientsApi.delete(patientId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] })
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
      navigate('/patients')
    },
  })

  if (patientQ.isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 text-brand-600 animate-spin" />
      </div>
    )
  }

  if (patientQ.isError || !patientQ.data) {
    return (
      <div className="max-w-md mx-auto px-4 py-12 text-center">
        <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
        <p className="text-slate-700 font-medium mb-4">Patient not found</p>
        <button onClick={() => navigate('/patients')}
          className="text-sm text-brand-700 underline">
          Back to patients
        </button>
      </div>
    )
  }

  const patient = patientQ.data
  const reports = reportsQ.data ?? []

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      {/* Back */}
      <button onClick={() => navigate(-1)}
        className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 mb-5">
        <ArrowLeft className="w-4 h-4" /> Back
      </button>

      {/* Patient header card */}
      <div className="bg-white border border-slate-100 rounded-2xl p-5 mb-6">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-full bg-brand-50 flex items-center justify-center flex-shrink-0">
            <User className="w-6 h-6 text-brand-600" />
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-lg font-semibold text-slate-800">
              {patient.name || 'Anonymous patient'}
            </h1>
            <p className="text-sm text-slate-500 mt-0.5">
              {[patient.age ? `${patient.age}y` : null, patient.gender].filter(Boolean).join(' · ')}
            </p>
            {patient.chief_complain_raw && (
              <div className="mt-2">
                <p className="text-xs text-slate-400">Original complaint</p>
                <p className="text-xs text-slate-600 mt-0.5 line-clamp-2">
                  {patient.chief_complain_raw.slice(0, 160)}{patient.chief_complain_raw.length > 160 ? '…' : ''}
                </p>
              </div>
            )}
            <p className="text-xs text-slate-400 mt-2">First seen {timeAgo(patient.created_at)}</p>
          </div>

          {/* Delete patient */}
          <div className="flex-shrink-0">
            {confirmDelete ? (
              <div className="flex flex-col items-end gap-1.5">
                <p className="text-xs text-red-600 font-medium">Delete patient?</p>
                <p className="text-xs text-slate-400 text-right">All sessions & reports will be removed.</p>
                <div className="flex gap-1.5 mt-1">
                  <button
                    onClick={() => deleteMutation.mutate()}
                    disabled={deleteMutation.isPending}
                    className="text-xs text-white bg-red-500 hover:bg-red-600 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
                  >
                    {deleteMutation.isPending ? 'Deleting…' : 'Yes, delete'}
                  </button>
                  <button
                    onClick={() => setConfirmDelete(false)}
                    className="text-xs text-slate-500 hover:text-slate-700 px-3 py-1.5 rounded-lg border border-slate-200 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setConfirmDelete(true)}
                className="p-2 rounded-xl hover:bg-red-50 text-slate-300 hover:text-red-400 transition-colors"
                title="Delete patient"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Timeline header */}
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-slate-700">
          Visit history
          {reports.length > 0 && (
            <span className="ml-2 text-xs font-normal text-slate-400">
              · {reports.length} {reports.length === 1 ? 'report' : 'reports'}
            </span>
          )}
        </h2>
      </div>

      {reportsQ.isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="w-6 h-6 text-brand-400 animate-spin" />
        </div>
      ) : reports.length === 0 ? (
        <div className="text-center py-10">
          <FlaskConical className="w-8 h-8 text-slate-200 mx-auto mb-2" />
          <p className="text-sm text-slate-400">No completed reports yet.</p>
          <p className="text-xs text-slate-300 mt-1">
            Reports appear here once a full analysis is confirmed.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {reports.map(report => (
            <ReportCard key={report.id} report={report} />
          ))}
        </div>
      )}
    </div>
  )
}
