import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { CellFrequencyRow } from '../api/cellFrequencies'
import CellFrequencyTable from './CellFrequencyTable'

// Deliberately not pre-sorted by percentage and not grouped by population,
// so "no sort applied" and "sorted" are actually distinguishable.
const ROWS: CellFrequencyRow[] = [
  { sample: 's2', population: 'nk_cell', count: 40, total_count: 100, percentage: 40 },
  { sample: 's1', population: 'b_cell', count: 10, total_count: 100, percentage: 10 },
  { sample: 's3', population: 'monocyte', count: 25, total_count: 100, percentage: 25 },
  { sample: 's1', population: 'cd4_t_cell', count: 15, total_count: 100, percentage: 15 },
]

// The sample cell also holds the mobile expand/collapse toggle button, so
// its text content isn't just the sample id -- pull out the text nodes only.
function sampleCellText(td: Element): string {
  return Array.from(td.childNodes)
    .filter((node) => node.nodeType === Node.TEXT_NODE)
    .map((node) => node.textContent)
    .join('')
    .trim()
}

// Excludes the mobile detail rows (class d-sm-none), which aren't data rows.
function renderedRowKeys(): string[] {
  return Array.from(document.querySelectorAll('tbody > tr:not(.d-sm-none)')).map((tr) => {
    const cells = tr.querySelectorAll('td')
    return `${sampleCellText(cells[0])}-${cells[1].textContent}`
  })
}

function rowKey(row: CellFrequencyRow): string {
  return `${row.sample}-${row.population}`
}

describe('CellFrequencyTable', () => {
  it('renders rows in the order they were received when no sort is applied', () => {
    render(<CellFrequencyTable rows={ROWS} />)

    expect(renderedRowKeys()).toEqual(ROWS.map(rowKey))
  })

  it('filters to only the selected population', () => {
    render(<CellFrequencyTable rows={ROWS} />)

    fireEvent.change(screen.getByLabelText('Filter by population'), {
      target: { value: 'b_cell' },
    })

    expect(renderedRowKeys()).toEqual(['s1-b_cell'])
  })

  it('shows "All" plus every population present in the data as filter options', () => {
    render(<CellFrequencyTable rows={ROWS} />)

    const options = screen
      .getAllByRole('option')
      .map((option) => (option as HTMLOptionElement).value)

    expect(options).toEqual(['all', 'b_cell', 'cd4_t_cell', 'monocyte', 'nk_cell'])
  })

  it('sorts by percentage ascending then descending, and Reset Sort restores the original order', () => {
    render(<CellFrequencyTable rows={ROWS} />)

    const sortedAscending = [...ROWS].sort((a, b) => a.percentage - b.percentage).map(rowKey)
    const sortedDescending = [...sortedAscending].reverse()

    // No sort applied yet -- no reset control.
    expect(screen.queryByText('Reset Sort')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /Percentage/ }))
    expect(renderedRowKeys()).toEqual(sortedAscending)
    expect(screen.getByText('Reset Sort')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /Percentage/ }))
    expect(renderedRowKeys()).toEqual(sortedDescending)
    expect(screen.getByText('Reset Sort')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Reset Sort'))
    expect(renderedRowKeys()).toEqual(ROWS.map(rowKey))
    expect(screen.queryByText('Reset Sort')).not.toBeInTheDocument()
  })

  it('expands a row to reveal Count and Total Count, and collapses it back', () => {
    render(<CellFrequencyTable rows={ROWS} />)

    const toggle = screen.getByRole('button', { name: 'Expand details for s1 b_cell' })
    expect(screen.queryByText('Count:')).not.toBeInTheDocument()

    fireEvent.click(toggle)
    expect(screen.getByText('Count:').nextSibling).toHaveTextContent('10')
    expect(screen.getByText('Total Count:').nextSibling).toHaveTextContent('100')
    // Other rows are unaffected.
    expect(
      screen.queryByRole('button', { name: /Collapse details for s2 nk_cell/ }),
    ).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Collapse details for s1 b_cell' }))
    expect(screen.queryByText('Count:')).not.toBeInTheDocument()
  })
})
