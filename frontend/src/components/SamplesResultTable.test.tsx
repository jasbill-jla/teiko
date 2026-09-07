import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { GroupCount, SampleRecord } from '../api/samples'
import SamplesResultTable from './SamplesResultTable'

function sample(overrides: Partial<SampleRecord>): SampleRecord {
  return {
    project_source_id: 'prj1',
    condition: 'melanoma',
    treatment: 'miraclib',
    subject_source_id: 'sbj1',
    age: 42,
    sex: 'F',
    response: 'yes',
    sample_type: 'PBMC',
    time_from_treatment: 0,
    b_cell: 1,
    cd8_t_cell: 1,
    cd4_t_cell: 1,
    nk_cell: 1,
    monocyte: 1,
    ...overrides,
  }
}

// Group-header rows carry class "table-secondary"; everything else in
// tbody is a data row (whether flat or inside an expanded group).
function dataRows(): HTMLTableRowElement[] {
  return Array.from(document.querySelectorAll('tbody > tr:not(.table-secondary)'))
}

function headerRows(): HTMLTableRowElement[] {
  return Array.from(document.querySelectorAll('tbody > tr.table-secondary'))
}

describe('SamplesResultTable', () => {
  it('renders a flat row per sample and no group headers when grouping is off', () => {
    const samples = [sample({ subject_source_id: 's1' }), sample({ subject_source_id: 's2' })]

    render(
      <SamplesResultTable samples={samples} counts={[]} grouping="" groupCountField={null} hiddenColumns={[]} />,
    )

    expect(headerRows()).toHaveLength(0)
    expect(dataRows()).toHaveLength(2)
  })

  it('hides columns listed in hiddenColumns from both the header row and data rows', () => {
    render(
      <SamplesResultTable
        samples={[sample({})]}
        counts={[]}
        grouping=""
        groupCountField={null}
        hiddenColumns={['condition', 'treatment']}
      />,
    )

    expect(screen.queryByRole('columnheader', { name: 'Condition' })).not.toBeInTheDocument()
    expect(screen.queryByRole('columnheader', { name: 'Treatment' })).not.toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Sample Type' })).toBeInTheDocument()
  })

  it('groups by project using the counts prop for the header, and starts collapsed', () => {
    const samples = [
      sample({ project_source_id: 'prj-a', subject_source_id: 's1' }),
      sample({ project_source_id: 'prj-a', subject_source_id: 's2' }),
      sample({ project_source_id: 'prj-b', subject_source_id: 's3' }),
    ]
    const counts: GroupCount[] = [
      { group: 'prj-a', count: 2 },
      { group: 'prj-b', count: 1 },
    ]

    render(
      <SamplesResultTable
        samples={samples}
        counts={counts}
        grouping="project"
        groupCountField={null}
        hiddenColumns={[]}
      />,
    )

    expect(headerRows()).toHaveLength(2)
    expect(screen.getByRole('button', { name: /Project prj-a — 2 samples/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Project prj-b — 1 sample/ })).toBeInTheDocument()
    expect(dataRows()).toHaveLength(0)
  })

  it('expands and collapses one group independently of others', () => {
    const samples = [
      sample({ project_source_id: 'prj-a', subject_source_id: 's1' }),
      sample({ project_source_id: 'prj-b', subject_source_id: 's2' }),
    ]
    const counts: GroupCount[] = [
      { group: 'prj-a', count: 1 },
      { group: 'prj-b', count: 1 },
    ]

    render(
      <SamplesResultTable
        samples={samples}
        counts={counts}
        grouping="project"
        groupCountField={null}
        hiddenColumns={[]}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: /Project prj-a — 1 sample/ }))
    expect(dataRows()).toHaveLength(1)
    expect(dataRows()[0].textContent).toContain('s1')

    fireEvent.click(screen.getByRole('button', { name: /Project prj-b — 1 sample/ }))
    expect(dataRows()).toHaveLength(2)

    fireEvent.click(screen.getByRole('button', { name: /Project prj-a — 1 sample/ }))
    expect(dataRows()).toHaveLength(1)
    expect(dataRows()[0].textContent).toContain('s2')
  })

  it('groups by subject sex, counting subjects under the "Sex" header label', () => {
    const samples = [sample({ sex: 'F', subject_source_id: 's1' }), sample({ sex: 'M', subject_source_id: 's2' })]
    const counts: GroupCount[] = [
      { group: 'F', count: 1 },
      { group: 'M', count: 1 },
    ]

    render(
      <SamplesResultTable
        samples={samples}
        counts={counts}
        grouping="subject"
        groupCountField="sex"
        hiddenColumns={[]}
      />,
    )

    expect(screen.getByRole('button', { name: /Sex: F — 1 subject/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Sex: M — 1 subject/ })).toBeInTheDocument()
  })

  it('groups by subject response, using the "none" sentinel key for a null response', () => {
    const samples = [sample({ response: null, subject_source_id: 's1' })]
    const counts: GroupCount[] = [{ group: 'none', count: 1 }]

    render(
      <SamplesResultTable
        samples={samples}
        counts={counts}
        grouping="subject"
        groupCountField="response"
        hiddenColumns={[]}
      />,
    )

    expect(screen.getByRole('button', { name: /Response: none — 1 subject/ })).toBeInTheDocument()
  })

  it('falls back to the block sample count when counts has no entry for a group', () => {
    const samples = [
      sample({ project_source_id: 'prj-a', subject_source_id: 's1' }),
      sample({ project_source_id: 'prj-a', subject_source_id: 's2' }),
    ]

    render(
      <SamplesResultTable samples={samples} counts={[]} grouping="project" groupCountField={null} hiddenColumns={[]} />,
    )

    expect(screen.getByRole('button', { name: /Project prj-a — 2 samples/ })).toBeInTheDocument()
  })
})
