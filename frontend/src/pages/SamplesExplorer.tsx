import { useState } from 'react'
import type { FormEvent } from 'react'
import { fetchSamples, type SamplesQuery, type SamplesResult } from '../api/samples'
import SamplesResultTable from '../components/SamplesResultTable'
import { downloadCsv, toCsv } from '../csv'

type Grouping = 'project' | 'subject'
type GroupCountField = 'sex' | 'response'

const SAMPLE_COLUMNS = [
  'project_source_id',
  'condition',
  'treatment',
  'subject_source_id',
  'age',
  'sex',
  'response',
  'sample_type',
  'time_from_treatment',
  'b_cell',
  'cd8_t_cell',
  'cd4_t_cell',
  'nk_cell',
  'monocyte',
] as const

const CSV_HEADERS = [
  'Project',
  'Condition',
  'Treatment',
  'Subject',
  'Age',
  'Sex',
  'Response',
  'Sample Type',
  'Time From Treatment',
  'B Cell',
  'CD8 T Cell',
  'CD4 T Cell',
  'NK Cell',
  'Monocyte',
]

export default function SamplesExplorer() {
  const [condition, setCondition] = useState('')
  const [treatment, setTreatment] = useState('')
  const [sampleType, setSampleType] = useState('')
  const [timeFromTreatment, setTimeFromTreatment] = useState('')
  const [grouping, setGrouping] = useState<Grouping>('project')
  const [groupCountField, setGroupCountField] = useState<GroupCountField | ''>('')

  const [result, setResult] = useState<SamplesResult | null>(null)
  const [appliedGrouping, setAppliedGrouping] = useState<Grouping>('project')
  const [appliedGroupCountField, setAppliedGroupCountField] = useState<GroupCountField | null>(
    null,
  )
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  function handleSubmit(e: FormEvent) {
    e.preventDefault()

    if (grouping === 'subject' && !groupCountField) {
      setError('Subject grouping (sex or response) is required when grouping by subject.')
      return
    }

    const query: SamplesQuery = {
      grouping,
      condition: condition || undefined,
      treatment: treatment || undefined,
      sample_type: sampleType || undefined,
      time_from_treatment: timeFromTreatment === '' ? undefined : Number(timeFromTreatment),
      group_count_field: grouping === 'subject' ? groupCountField || undefined : undefined,
    }

    setLoading(true)
    setError(null)
    fetchSamples(query)
      .then((data) => {
        setResult(data)
        setAppliedGrouping(grouping)
        setAppliedGroupCountField(grouping === 'subject' ? (groupCountField as GroupCountField) : null)
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }

  function handleExport() {
    if (!result) return
    const csv = toCsv(
      CSV_HEADERS,
      result.samples.map((sample) => SAMPLE_COLUMNS.map((key) => sample[key])),
    )
    downloadCsv('samples.csv', csv)
  }

  return (
    <div className="container-fluid py-4">
      <h1 className="h3 mb-4">Sample Explorer</h1>

      <form className="row row-cols-lg-auto g-3 align-items-end mb-4" onSubmit={handleSubmit}>
        <div className="col-12">
          <label htmlFor="se-condition" className="form-label mb-0">
            Condition
          </label>
          <input
            id="se-condition"
            className="form-control form-control-sm"
            value={condition}
            onChange={(e) => setCondition(e.target.value)}
            placeholder="(any)"
          />
        </div>
        <div className="col-12">
          <label htmlFor="se-treatment" className="form-label mb-0">
            Treatment
          </label>
          <input
            id="se-treatment"
            className="form-control form-control-sm"
            value={treatment}
            onChange={(e) => setTreatment(e.target.value)}
            placeholder="(any)"
          />
        </div>
        <div className="col-12">
          <label htmlFor="se-sample-type" className="form-label mb-0">
            Sample Type
          </label>
          <input
            id="se-sample-type"
            className="form-control form-control-sm"
            value={sampleType}
            onChange={(e) => setSampleType(e.target.value)}
            placeholder="(any)"
          />
        </div>
        <div className="col-12">
          <label htmlFor="se-time" className="form-label mb-0">
            Time From Treatment
          </label>
          <select
            id="se-time"
            className="form-select form-select-sm"
            value={timeFromTreatment}
            onChange={(e) => setTimeFromTreatment(e.target.value)}
          >
            <option value="">(any)</option>
            <option value="0">0 days</option>
            <option value="7">7 days</option>
            <option value="14">14 days</option>
          </select>
        </div>
        <div className="col-12">
          <label htmlFor="se-grouping" className="form-label mb-0">
            Group By
          </label>
          <select
            id="se-grouping"
            className="form-select form-select-sm"
            value={grouping}
            onChange={(e) => setGrouping(e.target.value as Grouping)}
          >
            <option value="project">Project</option>
            <option value="subject">Subject</option>
          </select>
        </div>
        {grouping === 'subject' && (
          <div className="col-12">
            <label htmlFor="se-group-count-field" className="form-label mb-0">
              Subject Grouping
            </label>
            <select
              id="se-group-count-field"
              className="form-select form-select-sm"
              value={groupCountField}
              onChange={(e) => setGroupCountField(e.target.value as GroupCountField | '')}
            >
              <option value="">(select)</option>
              <option value="sex">Sex</option>
              <option value="response">Response</option>
            </select>
          </div>
        )}
        <div className="col-12">
          <button type="submit" className="btn btn-primary btn-sm" disabled={loading}>
            {loading ? 'Loading…' : 'Submit'}
          </button>
        </div>
      </form>

      {error && <div className="alert alert-danger">{error}</div>}

      {result && (
        <>
          <div className="d-flex justify-content-between align-items-center mb-2">
            <span className="text-muted small">
              {result.samples.length.toLocaleString()} sample
              {result.samples.length === 1 ? '' : 's'}
            </span>
            <button type="button" className="btn btn-outline-secondary btn-sm" onClick={handleExport}>
              Export CSV
            </button>
          </div>
          <SamplesResultTable
            samples={result.samples}
            counts={result.counts}
            grouping={appliedGrouping}
            groupCountField={appliedGroupCountField}
          />
        </>
      )}
    </div>
  )
}
