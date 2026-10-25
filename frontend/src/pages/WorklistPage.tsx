import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { ClipboardList, Plus, Clock, CheckCircle, Loader2, AlertCircle, Trash2 } from 'lucide-react'
import { sessionsApi, type Session } from '@/api/sessions'
import { useAuthStore } from '@/stores/authStore'

const HITL_LABELS: Record<string, string> = {
  hitl_1_recommendation_approval: 'Review exam plan',
  hitl_2_exam_input:              'Enter examination findings',
  hitl_3_diagnosis_approval:      'Review diagnosis',
  hitl_3b_crag_missing_data:      'Answer clinical questions',
  hitl_4_crag_confirmation:       'Confirm final report',
}

export default function WorklistPage() {
  const fullName = useAuthStore(s => s.fullName)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: sessions, isLoading, isError, refetch } = useQuery({
    queryKey: ['sessions'],
    queryFn: sessionsApi.list,
    refetchInterval: 15_000,
  })

  const deleteMutation = useMutation({
    mutationFn: (threadId: string) => sessionsApi.delete(threadId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sessions'] }),
  })

  const needsAction = sessions?.filter(s => s.status === 'paused_hitl') ?? []
  const running     = sessions?.filter(s => s.status === 'running' || s.status === 'starting') ?? []
  const completed   = sessions?.filter(s => s.status === 'completed') ?? []
  const failed      = sessions?.filter(s => s.status === 'failed') ?? []

  const greeting = () => {
    const h = new Date().getHours()
    if (h < 12) return 'Good morning'
    if (h < 17) return 'Good afternoon'
    return 'Good evening'
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-800">
            {greeting()}{fullName ? `, Dr. ${fullName.split(' ').slice(-1)[0]}` : ''}
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">Your cases for today</p>
        </div>
        <button
          onClick={() => navigate('/new-patient')}
          className="flex items-center gap-2 bg-brand-700 hover:bg-brand-800 text-white text-sm font-medium px-4 py-2.5 rounded-xl transition-colors"
        >
          <Plus className="w-4 h-4" />
          New patient
        </button>
      </div>

      {isLoading && <WorklistSkeleton />}

      {isError && (
        <div className="bg-red-50 text-red-700 rounded-2xl p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium">Could not load sessions</p>
            <button onClick={() => refetch()} className="text-xs underline mt-0.5">Try again</button>
          </div>
        </div>
      )}

      {!isLoading && !isError && sessions?.length === 0 && (
        <EmptyState onNew={() => navigate('/new-patient')} />
      )}

      {needsAction.length > 0 && (
        <Section title="Needs your action" icon={<AlertCircle className="w-4 h-4 text-amber-500" />}>
          {needsAction.map(s => (
            <SessionCard
              key={s.id}
              session={s}
              onClick={() => navigate(`/session/${s.thread_id}`)}
              onDelete={() => deleteMutation.mutate(s.thread_id)}
              deleting={deleteMutation.isPending && deleteMutation.variables === s.thread_id}
            />
          ))}
        </Section>
      )}

      {running.length > 0 && (
        <Section title="Running now" icon={<Loader2 className="w-4 h-4 text-brand-600 animate-spin" />}>
          {running.map(s => (
            <SessionCard
              key={s.id}
              session={s}
              onClick={() => navigate(`/session/${s.thread_id}`)}
              onDelete={() => deleteMutation.mutate(s.thread_id)}
              deleting={deleteMutation.isPending && deleteMutation.variables === s.thread_id}
            />
          ))}
        </Section>
      )}

      {failed.length > 0 && (
        <Section title="Failed" icon={<AlertCircle className="w-4 h-4 text-red-500" />}>
          {failed.map(s => (
            <SessionCard
              key={s.id}
              session={s}
              onClick={() => navigate(`/session/${s.thread_id}`)}
              onDelete={() => deleteMutation.mutate(s.thread_id)}
              deleting={deleteMutation.isPending && deleteMutation.variables === s.thread_id}
            />
          ))}
        </Section>
      )}

      {completed.length > 0 && (
        <Section title="Completed" icon={<CheckCircle className="w-4 h-4 text-emerald-500" />} collapsible>
          {completed.map(s => (
            <SessionCard
              key={s.id}
              session={s}
              onClick={() => navigate(`/session/${s.thread_id}`)}
              onDelete={() => deleteMutation.mutate(s.thread_id)}
              deleting={deleteMutation.isPending && deleteMutation.variables === s.thread_id}
            />
          ))}
        </Section>
      )}

      <p className="text-center text-xs text-slate-400 mt-10">
        Decision support only. The final judgement is yours.
      </p>
    </div>
  )
}

