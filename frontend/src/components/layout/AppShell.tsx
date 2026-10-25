import { Outlet } from 'react-router-dom'
import { WifiOff } from 'lucide-react'
import Sidebar from './Sidebar'
import BottomNav from './BottomNav'
import { useConnectionStore } from '@/stores/connectionStore'

export default function AppShell() {
  const offline = useConnectionStore(s => s.offline)

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />
      <main className="md:ml-60 pb-20 md:pb-0 min-h-screen">
        {offline && (
          <div className="flex items-center justify-center gap-2 bg-amber-500 text-white text-xs font-medium px-4 py-2">
            <WifiOff className="w-3.5 h-3.5" />
            Connection lost — retrying…
          </div>
        )}
        <Outlet />
      </main>
      <BottomNav />
    </div>
  )
}
