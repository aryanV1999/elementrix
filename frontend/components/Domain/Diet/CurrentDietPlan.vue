<template>
  <div>
    <!-- Debug Info (remove later) -->
    <v-alert v-if="!parsedPlan && plan" type="warning" class="mb-4">
      <div>Unable to parse plan data. Raw data length: {{ plan.plan_data?.length || 0 }}</div>
      <div v-if="plan.plan_data">First 100 chars: {{ plan.plan_data.substring(0, 100) }}</div>
    </v-alert>

    <!-- Plan Header with Stats -->
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon start color="primary">{{ $globals.icons.calendar }}</v-icon>
        {{ plan?.name || $t("diet-generator.current-plan") }}
        <v-chip v-if="plan?.is_active" color="success" size="small" class="ml-2">
          {{ $t("diet-generator.active") }}
        </v-chip>
      </v-card-title>
      <v-card-subtitle v-if="plan?.description">
        {{ plan.description }}
      </v-card-subtitle>

      <v-card-text>
        <!-- Progress Bar -->
        <div v-if="stats" class="mb-4">
          <div class="d-flex justify-space-between mb-2">
            <span class="text-body-2">{{ $t("diet-generator.progress") }}</span>
            <span class="text-body-2 font-weight-bold">
              {{ stats.completed_meals }} / {{ stats.total_meals }} {{ $t("diet-generator.meals") }}
            </span>
          </div>
          <v-progress-linear
            :model-value="stats.completion_percentage"
            color="success"
            height="12"
            rounded
          >
            <template #default>
              <span class="text-caption white--text">{{ Math.round(stats.completion_percentage) }}%</span>
            </template>
          </v-progress-linear>
        </div>

        <!-- Nutrition Targets -->
        <v-row dense>
          <v-col cols="6" sm="3">
            <div class="text-center pa-2 rounded bg-orange-lighten-4">
              <div class="text-h6 font-weight-bold orange--text">{{ plan?.daily_calories || 0 }}</div>
              <div class="text-caption">{{ $t("diet-generator.calories") }}</div>
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="text-center pa-2 rounded bg-red-lighten-4">
              <div class="text-h6 font-weight-bold red--text">{{ plan?.target_protein?.toFixed(0) || 0 }}g</div>
              <div class="text-caption">{{ $t("diet-generator.protein") }}</div>
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="text-center pa-2 rounded bg-blue-lighten-4">
              <div class="text-h6 font-weight-bold blue--text">{{ plan?.target_carbs?.toFixed(0) || 0 }}g</div>
              <div class="text-caption">{{ $t("diet-generator.carbs") }}</div>
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="text-center pa-2 rounded bg-amber-lighten-4">
              <div class="text-h6 font-weight-bold amber--text text--darken-3">{{ plan?.target_fat?.toFixed(0) || 0 }}g</div>
              <div class="text-caption">{{ $t("diet-generator.fat") }}</div>
            </div>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Days Navigation -->
    <v-card v-if="isWeeklyPlan" class="mb-4">
      <v-tabs v-model="selectedDay" color="primary" center-active show-arrows>
        <v-tab v-for="day in 7" :key="day" :value="day">
          <div class="text-center">
            <div>{{ $t(`diet-generator.day-${day}`) }}</div>
            <v-icon v-if="isDayCompleted(day)" size="small" color="success">{{ $globals.icons.checkCircle }}</v-icon>
          </div>
        </v-tab>
      </v-tabs>
    </v-card>
    <v-card v-else-if="isDailyPlan" class="mb-4 pa-3 text-center">
      <div class="text-subtitle-2 text-grey">Daily Plan (same meals each day)</div>
    </v-card>

    <!-- Day's Meals -->
    <v-window v-model="selectedDay">
      <v-window-item v-for="day in (isWeeklyPlan ? 7 : 1)" :key="day" :value="day">
        <v-row>
          <v-col
            v-for="meal in getMealsForDay(day)"
            :key="`${day}-${meal.meal_type}-${meal.name}`"
            cols="12"
            md="6"
          >
            <v-card :class="{ 'border-success': isMealCompleted(day, meal.meal_type, meal.name) }">
              <v-card-title class="d-flex align-center">
                <v-checkbox
                  :model-value="isMealCompleted(day, meal.meal_type, meal.name)"
                  color="success"
                  hide-details
                  @update:model-value="(val: boolean) => handleMealToggle(day, meal.meal_type, meal.name, val)"
                />
                <div class="flex-grow-1">
                  <span class="text-overline text-grey">{{ meal.meal_type }}</span>
                  <div>{{ meal.name }}</div>
                </div>
              </v-card-title>

              <v-card-text>
                <!-- Ingredients -->
                <div class="mb-3">
                  <div class="text-subtitle-2 mb-1">{{ $t("diet-generator.ingredients") }}</div>
                  <v-chip-group>
                    <v-chip
                      v-for="(ingredient, idx) in meal.ingredients"
                      :key="idx"
                      size="small"
                      variant="outlined"
                    >
                      {{ ingredient }}
                    </v-chip>
                  </v-chip-group>
                </div>

                <!-- Nutrition -->
                <div class="d-flex justify-space-between text-body-2">
                  <span>🔥 {{ meal.calories }} cal</span>
                  <span>🥩 {{ meal.protein }}g</span>
                  <span>🍞 {{ meal.carbs }}g</span>
                  <span>🧈 {{ meal.fat }}g</span>
                </div>
              </v-card-text>

              <v-card-actions>
                <v-btn size="small" variant="text" @click="expandedMeal = expandedMeal === `${day}-${meal.name}` ? '' : `${day}-${meal.name}`">
                  {{ expandedMeal === `${day}-${meal.name}` ? $t("general.hide") : $t("diet-generator.view-instructions") }}
                </v-btn>
              </v-card-actions>

              <v-expand-transition>
                <div v-if="expandedMeal === `${day}-${meal.name}`">
                  <v-divider />
                  <v-card-text>
                    <div class="text-subtitle-2 mb-2">{{ $t("diet-generator.instructions") }}</div>
                    <p class="text-body-2">{{ meal.instructions }}</p>
                  </v-card-text>
                </div>
              </v-expand-transition>
            </v-card>
          </v-col>
        </v-row>
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import type { SavedDietPlan, MealTracking, PlanStats, WeeklyDietPlan, MealItem } from "~/lib/api/user/diet-generator";

