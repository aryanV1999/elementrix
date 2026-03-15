from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from mealie.core.config import get_app_settings
from mealie.core import root_logger
from mealie.db.db_setup import generate_session
from mealie.db.models.household.diet_plan import SavedDietPlan, DietPlanMealTracking
from mealie.repos.repository_diet_plans import RepositorySavedDietPlans, RepositoryMealTracking
from mealie.schema.diet import (
    DietInput,
    DietPlanResponse,
    WeeklyDietPlan,
    MealItem,
    MacroNutrients,
)
from mealie.schema.diet.saved_diet_plan import (
    SavedDietPlanCreate,
    SavedDietPlanOut,
    SavedDietPlanSummary,
    MealTrackingOut,
    ToggleMealRequest,
)
from mealie.services.diet import DietService

router = APIRouter(prefix="/diet")
logger = root_logger.get_logger(__name__)


def get_db():
    """Dependency that provides a database session"""
    yield from generate_session()


class CalorieCalculation:
    """Response model for calorie calculation preview"""
    def __init__(
        self,
        daily_calories: int,
        daily_adjustment: int,
        maintenance_calories: int,
        weight_change: float,
        timeline_days: int,
        macros: MacroNutrients,
    ):
        self.daily_calories = daily_calories
        self.daily_adjustment = daily_adjustment
        self.maintenance_calories = maintenance_calories
        self.weight_change = weight_change
        self.timeline_days = timeline_days
        self.macros = macros


def _check_gemini_enabled():
    """Check if Gemini API is enabled, raise 403 if not"""
    settings = get_app_settings()
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Diet Generator requires Gemini API to be enabled. Please configure GEMINI_API_KEY."
        )


@router.post("/calculate", response_model=dict)
async def calculate_calories(payload: DietInput):
    """
    Calculate daily calorie target based on weight goals.
    This is a preview endpoint that doesn't require Gemini AI.
    
    Returns calculated calories and macros without generating a diet plan.
    """
    daily_calories = payload.calculate_daily_calories()
    macros = payload.calculate_macros()
    
    weight_change = payload.target_weight - payload.current_weight
    total_calories_needed = weight_change * 7700
    days = payload.timeline_weeks * 7
    daily_adjustment = int(total_calories_needed / days)

    return {
        "daily_calories": daily_calories,
        "daily_adjustment": daily_adjustment,
        "maintenance_calories": payload.maintenance_calories,
        "weight_change": weight_change,
        "timeline_days": days,
        "macros": {
            "protein_g": macros.protein_g,
            "carbs_g": macros.carbs_g,
            "fat_g": macros.fat_g,
        },
        "summary": {
            "goal": "lose weight" if weight_change < 0 else "gain weight" if weight_change > 0 else "maintain weight",
            "weekly_change_kg": round(weight_change / payload.timeline_weeks, 2),
            "is_safe": 0.5 <= abs(weight_change / payload.timeline_weeks) <= 1.0 if weight_change != 0 else True,
        }
    }


@router.post("/generate", response_model=DietPlanResponse)
async def generate_diet_plan(payload: DietInput):
    """
    Generate a single day's diet plan using AI.
    
    This endpoint:
    1. Calculates calorie target based on weight goals
    2. Calculates macro targets (protein, carbs, fat)
    3. Calls Gemini AI to generate a personalized diet plan
    4. Optimizes meal portions to match targets
    5. Returns structured meal plan with nutrition info
    
    Request body:
    - current_weight: Current weight in kg
    - target_weight: Target weight in kg
    - maintenance_calories: Daily maintenance calories
    - timeline_weeks: Timeline in weeks (1-52)
    - diet_preference: vegetarian, non-vegetarian, vegan, keto, paleo
    - meals_per_day: Number of meals (2-6)
    - allergies: Optional list of food allergies
    - cuisine_preference: Optional cuisine preference
    - protein_preference: Optional protein preference
    
    Returns:
    - Daily calorie target
    - Macro targets
    - List of meals with nutrition breakdown
    """
    _check_gemini_enabled()
    
    try:
        service = DietService()
        result = await service.generate_daily_plan(payload)
        return result
    except ValueError as e:
        logger.error(f"Diet generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected error in diet generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate diet plan. Please try again."
        )


