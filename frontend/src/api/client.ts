import axios from 'axios'
import { useAuthStore } from '@/stores/authStore'
import { useConnectionStore } from '@/stores/connectionStore'

export const api = axios.create({
  baseURL: '/',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => {
    useConnectionStore.getState().setOffline(false)
    return res
  },
  (err) => {
    if (!err.response) {
      // Network error — no response at all
      useConnectionStore.getState().setOffline(true)
    } else {
      useConnectionStore.getState().setOffline(false)
      if (err.response.status === 401) {
        useAuthStore.getState().clear()
        window.location.hash = '/'
      }
    }
    return Promise.reject(err)
  },
)
