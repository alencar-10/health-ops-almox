"""update_enums_for_hardening

Revision ID: 8040f32211c5
Revises: a3c4b7a1de41
Create Date: 2026-05-13 13:57:22.594094

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8040f32211c5'
down_revision: Union[str, Sequence[str], None] = 'a3c4b7a1de41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new values to IngestionStatus enum
    # Note: Postgres doesn't allow ADD VALUE inside a transaction block in some versions, 
    # but Alembic usually handles this or we can use op.execute
    op.execute("ALTER TYPE ingestion_status_enum ADD VALUE 'VALIDATING'")
    op.execute("ALTER TYPE ingestion_status_enum ADD VALUE 'CONFIRMING'")
    
    # Add new value to MovementType enum
    op.execute("ALTER TYPE movement_type_enum ADD VALUE 'INITIAL_ENTRY'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
