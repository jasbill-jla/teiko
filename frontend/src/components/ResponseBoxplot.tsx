import type { Data } from 'plotly.js'
import Plot from '../plot'
import type { BoxplotStats, PopulationBoxplot } from '../api/responseFrequencyAnalysis'

interface Props {
  boxplot: PopulationBoxplot
}

const RESPONDER_COLOR = '#0d6efd'
const NON_RESPONDER_COLOR = '#dc3545'

// Plotly's box trace accepts precomputed five-number-summary stats directly
// (q1/median/q3/lowerfence/upperfence) instead of raw points -- exactly what
// the API already gives us -- but @types/plotly.js doesn't declare these
// fields, so this trace is built as a plain object and cast to Data rather
// than fighting the (incomplete) types for a legitimate, documented option.
function toBoxTrace(name: string, color: string, stats: BoxplotStats): Data {
  return {
    type: 'box',
    name,
    x: [name],
    q1: [stats.q1],
    median: [stats.median],
    q3: [stats.q3],
    lowerfence: [stats.minimum],
    upperfence: [stats.maximum],
    marker: { color },
    boxpoints: false,
  } as unknown as Data
}

export default function ResponseBoxplot({ boxplot }: Props) {
  const data: Data[] = [
    toBoxTrace('Responder', RESPONDER_COLOR, boxplot.responder),
    toBoxTrace('Non-Responder', NON_RESPONDER_COLOR, boxplot.non_responder),
  ]

  return (
    <Plot
      data={data}
      layout={{
        title: { text: boxplot.population },
        yaxis: { title: { text: 'Frequency (%)' } },
        showlegend: false,
        height: 320,
        margin: { t: 40, b: 40, l: 50, r: 20 },
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%' }}
      useResizeHandler
    />
  )
}
