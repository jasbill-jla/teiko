import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  fetchResponseFrequencyAnalysis,
  type ResponseFrequencyAnalysis,
} from '../api/responseFrequencyAnalysis'
import MedianFrequencyTable from '../components/MedianFrequencyTable'
import ResponseBoxplot from '../components/ResponseBoxplot'

// Fixed by this page -- no controls to change these, per the spec.
const CONDITION = 'melanoma'
const TREATMENT = 'miraclib'
const SAMPLE_TYPE = 'PBMC'
const DEFAULT_MEDIAN_THRESHOLD = 10

export default function ResponseAnalysis() {
  const [thresholdInput, setThresholdInput] = useState(String(DEFAULT_MEDIAN_THRESHOLD))
  const [appliedThreshold, setAppliedThreshold] = useState(DEFAULT_MEDIAN_THRESHOLD)
  const [data, setData] = useState<ResponseFrequencyAnalysis | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchResponseFrequencyAnalysis({
      condition: CONDITION,
      treatment: TREATMENT,
      sampleType: SAMPLE_TYPE,
      medianThreshold: appliedThreshold,
    })
      .then((result) => {
        setData(result)
        setError(null)
      })
      .catch((err: Error) => setError(err.message))
  }, [appliedThreshold])

  function handleRefresh(e: FormEvent) {
    e.preventDefault()
    const parsed = Number(thresholdInput)
    if (Number.isNaN(parsed)) return
    setAppliedThreshold(parsed)
  }

  return (
    <div className="container-fluid py-4">
      <h1 className="h3 mb-1">Response Frequency Analysis</h1>
      <p className="text-muted">
        {CONDITION} subjects treated with {TREATMENT}, {SAMPLE_TYPE} samples
      </p>

      <form className="d-flex align-items-end gap-2 mb-4" onSubmit={handleRefresh}>
        <div>
          <label htmlFor="median-threshold" className="form-label mb-0">
            Median difference threshold (percentage points)
          </label>
          <input
            id="median-threshold"
            type="number"
            step="0.1"
            className="form-control form-control-sm"
            value={thresholdInput}
            onChange={(e) => setThresholdInput(e.target.value)}
          />
        </div>
        <button type="submit" className="btn btn-primary btn-sm">
          Refresh
        </button>
      </form>

      {error && <div className="alert alert-danger">{error}</div>}
      {!error && !data && <p>Loading...</p>}

      {data && (
        <>
          {data.boxplots.length === 0 ? (
            <p className="text-muted">
              No cell population's median difference exceeds this threshold.
            </p>
          ) : (
            <div className="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-4 mb-4">
              {data.boxplots.map((boxplot) => (
                <div className="col" key={boxplot.population}>
                  <ResponseBoxplot boxplot={boxplot} />
                </div>
              ))}
            </div>
          )}

          <MedianFrequencyTable medians={data.medians} />
        </>
      )}
    </div>
  )
}
