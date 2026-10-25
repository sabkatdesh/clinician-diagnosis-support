import { useQuery, useQueryClient } from '@tanstack/react-query'
import { pipelineApi } from '@/api/pipeline'

export function usePipelineState(threadId: string | undefined) {
  return useQuery({
    queryKey: ['pipeline', threadId],
    queryFn: () => pipelineApi.getState(threadId!),
    enabled: !!threadId,
    staleTime: 0,
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data) return 3000
      if (data.status === 'complete') return false
      if (data.status === 'not_found') return false
      // Only stop polling when truly paused at a HITL gate waiting for the doctor
      if (data.status === 'paused' && data.paused_at) return false
      return 5000
    },
    refetchIntervalInBackground: false,
  })
}

export function useInvalidatePipeline() {
  const qc = useQueryClient()
  return (threadId: string) => {
    qc.invalidateQueries({ queryKey: ['pipeline', threadId] })
    qc.invalidateQueries({ queryKey: ['sessions'] })
  }
}
