"""SQLAlchemy Core table definitions for the teiko schema.

Every table's primary key is a surrogate auto-incrementing integer (`id`).
Condition and Treatment are not separate tables here: both carry a single
attribute (a name) with no evidence of needing more, so they're modeled as
plain nullable string columns on Subject rather than normalized dimension
tables — see the README's "Database Schema" section for the rationale.
"""

from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, Table

metadata = MetaData()

project = Table(
    "project",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("source_id", String, nullable=False, unique=True),
    Column("sample_type", String, nullable=False),
)

subject = Table(
    "subject",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("source_id", String, nullable=False, unique=True),
    Column("project_id", Integer, ForeignKey("project.id"), nullable=False),
    Column("age", Integer, nullable=False),
    Column("sex", String, nullable=False),
    Column("treatment_response", String, nullable=True),
    Column("condition_name", String, nullable=True),
    Column("treatment_name", String, nullable=True),
)

sample = Table(
    "sample",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("source_id", String, nullable=False, unique=True),
    Column("subject_id", Integer, ForeignKey("subject.id"), nullable=False),
    Column("time_from_treatment", Integer, nullable=False),
    Column("b_cell", Integer, nullable=False),
    Column("cd8_t_cell", Integer, nullable=False),
    Column("cd4_t_cell", Integer, nullable=False),
    Column("nk_cell", Integer, nullable=False),
    Column("monocyte", Integer, nullable=False),
)
