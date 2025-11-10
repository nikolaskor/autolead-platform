"""add emails table and email integration to dealerships

Revision ID: 003
Revises: a957a214e02b
Create Date: 2025-11-10

Adds:
- emails table for storing and processing incoming emails
- email integration fields to dealerships table
- RLS policy for emails table
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = 'a957a214e02b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""

    # Add email integration fields to dealerships table
    op.add_column('dealerships', sa.Column('email_integration_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('dealerships', sa.Column('email_forwarding_address', sa.String(255), nullable=True))
    op.add_column('dealerships', sa.Column('email_integration_settings', postgresql.JSONB(), nullable=True))

    # Create unique index on email_forwarding_address
    op.create_index('idx_dealerships_email_forwarding', 'dealerships', ['email_forwarding_address'], unique=True)

    # Create emails table
    op.create_table(
        'emails',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('dealership_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('message_id', sa.String(255), nullable=False, unique=True),
        sa.Column('from_email', sa.String(255), nullable=False),
        sa.Column('from_name', sa.String(255), nullable=True),
        sa.Column('to_email', sa.String(255), nullable=False),
        sa.Column('subject', sa.String(500), nullable=True),
        sa.Column('body_text', sa.Text(), nullable=True),
        sa.Column('body_html', sa.Text(), nullable=True),
        sa.Column('raw_headers', postgresql.JSONB(), nullable=True),
        sa.Column('attachments', postgresql.JSONB(), nullable=True),
        sa.Column('processing_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('classification', sa.String(50), nullable=True),
        sa.Column('classification_confidence', sa.Float(), nullable=True),
        sa.Column('classification_reasoning', sa.Text(), nullable=True),
        sa.Column('extracted_data', postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['dealership_id'], ['dealerships.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='SET NULL'),
    )

    # Create indexes on emails table
    op.create_index('idx_emails_dealership', 'emails', ['dealership_id'])
    op.create_index('idx_emails_lead', 'emails', ['lead_id'])
    op.create_index('idx_emails_message_id', 'emails', ['message_id'])
    op.create_index('idx_emails_from_email', 'emails', ['from_email'])
    op.create_index('idx_emails_status', 'emails', ['processing_status'])
    op.create_index('idx_emails_classification', 'emails', ['classification'])
    op.create_index('idx_emails_received', 'emails', ['received_at'])
    op.create_index('idx_emails_status_received', 'emails', ['processing_status', sa.text('received_at DESC')])
    op.create_index('idx_emails_dealership_received', 'emails', ['dealership_id', sa.text('received_at DESC')])

    # Enable RLS on emails table
    op.execute("""
        ALTER TABLE emails ENABLE ROW LEVEL SECURITY;

        CREATE POLICY dealership_isolation ON emails
        FOR ALL
        USING (
            dealership_id = NULLIF(current_setting('app.current_dealership_id', true), '')::uuid
        );
    """)


def downgrade() -> None:
    """Downgrade schema."""

    # Drop RLS policy and disable RLS
    op.execute("""
        DROP POLICY IF EXISTS dealership_isolation ON emails;
        ALTER TABLE emails DISABLE ROW LEVEL SECURITY;
    """)

    # Drop indexes
    op.drop_index('idx_emails_dealership_received', table_name='emails')
    op.drop_index('idx_emails_status_received', table_name='emails')
    op.drop_index('idx_emails_received', table_name='emails')
    op.drop_index('idx_emails_classification', table_name='emails')
    op.drop_index('idx_emails_status', table_name='emails')
    op.drop_index('idx_emails_from_email', table_name='emails')
    op.drop_index('idx_emails_message_id', table_name='emails')
    op.drop_index('idx_emails_lead', table_name='emails')
    op.drop_index('idx_emails_dealership', table_name='emails')

    # Drop emails table
    op.drop_table('emails')

    # Drop dealership email integration fields
    op.drop_index('idx_dealerships_email_forwarding', table_name='dealerships')
    op.drop_column('dealerships', 'email_integration_settings')
    op.drop_column('dealerships', 'email_forwarding_address')
    op.drop_column('dealerships', 'email_integration_enabled')
