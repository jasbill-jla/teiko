# teiko

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
- `backend/previsualizing/cell_frequencies.py` — queries `Sample`'s 5 count columns and melts each row into 5 output rows.
- `backend/schemas/cell_frequencies.py` — the `CellFrequencyRow` Pydantic response model.
- `backend/api/routes/cell_frequencies.py` — the route handler.
- `backend/main.py` — the FastAPI app; run with `uvicorn backend.main:app`.

## Frontend

`frontend/` — Vite + React + TypeScript. v1 is a single page (`src/pages/Dashboard.tsx`) rendering the cell-frequency summary table (`src/components/CellFrequencyTable.tsx`) from `GET /api/cell-frequencies`.

- **Styling:** plain Bootstrap CSS (`npm install bootstrap`, stylesheet imported once in `main.tsx`), not `react-bootstrap`. v1 has no JS-driven Bootstrap components (dropdowns, modals, tabs) — just `.table`/`.container` classes on regular JSX — and mixing Bootstrap's own DOM-manipulating JS with React's virtual DOM is a real source of bugs, so `react-bootstrap` is worth adding only once an interactive component actually needs it.
- **Types:** `src/types/api.ts` is generated, not hand-written — `python -m backend.export_openapi` writes the backend's OpenAPI schema to `frontend/openapi.json` (gitignored, regenerate on demand), then `npm run gen:types` (`openapi-typescript`) turns it into TS types. Keeps `CellFrequencyRow` in sync with the backend without hand-duplicating it. Required pinning the frontend's TypeScript to `5.9.3`: `openapi-typescript` doesn't yet support TypeScript 6.x (what Vite scaffolds by default), and 5.x is fully capable for this project.
- **Dev vs. serving:** `npm run dev` runs Vite's dev server, which proxies `/api/*` to `http://localhost:8000` (`vite.config.ts`) — so the browser only ever talks to one origin and no CORS setup is needed. For `make dashboard` (Makefile not built yet), the plan is: `npm run build` produces `frontend/dist`, and `backend/main.py` mounts it as static files alongside the API routes (registered first, so `/api/*` always resolves there) — one process, one port, matching the spec's "start the local server" (singular). That mount is skipped if `frontend/dist` doesn't exist, so backend-only contexts like the test suite aren't affected by it.

**Known limitation, not yet addressed:** the real dataset produces 52,500 rows (10,500 samples × 5 populations) with no pagination — verified in a real browser that it does render correctly, but it takes several seconds and produces a very large DOM (~4.8MB of HTML). Fine for v1's scope, but worth paginating or virtualizing before this is a good user experience.

## Testing

`tests/test_cell_frequencies_api.py` has integration tests for `GET /api/cell-frequencies`, using FastAPI's `TestClient` against a schema created with `metadata.create_all()` on a scratch SQLite file (not Alembic, and not the real `teiko.db`) — fast, isolated per test, and independent of whatever's actually loaded. Run with `pytest` from the repo root (needs `backend/requirements.txt` installed; a root-level `conftest.py` makes the `backend` package importable regardless of `pytest`'s own rootdir logic).

`httpx2`, not `httpx`, is what's installed: Starlette's `TestClient` now imports `httpx2` first and only falls back to `httpx` (with a deprecation warning) if `httpx2` isn't installed. No test code imports either package directly — only `fastapi.testclient.TestClient` — so this was a one-line dependency swap.

These are endpoint-level regression tests, not unit tests of the previsualizing/crunching logic — that layer is still expected to change as more of the dashboard gets built, so unit tests for it are deliberately deferred until it settles. `load_data.py` isn't tested either; it's closer to a test fixture (it produces the data everything else is tested against) than code under test.