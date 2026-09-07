import { Fragment, useMemo, useState } from 'react'
import type { GroupCount, SampleRecord } from '../api/samples'

interface Props {
  samples: SampleRecord[]
  counts: GroupCount[]
  grouping: 'project' | 'subject' | ''
  groupCountField: 'sex' | 'response' | null
}

const COLUMNS: { key: keyof SampleRecord; label: string }[] = [
  { key: 'project_source_id', label: 'Project' },
  { key: 'subject_source_id', label: 'Subject' },
  { key: 'condition', label: 'Condition' },
  { key: 'treatment', label: 'Treatment' },
  { key: 'age', label: 'Age' },
  { key: 'sex', label: 'Sex' },
  { key: 'response', label: 'Response' },
  { key: 'sample_type', label: 'Sample Type' },
  { key: 'time_from_treatment', label: 'Time (days)' },
  { key: 'b_cell', label: 'B Cell' },
  { key: 'cd8_t_cell', label: 'CD8 T Cell' },
  { key: 'cd4_t_cell', label: 'CD4 T Cell' },
  { key: 'nk_cell', label: 'NK Cell' },
  { key: 'monocyte', label: 'Monocyte' },
]

interface Block {
  key: string
  samples: SampleRecord[]
}

function groupKeyFor(
  sample: SampleRecord,
  grouping: 'project' | 'subject' | '',
  groupCountField: 'sex' | 'response' | null,
): string {
  if (grouping === '') return ''
  if (grouping === 'project') return sample.project_source_id
  if (groupCountField === 'sex') return sample.sex
  return sample.response ?? 'none'
}

// Groups consecutive samples sharing the same key -- the API guarantees
// same-group samples are already contiguous (sorted by group first), so
// this never re-sorts anything, just segments the existing order.
function buildBlocks(samples: SampleRecord[], keyFn: (sample: SampleRecord) => string): Block[] {
  const blocks: Block[] = []
  for (const sample of samples) {
    const key = keyFn(sample)
    const last = blocks[blocks.length - 1]
    if (last && last.key === key) {
      last.samples.push(sample)
    } else {
      blocks.push({ key, samples: [sample] })
    }
  }
  return blocks
}

export default function SamplesResultTable({ samples, counts, grouping, groupCountField }: Props) {
  // Collapsed by default -- lets every group's header (and its count) be
  // seen together without scrolling past every sample row first.
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  const blocks = useMemo(
    () => buildBlocks(samples, (sample) => groupKeyFor(sample, grouping, groupCountField)),
    [samples, grouping, groupCountField],
  )
  const countByGroup = useMemo(() => new Map(counts.map((c) => [c.group, c.count])), [counts])

  function toggle(key: string) {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }

  function headerLabel(block: Block): string {
    const count = countByGroup.get(block.key) ?? block.samples.length
    if (grouping === 'project') {
      return `Project ${block.key} — ${count.toLocaleString()} sample${count === 1 ? '' : 's'}`
    }
    const field = groupCountField === 'sex' ? 'Sex' : 'Response'
    return `${field}: ${block.key} — ${count.toLocaleString()} subject${count === 1 ? '' : 's'}`
  }

  let rowIndex = 0

  return (
    <div className="table-responsive">
      <table className="table table-striped table-hover table-sm">
        <thead>
          <tr>
            {COLUMNS.map((column) => (
              <th key={column.key} scope="col">
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {grouping === ''
            ? samples.map((sample) => (
                <tr key={`sample-${rowIndex++}`}>
                  {COLUMNS.map((column) => (
                    <td key={column.key}>{sample[column.key] ?? '—'}</td>
                  ))}
                </tr>
              ))
            : blocks.map((block) => {
                const isExpanded = expanded.has(block.key)
                return (
                  <Fragment key={block.key}>
                    <tr className="table-secondary">
                      <td colSpan={COLUMNS.length}>
                        <button
                          type="button"
                          className="btn btn-link btn-sm p-0 text-decoration-none fw-bold"
                          onClick={() => toggle(block.key)}
                          aria-expanded={isExpanded}
                        >
                          {isExpanded ? '▾' : '▸'} {headerLabel(block)}
                        </button>
                      </td>
                    </tr>
                    {isExpanded &&
                      block.samples.map((sample) => (
                        <tr key={`sample-${rowIndex++}`}>
                          {COLUMNS.map((column) => (
                            <td key={column.key}>{sample[column.key] ?? '—'}</td>
                          ))}
                        </tr>
                      ))}
                  </Fragment>
                )
              })}
        </tbody>
      </table>
    </div>
  )
}