@router.post("/generate-weekly", response_model=WeeklyDietPlan)
async def generate_weekly_diet_plan(payload: DietInput):
    """
    Generate a 7-day diet plan using AI.
    
    This endpoint generates a full week of meal plans with:
    - Varied meals across days
    - Consolidated grocery list
    - Balanced nutrition each day
    
    Note: This endpoint may take longer due to the larger response size.
    """
    _check_gemini_enabled()
    
    try:
        service = DietService()
        result = await service.generate_weekly_plan(payload)
        return result
    except ValueError as e:
        logger.error(f"Weekly diet generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected error in weekly diet generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate weekly diet plan. Please try again."
        )


@router.post("/regenerate-meal", response_model=MealItem)
async def regenerate_meal(
    payload: DietInput,
    meal_type: str = Query(..., description="Type of meal: Breakfast, Lunch, Snack, or Dinner"),
    exclude_meals: Optional[List[str]] = Query(default=None, description="List of meal names to avoid")
):
    """
    Regenerate a single meal.
    
    Use this endpoint when a user wants to replace a specific meal
    with an alternative option.
    
    Query parameters:
    - meal_type: Breakfast, Lunch, Snack, or Dinner
    - exclude_meals: Optional list of meal names to avoid
    """
    _check_gemini_enabled()
    
    valid_meal_types = ["Breakfast", "Lunch", "Snack", "Dinner"]
    if meal_type not in valid_meal_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid meal_type. Must be one of: {', '.join(valid_meal_types)}"
        )
    
    try:
        service = DietService()
        result = await service.regenerate_meal(payload, meal_type, exclude_meals)
        return result
    except ValueError as e:
        logger.error(f"Meal regeneration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected error in meal regeneration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate meal. Please try again."
        )


@router.get("/status")
async def get_diet_generator_status():
    """
    Check if Diet Generator feature is available.
    
    Returns the current status of Gemini AI integration.
    """
    settings = get_app_settings()
    return {
        "enabled": settings.GEMINI_ENABLED,
        "message": "Diet Generator is available" if settings.GEMINI_ENABLED else "Gemini AI is not configured",
    }


# ============================================
# Saved Diet Plans Endpoints
# ============================================

@router.post("/plans/save", response_model=SavedDietPlanOut)
async def save_diet_plan(
    data: SavedDietPlanCreate,
    user_id: UUID = Query(..., description="User ID"),
    group_id: UUID = Query(..., description="Group ID"),
    db: Session = Depends(get_db),
):
    """
    Save a generated diet plan for tracking.
    
    This endpoint saves a diet plan to the database so users can:
    - Track meal completion
    - Follow the plan over time
    - View their progress
    """
    try:
        repo = RepositorySavedDietPlans(db)
        plan = repo.create_plan(user_id, group_id, data)
        return SavedDietPlanOut.model_validate(plan)
    except Exception as e:
        logger.exception(f"Error saving diet plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save diet plan"
        )


@router.get("/plans/active", response_model=Optional[SavedDietPlanOut])
async def get_active_diet_plan(
    user_id: UUID = Query(..., description="User ID"),
    db: Session = Depends(get_db),
):
    """
    Get the currently active diet plan for a user.
    
    Returns the plan the user is currently following, or null if none is active.
    """
    try:
        repo = RepositorySavedDietPlans(db)
        plan = repo.get_active_plan_for_user(user_id)
        if plan:
            return SavedDietPlanOut.model_validate(plan)
        return None
    except Exception as e:
        logger.exception(f"Error fetching active diet plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch active diet plan"
        )


