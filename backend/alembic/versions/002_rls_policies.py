"""rls policies

Revision ID: 002
Revises: 001
Create Date: 2025-11-04

Enables Row-Level Security (RLS) on multi-tenant tables and creates policies
to enforce data isolation between dealerships.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable Row-Level Security on multi-tenant tables
    op.execute("ALTER TABLE leads ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE conversations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE vehicles ENABLE ROW LEVEL SECURITY")
    
    # Create RLS policy for leads table
    # Users can only access leads from their dealership
    # Fail-closed: returns no rows if app.current_dealership_id is unset
    op.execute("""
        CREATE POLICY dealership_isolation_leads ON leads
        FOR ALL
        USING (
            dealership_id = NULLIF(current_setting('app.current_dealership_id', true), '')::uuid
        )
    """)
    
    # Create RLS policy for conversations table
    # Users can only access conversations from their dealership
    # Fail-closed: returns no rows if app.current_dealership_id is unset
    op.execute("""
        CREATE POLICY dealership_isolation_conversations ON conversations
        FOR ALL
        USING (
            dealership_id = NULLIF(current_setting('app.current_dealership_id', true), '')::uuid
        )
    """)
    
    # Create RLS policy for vehicles table
    # Users can only access vehicles from their dealership
    # Fail-closed: returns no rows if app.current_dealership_id is unset
    op.execute("""
        CREATE POLICY dealership_isolation_vehicles ON vehicles
        FOR ALL
        USING (
            dealership_id = NULLIF(current_setting('app.current_dealership_id', true), '')::uuid
        )
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS dealership_isolation_leads ON leads")
    op.execute("DROP POLICY IF EXISTS dealership_isolation_conversations ON conversations")
    op.execute("DROP POLICY IF EXISTS dealership_isolation_vehicles ON vehicles")
    
    # Disable Row-Level Security
    op.execute("ALTER TABLE leads DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE conversations DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE vehicles DISABLE ROW LEVEL SECURITY")

