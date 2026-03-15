"""
Repository for saved diet plan CRUD operations.
"""
from datetime import datetime
from typing import Optional
from collections.abc import Sequence

from pydantic import UUID4
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from mealie.db.models.household.diet_plan import SavedDietPlan, DietPlanMealTracking
from mealie.repos.repository_generic import RepositoryGeneric
from mealie.schema.diet.saved_diet_plan import (
    SavedDietPlanCreate,
    SavedDietPlanOut,
    SavedDietPlanSummary,
    MealTrackingCreate,
    MealTrackingOut,
    MealTrackingUpdate,
)


class RepositorySavedDietPlans(RepositoryGeneric[SavedDietPlanOut, SavedDietPlan]):
    """Repository for saved diet plan operations"""

    def __init__(self, session: Session) -> None:
        super().__init__(session, "id", SavedDietPlan, SavedDietPlanOut)

    def get_active_plan_for_user(self, user_id: UUID4) -> SavedDietPlan | None:
        """Get the currently active diet plan for a user"""
        stmt = select(SavedDietPlan).where(
            and_(
                SavedDietPlan.user_id == user_id,
                SavedDietPlan.is_active == True
            )
        )
        return self.session.execute(stmt).scalars().first()

    def get_plans_for_user(self, user_id: UUID4) -> Sequence[SavedDietPlan]:
        """Get all diet plans for a user"""
        stmt = select(SavedDietPlan).where(
            SavedDietPlan.user_id == user_id
        ).order_by(SavedDietPlan.created_at.desc())
        return self.session.execute(stmt).scalars().all()

    def deactivate_all_plans_for_user(self, user_id: UUID4) -> None:
        """Deactivate all diet plans for a user (before activating a new one)"""
        plans = self.get_plans_for_user(user_id)
        for plan in plans:
            plan.is_active = False
        self.session.commit()

    def create_plan(
        self,
        user_id: UUID4,
        group_id: UUID4,
        data: SavedDietPlanCreate
    ) -> SavedDietPlan:
        """Create a new saved diet plan"""
        # Deactivate existing active plans first
        if data.is_active:
            self.deactivate_all_plans_for_user(user_id)

        plan = SavedDietPlan(
            session=self.session,
            user_id=user_id,
            group_id=group_id,
            name=data.name,
            description=data.description,
            is_active=data.is_active,
            plan_data=data.plan_data,
            daily_calories=data.daily_calories,
            target_protein=data.target_protein,
            target_carbs=data.target_carbs,
            target_fat=data.target_fat,
            start_date=data.start_date or datetime.utcnow(),
            end_date=data.end_date,
        )
        self.session.add(plan)
        self.session.commit()
        self.session.refresh(plan)
        return plan

    def get_one(self, plan_id: UUID4) -> SavedDietPlan | None:
        """Get a single diet plan by ID - override to avoid loader_options"""
        stmt = select(SavedDietPlan).where(SavedDietPlan.id == plan_id)
        return self.session.execute(stmt).scalars().first()

    def delete(self, plan_id: UUID4) -> None:
        """Delete a diet plan - override to use direct delete"""
        plan = self.get_one(plan_id)
        if plan:
            self.session.delete(plan)
            self.session.commit()

    def activate_plan(self, plan_id: UUID4, user_id: UUID4) -> SavedDietPlan | None:
        """Activate a specific diet plan (deactivates others)"""
        plan = self.get_one(plan_id)
        if plan and plan.user_id == user_id:
            self.deactivate_all_plans_for_user(user_id)
            plan.is_active = True
            self.session.commit()
            self.session.refresh(plan)
            return plan
        return None