const { $globals } = useNuxtApp();

interface Props {
  plan: SavedDietPlan | null;
  stats: PlanStats | null;
  tracking: MealTracking[];
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: "toggle-meal", dayNumber: number, mealType: string, mealName: string, isCompleted: boolean): void;
  (e: "view-full-plan"): void;
}>();

const selectedDay = ref(1);
const expandedMeal = ref("");

const parsedPlan = computed<any>(() => {
  if (!props.plan?.plan_data) {
    console.log('No plan_data available');
    return null;
  }
  try {
    const parsed = JSON.parse(props.plan.plan_data);
    console.log('Parsed plan:', parsed);
    return parsed;
  } catch (e) {
    console.error('Failed to parse plan_data:', e);
    return null;
  }
});

const isWeeklyPlan = computed(() => {
  return parsedPlan.value && Array.isArray(parsedPlan.value.days);
});

const isDailyPlan = computed(() => {
  return parsedPlan.value && Array.isArray(parsedPlan.value.meals) && !parsedPlan.value.days;
});

function getMealsForDay(day: number): MealItem[] {
  if (!parsedPlan.value) return [];
  
  // Handle weekly plan
  if (isWeeklyPlan.value) {
    const dayPlan = parsedPlan.value.days?.find((d: any) => d.day === day);
    return dayPlan?.meals || [];
  }
  
  // Handle daily plan - show same meals for all days
  if (isDailyPlan.value) {
    return parsedPlan.value.meals || [];
  }
  
  return [];
}

function isMealCompleted(day: number, mealType: string, mealName: string): boolean {
  return props.tracking.some(
    t => t.day_number === day && t.meal_type === mealType && t.meal_name === mealName && t.is_completed
  );
}

function isDayCompleted(day: number): boolean {
  return props.stats?.days_completed?.includes(day) || false;
}

function handleMealToggle(day: number, mealType: string, mealName: string, isCompleted: boolean) {
  emit("toggle-meal", day, mealType, mealName, isCompleted);
}
</script>

<style scoped>
.border-success {
  border: 2px solid rgb(var(--v-theme-success)) !important;
}
</style>
