import { useEffect, useState } from 'react'
import { fetchCellFrequencies, type CellFrequencyRow } from '../api/cellFrequencies'
import CellFrequencyTable from '../components/CellFrequencyTable'

export default function Dashboard() {
  const [rows, setRows] = useState<CellFrequencyRow[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchCellFrequencies()
      .then(setRows)
      .catch((err: Error) => setError(err.message))
  }, [])

  return (
    <div className="container-fluid py-4">
      <h1 className="h3 mb-4">Cell Population Frequencies</h1>
      {error && <div className="alert alert-danger">{error}</div>}
      {!error && !rows && <p>Loading...</p>}
      {rows && <CellFrequencyTable rows={rows} />}
    </div>
  )
}
