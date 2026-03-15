import { BaseCRUDAPIReadOnly } from "../base/base-clients";
import type { ApiRequestInstance } from  "../types/non-generated";

const prefix = "/api";

const routes = {
  status: `${prefix}/diet/status`,
  calculate: `${prefix}/diet/calculate`,
  generate: `${prefix}/diet/generate`,
  generateWeekly: `${prefix}/diet/generate-weekly`,
  regenerateMeal: `${prefix}/diet/regenerate-meal`,
  // Saved plans
  savePlan: `${prefix}/diet/plans/save`,
  activePlan: `${prefix}/diet/plans/active`,
  allPlans: `${prefix}/diet/plans`,
  getPlan: (id: string) => `${prefix}/diet/plans/${id}`,
  activatePlan: (id: string) => `${prefix}/diet/plans/${id}/activate`,
  deletePlan: (id: string) => `${prefix}/diet/plans/${id}`,
  trackMeal: (id: string) => `${prefix}/diet/plans/${id}/track-meal`,
  getTracking: (id: string) => `${prefix}/diet/plans/${id}/tracking`,
  getStats: (id: string) => `${prefix}/diet/plans/${id}/stats`,
};

// Type definitions
export interface DietInput {
  current_weight: number;
  target_weight: number;
  maintenance_calories: number;
  timeline_weeks: number;
  diet_preference: "vegetarian" | "non-vegetarian" | "vegan" | "keto" | "paleo";
  meals_per_day: number;
  allergies?: string[];
  cuisine_preference?: string;
  protein_preference?: string;
}

export interface MacroNutrients {
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g?: number;
}

export interface MealItem {
  meal_type: string;
  name: string;
  ingredients: string[];
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  instructions: string;
  serving_size?: string;
}

export interface DayPlan {
  day: number;
  total_calories: number;
  total_protein: number;
  total_carbs: number;
  total_fat: number;
  meals: MealItem[];
}

export interface DietPlanResponse {
  daily_calories: number;
  target_protein: number;
  target_carbs: number;
  target_fat: number;
  meals: MealItem[];
  notes?: string;
}

export interface WeeklyDietPlan {
  daily_calories: number;
  target_protein: number;
  target_carbs: number;
  target_fat: number;
  total_days: number;
  days: DayPlan[];
  notes?: string;
  grocery_list?: string[];
}

export interface CalorieCalculation {
  daily_calories: number;
  daily_adjustment: number;
  maintenance_calories: number;
  weight_change: number;
  timeline_days: number;
  macros: MacroNutrients;
  summary: {
    goal: string;
    weekly_change_kg: number;
    is_safe: boolean;
  };
}

export interface DietGeneratorStatus {
  enabled: boolean;
  message: string;
}

// Saved Diet Plan Types
export interface MealTracking {
  id: string;
  diet_plan_id: string;
  day_number: number;
  meal_type: string;
  meal_name: string;
  is_completed: boolean;
  completed_at?: string;
  notes?: string;
  created_at?: string;
}

export interface SavedDietPlanSummary {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  is_active: boolean;
  daily_calories: number;
  target_protein: number;
  target_carbs: number;
  target_fat: number;
  start_date?: string;
  created_at?: string;
}

export interface SavedDietPlan extends SavedDietPlanSummary {
  plan_data: string;  // JSON serialized WeeklyDietPlan
  end_date?: string;
  meal_tracking: MealTracking[];
}

export interface SavedDietPlanCreate {
  name?: string;
  description?: string;
  is_active?: boolean;
  plan_data: string;
  daily_calories: number;
  target_protein: number;
  target_carbs: number;
  target_fat: number;
  start_date?: string;
  end_date?: string;
}

export interface ToggleMealRequest {
  day_number: number;
  meal_type: string;
  meal_name: string;
  is_completed: boolean;
}

export interface PlanStats {
  total_meals: number;
  completed_meals: number;
  completion_percentage: number;
  days_completed: number[];
}

