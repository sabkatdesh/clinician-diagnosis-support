import { useNavigate } from 'react-router-dom'
import { LogOut, User, Building2 } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'

export default function SettingsPage() {
  const { fullName, hospital, clear } = useAuthStore()
  const navigate = useNavigate()

  function logout() {
    clear()
    navigate('/')
  }

  return (
    <div className="max-w-md mx-auto px-4 py-6">
      <h1 className="text-xl font-semibold text-slate-800 mb-6">Settings</h1>

      {/* Profile card */}
      <div className="bg-white rounded-2xl border border-slate-100 p-5 mb-4">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-4">Profile</h2>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <User className="w-4 h-4 text-slate-400 flex-shrink-0" />
            <div>
              <p className="text-xs text-slate-400">Name</p>
              <p className="text-sm font-medium text-slate-700">{fullName ?? '—'}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Building2 className="w-4 h-4 text-slate-400 flex-shrink-0" />
            <div>
              <p className="text-xs text-slate-400">Hospital</p>
              <p className="text-sm font-medium text-slate-700">{hospital ?? '—'}</p>
            </div>
          </div>
        </div>
      </div>

      <button
        onClick={logout}
        className="w-full flex items-center justify-center gap-2 bg-white border border-red-200 text-red-600 hover:bg-red-50 font-medium text-sm px-4 py-3 rounded-xl transition-colors"
      >
        <LogOut className="w-4 h-4" />
        Sign out
      </button>

      <p className="text-center text-xs text-slate-400 mt-8">
        Decision support only. The final judgement is yours.
      </p>
    </div>
  )
}
