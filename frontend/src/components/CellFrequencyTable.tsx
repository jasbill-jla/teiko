import type { CellFrequencyRow } from '../api/cellFrequencies'

interface Props {
  rows: CellFrequencyRow[]
}

export default function CellFrequencyTable({ rows }: Props) {
  return (
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
          {rows.map((row) => (
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
  )
}
