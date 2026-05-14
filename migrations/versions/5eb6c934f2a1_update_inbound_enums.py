"""update_inbound_enums

Revision ID: 5eb6c934f2a1
Revises: ab2f91267393
Create Date: 2026-05-13 19:08:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5eb6c934f2a1'
down_revision = 'ab2f91267393'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Postgres ENUMs cannot be easily altered in a transaction.
    # We use COMMIT to exit the transaction for these commands.
    op.execute("COMMIT")
    
    # InboundType
    for val in ['TRANSFER']:
        op.execute(f"ALTER TYPE inboundtype ADD VALUE IF NOT EXISTS '{val}'")
    
    # InboundStatus
    for val in ['NEW', 'MATCHED', 'CONFIRMED', 'POSTED', 'ERP_SYNCED', 'DIVERGENT']:
        op.execute(f"ALTER TYPE inboundstatus ADD VALUE IF NOT EXISTS '{val}'")

def downgrade() -> None:
    pass # Removing enum values is complex in Postgres
