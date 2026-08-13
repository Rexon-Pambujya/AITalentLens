"""add ivfflat vector similarity indexes

Revision ID: 941a3a9195da
Revises: 957b5d0ee13f
Create Date: 2026-08-11 20:12:34.389776

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '941a3a9195da'
down_revision: Union[str, None] = '957b5d0ee13f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ivfflat indexes for approximate-nearest-neighbor cosine search
    # (spec section 12: pgvector semantic matching). `lists` is a coarse
    # starting point tuned for a small/dev-sized corpus - see
    # docs/architecture.md for guidance on retuning as candidate volume
    # grows (rule of thumb: lists ~= rows / 1000, rebuilt periodically).
    op.execute(
        "CREATE INDEX ix_resume_embeddings_embedding_cosine "
        "ON resume_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
    op.execute(
        "CREATE INDEX ix_job_requirements_embedding_cosine "
        "ON job_requirements USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
    op.execute(
        "CREATE INDEX ix_experiences_embedding_cosine "
        "ON experiences USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
    op.execute(
        "CREATE INDEX ix_projects_embedding_cosine "
        "ON projects USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
    op.execute(
        "CREATE INDEX ix_jobs_embedding_cosine "
        "ON jobs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
    # Full-text search support for keyword search over resumes (section 29:
    # hybrid keyword + semantic search).
    op.execute(
        "CREATE INDEX ix_resumes_raw_text_fts ON resumes "
        "USING gin (to_tsvector('english', coalesce(raw_text, '')))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_resumes_raw_text_fts")
    op.execute("DROP INDEX IF EXISTS ix_jobs_embedding_cosine")
    op.execute("DROP INDEX IF EXISTS ix_projects_embedding_cosine")
    op.execute("DROP INDEX IF EXISTS ix_experiences_embedding_cosine")
    op.execute("DROP INDEX IF EXISTS ix_job_requirements_embedding_cosine")
    op.execute("DROP INDEX IF EXISTS ix_resume_embeddings_embedding_cosine")
