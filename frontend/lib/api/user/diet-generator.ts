import { BaseCRUDAPIReadOnly } from "../base/base-clients";
import type { ApiRequestInstance } from  "../types/non-generated";

const prefix = "/api";

const routes = {
  status: `${prefix}/diet/status`,
  calculate: `${prefix}/diet/calculate`,
  generate: `${prefix}/diet/generate`,
  generateWeekly: `${prefix}/diet/generate-weekly`,
  regenerateMeal: `${prefix}/diet/regenerate-meal`,
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
}
