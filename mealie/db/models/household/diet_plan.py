"""
Database models for saved diet plans with meal tracking functionality.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, orm
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column

from .._model_base import BaseMixins, SqlAlchemyBase
from .._model_utils.auto_init import auto_init
from .._model_utils.datetime import NaiveDateTime, get_utc_now
from .._model_utils.guid import GUID

if TYPE_CHECKING:
    from ..group import Group
    from ..users import User
    from .household import Household


class SavedDietPlan(SqlAlchemyBase, BaseMixins):
    """
    Model for storing user's saved diet plans.
    Each plan contains the full weekly plan data as JSON and tracks meal completion.
    """
    __tablename__ = "saved_diet_plans"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    
    # User and group associations
    user_id: Mapped[GUID] = mapped_column(GUID, ForeignKey("users.id"), nullable=False, index=True)
    user: Mapped[Optional["User"]] = orm.relationship("User", back_populates="diet_plans")
    
    group_id: Mapped[GUID | None] = mapped_column(GUID, ForeignKey("groups.id"), index=True)
    group: Mapped[Optional["Group"]] = orm.relationship("Group")
    
    household_id: AssociationProxy[GUID] = association_proxy("user", "household_id")
    household: AssociationProxy["Household"] = association_proxy("user", "household")
    
    # Plan metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="My Diet Plan")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Diet plan data (stored as JSON string)
    plan_data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON serialized WeeklyDietPlan
    
    # Plan configuration
    daily_calories: Mapped[int] = mapped_column(Integer, nullable=False)
    target_protein: Mapped[float] = mapped_column(nullable=False)
    target_carbs: Mapped[float] = mapped_column(nullable=False)
    target_fat: Mapped[float] = mapped_column(nullable=False)
    
    # Dates
    start_date: Mapped[datetime | None] = mapped_column(NaiveDateTime, default=get_utc_now)
    end_date: Mapped[datetime | None] = mapped_column(NaiveDateTime, nullable=True)
    
    # Relationships
    meal_tracking: Mapped[list["DietPlanMealTracking"]] = orm.relationship(
        "DietPlanMealTracking",
        back_populates="diet_plan",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    @auto_init()
    def __init__(self, **_) -> None:
        pass


class DietPlanMealTracking(SqlAlchemyBase, BaseMixins):
    """
    Model for tracking individual meal completion within a diet plan.
    Each record represents a meal on a specific day.
    """
    __tablename__ = "diet_plan_meal_tracking"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    
    # Foreign key to the diet plan
    diet_plan_id: Mapped[GUID] = mapped_column(
        GUID, 
        ForeignKey("saved_diet_plans.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    diet_plan: Mapped["SavedDietPlan"] = orm.relationship("SavedDietPlan", back_populates="meal_tracking")
    
    # Day and meal identification
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-7 for weekly plan
    meal_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Breakfast, Lunch, Dinner, Snack
    meal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Tracking
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(NaiveDateTime, nullable=True)
    
    # Optional notes from user
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    @auto_init()
    def __init__(self, **_) -> None:
        pass
