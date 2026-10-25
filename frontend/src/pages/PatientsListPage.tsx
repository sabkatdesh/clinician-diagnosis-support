import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AlertCircle, User, Search, ChevronRight, Trash2 } from 'lucide-react'
import { patientsApi, type Patient } from '@/api/sessions'

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.floor(diff / 60000)
  const h = Math.floor(m / 60)
  const d = Math.floor(h / 24)
  if (d > 30) return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
  if (d > 0) return `${d}d ago`
  if (h > 0) return `${h}h ago`
  if (m > 0) return `${m}m ago`
  return 'just now'
}

function PatientListSkeleton() {
  return (
    <div className="bg-white border border-slate-100 rounded-2xl overflow-hidden animate-pulse">
      {[1, 2, 3, 4].map(i => (
        <div key={i} className="flex items-center gap-3 px-4 py-3.5 border-b border-slate-50 last:border-0">
          <div className="w-9 h-9 rounded-full bg-slate-100 flex-shrink-0" />
          <div className="flex-1 space-y-1.5">
            <div className="h-3.5 bg-slate-100 rounded-full w-32" />
            <div className="h-3 bg-slate-100 rounded-full w-48" />
          </div>
          <div className="h-3 bg-slate-100 rounded-full w-10" />
        </div>
      ))}
    </div>
  )
}

function PatientRow({
  patient,
  onClick,
  onDelete,
  deleting,
}: {
  patient: Patient
  onClick: () => void
  onDelete: () => void
  deleting: boolean
}) {
  const [confirmDelete, setConfirmDelete] = useState(false)

  return (
    <div className="flex items-center gap-3 px-4 py-3.5 border-b border-slate-50 last:border-0 group hover:bg-slate-50 transition-colors">
      <button
        type="button"
        onClick={onClick}
        className="flex items-center gap-3 flex-1 min-w-0 text-left"
      >
        <div className="w-9 h-9 rounded-full bg-brand-50 flex items-center justify-center flex-shrink-0">
          <User className="w-4.5 h-4.5 text-brand-600" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-800 truncate">
            {patient.name || 'Anonymous patient'}
          </p>
          <p className="text-xs text-slate-400 mt-0.5">
            {[patient.age ? `${patient.age}y` : null, patient.gender].filter(Boolean).join(' · ')}
            {patient.chief_complain_raw && (
              <span className="text-slate-300"> · </span>
            )}
            {patient.chief_complain_raw && (
              <span className="text-slate-400 truncate">
                {patient.chief_complain_raw.slice(0, 60)}{patient.chief_complain_raw.length > 60 ? '…' : ''}
              </span>
            )}
          </p>
        </div>
        <div className="flex-shrink-0 flex items-center gap-2 ml-1">
          <span className="text-xs text-slate-300">{timeAgo(patient.created_at)}</span>
          <ChevronRight className="w-4 h-4 text-slate-300" />
        </div>
      </button>

      {/* Delete control */}
      <div className="flex-shrink-0 flex items-center gap-1 ml-1">
        {confirmDelete ? (
          <>
            <button
              onClick={() => { onDelete(); setConfirmDelete(false) }}
              disabled={deleting}
              className="text-xs text-white bg-red-500 hover:bg-red-600 px-2 py-1 rounded-lg transition-colors"
            >
              {deleting ? '…' : 'Delete'}
            </button>
            <button
              onClick={() => setConfirmDelete(false)}
              className="text-xs text-slate-500 hover:text-slate-700 px-2 py-1 rounded-lg border border-slate-200 transition-colors"
            >
              Cancel
            </button>
          </>
        ) : (
          <button
            onClick={() => setConfirmDelete(true)}
            className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-red-50 text-slate-300 hover:text-red-400 transition-all"
            title="Delete patient"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  )
}

export default function PatientsListPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [query, setQuery] = useState('')

  const { data: patients, isLoading, isError } = useQuery({
    queryKey: ['patients'],
    queryFn: patientsApi.list,
    staleTime: 30_000,
  })

  const deleteMutation = useMutation({
    mutationFn: (patientId: string) => patientsApi.delete(patientId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] })
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
    },
  })

  const filtered = (patients ?? []).filter(p => {
    if (!query.trim()) return true
    const q = query.toLowerCase()
    return (
      (p.name ?? '').toLowerCase().includes(q) ||
      (p.chief_complain_raw ?? '').toLowerCase().includes(q) ||
      (p.gender ?? '').toLowerCase().includes(q)
    )
  })

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      <div className="mb-5">
        <h1 className="text-xl font-semibold text-slate-800">Patients</h1>
        {patients && (
          <p className="text-sm text-slate-400 mt-0.5">
            {patients.length} {patients.length === 1 ? 'patient' : 'patients'} on record
          </p>
        )}
      </div>

      {/* Search */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search by name or complaint…"
          className="input-field pl-9"
        />
      </div>

      {/* List */}
      {isLoading ? (
        <PatientListSkeleton />
      ) : isError ? (
        <div className="text-center py-12">
          <AlertCircle className="w-8 h-8 text-red-300 mx-auto mb-2" />
          <p className="text-sm text-slate-500">Could not load patients.</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12">
          <User className="w-8 h-8 text-slate-200 mx-auto mb-2" />
          <p className="text-sm text-slate-400">
            {query ? 'No patients match your search.' : 'No patients yet.'}
          </p>
        </div>
      ) : (
        <div className="bg-white border border-slate-100 rounded-2xl overflow-hidden">
          {filtered.map(patient => (
            <PatientRow
              key={patient.id}
              patient={patient}
              onClick={() => navigate(`/patients/${patient.id}`)}
              onDelete={() => deleteMutation.mutate(patient.id)}
              deleting={deleteMutation.isPending && deleteMutation.variables === patient.id}
            />
          ))}
        </div>
      )}
    </div>
  )
}
