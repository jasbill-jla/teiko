# teiko

## Running

Three Makefile targets, run in order, from the repo root:

- `make setup` — creates a Python venv (`.venv`) and installs `backend/requirements.txt`; installs the frontend's npm packages.
- `make pipeline` — runs the entire data pipeline end-to-end: applies the Alembic migrations and loads `data/cell-count.csv` into `teiko.db`. Safe to re-run.
- `make dashboard` — builds the frontend (`frontend/dist`) and starts a single server (`uvicorn backend.main:app`) on `http://0.0.0.0:8000` that serves both the API and the built dashboard from one port. Runs in the foreground; in a Codespace, forward/open port 8000 to view it.

In GitHub Codespaces: open the repo in a Codespace, then run the three commands above in the terminal. Codespaces auto-forwards port 8000 once `make dashboard` is running.

## Database Schema

Implemented as three tables: `Project`, `Subject`, `Sample` — see `backend/models/tables.py` for the SQLAlchemy Core definitions.

Schema changes are managed with [Alembic](https://alembic.sqlalchemy.org/) migrations (`backend/alembic/`, config at `alembic.ini`), not by calling `create_all()` directly — the pipeline's DB setup runs `alembic upgrade head` under the hood. The initial migration (`backend/alembic/versions/0b3fbdd2ef15_create_project_subject_sample_tables.py`) creates exactly this schema; any future schema change is a new migration on top of it rather than an edit to the models with no record of how to get an existing database there.

### Loading the data

`load_data.py`, at the repo root, initializes the database and loads every row of `data/cell-count.csv` (the committed input file). It calls `init_db()` first (running migrations, so it never reimplements schema creation), then loads the CSV — the two are separate concerns that compose rather than conflict: migrations own structure, this script owns data. It's safe to run more than once: each run wipes the three tables and reloads from the CSV, rather than appending or erroring on the `source_id` uniqueness constraints.

The generated SQLite file lands at `teiko.db` in the repo root, per the spec's requirement that the database file live there.

Two CSV values are normalized to `NULL` rather than stored literally, matching the nullable `condition_name`/`treatment_name`/`treatment_response` columns on `Subject`: a `condition` of `"healthy"` means no diagnosed condition, and a `treatment` of `"none"` means no treatment was given — both are the absence of that attribute, not a named category. `response` is already blank in the CSV for these same untreated/healthy subjects.

For the entity analysis behind this schema, see [`docs/erd.md`](docs/erd.md). That diagram documents `Condition` and `Treatment` as their own entities because that's the honest shape of the domain (a subject has at most one condition and one treatment, each identified by a name) — but the ERD is the analysis that led to this schema, not a description of it, and was never intended to be isomorphic with the implementation. The database schema below intentionally departs from it in one place, explained below.

### Surrogate integer primary keys, CSV identifiers preserved as unique attributes

Every table's primary key is a surrogate auto-incrementing integer (`id`), not the identifier that appears in the CSV. The CSV-native identifier is kept as a separate `source_id` column instead, `UNIQUE NOT NULL`. Every foreign key in the schema references the target table's surrogate integer `id` — never a CSV string.

**Why:**
- **Consistency.** One PK/FK typing convention across every table and every join, instead of string keys on some tables and synthetic keys on others.
- **Decoupling.** Internal referential integrity doesn't depend on the source system's identifiers staying unique, stable, or well-formed forever. If a `Project.source_id` ever needed correcting upstream, no foreign key anywhere in the schema would need to change.
- **No functional loss.** The `UNIQUE` constraint on `source_id` still gets its own index, so "look up the row for this CSV id" is exactly as fast as if that column were the primary key.
- **The performance argument holds across engines, though the mechanism differs per engine:**
  - *SQLite:* `INTEGER PRIMARY KEY` is an alias for the table's internal rowid — there's no separate B-tree for the PK at all. A `TEXT` PK requires its own tree with variable-length keys.
  - *PostgreSQL:* no rowid-aliasing trick, but integer comparison and hashing are fixed-width machine operations, while text comparison under a locale-aware collation (the default in most installs) and variable-length storage cost more per comparison, per hash, and per index page.
  - *MySQL/InnoDB:* tables are clustered by the PK, and every secondary index stores the PK value as its row pointer — so a wide string PK bloats *every* secondary index on the table, not just the PK's own. Small sequential integers are also the best case for InnoDB's clustered inserts (append-only, no page splits), unlike a non-sequential key such as a UUID.
- The design costs nothing today — same number of columns, one `UNIQUE` index in place of a PK index — but avoids a compounding cost later.

### Condition and Treatment are columns on Subject, not tables

The ERD models `Condition` and `Treatment` as separate entities. The implemented schema instead stores them as plain nullable columns on `Subject` — `condition_name`, `treatment_name` — with no `Condition`/`Treatment` tables at all.

- Both entities carry exactly one attribute (a name) and a 0..1-per-subject cardinality with no fan-out — that's a plain attribute of Subject, not a relationship that needs its own table.
- Nothing in the CSV or the requirements suggests either will ever carry additional attributes. `Subject.treatment_response` is already modeled the same way — a bare string column for a small, fixed categorical value — so this keeps Subject's three categorical fields consistent with each other rather than treating two of them differently from the third for reasons the data doesn't support.
- What this avoids is query and code complexity, not runtime cost: a join from Subject to a two-attribute dimension table on an indexed integer key is already the cheapest possible join shape, so removing it isn't a performance win. It does mean every query or previsualizing step that filters or groups by condition or treatment does so directly on a Subject column instead of via a join, and there are two fewer tables and relationships to keep in sync with the pipeline's ingest step.
- This is a reversible bet, not a dead end: if a real requirement ever needs per-condition or per-treatment attributes, that's a straightforward migration — extract the distinct values into a new table, backfill, replace the string column with a foreign key — not a redesign of `Project`, `Subject`, or `Sample`.

### Scaling to hundreds of projects, thousands of samples, and ad hoc analytics

At the scale named above (low hundreds of `Project` rows, low thousands of `Sample` rows), raw point-lookup latency wouldn't meaningfully differ between a string-keyed and integer-keyed design in any of these engines — the tables are small enough to live entirely in buffer cache. The design matters more for the *shape* of the workload than the *size* of the data:

- "Various types of analytics" implies joins, group-bys, and aggregations across `Project` × `Subject` × `Sample` — scanning, hashing, and comparing keys across a large fraction of a table repeatedly, not single-row point lookups. That's exactly where a wider, collation-aware, variable-length key pays its cost once per row touched rather than once per query. Grouping or filtering by condition/treatment specifically is cheaper still, since those are native `Subject` columns rather than a joined table at all.
- As sample volume grows past today's thousands, row width and index size scale with it. Integer foreign keys keep `Sample` and `Subject` rows narrow and every index on them compact, which directly affects how much of the working set stays in memory versus spilling to disk.
- The design also isolates future growth in dimensionality: adding new per-subject or per-sample attributes, new dimension tables (e.g. a study site or lab batch), or new cross-cutting analytics doesn't require touching existing foreign key types or migrating string keys — every join in the schema is already a plain integer equality.

## API

**`GET /api/cell-frequencies`** — no parameters. Returns the relative-frequency summary table: one JSON object per (sample, cell population) pair, 5 populations × every sample:

```json
{
  "sample": "sample00000",
  "population": "b_cell",
  "count": 10908,
  "total_count": 93214,
  "percentage": 11.702104834037806
}
```

`percentage` is `count` as a percent of `total_count` (0-100, not a 0-1 ratio). Computed at request time, not by the offline pipeline — it's cheap arithmetic over `Sample` rows that already exist, not the kind of aggregation worth pre-crunching:
- `backend/crunching/cell_frequencies.py` — queries `Sample`'s 5 count columns and melts each row into 5 output rows; this is the population frequency dataset itself, so other analyses that need it (not just this endpoint) call this same function rather than re-querying `Sample`.
- `backend/schemas/cell_frequencies.py` — the `CellFrequencyRow` Pydantic response model.
- `backend/api/routes/cell_frequencies.py` — the route handler.
- `backend/main.py` — the FastAPI app; run with `uvicorn backend.main:app`.

**`GET /api/response-frequency-analysis`** — query params `condition`, `treatment`, `sample_type` (all required strings, e.g. `melanoma`/`miraclib`/`PBMC`), `median_threshold` (required float). Compares responding vs. non-responding subjects with the given condition/treatment, restricted to samples of the given type:

```json
{
  "medians": [
    {"population": "b_cell", "responder_median": 9.43, "non_responder_median": 9.79}
  ],
  "boxplots": [
    {
      "population": "b_cell",
      "responder": {"minimum": 2.37, "q1": 7.30, "median": 9.43, "q3": 11.87, "maximum": 25.12},
      "non_responder": {"minimum": 2.06, "q1": 7.81, "median": 9.79, "q3": 11.82, "maximum": 21.30}
    }
  ]
}
```

`medians` always lists every population with data for both response groups (5 entries, in a matched real dataset). `boxplots` — one two-sided five-number summary per population, for drawing a pair of box-and-whisker plots — is filtered to only the populations whose `|responder_median - non_responder_median|` is **strictly greater than** `median_threshold`; a threshold no population clears returns `"boxplots": []`, and an unmatched condition/treatment/sample_type returns both lists empty rather than erroring. Built from four crunching functions designed to compose (`backend/crunching/response_frequencies.py`'s `get_response_frequencies`/`get_response_median_frequencies`/`get_significant_response_populations`, plus `backend/crunching/response_frequency_stats.py`'s `compute_boxplot_stats`), so the raw per-sample data is queried once and reused for both the medians and the boxplot stats — see `backend/previsualizing/response_frequency_analysis.py` for how they're assembled into this response shape.

"Significant" here is a plain absolute median difference in percentage points, not a statistical test — considered twice and deliberately kept simple both times:
- **Mann-Whitney U** (the natural non-parametric test for comparing two continuous distributions, and the closest counterpart to a median/quartile-based approach) was the first option raised. It has a real applicability problem in this data, not just an implementation cost: melanoma+miraclib+PBMC is 656 distinct subjects across 1,968 samples, so per-sample data points aren't independent (repeated measures per subject) — a rank-sum test would need collapsing to one value per subject first, plus a multiple-comparisons correction across the 5 populations tested at once, or the p-values wouldn't mean what they'd look like they mean.
- **Chi-squared** was raised next, and doesn't fit at all: it tests association between *categorical* variables via a contingency table of counts, but a population's relative frequency here is a continuous measurement — using chi-squared would mean first binning that continuous value into categories, an arbitrary choice that throws away information the current approach doesn't need to discard.

Final call: keep the plain magnitude threshold. Not because Mann-Whitney U is wrong, but because applying it without genuinely understanding the independence-assumption and multiple-comparisons issues above would mean leaning on an explanation supplied after the fact rather than the analysis actually being the author's own — a judgment about ownership of the work, not a technical one.

## Frontend

`frontend/` — Vite + React + TypeScript, two pages: `src/pages/Dashboard.tsx` (the cell-frequency summary table, `src/components/CellFrequencyTable.tsx`, from `GET /api/cell-frequencies`) and `src/pages/ResponseAnalysis.tsx` (responder vs. non-responder analysis for melanoma/miraclib/PBMC, from `GET /api/response-frequency-analysis`).

- **Navigation:** `App.tsx` switches between the two pages with plain `useState`, not a router. `frontend/dist` is served via FastAPI's `StaticFiles(html=True)` with no SPA fallback for sub-paths, so a real path-based route (e.g. `/response-analysis`) would 404 on direct navigation or a refresh unless the backend also grew a catch-all route to `index.html`. Two pages doesn't justify that yet — worth reconsidering (a router, plus the backend fallback) if more pages get added.
- **Response Analysis page:** fixed to `condition=melanoma`, `treatment=miraclib`, `sample_type=PBMC` (no controls for these, per the spec); the only input is the median-difference threshold (percentage points, default `0.35`), applied on an explicit "Refresh" click rather than on every keystroke. Renders one compound box-and-whisker chart per `boxplots` entry (`src/components/ResponseBoxplot.tsx`, one per qualifying population, responder and non-responder boxes on the same y-axis so they're directly comparable), then `src/components/MedianFrequencyTable.tsx` listing every population's responder/non-responder median and their difference (from `medians`, unaffected by the threshold). With the real data, the largest median difference among the 5 populations is well under 1 percentage point (`cd4_t_cell` at ~0.56, the biggest of the five) — `0.35` was chosen empirically against that so the default view isn't empty (it clears `b_cell` and `cd4_t_cell`), not because it means anything statistically. This is still a plain magnitude cutoff, not a statistical test — see the API section below for why that was a deliberate choice, reconsidered and kept after discussion.
- **Charting:** `react-plotly.js`, per the original plan — Plotly's box trace accepts precomputed five-number-summary stats (`q1`/`median`/`q3`/`lowerfence`/`upperfence`) directly instead of raw points, matching what the API already returns, so the frontend does no statistical computation of its own. Imports `plotly.js-dist-min` (a self-contained prebuilt bundle) rather than the plain `plotly.js` package, which needs webpack-specific loader config for its GLSL shader imports that Vite doesn't provide — `src/plot.ts` wires it up via `react-plotly.js/factory`. `@types/plotly.js` doesn't declare the precomputed-stats box trace fields, so `ResponseBoxplot.tsx` builds that trace as a plain object cast to `Data` rather than fighting the (incomplete) types for a legitimate, documented Plotly option.
- **Known cost, not yet addressed:** `plotly.js-dist-min` alone is most of a ~4.3MB JS bundle (~1.3MB gzipped) — the full library, not a subset. Fine for now; a partial Plotly build (e.g. `plotly.js-cartesian-dist-min`, which still includes box traces) would cut this substantially if bundle size becomes a real problem.
- **Styling:** plain Bootstrap CSS (`npm install bootstrap`, stylesheet imported once in `main.tsx`), not `react-bootstrap`. v1 has no JS-driven Bootstrap components (dropdowns, modals, tabs) — just `.table`/`.container` classes on regular JSX — and mixing Bootstrap's own DOM-manipulating JS with React's virtual DOM is a real source of bugs, so `react-bootstrap` is worth adding only once an interactive component actually needs it.
- **Types:** `src/types/api.ts` is generated, not hand-written — `python -m backend.export_openapi` writes the backend's OpenAPI schema to `frontend/openapi.json` (gitignored, regenerate on demand), then `npm run gen:types` (`openapi-typescript`) turns it into TS types. Keeps `CellFrequencyRow` in sync with the backend without hand-duplicating it. Required pinning the frontend's TypeScript to `5.9.3`: `openapi-typescript` doesn't yet support TypeScript 6.x (what Vite scaffolds by default), and 5.x is fully capable for this project.
- **Dev vs. serving:** `npm run dev` runs Vite's dev server, which proxies `/api/*` to `http://localhost:8000` (`vite.config.ts`) — so the browser only ever talks to one origin and no CORS setup is needed. `make dashboard` runs `npm run build` to produce `frontend/dist`, and `backend/main.py` mounts it as static files alongside the API routes (registered first, so `/api/*` always resolves there) — one process, one port, matching the spec's "start the local server" (singular). That mount is skipped if `frontend/dist` doesn't exist, so backend-only contexts like the test suite aren't affected by it.
- **Responsive table:** below the `sm` breakpoint (576px, phone-sized), `CellFrequencyTable` drops the Count and Total Count columns and adds a per-row `▸`/`▾` toggle (in the Sample cell) that expands a detail line showing both values. This is CSS-only gating (Bootstrap's `d-none`/`d-sm-table-cell`/`d-sm-none` utilities) — the toggle and detail row exist in the DOM at every width, they're just hidden above `sm`, so there's no JS media-query listener to keep in sync with a resize.

**Performance:** the real dataset produces 52,500 rows (10,500 samples × 5 populations). `backend/main.py` gzips the `/api/cell-frequencies` response (`GZipMiddleware`), which cuts the ~6MB JSON payload to ~1MB over the wire — worth doing regardless of dataset size, since in Codespaces that request crosses the port-forwarding tunnel, a real network hop, not loopback. Fetching all 52,500 rows up front (rather than paging the API) is still deliberate: at this scale it's one ~1s gzipped request, and `CellFrequencyTable` paginates client-side (100 rows/page) so only one page's worth of `<tr>`s is ever mounted in the DOM — the render cost that dominated before pagination. Server-side pagination would be the next step if either the dataset or the payload grew enough that shipping every row up front stopped being cheap.

## Testing

### Backend

`tests/test_cell_frequencies_api.py` has integration tests for `GET /api/cell-frequencies`, using FastAPI's `TestClient` against a schema created with `metadata.create_all()` on a scratch SQLite file (not Alembic, and not the real `teiko.db`) — fast, isolated per test, and independent of whatever's actually loaded. Run with `pytest` from the repo root (needs `backend/requirements.txt` installed; a root-level `conftest.py` makes the `backend` package importable regardless of `pytest`'s own rootdir logic).

`httpx2`, not `httpx`, is what's installed: Starlette's `TestClient` now imports `httpx2` first and only falls back to `httpx` (with a deprecation warning) if `httpx2` isn't installed. No test code imports either package directly — only `fastapi.testclient.TestClient` — so this was a one-line dependency swap.

These are endpoint-level regression tests, not unit tests of the previsualizing/crunching logic — that layer is still expected to change as more of the dashboard gets built, so unit tests for it are deliberately deferred until it settles. `load_data.py` isn't tested either; it's closer to a test fixture (it produces the data everything else is tested against) than code under test.

`test_multiple_samples_are_independent_and_ordered` and `test_samples_ordered_by_insertion_not_by_source_id` pin down the ordering `get_cell_frequencies` produces (`Sample.id` — insertion order — then the fixed `POPULATIONS` tuple order per sample): the second test specifically inserts samples whose `source_id` sorts the *opposite* of insertion order, so it can't pass by accident of the two orderings coinciding. The frontend's default (unsorted) table order depends on this staying true, since it does no client-side re-sort of its own.

### Frontend

`frontend/src/components/CellFrequencyTable.test.tsx` covers the table's client-side behavior with Vitest + React Testing Library: the default (unsorted) render preserves the order the `rows` prop was given in; the population filter narrows to matching rows and its options are derived from the data; clicking the "Percentage" header sorts ascending then descending; and "Reset Sort" appears only while a sort is active, and restores the original order when clicked. Run with `npm run test` (or `npm test`) from `frontend/`.

`frontend/src/setupTests.ts` calls `cleanup()` after each test — required because `vite.config.ts`'s `test` block doesn't set `globals: true` (kept off deliberately, so test files import `describe`/`it`/`expect` from `vitest` explicitly rather than relying on ambient globals), and React Testing Library's automatic cleanup only self-registers when it detects those globals. Without it, each `render()` call in a later test would stack on top of the previous test's DOM instead of starting fresh.