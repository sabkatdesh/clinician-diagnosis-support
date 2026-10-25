import { create } from 'zustand'

interface ConnectionState {
  offline: boolean
  setOffline: (v: boolean) => void
}

export const useConnectionStore = create<ConnectionState>(set => ({
  offline: false,
  setOffline: offline => set({ offline }),
}))
