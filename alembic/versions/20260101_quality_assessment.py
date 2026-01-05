"""Add quality assessment fields

Revision ID: 20260101_quality
Revises: 20260101_catalog
Create Date: 2026-01-01
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '20260101_quality'
down_revision = '20260101_catalog'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add production readiness and quality fields to catalog_projects
    op.add_column(
        'catalog_projects',
        sa.Column('production_readiness', sa.String(20), default='unknown')
    )
    op.add_column(
        'catalog_projects',
        sa.Column('quality_score', sa.Float, nullable=True)
    )
    op.add_column(
        'catalog_projects',
        sa.Column('quality_assessment', sa.JSON, nullable=True)
    )
    op.add_column(
        'catalog_projects',
        sa.Column('quality_indicators', sa.JSON, nullable=True)
    )
    op.add_column(
        'catalog_projects',
        sa.Column('last_quality_check_at', sa.DateTime(timezone=True), nullable=True)
    )

    # Create index for production readiness
    op.create_index(
        'ix_catalog_projects_production_readiness',
        'catalog_projects',
        ['production_readiness']
    )


def downgrade() -> None:
    op.drop_index('ix_catalog_projects_production_readiness', 'catalog_projects')
    op.drop_column('catalog_projects', 'last_quality_check_at')
    op.drop_column('catalog_projects', 'quality_indicators')
    op.drop_column('catalog_projects', 'quality_assessment')
    op.drop_column('catalog_projects', 'quality_score')
    op.drop_column('catalog_projects', 'production_readiness')
