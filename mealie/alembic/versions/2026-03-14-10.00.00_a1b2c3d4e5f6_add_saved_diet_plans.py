"""add saved diet plans

Revision ID: a1b2c3d4e5f6
Revises: 1d9a002d7234
Create Date: 2026-03-14 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "1d9a002d7234"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    # Create saved_diet_plans table
    op.create_table(
        "saved_diet_plans",
        sa.Column("id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("user_id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("group_id", mealie.db.migration_types.GUID(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("plan_data", sa.Text(), nullable=False),
        sa.Column("daily_calories", sa.Integer(), nullable=False),
        sa.Column("target_protein", sa.Float(), nullable=False),
        sa.Column("target_carbs", sa.Float(), nullable=False),
        sa.Column("target_fat", sa.Float(), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=True),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("update_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_saved_diet_plans_user_id"), "saved_diet_plans", ["user_id"], unique=False)
    op.create_index(op.f("ix_saved_diet_plans_group_id"), "saved_diet_plans", ["group_id"], unique=False)
    op.create_index(op.f("ix_saved_diet_plans_is_active"), "saved_diet_plans", ["is_active"], unique=False)
    op.create_index(op.f("ix_saved_diet_plans_created_at"), "saved_diet_plans", ["created_at"], unique=False)

    # Create diet_plan_meal_tracking table
    op.create_table(
        "diet_plan_meal_tracking",
        sa.Column("id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("diet_plan_id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("meal_type", sa.String(length=50), nullable=False),
        sa.Column("meal_name", sa.String(length=255), nullable=False),
        sa.Column("is_completed", sa.Boolean(), nullable=False, default=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("update_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["diet_plan_id"], ["saved_diet_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_diet_plan_meal_tracking_diet_plan_id"), 
        "diet_plan_meal_tracking", 
        ["diet_plan_id"], 
        unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_diet_plan_meal_tracking_diet_plan_id"), table_name="diet_plan_meal_tracking")
    op.drop_table("diet_plan_meal_tracking")
    
    op.drop_index(op.f("ix_saved_diet_plans_created_at"), table_name="saved_diet_plans")
    op.drop_index(op.f("ix_saved_diet_plans_is_active"), table_name="saved_diet_plans")
    op.drop_index(op.f("ix_saved_diet_plans_group_id"), table_name="saved_diet_plans")
    op.drop_index(op.f("ix_saved_diet_plans_user_id"), table_name="saved_diet_plans")
    op.drop_table("saved_diet_plans")
