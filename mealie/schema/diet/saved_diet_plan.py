"""
Pydantic schemas for saved diet plans with meal tracking.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import UUID4, BaseModel, Field


class MealTrackingBase(BaseModel):
    """Base schema for meal tracking"""
    day_number: int = Field(..., ge=1, le=7, description="Day number (1-7)")
    meal_type: str = Field(..., description="Type of meal: Breakfast, Lunch, Dinner, Snack")
    meal_name: str = Field(..., description="Name of the meal")
    is_completed: bool = Field(default=False, description="Whether the meal has been eaten")
    notes: Optional[str] = Field(None, description="Optional user notes")


class MealTrackingCreate(MealTrackingBase):
    """Schema for creating meal tracking record"""
    pass


class MealTrackingUpdate(BaseModel):
    """Schema for updating meal tracking record"""
    is_completed: Optional[bool] = None
    notes: Optional[str] = None


class MealTrackingOut(MealTrackingBase):
    """Schema for meal tracking output"""
    id: UUID4
    diet_plan_id: UUID4
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SavedDietPlanBase(BaseModel):
    """Base schema for saved diet plan"""
    name: str = Field(default="My Diet Plan", max_length=255, description="Name of the diet plan")
    description: Optional[str] = Field(None, description="Optional description")
    is_active: bool = Field(default=True, description="Whether this is the active plan")


class SavedDietPlanCreate(SavedDietPlanBase):
    """Schema for creating a saved diet plan"""
    plan_data: str = Field(..., description="JSON serialized diet plan data")
    daily_calories: int = Field(..., description="Target daily calories")
    target_protein: float = Field(..., description="Target protein in grams")
    target_carbs: float = Field(..., description="Target carbs in grams")
    target_fat: float = Field(..., description="Target fat in grams")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SavedDietPlanUpdate(BaseModel):
    """Schema for updating a saved diet plan"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SavedDietPlanSummary(SavedDietPlanBase):
    """Summary schema for listing diet plans"""
    id: UUID4
    user_id: UUID4
    daily_calories: int
    target_protein: float
    target_carbs: float
    target_fat: float
    start_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SavedDietPlanOut(SavedDietPlanSummary):
    """Full schema for diet plan output including plan data"""
    plan_data: str  # JSON serialized WeeklyDietPlan
    end_date: Optional[datetime] = None
    meal_tracking: List[MealTrackingOut] = []

    class Config:
        from_attributes = True


class SavedDietPlanPagination(BaseModel):
    """Pagination response for diet plans"""
    page: int = 1
    per_page: int = 10
    total: int = 0
    total_pages: int = 0
    items: List[SavedDietPlanSummary] = []


class ToggleMealRequest(BaseModel):
    """Request schema for toggling meal completion"""
    day_number: int = Field(..., ge=1, le=7, description="Day number (1-7)")
    meal_type: str = Field(..., description="Type of meal: Breakfast, Lunch, Dinner, Snack")
    meal_name: str = Field(..., description="Name of the meal")
    is_completed: bool = Field(..., description="Whether the meal has been eaten")


class ToggleMealRequest(BaseModel):
    """Request to toggle a meal's completion status"""
    day_number: int = Field(..., ge=1, le=7)
    meal_type: str
    meal_name: str
    is_completed: bool


class BulkToggleMealsRequest(BaseModel):
    """Request to toggle multiple meals at once"""
    meals: List[ToggleMealRequest]


class DietPlanStats(BaseModel):
    """Statistics for a diet plan"""
    total_meals: int
    completed_meals: int
    completion_percentage: float
    days_completed: List[int]  # List of day numbers with all meals completed
