import { NavLink } from 'react-router-dom'
import { ClipboardList, UserPlus, Users, Settings } from 'lucide-react'

const items = [
  { to: '/worklist', icon: ClipboardList, label: 'Worklist' },
  { to: '/new-patient', icon: UserPlus, label: 'New patient' },
  { to: '/patients', icon: Users, label: 'Patients' },
  { to: '/settings', icon: Settings, label: 'Me' },
]

export default function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-100 safe-bottom z-40 md:hidden">
      <div className="flex">
        {items.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center gap-1 py-3 text-xs font-medium transition-colors ${
                isActive ? 'text-brand-700' : 'text-slate-400 hover:text-slate-600'
              }`
            }
          >
            <Icon className="w-5 h-5" />
            {label}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
