import type { components } from '../types/api'

export type ResponseFrequencyAnalysis = components['schemas']['ResponseFrequencyAnalysis']
export type PopulationBoxplot = components['schemas']['PopulationBoxplot']
export type BoxplotStats = components['schemas']['BoxplotStats']

export interface ResponseFrequencyAnalysisParams {
  condition: string
  treatment: string
  sampleType: string
}

export async function fetchResponseFrequencyAnalysis(
  params: ResponseFrequencyAnalysisParams,
): Promise<ResponseFrequencyAnalysis> {
  const query = new URLSearchParams({
    condition: params.condition,
    treatment: params.treatment,
    sample_type: params.sampleType,
  })
  const response = await fetch(`/api/response-frequency-analysis?${query}`)
  if (!response.ok) {
    throw new Error(`GET /api/response-frequency-analysis failed: ${response.status}`)
  }
  return response.json()
}
