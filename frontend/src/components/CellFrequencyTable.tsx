import { useMemo, useState } from 'react'
import type { CellFrequencyRow } from '../api/cellFrequencies'

interface Props {
  rows: CellFrequencyRow[]
}

const PAGE_SIZE = 100

export default function CellFrequencyTable({ rows }: Props) {
  const [page, setPage] = useState(0)
  const pageCount = Math.max(1, Math.ceil(rows.length / PAGE_SIZE))
  // Rows can change (e.g. a future filter) out from under an existing page
  // number; clamp instead of trusting `page` to still be in range.
  const currentPage = Math.min(page, pageCount - 1)
  const pageRows = useMemo(
    () => rows.slice(currentPage * PAGE_SIZE, currentPage * PAGE_SIZE + PAGE_SIZE),
    [rows, currentPage],
  )

  return (
    <div>
      <div className="table-responsive">
        <table className="table table-striped table-hover table-sm">
          <thead>
            <tr>
              <th scope="col">Sample</th>
              <th scope="col">Population</th>
              <th scope="col">Count</th>
              <th scope="col">Total Count</th>
              <th scope="col">Percentage</th>
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
        totalRows={rows.length}
        onPageChange={setPage}
      />
    </div>
  )
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
