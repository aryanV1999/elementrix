from typing import Optional, List

from fastapi import APIRouter, HTTPException, status

from mealie.core.config import get_app_settings
from mealie.core import root_logger
from mealie.schema.diet import (
    DietInput,
    DietPlanResponse,
    WeeklyDietPlan,
    MealItem,
    MacroNutrients,
)
from mealie.services.diet import DietService

router = APIRouter(prefix="/diet")
logger = root_logger.get_logger(__name__)


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
    meal_type: str,
    exclude_meals: Optional[List[str]] = None
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
