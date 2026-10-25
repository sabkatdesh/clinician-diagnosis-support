import { Component, type ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'

interface State { error: Error | null }

export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex flex-col items-center justify-center min-h-screen px-6 text-center bg-slate-50">
          <AlertTriangle className="w-12 h-12 text-amber-400 mb-4" />
          <h1 className="text-lg font-semibold text-slate-800 mb-2">Something went wrong</h1>
          <p className="text-sm text-slate-500 mb-6 max-w-xs">{this.state.error.message}</p>
          <button
            onClick={() => window.location.reload()}
            className="bg-brand-700 hover:bg-brand-800 text-white text-sm font-medium px-5 py-2.5 rounded-xl transition-colors"
          >
            Reload page
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
