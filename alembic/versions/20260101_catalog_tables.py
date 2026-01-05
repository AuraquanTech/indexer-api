"""Add catalog tables

Revision ID: 20260101_catalog
Revises:
Create Date: 2026-01-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = '20260101_catalog'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create catalog_projects table
    op.create_table(
        'catalog_projects',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id'), nullable=False),

        # Core info
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('path', sa.Text, nullable=False),

        # Classification
        sa.Column('type', sa.String(20), default='other'),
        sa.Column('lifecycle', sa.String(20), default='active'),

        # Tech stack (JSON arrays)
        sa.Column('languages', sa.JSON, default=list),
        sa.Column('frameworks', sa.JSON, default=list),
        sa.Column('tags', sa.JSON, default=list),

        # Repository info
        sa.Column('repository_url', sa.String(500), nullable=True),
        sa.Column('default_branch', sa.String(100), nullable=True),
        sa.Column('license_spdx', sa.String(50), nullable=True),

        # GitHub metrics
        sa.Column('github_stars', sa.Integer, nullable=True),
        sa.Column('github_forks', sa.Integer, nullable=True),
        sa.Column('github_watchers', sa.Integer, nullable=True),
        sa.Column('open_issues', sa.Integer, nullable=True),
        sa.Column('open_prs', sa.Integer, nullable=True),

        # Code metrics
        sa.Column('loc_total', sa.BigInteger, nullable=True),
        sa.Column('file_count', sa.Integer, nullable=True),
        sa.Column('avg_complexity', sa.Float, nullable=True),
        sa.Column('test_coverage', sa.Float, nullable=True),

        # Health score (0-100)
        sa.Column('health_score', sa.Float, nullable=True),

        # Sync tracking
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_commit_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_commit_sha', sa.String(40), nullable=True),

        # Extra metadata
        sa.Column('extra_metadata', sa.JSON, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create unique constraints
    op.create_unique_constraint(
        'uq_catalog_org_name',
        'catalog_projects',
        ['organization_id', 'name']
    )
    op.create_unique_constraint(
        'uq_catalog_org_path',
        'catalog_projects',
        ['organization_id', 'path']
    )

    # Create indexes
    op.create_index('ix_catalog_projects_lifecycle', 'catalog_projects', ['lifecycle'])
    op.create_index('ix_catalog_projects_type', 'catalog_projects', ['type'])
    op.create_index('ix_catalog_projects_org', 'catalog_projects', ['organization_id'])

    # Create catalog_jobs table
    op.create_table(
        'catalog_jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('catalog_projects.id'), nullable=True),

        sa.Column('job_type', sa.String(30), nullable=False),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('priority', sa.Integer, default=5),

        # Execution tracking
        sa.Column('attempts', sa.Integer, default=0),
        sa.Column('max_attempts', sa.Integer, default=3),
        sa.Column('run_after', sa.DateTime(timezone=True), server_default=sa.func.now()),

        # Results
        sa.Column('result', sa.JSON, nullable=True),
        sa.Column('last_error', sa.JSON, nullable=True),

        # Timing
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_catalog_jobs_status', 'catalog_jobs', ['status'])
    op.create_index('ix_catalog_jobs_run_after', 'catalog_jobs', ['run_after'])

    # Create catalog_job_runs table
    op.create_table(
        'catalog_job_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('job_id', sa.String(36), sa.ForeignKey('catalog_jobs.id', ondelete='CASCADE'), nullable=False),

        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),

        sa.Column('result', sa.JSON, nullable=True),
        sa.Column('error', sa.JSON, nullable=True),
    )

    op.create_index('ix_catalog_job_runs_job', 'catalog_job_runs', ['job_id'])

    # Create FTS5 virtual table for full-text search (SQLite only)
    # This creates an external content FTS5 table that references catalog_projects
    op.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS catalog_projects_fts USING fts5(
            name,
            title,
            description,
            path,
            content='catalog_projects',
            content_rowid='rowid'
        )
    """)

    # Create triggers to keep FTS in sync
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS catalog_projects_ai AFTER INSERT ON catalog_projects BEGIN
            INSERT INTO catalog_projects_fts(rowid, name, title, description, path)
            VALUES (new.rowid, new.name, new.title, new.description, new.path);
        END
    """)

    op.execute("""
        CREATE TRIGGER IF NOT EXISTS catalog_projects_ad AFTER DELETE ON catalog_projects BEGIN
            INSERT INTO catalog_projects_fts(catalog_projects_fts, rowid, name, title, description, path)
            VALUES ('delete', old.rowid, old.name, old.title, old.description, old.path);
        END
    """)

    op.execute("""
        CREATE TRIGGER IF NOT EXISTS catalog_projects_au AFTER UPDATE ON catalog_projects BEGIN
            INSERT INTO catalog_projects_fts(catalog_projects_fts, rowid, name, title, description, path)
            VALUES ('delete', old.rowid, old.name, old.title, old.description, old.path);
            INSERT INTO catalog_projects_fts(rowid, name, title, description, path)
            VALUES (new.rowid, new.name, new.title, new.description, new.path);
        END
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS catalog_projects_au")
    op.execute("DROP TRIGGER IF EXISTS catalog_projects_ad")
    op.execute("DROP TRIGGER IF EXISTS catalog_projects_ai")

    # Drop FTS table
    op.execute("DROP TABLE IF EXISTS catalog_projects_fts")

    # Drop tables
    op.drop_table('catalog_job_runs')
    op.drop_table('catalog_jobs')
    op.drop_table('catalog_projects')
