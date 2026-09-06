import { useEffect, useState } from 'react'
import {
  fetchResponseFrequencyAnalysis,
  type PopulationBoxplot,
  type ResponseFrequencyAnalysis,
} from '../api/responseFrequencyAnalysis'
import ResponseBoxplot from '../components/ResponseBoxplot'

// Fixed by this page -- no controls to change these, per the spec.
const CONDITION = 'melanoma'
const TREATMENT = 'miraclib'
const SAMPLE_TYPE = 'PBMC'

export default function ResponseAnalysis() {
  const [data, setData] = useState<ResponseFrequencyAnalysis | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchResponseFrequencyAnalysis({
      condition: CONDITION,
      treatment: TREATMENT,
      sampleType: SAMPLE_TYPE,
    })
      .then((result) => {
        setData(result)
        setError(null)
      })
      .catch((err: Error) => setError(err.message))
  }, [])

  return (
    <div className="container-fluid py-4">
      <h1 className="h3 mb-1">Response Frequency Analysis</h1>
      <p className="text-muted">
        {CONDITION} subjects treated with {TREATMENT}, {SAMPLE_TYPE} samples
      </p>

      {error && <div className="alert alert-danger">{error}</div>}
      {!error && !data && <p>Loading...</p>}

      {data && (
        <>
          <p className="fst-italic">{data.methodology}</p>
          <BoxplotSections boxplots={data.boxplots} />
        </>
      )}
    </div>
  )
}

function BoxplotSections({ boxplots }: { boxplots: PopulationBoxplot[] }) {
  const significant = boxplots.filter((boxplot) => boxplot.significant)
  const notSignificant = boxplots.filter((boxplot) => !boxplot.significant)

  return (
    <>
      <h2 className="h5">Statistically Significant ({significant.length})</h2>
      {significant.length === 0 ? (
        <p className="text-muted">No cell population reached statistical significance.</p>
      ) : (
        <BoxplotGrid boxplots={significant} />
      )}

      <div className="d-flex align-items-center my-4" role="separator">
        <hr className="flex-grow-1" />
        <span className="mx-3 text-muted small text-uppercase">
          Below: not statistically significant
        </span>
        <hr className="flex-grow-1" />
      </div>

      <h2 className="h5">Not Statistically Significant ({notSignificant.length})</h2>
      {notSignificant.length === 0 ? (
        <p className="text-muted">Every cell population reached statistical significance.</p>
      ) : (
        <BoxplotGrid boxplots={notSignificant} />
      )}
    </>
  )
}

function BoxplotGrid({ boxplots }: { boxplots: PopulationBoxplot[] }) {
  return (
    <div className="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-4 mb-4">
      {boxplots.map((boxplot) => (
        <div className="col" key={boxplot.population}>
          <ResponseBoxplot boxplot={boxplot} />
        </div>
      ))}
    </div>
  )
}
