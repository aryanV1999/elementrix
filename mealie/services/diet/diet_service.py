from typing import Optional, List

from mealie.core import root_logger
from mealie.core.config import get_app_settings
from mealie.services.openai.openai import OpenAIService, OpenAIDataInjection
from mealie.schema.diet import (
    DietInput,
    DietPlanResponse,
    WeeklyDietPlan,
    MealItem,
    DayPlan,
)

from .._base_service import BaseService

logger = root_logger.get_logger(__name__)


class DietService(BaseService):
    """
    Service for generating AI-powered diet plans using Gemini AI.
    
    This service handles:
    - Calorie and macro calculations
    - Building prompts for Gemini
    - Parsing and validating responses
    - Meal optimization (adjusting portions to match targets)
    """

    PROMPT_DAILY = "diet.generate-plan"
    PROMPT_WEEKLY = "diet.generate-weekly-plan"

    def __init__(self) -> None:
        settings = get_app_settings()
        if not settings.GEMINI_ENABLED:
            raise ValueError("Gemini AI is not enabled. Diet Generator requires Gemini AI.")
        
        self.ai_service = OpenAIService()  # Uses Gemini under the hood
        super().__init__()

    def _build_user_message(self, payload: DietInput, daily_calories: int, macros: dict) -> str:
        """Build the user message with diet requirements"""
        
        message_parts = [
            f"Generate a healthy daily diet plan with the following requirements:",
            f"",
            f"Daily calories: {daily_calories}",
            f"Target protein: {macros['protein_g']}g",
            f"Target carbs: {macros['carbs_g']}g",
            f"Target fat: {macros['fat_g']}g",
            f"Meals per day: {payload.meals_per_day}",
            f"Diet preference: {payload.diet_preference.value}",
        ]

        if payload.allergies:
            message_parts.append(f"Allergies (MUST AVOID): {', '.join(payload.allergies)}")
        
        if payload.cuisine_preference:
            message_parts.append(f"Cuisine preference: {payload.cuisine_preference}")
        
        if payload.protein_preference:
            message_parts.append(f"Protein preference: {payload.protein_preference}")

        message_parts.extend([
            "",
            f"Generate exactly {payload.meals_per_day} meals that sum up to approximately {daily_calories} calories.",
            "Ensure meals are balanced, nutritious, and practical to prepare.",
        ])

        return "\n".join(message_parts)

    def _build_weekly_message(self, payload: DietInput, daily_calories: int, macros: dict) -> str:
        """Build the user message for weekly diet plan"""
        
        message_parts = [
            f"Generate a comprehensive 7-day diet plan with the following requirements:",
            f"",
            f"Daily calories per day: {daily_calories}",
            f"Target protein per day: {macros['protein_g']}g",
            f"Target carbs per day: {macros['carbs_g']}g",
            f"Target fat per day: {macros['fat_g']}g",
            f"Meals per day: {payload.meals_per_day}",
            f"Diet preference: {payload.diet_preference.value}",
        ]

        if payload.allergies:
            message_parts.append(f"Allergies (MUST AVOID): {', '.join(payload.allergies)}")
        
        if payload.cuisine_preference:
            message_parts.append(f"Cuisine preference: {payload.cuisine_preference}")
        
        if payload.protein_preference:
            message_parts.append(f"Protein preference: {payload.protein_preference}")

        message_parts.extend([
            "",
            f"Generate a full 7-day plan with {payload.meals_per_day} meals per day.",
            f"Each day should sum to approximately {daily_calories} calories.",
            "Vary meals across days to prevent monotony.",
            "Include a consolidated grocery list for the entire week.",
        ])

        return "\n".join(message_parts)

    def _optimize_meal_portions(self, meal: MealItem, adjustment_ratio: float) -> MealItem:
        """
        Adjust meal portions to better match calorie targets.
        
        Args:
            meal: The meal to optimize
            adjustment_ratio: Ratio to multiply portions by (e.g., 0.9 to reduce by 10%)
        
        Returns:
            Meal with adjusted nutritional values
        """
        if adjustment_ratio == 1.0:
            return meal
        
        return MealItem(
            meal_type=meal.meal_type,
            name=meal.name,
            ingredients=meal.ingredients,
            calories=int(round(meal.calories * adjustment_ratio)),
            protein=round(meal.protein * adjustment_ratio, 1),
            carbs=round(meal.carbs * adjustment_ratio, 1),
            fat=round(meal.fat * adjustment_ratio, 1),
            instructions=meal.instructions,
            serving_size=meal.serving_size,
        )

    def _optimize_day_plan(self, day: DayPlan, target_calories: int, tolerance: float = 0.05) -> DayPlan:
        """
        Optimize a day's meal plan to match target calories.
        
        Args:
            day: The day plan to optimize
            target_calories: Target calorie count
            tolerance: Acceptable variance (default 5%)
        
        Returns:
            Optimized day plan
        """
        actual_calories = sum(m.calories for m in day.meals)
        variance = abs(actual_calories - target_calories) / target_calories

        if variance <= tolerance:
            return day

        adjustment_ratio = target_calories / actual_calories
        optimized_meals = [self._optimize_meal_portions(m, adjustment_ratio) for m in day.meals]

        return DayPlan(
            day=day.day,
            total_calories=sum(m.calories for m in optimized_meals),
            total_protein=sum(m.protein for m in optimized_meals),
            total_carbs=sum(m.carbs for m in optimized_meals),
            total_fat=sum(m.fat for m in optimized_meals),
            meals=optimized_meals,
        )

    async def generate_daily_plan(self, payload: DietInput) -> DietPlanResponse:
        """
        Generate a single day's diet plan.
        
        Args:
            payload: Diet input parameters
        
        Returns:
            Generated diet plan response
        
        Raises:
            ValueError: If OpenAI returns invalid or empty response
        """
        daily_calories = payload.calculate_daily_calories()
        macros = payload.calculate_macros()
        
        logger.info(f"Generating diet plan: {daily_calories} cal, {macros}")

        # Build prompt with data injection
        prompt = self.ai_service.get_prompt(
            self.PROMPT_DAILY,
            data_injections=[
                OpenAIDataInjection(
                    description="Target Macronutrients",
                    value=macros.model_dump_json()
                )
            ]
        )

        message = self._build_user_message(payload, daily_calories, macros.model_dump())

        # Call OpenAI
        response = await self.ai_service.get_response(
            prompt=prompt,
            message=message,
            response_schema=DietPlanResponse,
        )

        if response is None:
            raise ValueError("Gemini returned no content for diet plan generation")

        # Validate and optimize the response
        actual_calories = sum(m.calories for m in response.meals)
        tolerance = 0.05  # 5% tolerance

        if abs(actual_calories - daily_calories) / daily_calories > tolerance:
            logger.warning(
                f"Generated calories ({actual_calories}) differ from target ({daily_calories}). Optimizing..."
            )
            adjustment_ratio = daily_calories / actual_calories
            response.meals = [self._optimize_meal_portions(m, adjustment_ratio) for m in response.meals]

        # Update response with calculated targets
        response.daily_calories = daily_calories
        response.target_protein = macros.protein_g
        response.target_carbs = macros.carbs_g
        response.target_fat = macros.fat_g

        return response

    async def generate_weekly_plan(self, payload: DietInput) -> WeeklyDietPlan:
        """
        Generate a 7-day diet plan.
        
        Args:
            payload: Diet input parameters
        
        Returns:
            Generated weekly diet plan
        
        Raises:
            ValueError: If OpenAI returns invalid or empty response
        """
        daily_calories = payload.calculate_daily_calories()
        macros = payload.calculate_macros()
        
        logger.info(f"Generating weekly diet plan: {daily_calories} cal/day, {macros}")

        # Build prompt with data injection
        prompt = self.ai_service.get_prompt(
            self.PROMPT_WEEKLY,
            data_injections=[
                OpenAIDataInjection(
                    description="Target Daily Macronutrients",
                    value=macros.model_dump_json()
                )
            ]
        )

        message = self._build_weekly_message(payload, daily_calories, macros.model_dump())

        # Call OpenAI
        response = await self.ai_service.get_response(
            prompt=prompt,
            message=message,
            response_schema=WeeklyDietPlan,
        )

        if response is None:
            raise ValueError("Gemini returned no content for weekly diet plan generation")

        # Optimize each day's plan
        optimized_days = [self._optimize_day_plan(day, daily_calories) for day in response.days]
        response.days = optimized_days

        # Update response with calculated targets
        response.daily_calories = daily_calories
        response.target_protein = macros.protein_g
        response.target_carbs = macros.carbs_g
        response.target_fat = macros.fat_g

        # Generate grocery list if not present
        if not response.grocery_list:
            all_ingredients = set()
            for day in response.days:
                for meal in day.meals:
                    all_ingredients.update(meal.ingredients)
            response.grocery_list = sorted(list(all_ingredients))

        return response

    async def regenerate_meal(
        self,
        payload: DietInput,
        meal_type: str,
        exclude_meals: Optional[List[str]] = None
    ) -> MealItem:
        """
        Regenerate a single meal (useful for replacing a meal user doesn't like).
        
        Args:
            payload: Diet input parameters
            meal_type: Type of meal to regenerate (Breakfast, Lunch, Snack, Dinner)
            exclude_meals: List of meal names to avoid
        
        Returns:
            A new meal item
        """
        daily_calories = payload.calculate_daily_calories()
        macros = payload.calculate_macros()

        # Calculate approximate calories for this meal type
        meal_calorie_ratios = {
            "Breakfast": 0.275,
            "Lunch": 0.325,
            "Snack": 0.125,
            "Dinner": 0.275,
        }
        target_meal_calories = int(daily_calories * meal_calorie_ratios.get(meal_type, 0.25))

        message_parts = [
            f"Generate a single {meal_type} meal with the following requirements:",
            f"",
            f"Target calories: {target_meal_calories}",
            f"Target protein: {round(macros.protein_g * meal_calorie_ratios.get(meal_type, 0.25))}g",
            f"Diet preference: {payload.diet_preference.value}",
        ]

        if payload.allergies:
            message_parts.append(f"Allergies (MUST AVOID): {', '.join(payload.allergies)}")

        if exclude_meals:
            message_parts.append(f"Avoid these meals (already used): {', '.join(exclude_meals)}")

        if payload.cuisine_preference:
            message_parts.append(f"Cuisine preference: {payload.cuisine_preference}")

        message_parts.append("")
        message_parts.append("Return a single meal object matching the MealItem schema.")

        prompt = self.ai_service.get_prompt(self.PROMPT_DAILY)
        message = "\n".join(message_parts)

        # For single meal, use MealItem schema directly
        response = await self.ai_service.get_response(
            prompt=prompt,
            message=message,
            response_schema=MealItem,
        )

        if response is None:
            raise ValueError(f"Failed to generate {meal_type} meal")

        return response
