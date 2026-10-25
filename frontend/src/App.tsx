import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import AppShell from '@/components/layout/AppShell'
import AuthPage from '@/pages/AuthPage'
import WorklistPage from '@/pages/WorklistPage'
import NewPatientPage from '@/pages/NewPatientPage'
import SessionPage from '@/pages/SessionPage'
import SettingsPage from '@/pages/SettingsPage'
import PatientsListPage from '@/pages/PatientsListPage'
import PatientProfilePage from '@/pages/PatientProfilePage'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = useAuthStore(s => s.token)
  return token ? <>{children}</> : <Navigate to="/" replace />
}

export default function App() {
  const token = useAuthStore(s => s.token)

  return (
    <Routes>
      {/* Public */}
      <Route
        path="/"
        element={token ? <Navigate to="/worklist" replace /> : <AuthPage />}
      />

      {/* Protected */}
      <Route element={<RequireAuth><AppShell /></RequireAuth>}>
        <Route path="/worklist"    element={<WorklistPage />} />
        <Route path="/new-patient" element={<NewPatientPage />} />
        <Route path="/patients"              element={<PatientsListPage />} />
        <Route path="/patients/:patientId"   element={<PatientProfilePage />} />
        <Route path="/session/:threadId" element={<SessionPage />} />
        <Route path="/settings"    element={<SettingsPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
