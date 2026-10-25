export default function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <h1 className="text-lg font-semibold text-slate-700 mb-2">{title}</h1>
      <p className="text-sm text-slate-400">Coming in the next phase</p>
    </div>
  )
}