class RepositoryMealTracking(RepositoryGeneric[MealTrackingOut, DietPlanMealTracking]):
    """Repository for meal tracking operations"""

    def __init__(self, session: Session) -> None:
        super().__init__(session, "id", DietPlanMealTracking, MealTrackingOut)

    def get_tracking_for_plan(self, diet_plan_id: UUID4) -> Sequence[DietPlanMealTracking]:
        """Get all tracking records for a diet plan"""
        stmt = select(DietPlanMealTracking).where(
            DietPlanMealTracking.diet_plan_id == diet_plan_id
        ).order_by(DietPlanMealTracking.day_number, DietPlanMealTracking.meal_type)
        return self.session.execute(stmt).scalars().all()

    def get_tracking_for_day(
        self, 
        diet_plan_id: UUID4, 
        day_number: int
    ) -> Sequence[DietPlanMealTracking]:
        """Get tracking records for a specific day"""
        stmt = select(DietPlanMealTracking).where(
            and_(
                DietPlanMealTracking.diet_plan_id == diet_plan_id,
                DietPlanMealTracking.day_number == day_number
            )
        )
        return self.session.execute(stmt).scalars().all()

    def toggle_meal_completion(
        self,
        diet_plan_id: UUID4,
        day_number: int,
        meal_type: str,
        meal_name: str,
        is_completed: bool
    ) -> DietPlanMealTracking:
        """Toggle or create a meal completion record"""
        # Try to find existing record
        stmt = select(DietPlanMealTracking).where(
            and_(
                DietPlanMealTracking.diet_plan_id == diet_plan_id,
                DietPlanMealTracking.day_number == day_number,
                DietPlanMealTracking.meal_type == meal_type,
                DietPlanMealTracking.meal_name == meal_name
            )
        )
        record = self.session.execute(stmt).scalars().first()

        if record:
            record.is_completed = is_completed
            record.completed_at = datetime.utcnow() if is_completed else None
        else:
            record = DietPlanMealTracking(
                session=self.session,
                diet_plan_id=diet_plan_id,
                day_number=day_number,
                meal_type=meal_type,
                meal_name=meal_name,
                is_completed=is_completed,
                completed_at=datetime.utcnow() if is_completed else None,
            )
            self.session.add(record)

        self.session.commit()
        self.session.refresh(record)
        return record

    def get_completion_stats(self, diet_plan_id: UUID4) -> dict:
        """Get completion statistics for a diet plan"""
        # Get the plan to calculate total meals
        from mealie.db.models.household.diet_plan import SavedDietPlan
        plan = self.session.query(SavedDietPlan).filter(SavedDietPlan.id == diet_plan_id).first()
        
        if not plan:
            return {
                "total_meals": 0,
                "completed_meals": 0,
                "completion_percentage": 0,
                "days_completed": [],
            }
        
        # Parse plan data to get total meals
        import json
        try:
            plan_data = json.loads(plan.plan_data)
            
            # Check if it's a weekly plan (has days array) or daily plan (has meals array)
            if "days" in plan_data and isinstance(plan_data["days"], list):
                # Weekly plan - count meals from all days
                total_meals_in_plan = sum(len(day.get("meals", [])) for day in plan_data["days"])
            elif "meals" in plan_data and isinstance(plan_data["meals"], list):
                # Daily plan - meals repeat for 7 days
                total_meals_in_plan = len(plan_data["meals"]) * 7
            else:
                total_meals_in_plan = 0
        except (json.JSONDecodeError, KeyError, TypeError):
            total_meals_in_plan = 0
        
        # Get tracking records
        records = self.get_tracking_for_plan(diet_plan_id)
        completed = sum(1 for r in records if r.is_completed)
        
        # Track which days are fully completed
        days_meals = {}
        days_completed_meals = {}
        
        # Calculate meals per day from plan
        if "days" in plan_data and isinstance(plan_data["days"], list):
            for day_data in plan_data["days"]:
                day_num = day_data.get("day", 0)
                if day_num:
                    days_meals[day_num] = len(day_data.get("meals", []))
        elif "meals" in plan_data and isinstance(plan_data["meals"], list):
            # Daily plan - same meals each day
            meals_per_day = len(plan_data["meals"])
            for day in range(1, 8):
                days_meals[day] = meals_per_day
        
        for record in records:
            day = record.day_number
            if day not in days_completed_meals:
                days_completed_meals[day] = 0
            if record.is_completed:
                days_completed_meals[day] += 1
        
        fully_completed_days = [
            day for day, meal_count in days_meals.items()
            if days_completed_meals.get(day, 0) == meal_count and meal_count > 0
        ]

        return {
            "total_meals": total_meals_in_plan,
            "completed_meals": completed,
            "completion_percentage": (completed / total_meals_in_plan * 100) if total_meals_in_plan > 0 else 0,
            "days_completed": sorted(fully_completed_days),
        }
