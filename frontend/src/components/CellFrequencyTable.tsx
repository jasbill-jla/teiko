import { useMemo, useState } from 'react'
import type { CellFrequencyRow } from '../api/cellFrequencies'

interface Props {
  rows: CellFrequencyRow[]
}

const PAGE_SIZE = 100
const ALL_POPULATIONS = 'all'

type SortDirection = 'asc' | 'desc' | null

export default function CellFrequencyTable({ rows }: Props) {
  const [page, setPage] = useState(0)
  const [populationFilter, setPopulationFilter] = useState(ALL_POPULATIONS)
  const [percentageSort, setPercentageSort] = useState<SortDirection>(null)

  // Derived from the data rather than hardcoded, so the filter stays in
  // sync with whatever populations the backend actually returns.
  const populations = useMemo(
    () => Array.from(new Set(rows.map((row) => row.population))).sort(),
    [rows],
  )

  const visibleRows = useMemo(() => {
    const filtered =
      populationFilter === ALL_POPULATIONS
        ? rows
        : rows.filter((row) => row.population === populationFilter)
    if (!percentageSort) return filtered
    const sorted = [...filtered].sort((a, b) => a.percentage - b.percentage)
    return percentageSort === 'desc' ? sorted.reverse() : sorted
  }, [rows, populationFilter, percentageSort])

  const pageCount = Math.max(1, Math.ceil(visibleRows.length / PAGE_SIZE))
  // Rows can change (a new filter/sort) out from under an existing page
  // number; clamp instead of trusting `page` to still be in range.
  const currentPage = Math.min(page, pageCount - 1)
  const pageRows = useMemo(
    () => visibleRows.slice(currentPage * PAGE_SIZE, currentPage * PAGE_SIZE + PAGE_SIZE),
    [visibleRows, currentPage],
  )

  function handlePopulationFilterChange(value: string) {
    setPopulationFilter(value)
    setPage(0)
  }

  function toggleSort() {
    setPercentageSort((prev) => (prev === 'asc' ? 'desc' : 'asc'))
    setPage(0)
  }

  function resetSort() {
    setPercentageSort(null)
    setPage(0)
  }

  return (
    <div>
      <div className="d-flex align-items-center gap-2 mb-2">
        <label htmlFor="population-filter" className="col-form-label col-form-label-sm">
          Filter by population
        </label>
        <select
          id="population-filter"
          className="form-select form-select-sm w-auto"
          value={populationFilter}
          onChange={(e) => handlePopulationFilterChange(e.target.value)}
        >
          <option value={ALL_POPULATIONS}>All</option>
          {populations.map((population) => (
            <option key={population} value={population}>
              {population}
            </option>
          ))}
        </select>
      </div>
      <div className="table-responsive">
        <table className="table table-striped table-hover table-sm">
          <thead>
            <tr>
              <th scope="col">Sample</th>
              <th scope="col">Population</th>
              <th scope="col">Count</th>
              <th scope="col">Total Count</th>
              <th scope="col">
                <button
                  type="button"
                  className="btn btn-link btn-sm p-0 text-decoration-none"
                  onClick={toggleSort}
                >
                  Percentage{sortIndicator(percentageSort)}
                </button>
                {percentageSort && (
                  <button
                    type="button"
                    className="btn btn-link btn-sm p-0 text-decoration-none text-muted ms-2"
                    onClick={resetSort}
                  >
                    Reset sort
                  </button>
                )}
              </th>
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row) => (
              <tr key={`${row.sample}-${row.population}`}>
                <td>{row.sample}</td>
                <td>{row.population}</td>
                <td>{row.count.toLocaleString()}</td>
                <td>{row.total_count.toLocaleString()}</td>
                <td>{row.percentage.toFixed(2)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Pagination
        currentPage={currentPage}
        pageCount={pageCount}
        totalRows={visibleRows.length}
        onPageChange={setPage}
      />
    </div>
  )
}

function sortIndicator(direction: SortDirection) {
  if (direction === 'asc') return ' ▲'
  if (direction === 'desc') return ' ▼'
  return ''
}

interface PaginationProps {
  currentPage: number
  pageCount: number
  totalRows: number
  onPageChange: (page: number) => void
}

function Pagination({ currentPage, pageCount, totalRows, onPageChange }: PaginationProps) {
  const firstRow = totalRows === 0 ? 0 : currentPage * PAGE_SIZE + 1
  const lastRow = Math.min(totalRows, (currentPage + 1) * PAGE_SIZE)

  return (
    <div className="d-flex justify-content-between align-items-center">
      <span className="text-muted small">
        Showing {firstRow.toLocaleString()}-{lastRow.toLocaleString()} of{' '}
        {totalRows.toLocaleString()}
      </span>
      <nav aria-label="Cell frequency table pages">
        <ul className="pagination pagination-sm mb-0">
          <li className={`page-item ${currentPage === 0 ? 'disabled' : ''}`}>
            <button
              type="button"
              className="page-link"
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage === 0}
            >
              Previous
            </button>
          </li>
          <li className="page-item disabled">
            <span className="page-link">
              Page {currentPage + 1} of {pageCount}
            </span>
          </li>
          <li className={`page-item ${currentPage >= pageCount - 1 ? 'disabled' : ''}`}>
            <button
              type="button"
              className="page-link"
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage >= pageCount - 1}
            >
              Next
            </button>
          </li>
        </ul>
      </nav>
    </div>
  )
}
