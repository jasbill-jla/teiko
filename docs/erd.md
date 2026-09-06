# Entity-Relationship Diagram

```mermaid
erDiagram
    PROJECT ||--|{ SUBJECT      : "has"
    CONDITION o|--o{ SUBJECT    : "diagnosed with"
    TREATMENT o|--o{ SUBJECT    : "received"
    SUBJECT ||--o{ SAMPLE       : "has"

    PROJECT {
        int id PK
        string source_id UK "CSV project id"
        string sample_type
    }
    SUBJECT {
        int id PK
        string source_id UK "CSV subject id"
        int project_id FK
        int age
        string sex
        string treatment_response
        int condition_id FK "nullable"
        int treatment_id FK "nullable"
    }
    CONDITION {
        int id PK
        string name UK
    }
    TREATMENT {
        int id PK
        string name UK
    }
    SAMPLE {
        int id PK
        string source_id UK "CSV sample id"
        int subject_id FK
        int time_from_treatment
        int b_cell
        int cd8_t_cell
        int cd4_t_cell
        int nk_cell
        int monocyte
    }
```

## Cardinalities

- **Project ↔ Subject**: 1 project → 1..* subjects; each subject → exactly 1 project.
- **Condition ↔ Subject**: 1 condition → 0..* subjects; each subject → 0..1 condition (nullable FK on Subject).
- **Treatment ↔ Subject**: 1 treatment → 0..* subjects; each subject → 0..1 treatment (nullable FK on Subject).
- **Subject ↔ Sample**: 1 subject → 0..* samples; each sample → exactly 1 subject.

## Notes

- `sample_type` lives on Project, not Sample: in the source CSV it is fully determined by project (each project uses exactly one sample_type across all its samples), and PBMC vs. WB is a lab-processing/protocol choice that's realistically standardized per study site rather than varying per subject or per draw. Storing it on Sample would be a transitive functional dependency (Sample → Subject → Project → sample_type).
- No direct Condition↔Treatment relationship: the CSV shows a full cross-product of the two active treatments against the two non-healthy conditions, with no combination missing — consistent with treatment being assigned independently of condition, not with condition constraining eligible treatments. More importantly, any condition-treatment pairing is already derivable by joining through Subject's own `condition_id`/`treatment_id` FKs; a dedicated `condition_treatment` junction table would just duplicate that with no independent source of truth behind it.
- Every PK is a surrogate auto-incrementing integer (`id`), never the CSV's own identifier. `Project`, `Subject`, and `Sample` each keep their CSV-native identifier as `source_id`, and `Condition`/`Treatment` keep theirs as `name` (they have no id in the CSV, only a label) — both `UNIQUE NOT NULL`, both still get their own index, so looking a row up by its CSV id is exactly as fast as if it were the PK. Every FK in the schema references the target's surrogate integer `id`, never a CSV string. See the README's "Database Schema" section for the full rationale and how this scales.
