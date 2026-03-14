from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator

from mealie.schema.openai._base import OpenAIBase


class DietPreference(str, Enum):
    VEGETARIAN = "vegetarian"
    NON_VEGETARIAN = "non-vegetarian"
    VEGAN = "vegan"
    KETO = "keto"
    PALEO = "paleo"


class MacroNutrients(BaseModel):
    """Macro nutrient breakdown"""
    protein_g: float = Field(..., description="Protein in grams")
    carbs_g: float = Field(..., description="Carbohydrates in grams")
    fat_g: float = Field(..., description="Fat in grams")
    fiber_g: Optional[float] = Field(None, description="Fiber in grams")

    @classmethod
    def from_calories(cls, calories: int, protein_pct: float = 0.30, carbs_pct: float = 0.40, fat_pct: float = 0.30) -> "MacroNutrients":
        """
        Calculate macros from calories using percentage split.
        Default: 30% protein, 40% carbs, 30% fat
        """
        protein = (calories * protein_pct) / 4  # 4 calories per gram
        carbs = (calories * carbs_pct) / 4      # 4 calories per gram
        fat = (calories * fat_pct) / 9          # 9 calories per gram
        return cls(
            protein_g=round(protein, 1),
            carbs_g=round(carbs, 1),
            fat_g=round(fat, 1),
        )


class DietInput(BaseModel):
    """Input parameters for diet generation"""
    current_weight: float = Field(..., gt=0, description="Current weight in kg")
    target_weight: float = Field(..., gt=0, description="Target weight in kg")
    maintenance_calories: int = Field(..., gt=0, description="Daily maintenance calories")
    timeline_weeks: int = Field(..., ge=1, le=52, description="Timeline in weeks")
    diet_preference: DietPreference = Field(default=DietPreference.NON_VEGETARIAN, description="Diet preference")
    meals_per_day: int = Field(default=4, ge=2, le=6, description="Number of meals per day")
    
    # Optional inputs
    allergies: Optional[List[str]] = Field(default=None, description="Food allergies")
    cuisine_preference: Optional[str] = Field(default=None, description="Preferred cuisine")
    protein_preference: Optional[str] = Field(default=None, description="Protein preference (e.g., chicken, fish)")

    @field_validator("allergies", mode="before")
    def filter_empty_allergies(cls, v):
        if v is None:
            return None
        return [a for a in v if a and a.strip()]

    def calculate_daily_calories(self) -> int:
        """
        Calculate daily calorie target based on weight goals.
        
        Formula:
        - weight_change = target_weight - current_weight
        - total_calories = weight_change * 7700 (calories per kg)
        - days = timeline_weeks * 7
        - daily_adjustment = total_calories / days
        - daily_calories = maintenance_calories + daily_adjustment
        """
        weight_change = self.target_weight - self.current_weight
        total_calories_needed = weight_change * 7700  # 7700 calories per kg
        days = self.timeline_weeks * 7
        daily_adjustment = total_calories_needed / days
        daily_calories = self.maintenance_calories + daily_adjustment
        
        # Ensure minimum safe calorie intake (1200 for women, 1500 for men - using 1200 as floor)
        return max(int(round(daily_calories)), 1200)

    def calculate_macros(self) -> MacroNutrients:
        """Calculate macro targets based on daily calories"""
        return MacroNutrients.from_calories(self.calculate_daily_calories())


class MealItem(OpenAIBase):
    """A single meal with nutrition information"""
    meal_type: str = Field(..., description="Type of meal: Breakfast, Lunch, Snack, Dinner")
    name: str = Field(..., description="Name of the meal")
    ingredients: List[str] = Field(..., description="List of ingredients")
    calories: int = Field(..., ge=0, description="Calories in the meal")
    protein: float = Field(..., ge=0, description="Protein in grams")
    carbs: float = Field(..., ge=0, description="Carbohydrates in grams")
    fat: float = Field(..., ge=0, description="Fat in grams")
    instructions: str = Field(..., description="Cooking instructions")
    serving_size: Optional[str] = Field(None, description="Serving size description")


class DayPlan(OpenAIBase):
    """A single day's diet plan"""
    day: int = Field(..., ge=1, le=7, description="Day number (1-7)")
    total_calories: int = Field(..., ge=0, description="Total calories for the day")
    total_protein: float = Field(..., ge=0, description="Total protein for the day")
    total_carbs: float = Field(..., ge=0, description="Total carbs for the day")
    total_fat: float = Field(..., ge=0, description="Total fat for the day")
    meals: List[MealItem] = Field(..., description="List of meals for the day")


class DietPlanResponse(OpenAIBase):
    """Response containing the generated diet plan"""
    daily_calories: int = Field(..., description="Target daily calories")
    target_protein: float = Field(..., description="Target daily protein in grams")
    target_carbs: float = Field(..., description="Target daily carbs in grams")
    target_fat: float = Field(..., description="Target daily fat in grams")
    meals: List[MealItem] = Field(..., description="List of meals for a single day")
    notes: Optional[str] = Field(None, description="Additional notes or tips")


class WeeklyDietPlan(OpenAIBase):
    """Weekly diet plan response"""
    daily_calories: int = Field(..., description="Target daily calories")
    target_protein: float = Field(..., description="Target daily protein in grams")
    target_carbs: float = Field(..., description="Target daily carbs in grams")
    target_fat: float = Field(..., description="Target daily fat in grams")
    total_days: int = Field(default=7, description="Number of days in the plan")
    days: List[DayPlan] = Field(..., description="List of daily plans")
    notes: Optional[str] = Field(None, description="Additional notes or tips")
    grocery_list: Optional[List[str]] = Field(None, description="Consolidated grocery list")
