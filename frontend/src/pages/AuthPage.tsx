import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Stethoscope } from 'lucide-react'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/authStore'

export default function AuthPage() {
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [hospital, setHospital] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [signedUp, setSignedUp] = useState(false)

  const setAuth = useAuthStore(s => s.setAuth)
  const setProfile = useAuthStore(s => s.setProfile)
  const navigate = useNavigate()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (mode === 'login') {
        const res = await authApi.login(email, password)
        setAuth(res.access_token, res.doctor_id)
        const profile = await authApi.me()
        setProfile(profile.full_name, profile.hospital)
        navigate('/worklist')
      } else {
        await authApi.signup(email, password, fullName, hospital)
        setSignedUp(true)
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (signedUp) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
        <div className="w-full max-w-sm text-center">
          <div className="w-14 h-14 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4">
            <Stethoscope className="w-7 h-7 text-emerald-600" />
          </div>
          <h1 className="text-xl font-semibold text-slate-800 mb-2">Check your email</h1>
          <p className="text-slate-500 text-sm mb-6">
            We sent a confirmation link to <strong>{email}</strong>. Click it to activate your account, then sign in.
          </p>
          <button
            onClick={() => { setSignedUp(false); setMode('login') }}
            className="text-brand-700 text-sm font-medium hover:underline"
          >
            Back to sign in
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-brand-700 flex items-center justify-center mx-auto mb-3">
            <Stethoscope className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-xl font-semibold text-slate-800">Clinical AI</h1>
          <p className="text-sm text-slate-500 mt-1">Decision support for clinicians</p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
          {/* Tab toggle */}
          <div className="flex rounded-xl bg-slate-100 p-1 mb-6">
            {(['login', 'signup'] as const).map(m => (
              <button
                key={m}
                onClick={() => { setMode(m); setError('') }}
                className={`flex-1 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  mode === m
                    ? 'bg-white text-slate-800 shadow-sm'
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                {m === 'login' ? 'Sign in' : 'Sign up'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'signup' && (
              <>
                <Field
                  label="Full name"
                  type="text"
                  value={fullName}
                  onChange={setFullName}
                  placeholder="Dr. Sarah Ahmed"
                  required
                />
                <Field
                  label="Hospital or clinic"
                  type="text"
                  value={hospital}
                  onChange={setHospital}
                  placeholder="Dhaka Medical College"
                  required
                />
              </>
            )}

            <Field
              label="Email"
              type="email"
              value={email}
              onChange={setEmail}
              placeholder="you@hospital.com"
              required
            />

            {/* Password with show/hide */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm text-slate-800 pr-10 focus:outline-none focus:ring-2 focus:ring-brand-600 focus:border-transparent placeholder:text-slate-400"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {error && (
              <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-brand-700 hover:bg-brand-800 text-white font-medium rounded-xl py-2.5 text-sm transition-colors disabled:opacity-60"
            >
              {loading ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-slate-400 mt-6">
          Decision support only — not a substitute for clinical judgement
        </p>
      </div>
    </div>
  )
}

function Field({
  label, type, value, onChange, placeholder, required,
}: {
  label: string
  type: string
  value: string
  onChange: (v: string) => void
  placeholder: string
  required?: boolean
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1.5">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-600 focus:border-transparent placeholder:text-slate-400"
      />
    </div>
  )
}
