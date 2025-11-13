"""add facebook integration to dealerships

Revision ID: 004
Revises: 003
Create Date: 2025-11-13

Adds:
- facebook_integration_enabled field to dealerships table
- facebook_page_tokens (JSONB) field for storing encrypted Page Access Tokens
- facebook_integration_settings (JSONB) for future configuration
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema - add Facebook integration fields."""

    # Add Facebook integration fields to dealerships table
    op.add_column(
        'dealerships',
        sa.Column('facebook_integration_enabled', sa.Boolean(), nullable=False, server_default='false')
    )

    op.add_column(
        'dealerships',
        sa.Column('facebook_page_tokens', postgresql.JSONB(), nullable=True,
                  comment='Encrypted Page Access Tokens - format: {"page_id": "encrypted_token"}')
    )

    op.add_column(
        'dealerships',
        sa.Column('facebook_integration_settings', postgresql.JSONB(), nullable=True,
                  comment='Facebook integration settings like app_id, webhook_url, etc.')
    )


def downgrade() -> None:
    """Downgrade schema - remove Facebook integration fields."""

    op.drop_column('dealerships', 'facebook_integration_settings')
    op.drop_column('dealerships', 'facebook_page_tokens')
    op.drop_column('dealerships', 'facebook_integration_enabled')
