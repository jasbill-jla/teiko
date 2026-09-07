import type { components, operations } from '../types/api'

export type SampleRecord = components['schemas']['SampleRecord']
export type GroupCount = components['schemas']['GroupCount']
export type SamplesResult = components['schemas']['SamplesResult']
export type SamplesQuery = NonNullable<
  operations['read_samples_api_samples_get']['parameters']['query']
>
export type SampleFilterField =
  operations['read_samples_field_values_api_samples_field_values_get']['parameters']['query']['field']

export async function fetchSamples(query: SamplesQuery): Promise<SamplesResult> {
  const params = new URLSearchParams()
  if (query.grouping) params.set('grouping', query.grouping)
  // Condition/treatment: undefined omits the filter entirely (match
  // everything); an explicit "" filters for no value recorded (IS NULL) --
  // see previsualizing.samples.get_field_values on the backend.
  if (query.condition != null) params.set('condition', query.condition)
  if (query.treatment != null) params.set('treatment', query.treatment)
  if (query.sample_type) params.set('sample_type', query.sample_type)
  if (query.time_from_treatment !== null && query.time_from_treatment !== undefined) {
    params.set('time_from_treatment', String(query.time_from_treatment))
  }
  if (query.group_count_field) params.set('group_count_field', query.group_count_field)

  const response = await fetch(`/api/samples?${params}`)
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = body && typeof body.detail === 'string' ? body.detail : response.statusText
    throw new Error(`GET /api/samples failed: ${response.status} ${detail}`)
  }
  return response.json()
}

export async function fetchSampleFieldValues(field: SampleFilterField): Promise<string[]> {
  const response = await fetch(`/api/samples/field-values?${new URLSearchParams({ field })}`)
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = body && typeof body.detail === 'string' ? body.detail : response.statusText
    throw new Error(`GET /api/samples/field-values failed: ${response.status} ${detail}`)
  }
  return response.json()
}
