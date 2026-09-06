# teiko

## Database Schema

Full entity-relationship diagram: [`docs/erd.md`](docs/erd.md).

**Entities:** `Project`, `Subject`, `Condition`, `Treatment`, `Sample` — the CSV's project/subject/condition/treatment/sample columns normalized into separate tables (a subject belongs to one project and has at most one condition and one treatment; a subject has many samples) rather than kept as one flat, repeating table.

### Surrogate integer primary keys, CSV identifiers preserved as unique attributes

Every table's primary key is a surrogate auto-incrementing integer (`id`), not the identifier that appears in the CSV. The CSV-native identifier is kept as a separate, `UNIQUE NOT NULL` column instead: `source_id` on `Project`/`Subject`/`Sample`, or `name` on `Condition`/`Treatment` (which have no id in the CSV, only a label). Every foreign key in the schema references the target table's surrogate integer `id` — never a CSV string.

**Why:**
- **Consistency.** One PK/FK typing convention across every table and every join, instead of string keys on some tables and synthetic keys on others.
- **Decoupling.** Internal referential integrity doesn't depend on the source system's identifiers staying unique, stable, or well-formed forever. If a `Project.source_id` ever needed correcting upstream, no foreign key anywhere in the schema would need to change.
- **No functional loss.** The `UNIQUE` constraint on `source_id`/`name` still gets its own index, so "look up the row for this CSV id" is exactly as fast as if that column were the primary key.
- **The performance argument holds across engines, though the mechanism differs per engine:**
  - *SQLite:* `INTEGER PRIMARY KEY` is an alias for the table's internal rowid — there's no separate B-tree for the PK at all. A `TEXT` PK requires its own tree with variable-length keys.
  - *PostgreSQL:* no rowid-aliasing trick, but integer comparison and hashing are fixed-width machine operations, while text comparison under a locale-aware collation (the default in most installs) and variable-length storage cost more per comparison, per hash, and per index page.
  - *MySQL/InnoDB:* tables are clustered by the PK, and every secondary index stores the PK value as its row pointer — so a wide string PK bloats *every* secondary index on the table, not just the PK's own. Small sequential integers are also the best case for InnoDB's clustered inserts (append-only, no page splits), unlike a non-sequential key such as a UUID.
- The design costs nothing today — same number of columns, one `UNIQUE` index in place of a PK index — but avoids a compounding cost later.

### Scaling to hundreds of projects, thousands of samples, and ad hoc analytics

At the scale named above (low hundreds of `Project` rows, low thousands of `Sample` rows), raw point-lookup latency wouldn't meaningfully differ between a string-keyed and integer-keyed design in any of these engines — the tables are small enough to live entirely in buffer cache. The design matters more for the *shape* of the workload than the *size* of the data:

- "Various types of analytics" implies joins, group-bys, and aggregations across `Project` × `Subject` × `Condition` × `Treatment` × `Sample` — scanning, hashing, and comparing keys across a large fraction of a table repeatedly, not single-row point lookups. That's exactly where a wider, collation-aware, variable-length key pays its cost once per row touched rather than once per query.
- As sample volume grows past today's thousands, row width and index size scale with it. Integer foreign keys keep `Sample` and `Subject` rows narrow and every index on them compact, which directly affects how much of the working set stays in memory versus spilling to disk.
- The design also isolates future growth in dimensionality: adding new per-subject or per-sample attributes, new dimension tables (e.g. a study site or lab batch), or new cross-cutting analytics doesn't require touching existing foreign key types or migrating string keys — every join in the schema is already a plain integer equality.