function Section({
  title, icon, children, collapsible = false,
}: {
  title: string
  icon: React.ReactNode
  children: React.ReactNode
  collapsible?: boolean
}) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 mb-3">
        {icon}
        <h2 className="text-sm font-semibold text-slate-600 uppercase tracking-wide">{title}</h2>
      </div>
      <div className="space-y-3">{children}</div>
    </div>
  )
}

function SessionCard({
  session,
  onClick,
  onDelete,
  deleting,
}: {
  session: Session
  onClick: () => void
  onDelete: () => void
  deleting: boolean
}) {
  const [confirmDelete, setConfirmDelete] = useState(false)
  const actionLabel = session.paused_at ? HITL_LABELS[session.paused_at] : null
  const age = timeAgo(session.created_at)

  const patientName = session.patients?.name || null
  const patientLabel = patientName
    ? patientName
    : session.patient_id
      ? `Patient ${session.patient_id.slice(0, 8)}…`
      : 'New patient'

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirmDelete) {
      onDelete()
      setConfirmDelete(false)
    } else {
      setConfirmDelete(true)
    }
  }

  const handleCancelDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    setConfirmDelete(false)
  }

  return (
    <div
      className="w-full text-left bg-white rounded-2xl border border-slate-100 p-4 hover:border-brand-200 hover:shadow-sm transition-all group"
    >
      <div className="flex items-start justify-between gap-3">
        <button onClick={onClick} className="flex-1 min-w-0 text-left">
          <p className="text-sm font-medium text-slate-800 truncate">{patientLabel}</p>
          {actionLabel && (
            <p className="text-xs text-amber-600 font-medium mt-0.5">{actionLabel}</p>
          )}
        </button>
        <div className="flex items-center gap-2 flex-shrink-0">
          <StatusBadge status={session.status} />
          {confirmDelete ? (
            <div className="flex items-center gap-1" onClick={e => e.stopPropagation()}>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="text-xs text-white bg-red-500 hover:bg-red-600 px-2 py-1 rounded-lg transition-colors"
              >
                {deleting ? '…' : 'Delete'}
              </button>
              <button
                onClick={handleCancelDelete}
                className="text-xs text-slate-500 hover:text-slate-700 px-2 py-1 rounded-lg border border-slate-200 transition-colors"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={handleDelete}
              className="opacity-0 group-hover:opacity-100 p-1 rounded-lg hover:bg-red-50 text-slate-300 hover:text-red-400 transition-all"
              title="Delete session"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
      <button onClick={onClick} className="w-full text-left">
        <div className="flex items-center gap-1.5 mt-2.5">
          <Clock className="w-3 h-3 text-slate-300" />
          <span className="text-xs text-slate-400">{age}</span>
          {session.current_stage && (
            <span className="text-xs text-slate-300 ml-1">· {session.current_stage}</span>
          )}
        </div>
      </button>
    </div>
  )
}

function StatusBadge({ status }: { status: Session['status'] }) {
  const map = {
    starting:    { label: 'Starting',   cls: 'bg-slate-100 text-slate-500' },
    running:     { label: 'Running',    cls: 'bg-brand-50 text-brand-700' },
    paused_hitl: { label: 'Needs you',  cls: 'bg-amber-50 text-amber-700' },
    completed:   { label: 'Complete',   cls: 'bg-emerald-50 text-emerald-700' },
    failed:      { label: 'Failed',     cls: 'bg-red-50 text-red-600' },
  }
  const { label, cls } = map[status]
  return (
    <span className={`text-xs font-medium px-2.5 py-1 rounded-full flex-shrink-0 ${cls}`}>
      {label}
    </span>
  )
}

function EmptyState({ onNew }: { onNew: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <ClipboardList className="w-12 h-12 text-slate-200 mb-4" />
      <h2 className="text-base font-medium text-slate-700 mb-1">No cases yet</h2>
      <p className="text-sm text-slate-400 mb-6">Start by adding your first patient</p>
      <button
        onClick={onNew}
        className="flex items-center gap-2 bg-brand-700 hover:bg-brand-800 text-white text-sm font-medium px-5 py-2.5 rounded-xl transition-colors"
      >
        <Plus className="w-4 h-4" />
        New patient
      </button>
    </div>
  )
}

function WorklistSkeleton() {
  return (
    <div className="space-y-3 animate-pulse">
      {[1, 2, 3].map(i => (
        <div key={i} className="bg-white rounded-2xl border border-slate-100 p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 space-y-2">
              <div className="h-3.5 bg-slate-100 rounded-full w-40" />
              <div className="h-3 bg-slate-100 rounded-full w-24" />
            </div>
            <div className="h-6 w-20 bg-slate-100 rounded-full" />
          </div>
          <div className="mt-3 h-3 bg-slate-100 rounded-full w-16" />
        </div>
      ))}
    </div>
  )
}

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 1)   return 'just now'
  if (mins < 60)  return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)   return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}
