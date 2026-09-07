import { useEffect, useState } from 'react'
import type { FormEvent, MouseEvent } from 'react'
import {
  fetchSampleFieldValues,
  fetchSamples,
  type SampleRecord,
  type SamplesQuery,
  type SamplesResult,
} from '../api/samples'
import SamplesResultTable from '../components/SamplesResultTable'
import { downloadCsv, toCsv } from '../csv'

type Grouping = 'project' | 'subject' | ''
type GroupCountField = 'sex' | 'response'
type FilterColumn = 'condition' | 'treatment' | 'sample_type' | 'time_from_treatment'

const FILTER_FIELDS = ['condition', 'treatment', 'sample_type', 'time_from_treatment'] as const
type FilterFieldValues = Record<(typeof FILTER_FIELDS)[number], string[]>

const SAMPLE_COLUMNS: { key: keyof SampleRecord; header: string }[] = [
  { key: 'project_source_id', header: 'Project' },
  { key: 'condition', header: 'Condition' },
  { key: 'treatment', header: 'Treatment' },
  { key: 'subject_source_id', header: 'Subject' },
  { key: 'age', header: 'Age' },
  { key: 'sex', header: 'Sex' },
  { key: 'response', header: 'Response' },
  { key: 'sample_type', header: 'Sample Type' },
  { key: 'time_from_treatment', header: 'Time From Treatment' },
  { key: 'b_cell', header: 'B Cell' },
  { key: 'cd8_t_cell', header: 'CD8 T Cell' },
  { key: 'cd4_t_cell', header: 'CD4 T Cell' },
  { key: 'nk_cell', header: 'NK Cell' },
  { key: 'monocyte', header: 'Monocyte' },
]

export default function SamplesExplorer() {
  const [condition, setCondition] = useState('')
  const [treatment, setTreatment] = useState('')
  const [sampleType, setSampleType] = useState('')
  const [timeFromTreatment, setTimeFromTreatment] = useState('')
  const [grouping, setGrouping] = useState<Grouping>('')
  const [groupCountField, setGroupCountField] = useState<GroupCountField | ''>('')

  const [result, setResult] = useState<SamplesResult | null>(null)
  const [appliedGrouping, setAppliedGrouping] = useState<Grouping>('')
  const [appliedGroupCountField, setAppliedGroupCountField] = useState<GroupCountField | null>(
    null,
  )
  const [appliedFilterColumns, setAppliedFilterColumns] = useState<(keyof SampleRecord)[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const [fieldValues, setFieldValues] = useState<FilterFieldValues>({
    condition: [],
    treatment: [],
    sample_type: [],
    time_from_treatment: [],
  })

  useEffect(() => {
    Promise.all(FILTER_FIELDS.map((field) => fetchSampleFieldValues(field)))
      .then((results) => {
        setFieldValues(
          Object.fromEntries(FILTER_FIELDS.map((field, i) => [field, results[i]])) as FilterFieldValues,
        )
      })
      .catch((err: Error) => setError(err.message))
  }, [])

  function runSearch(
    query: SamplesQuery,
    queryGrouping: Grouping,
    queryGroupCountField: GroupCountField | '',
    queryFilterColumns: (keyof SampleRecord)[],
  ) {
    setLoading(true)
    setError(null)
    fetchSamples(query)
      .then((data) => {
        setResult(data)
        setAppliedGrouping(queryGrouping)
        setAppliedGroupCountField(
          queryGrouping === 'subject' ? (queryGroupCountField as GroupCountField) : null,
        )
        setAppliedFilterColumns(queryFilterColumns)
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()

    if (grouping === 'subject' && !groupCountField) {
      setError('Subject grouping (sex or response) is required when grouping by subject.')
      return
    }

    const filterColumns: FilterColumn[] = [
      ...(condition ? (['condition'] as const) : []),
      ...(treatment ? (['treatment'] as const) : []),
      ...(sampleType ? (['sample_type'] as const) : []),
      ...(timeFromTreatment !== '' ? (['time_from_treatment'] as const) : []),
    ]

    runSearch(
      {
        grouping: grouping || undefined,
        condition: condition || undefined,
        treatment: treatment || undefined,
        sample_type: sampleType || undefined,
        time_from_treatment: timeFromTreatment === '' ? undefined : Number(timeFromTreatment),
        group_count_field: grouping === 'subject' ? groupCountField || undefined : undefined,
      },
      grouping,
      groupCountField,
      filterColumns,
    )
  }

  function handleReset(e: MouseEvent) {
    e.preventDefault()
    setCondition('')
    setTreatment('')
    setSampleType('')
    setTimeFromTreatment('')
    setGrouping('')
    setGroupCountField('')
    setResult(null)
    setAppliedGrouping('')
    setAppliedGroupCountField(null)
    setAppliedFilterColumns([])
    setError(null)
  }

  function handleExport() {
    if (!result) return
    const columns = SAMPLE_COLUMNS.filter((column) => !appliedFilterColumns.includes(column.key))
    const csv = toCsv(
      columns.map((column) => column.header),
      result.samples.map((sample) => columns.map((column) => sample[column.key])),
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
          <select
            id="se-condition"
            className="form-select form-select-sm"
            value={condition}
            onChange={(e) => setCondition(e.target.value)}
          >
            <option value="">(all)</option>
            {fieldValues.condition.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </div>
        <div className="col-12">
          <label htmlFor="se-treatment" className="form-label mb-0">
            Treatment
          </label>
          <select
            id="se-treatment"
            className="form-select form-select-sm"
            value={treatment}
            onChange={(e) => setTreatment(e.target.value)}
          >
            <option value="">(all)</option>
            {fieldValues.treatment.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </div>
        <div className="col-12">
          <label htmlFor="se-sample-type" className="form-label mb-0">
            Sample Type
          </label>
          <select
            id="se-sample-type"
            className="form-select form-select-sm"
            value={sampleType}
            onChange={(e) => setSampleType(e.target.value)}
          >
            <option value="">(all)</option>
            {fieldValues.sample_type.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
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
            <option value="">(all)</option>
            {fieldValues.time_from_treatment.map((value) => (
              <option key={value} value={value}>
                {value} days
              </option>
            ))}
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
            <option value="">(none)</option>
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

      <div className="mb-4">
        <a href="#" className="small" onClick={handleReset}>
          Reset
        </a>
      </div>

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
            hiddenColumns={appliedFilterColumns}
          />
        </>
      )}
    </div>
  )
}
