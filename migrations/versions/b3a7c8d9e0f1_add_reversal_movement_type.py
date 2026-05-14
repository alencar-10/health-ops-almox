"""add_reversal_movement_type

Revision ID: b3a7c8d9e0f1
Revises: 5eb6c934f2a1
Create Date: 2026-05-13 19:14:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b3a7c8d9e0f1'
down_revision = '5eb6c934f2a1'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("COMMIT")
    op.execute("ALTER TYPE movement_type_enum ADD VALUE IF NOT EXISTS 'REVERSAL'")

def downgrade() -> None:
    pass
