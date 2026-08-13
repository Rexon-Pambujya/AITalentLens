"""add match summary

Revision ID: 9c62a622627b
Revises: 941a3a9195da
Create Date: 2026-08-13 15:50:14.499473

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c62a622627b'
down_revision: Union[str, None] = '941a3a9195da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # NOTE: autogenerate also proposed dropping the ivfflat/GIN indexes from
    # the prior raw-SQL migration (941a3a9195da) - that's a false positive
    # because those indexes were created with op.execute() rather than
    # declared as SQLAlchemy Index() objects, so autogenerate can't see them
    # in the model metadata. Left out deliberately; dropping them would
    # regress semantic search and full-text search performance.
    op.add_column('matches', sa.Column('summary', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('matches', 'summary')
