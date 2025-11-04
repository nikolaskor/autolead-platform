"""initial schema

Revision ID: 001
Revises: 
Create Date: 2025-11-04

Creates all core tables for the Norvalt platform:
- dealerships: Car dealership organizations
- users: Sales reps, managers, and admins
- leads: Customer inquiries from all sources
- conversations: Message history
- vehicles: Inventory (optional, for future use)
- automation_rules: Follow-up sequences (optional, for future use)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create dealerships table
    op.create_table(
        'dealerships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('clerk_org_id', sa.String(255), nullable=False, unique=True),
        sa.Column('subscription_status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('subscription_tier', sa.String(50), nullable=False, server_default='starter'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_dealerships_clerk_org', 'dealerships', ['clerk_org_id'])
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('dealership_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('clerk_user_id', sa.String(255), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, server_default='sales_rep'),
        sa.Column('notification_preferences', postgresql.JSONB(), nullable=False, server_default='{"sms": true, "email": true}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['dealership_id'], ['dealerships.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_users_dealership', 'users', ['dealership_id'])
    op.create_index('idx_users_clerk', 'users', ['clerk_user_id'])
    
    # Create leads table
    op.create_table(
        'leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('dealership_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('source_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='new'),
        sa.Column('customer_name', sa.String(255), nullable=True),
        sa.Column('customer_email', sa.String(255), nullable=True),
        sa.Column('customer_phone', sa.String(50), nullable=True),
        sa.Column('vehicle_interest', sa.String(255), nullable=True),
        sa.Column('initial_message', sa.Text(), nullable=True),
        sa.Column('lead_score', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('last_contact_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('converted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('first_response_time', sa.Interval(), nullable=True),
        sa.ForeignKeyConstraint(['dealership_id'], ['dealerships.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='SET NULL'),
        sa.CheckConstraint(
            "customer_email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$' OR customer_email IS NULL",
            name='valid_email'
        ),
    )
    op.create_index('idx_leads_dealership', 'leads', ['dealership_id'])
    op.create_index('idx_leads_status', 'leads', ['status'])
    op.create_index('idx_leads_source', 'leads', ['source'])
    op.create_index('idx_leads_created', 'leads', ['created_at'])
    op.create_index('idx_leads_created_desc', 'leads', [sa.text('created_at DESC')])
    op.create_index('idx_leads_email', 'leads', ['customer_email'])
    
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dealership_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('direction', sa.String(20), nullable=False),
        sa.Column('sender', sa.String(255), nullable=True),
        sa.Column('sender_type', sa.String(20), nullable=True),
        sa.Column('message_content', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dealership_id'], ['dealerships.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_conversations_lead', 'conversations', ['lead_id'])
    op.create_index('idx_conversations_created', 'conversations', ['created_at'])
    op.create_index('idx_conversations_created_desc', 'conversations', [sa.text('created_at DESC')])
    
    # Create vehicles table (optional, for future use)
    op.create_table(
        'vehicles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('dealership_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('make', sa.String(100), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('vin', sa.String(17), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='available'),
        sa.Column('price', sa.Numeric(10, 2), nullable=True),
        sa.Column('mileage', sa.Integer(), nullable=True),
        sa.Column('fuel_type', sa.String(50), nullable=True),
        sa.Column('listing_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['dealership_id'], ['dealerships.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_vehicles_dealership', 'vehicles', ['dealership_id'])
    op.create_index('idx_vehicles_status', 'vehicles', ['status'])
    
    # Create automation_rules table (optional, for future use)
    op.create_table(
        'automation_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('dealership_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('trigger_type', sa.String(50), nullable=False),
        sa.Column('trigger_conditions', postgresql.JSONB(), nullable=True),
        sa.Column('actions', postgresql.JSONB(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['dealership_id'], ['dealerships.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_automation_dealership', 'automation_rules', ['dealership_id'])


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('automation_rules')
    op.drop_table('vehicles')
    op.drop_table('conversations')
    op.drop_table('leads')
    op.drop_table('users')
    op.drop_table('dealerships')

