# Entity-Relationship Diagram

```mermaid
erDiagram
    PROJECT ||--|{ SUBJECT      : "has"
    CONDITION o|--o{ SUBJECT    : "diagnosed with"
    TREATMENT o|--o{ SUBJECT    : "received"
    SUBJECT ||--o{ SAMPLE       : "has"
    CONDITION }o--o{ TREATMENT  : "associated with"

    PROJECT {
        string id PK
        string sample_type
    }
    SUBJECT {
        string id PK
        string project_id FK
        int age
        string sex
        string treatment_response
        string condition_id FK "nullable"
        string treatment_id FK "nullable"
    }
    CONDITION {
        string id PK
        string name
    }
    TREATMENT {
        string id PK
        string name
    }
    SAMPLE {
        string id PK
        string subject_id FK
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
- **Condition ↔ Treatment**: many-to-many, both directions unbounded.

## Notes

- `sample_type` lives on Project, not Sample: in the source CSV it is fully determined by project (each project uses exactly one sample_type across all its samples), and PBMC vs. WB is a lab-processing/protocol choice that's realistically standardized per study site rather than varying per subject or per draw. Storing it on Sample would be a transitive functional dependency (Sample → Subject → Project → sample_type).
- The Condition↔Treatment many-to-many relationship will require a junction table (e.g. `condition_treatment(condition_id, treatment_id)`) in the relational (SQLite) implementation, since it isn't its own conceptual entity here.
