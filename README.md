# teiko

## Database Schema

Implemented as three tables: `Project`, `Subject`, `Sample` — see `backend/models/tables.py` for the SQLAlchemy Core definitions.

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