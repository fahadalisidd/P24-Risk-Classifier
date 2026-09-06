"""Initial schema migration for P24 Risk Classifier.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. risk_rules
    op.create_table(
        'risk_rules',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('rule_id', sa.String(length=64), nullable=False, unique=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('conditions', sa.JSON(), nullable=False),
        sa.Column('result_action', sa.String(length=32), nullable=False),
        sa.Column('target_category', sa.Integer(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_risk_rules_rule_id', 'risk_rules', ['rule_id'])

    # 2. policy_overrides
    op.create_table(
        'policy_overrides',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('conditions', sa.JSON(), nullable=False),
        sa.Column('forced_category', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 3. policy_pins
    op.create_table(
        'policy_pins',
        sa.Column('pin_id', sa.String(length=64), primary_key=True),
        sa.Column('policy_id', sa.String(length=64), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('review_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
    )
    op.create_index('ix_policy_pins_policy_id', 'policy_pins', ['policy_id'])
    op.create_index('ix_policy_pins_review_date', 'policy_pins', ['review_date'])
    op.create_index('ix_policy_pins_expires_at', 'policy_pins', ['expires_at'])

    # 4. risk_evaluations
    op.create_table(
        'risk_evaluations',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('operation_id', sa.String(length=128), nullable=False),
        sa.Column('operation_type', sa.String(length=64), nullable=False),
        sa.Column('scope', sa.String(length=32), nullable=False),
        sa.Column('reversibility', sa.String(length=32), nullable=False),
        sa.Column('persistence', sa.String(length=32), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('risk_score', sa.Integer(), nullable=False),
        sa.Column('base_category', sa.Integer(), nullable=False),
        sa.Column('rubric_category', sa.Integer(), nullable=False),
        sa.Column('final_category', sa.Integer(), nullable=False),
        sa.Column('matched_rules', sa.JSON(), nullable=False),
        sa.Column('override_applied', sa.Boolean(), nullable=False),
        sa.Column('override_category', sa.Integer(), nullable=True),
        sa.Column('override_reason', sa.Text(), nullable=True),
        sa.Column('classification_reasons', sa.JSON(), nullable=False),
        sa.Column('required_obligations', sa.JSON(), nullable=False),
        sa.Column('obligations_satisfied', sa.Boolean(), nullable=False),
        sa.Column('missing_obligations', sa.JSON(), nullable=False),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_risk_evaluations_operation_id', 'risk_evaluations', ['operation_id'])

    # 5. reviews
    op.create_table(
        'reviews',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('operation_id', sa.String(length=128), nullable=False),
        sa.Column('reviewer_id', sa.String(length=128), nullable=False),
        sa.Column('category', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('operation_id', 'reviewer_id', name='uq_operation_reviewer'),
    )
    op.create_index('ix_reviews_operation_id', 'reviews', ['operation_id'])
    op.create_index('ix_reviews_reviewer_id', 'reviews', ['reviewer_id'])

    # 6. review_disagreements
    op.create_table(
        'review_disagreements',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('operation_id', sa.String(length=128), nullable=False),
        sa.Column('reviewer_a', sa.String(length=128), nullable=False),
        sa.Column('category_a', sa.Integer(), nullable=False),
        sa.Column('reviewer_b', sa.String(length=128), nullable=False),
        sa.Column('category_b', sa.Integer(), nullable=False),
        sa.Column('note', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_review_disagreements_operation_id', 'review_disagreements', ['operation_id'])


def downgrade() -> None:
    op.drop_table('review_disagreements')
    op.drop_table('reviews')
    op.drop_table('risk_evaluations')
    op.drop_table('policy_pins')
    op.drop_table('policy_overrides')
    op.drop_table('risk_rules')
