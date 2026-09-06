import type { PopulationMedianFrequencies } from '../api/responseFrequencyAnalysis'

interface Props {
  medians: PopulationMedianFrequencies[]
}

export default function MedianFrequencyTable({ medians }: Props) {
  return (
    <div className="table-responsive">
      <table className="table table-striped table-hover table-sm">
        <thead>
          <tr>
            <th scope="col">Population</th>
            <th scope="col">Responder Median</th>
            <th scope="col">Non-Responder Median</th>
            <th scope="col">Difference</th>
          </tr>
        </thead>
        <tbody>
          {medians.map((row) => {
            const difference = row.responder_median - row.non_responder_median
            return (
              <tr key={row.population}>
                <td>{row.population}</td>
                <td>{row.responder_median.toFixed(2)}%</td>
                <td>{row.non_responder_median.toFixed(2)}%</td>
                <td>
                  {difference >= 0 ? '+' : ''}
                  {difference.toFixed(2)} pp
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
