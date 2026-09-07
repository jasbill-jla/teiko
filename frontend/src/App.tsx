import { lazy, Suspense, useState } from 'react'
import Dashboard from './pages/Dashboard'
import SamplesExplorer from './pages/SamplesExplorer'

// Lazy-loaded: pulls in plotly.js (~4 MB minified on its own), so keep it
// out of the main bundle and only fetch it when this page is visited.
const ResponseAnalysis = lazy(() => import('./pages/ResponseAnalysis'))

type Page = 'cell-frequencies' | 'response-analysis' | 'samples-explorer'

// Plain state, not a router -- frontend/dist is served via FastAPI's
// StaticFiles(html=True) with no SPA fallback for sub-paths, so a
// path-based route would 404 on direct navigation/refresh. Fine for a
// handful of pages; worth revisiting with a real router + backend fallback
// if this grows much further.
export default function App() {
  const [page, setPage] = useState<Page>('cell-frequencies')

  return (
    <div>
      <nav className="navbar navbar-expand navbar-light bg-light border-bottom px-3">
        <span className="navbar-brand">teiko</span>
        <ul className="navbar-nav">
          <li className="nav-item">
            <button
              type="button"
              className={`nav-link btn btn-link ${page === 'cell-frequencies' ? 'active fw-bold' : ''}`}
              onClick={() => setPage('cell-frequencies')}
            >
              Cell Frequencies
            </button>
          </li>
          <li className="nav-item">
            <button
              type="button"
              className={`nav-link btn btn-link ${page === 'response-analysis' ? 'active fw-bold' : ''}`}
              onClick={() => setPage('response-analysis')}
            >
              Response Analysis
            </button>
          </li>
          <li className="nav-item">
            <button
              type="button"
              className={`nav-link btn btn-link ${page === 'samples-explorer' ? 'active fw-bold' : ''}`}
              onClick={() => setPage('samples-explorer')}
            >
              Sample Explorer
            </button>
          </li>
        </ul>
      </nav>
      {page === 'cell-frequencies' && <Dashboard />}
      {page === 'response-analysis' && (
        <Suspense fallback={<div className="p-3">Loading…</div>}>
          <ResponseAnalysis />
        </Suspense>
      )}
      {page === 'samples-explorer' && <SamplesExplorer />}
    </div>
  )
}
