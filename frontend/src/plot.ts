import Plotly from 'plotly.js-dist-min'
import createPlotlyComponent from 'react-plotly.js/factory'

// plotly.js-dist-min (a self-contained, pre-built bundle) instead of the
// plain plotly.js package -- the latter needs a bundler-specific loader for
// its raw GLSL shader imports (webpack-only tooling), which Vite doesn't
// provide out of the box. This is the pattern react-plotly.js's own docs
// recommend for bundlers other than webpack.
export default createPlotlyComponent(Plotly)