export class DietGeneratorAPI {
  private requests: ApiRequestInstance;

  constructor(requests: ApiRequestInstance) {
    this.requests = requests;
  }

  /**
   * Check if Diet Generator feature is available
   */
  async getStatus() {
    return await this.requests.get<DietGeneratorStatus>(routes.status);
  }

  /**
   * Calculate daily calorie target without generating a plan
   * This is useful for preview before generating
   */
  async calculateCalories(payload: DietInput) {
    return await this.requests.post<CalorieCalculation>(routes.calculate, payload);
  }

  /**
   * Generate a single day's diet plan
   */
  async generateDailyPlan(payload: DietInput) {
    return await this.requests.post<DietPlanResponse>(routes.generate, payload);
  }

  /**
   * Generate a 7-day diet plan
   */
  async generateWeeklyPlan(payload: DietInput) {
    return await this.requests.post<WeeklyDietPlan>(routes.generateWeekly, payload);
  }

  /**
   * Regenerate a single meal
   */
  async regenerateMeal(payload: DietInput, mealType: string, excludeMeals?: string[]) {
    const params = new URLSearchParams();
    params.append("meal_type", mealType);
    if (excludeMeals && excludeMeals.length > 0) {
      excludeMeals.forEach((meal) => params.append("exclude_meals", meal));
    }
    return await this.requests.post<MealItem>(
      `${routes.regenerateMeal}?${params.toString()}`,
      payload
    );
  }

  // ============================================
  // Saved Diet Plan Methods
  // ============================================

  /**
   * Save a generated diet plan for tracking
   */
  async savePlan(userId: string, groupId: string, data: SavedDietPlanCreate) {
    const params = new URLSearchParams();
    params.append("user_id", userId);
    params.append("group_id", groupId);
    return await this.requests.post<SavedDietPlan>(
      `${routes.savePlan}?${params.toString()}`,
      data
    );
  }

  /**
   * Get the currently active diet plan for a user
   */
  async getActivePlan(userId: string) {
    const params = new URLSearchParams();
    params.append("user_id", userId);
    return await this.requests.get<SavedDietPlan | null>(
      `${routes.activePlan}?${params.toString()}`
    );
  }

  /**
   * Get all saved diet plans for a user
   */
  async getAllPlans(userId: string) {
    const params = new URLSearchParams();
    params.append("user_id", userId);
    return await this.requests.get<SavedDietPlanSummary[]>(
      `${routes.allPlans}?${params.toString()}`
    );
  }

  /**
   * Get a specific diet plan by ID
   */
  async getPlan(planId: string) {
    return await this.requests.get<SavedDietPlan>(routes.getPlan(planId));
  }

  /**
   * Activate a specific diet plan
   */
  async activatePlan(planId: string, userId: string) {
    const params = new URLSearchParams();
    params.append("user_id", userId);
    return await this.requests.post<SavedDietPlan>(
      `${routes.activatePlan(planId)}?${params.toString()}`,
      {}
    );
  }

  /**
   * Delete a saved diet plan
   */
  async deletePlan(planId: string, userId: string) {
    const params = new URLSearchParams();
    params.append("user_id", userId);
    return await this.requests.delete<{ status: string; message: string }>(
      `${routes.deletePlan(planId)}?${params.toString()}`
    );
  }

  /**
   * Toggle a meal's completion status
   */
  async toggleMealCompletion(planId: string, data: ToggleMealRequest) {
    return await this.requests.post<MealTracking>(routes.trackMeal(planId), data);
  }

  /**
   * Get all meal tracking records for a diet plan
   */
  async getTracking(planId: string) {
    return await this.requests.get<MealTracking[]>(routes.getTracking(planId));
  }

  /**
   * Get completion statistics for a diet plan
   */
  async getStats(planId: string) {
    return await this.requests.get<PlanStats>(routes.getStats(planId));
  }
}
