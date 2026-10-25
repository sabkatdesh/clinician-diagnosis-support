import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  doctorId: string | null
  fullName: string | null
  hospital: string | null
  setAuth: (token: string, doctorId: string) => void
  setProfile: (fullName: string, hospital: string) => void
  clear: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      doctorId: null,
      fullName: null,
      hospital: null,
      setAuth: (token, doctorId) => set({ token, doctorId }),
      setProfile: (fullName, hospital) => set({ fullName, hospital }),
      clear: () => set({ token: null, doctorId: null, fullName: null, hospital: null }),
    }),
    { name: 'cads_auth' },
  ),
)
