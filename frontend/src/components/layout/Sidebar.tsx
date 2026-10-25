import { NavLink } from 'react-router-dom'
import { ClipboardList, UserPlus, Users, Settings, Stethoscope } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'

const items = [
  { to: '/worklist', icon: ClipboardList, label: 'Worklist' },
  { to: '/new-patient', icon: UserPlus, label: 'New patient' },
  { to: '/patients', icon: Users, label: 'Patients' },
]

export default function Sidebar() {
  const fullName = useAuthStore(s => s.fullName)
  const hospital = useAuthStore(s => s.hospital)

  return (
    <aside className="hidden md:flex flex-col w-60 min-h-screen bg-white border-r border-slate-100 fixed left-0 top-0 bottom-0 z-40">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-slate-100">
        <div className="w-9 h-9 rounded-xl bg-brand-700 flex items-center justify-center flex-shrink-0">
          <Stethoscope className="w-5 h-5 text-white" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-slate-800 truncate">Clinical AI</p>
          <p className="text-xs text-slate-400 truncate">{hospital ?? 'Decision support'}</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {items.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-brand-50 text-brand-700'
                  : 'text-slate-500 hover:bg-slate-50 hover:text-slate-700'
              }`
            }
          >
            <Icon className="w-4.5 h-4.5 flex-shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Profile */}
      <div className="px-3 py-4 border-t border-slate-100">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
              isActive
                ? 'bg-brand-50 text-brand-700'
                : 'text-slate-500 hover:bg-slate-50 hover:text-slate-700'
            }`
          }
        >
          <Settings className="w-4.5 h-4.5 flex-shrink-0" />
          <div className="min-w-0">
            <p className="truncate">{fullName ?? 'Settings'}</p>
          </div>
        </NavLink>
      </div>
    </aside>
  )
}
