"""Install pg_idkit extension for UUIDv7 support.

Revision ID: 001_pg_idkit_extension
Revises:
Create Date: 2025-12-06

This migration installs the pg_idkit PostgreSQL extension which provides
UUIDv7 generation capability. The extension is installed with IF NOT EXISTS
to be idempotent.

Note: pg_idkit must be available in the PostgreSQL server. For local dev,
install via: CREATE EXTENSION pg_idkit; or use a Docker image with it pre-installed.
For managed databases (RDS, Cloud SQL), check extension availability.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "001_pg_idkit_extension"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Install pg_idkit extension for UUIDv7 support."""
    # pg_idkit provides idkit_uuidv7_generate() function
    # Using IF NOT EXISTS makes this migration idempotent
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_idkit")


def downgrade() -> None:
    """Remove pg_idkit extension."""
    op.execute("DROP EXTENSION IF EXISTS pg_idkit")
