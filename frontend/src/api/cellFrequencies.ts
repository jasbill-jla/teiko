import type { components } from '../types/api'

export type CellFrequencyRow = components['schemas']['CellFrequencyRow']

export async function fetchCellFrequencies(): Promise<CellFrequencyRow[]> {
  const response = await fetch('/api/cell-frequencies')
  if (!response.ok) {
    throw new Error(`GET /api/cell-frequencies failed: ${response.status}`)
  }
  return response.json()
}
