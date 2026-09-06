import { useState } from 'react'
import Dashboard from './pages/Dashboard'
import ResponseAnalysis from './pages/ResponseAnalysis'

type Page = 'cell-frequencies' | 'response-analysis'

// Plain state, not a router -- frontend/dist is served via FastAPI's
// StaticFiles(html=True) with no SPA fallback for sub-paths, so a
// path-based route would 404 on direct navigation/refresh. Fine for two
// pages; worth revisiting with a real router + backend fallback if this
// grows.
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
        </ul>
      </nav>
      {page === 'cell-frequencies' ? <Dashboard /> : <ResponseAnalysis />}
    </div>
  )
}