@router.get("/plans", response_model=List[SavedDietPlanSummary])
async def get_all_diet_plans(
    user_id: UUID = Query(..., description="User ID"),
    db: Session = Depends(get_db),
):
    """
    Get all saved diet plans for a user.
    
    Returns a list of all saved plans with summary information.
    """
    try:
        repo = RepositorySavedDietPlans(db)
        plans = repo.get_plans_for_user(user_id)
        return [SavedDietPlanSummary.model_validate(p) for p in plans]
    except Exception as e:
        logger.exception(f"Error fetching diet plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch diet plans"
        )


@router.get("/plans/{plan_id}", response_model=SavedDietPlanOut)
async def get_diet_plan(
    plan_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get a specific diet plan by ID.
    """
    try:
        repo = RepositorySavedDietPlans(db)
        plan = repo.get_one(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diet plan not found"
            )
        return SavedDietPlanOut.model_validate(plan)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching diet plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch diet plan"
        )


@router.post("/plans/{plan_id}/activate", response_model=SavedDietPlanOut)
async def activate_diet_plan(
    plan_id: UUID,
    user_id: UUID = Query(..., description="User ID"),
    db: Session = Depends(get_db),
):
    """
    Activate a specific diet plan (deactivates others).
    """
    try:
        repo = RepositorySavedDietPlans(db)
        plan = repo.activate_plan(plan_id, user_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diet plan not found or not authorized"
            )
        return SavedDietPlanOut.model_validate(plan)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error activating diet plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate diet plan"
        )


@router.delete("/plans/{plan_id}")
async def delete_diet_plan(
    plan_id: UUID,
    user_id: UUID = Query(..., description="User ID"),
    db: Session = Depends(get_db),
):
    """
    Delete a saved diet plan.
    """
    try:
        repo = RepositorySavedDietPlans(db)
        plan = repo.get_one(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diet plan not found"
            )
        if plan.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this plan"
            )
        repo.delete(plan_id)
        return {"status": "success", "message": "Diet plan deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting diet plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete diet plan"
        )


# ============================================
# Meal Tracking Endpoints
# ============================================

@router.post("/plans/{plan_id}/track-meal", response_model=MealTrackingOut)
async def toggle_meal_completion(
    plan_id: UUID,
    data: ToggleMealRequest,
    db: Session = Depends(get_db),
):
    """
    Toggle a meal's completion status.
    
    Use this when a user marks a meal as eaten or uneaten.
    """
    try:
        repo = RepositoryMealTracking(db)
        tracking = repo.toggle_meal_completion(
            diet_plan_id=plan_id,
            day_number=data.day_number,
            meal_type=data.meal_type,
            meal_name=data.meal_name,
            is_completed=data.is_completed,
        )
        return MealTrackingOut.model_validate(tracking)
    except Exception as e:
        logger.exception(f"Error tracking meal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track meal"
        )


@router.get("/plans/{plan_id}/tracking", response_model=List[MealTrackingOut])
async def get_plan_tracking(
    plan_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get all meal tracking records for a diet plan.
    """
    try:
        repo = RepositoryMealTracking(db)
        tracking = repo.get_tracking_for_plan(plan_id)
        return [MealTrackingOut.model_validate(t) for t in tracking]
    except Exception as e:
        logger.exception(f"Error fetching tracking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tracking data"
        )


@router.get("/plans/{plan_id}/stats")
async def get_plan_stats(
    plan_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get completion statistics for a diet plan.
    
    Returns:
    - total_meals: Total meals in the plan
    - completed_meals: Number of completed meals
    - completion_percentage: Percentage complete
    - days_completed: List of fully completed days
    """
    try:
        repo = RepositoryMealTracking(db)
        stats = repo.get_completion_stats(plan_id)
        return stats
    except Exception as e:
        logger.exception(f"Error fetching stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch statistics"
        )
