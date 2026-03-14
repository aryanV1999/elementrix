<template>
  <v-container class="pa-4">
    <v-row>
      <v-col cols="12">
        <v-card class="mb-4">
          <v-card-title class="d-flex align-center">
            <v-icon start color="primary">{{ $globals.icons.food }}</v-icon>
            {{ $t("diet-generator.title") }}
          </v-card-title>
          <v-card-subtitle>
            {{ $t("diet-generator.subtitle") }}
          </v-card-subtitle>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <!-- Input Form Column -->
      <v-col cols="12" md="4">
        <DietInputForm
          v-model="dietInput"
          :loading="loading"
          :calculation="calorieCalculation"
          @calculate="calculateCalories"
          @generate="generateDailyPlan"
          @generate-weekly="generateWeeklyPlan"
        />
      </v-col>

      <!-- Results Column -->
      <v-col cols="12" md="8">
        <div v-if="loading" class="d-flex justify-center align-center" style="min-height: 400px;">
          <div class="text-center">
            <v-progress-circular indeterminate color="primary" size="64" />
            <p class="mt-4 text-body-1">{{ $t("diet-generator.generating") }}</p>
          </div>
        </div>

        <template v-else-if="dietPlan || weeklyPlan">
          <!-- Nutrition Summary -->
          <NutritionSummary
            v-if="dietPlan || weeklyPlan"
            :daily-calories="activePlan?.daily_calories || 0"
            :target-protein="activePlan?.target_protein || 0"
            :target-carbs="activePlan?.target_carbs || 0"
            :target-fat="activePlan?.target_fat || 0"
            class="mb-4"
          />

          <!-- Daily Plan Display -->
          <DietPlanDisplay
            v-if="dietPlan && !weeklyPlan"
            :plan="dietPlan"
            @regenerate-meal="handleRegenerateMeal"
          />

          <!-- Weekly Plan Display -->
          <WeeklyPlanDisplay
            v-if="weeklyPlan"
            :plan="weeklyPlan"
            @regenerate-meal="handleRegenerateMeal"
          />
        </template>

        <template v-else>
          <v-card class="d-flex justify-center align-center" style="min-height: 400px;">
            <div class="text-center pa-8">
              <v-icon size="80" color="grey-lighten-1">{{ $globals.icons.food }}</v-icon>
              <h3 class="mt-4 text-h6 text-grey">{{ $t("diet-generator.no-plan-yet") }}</h3>
              <p class="text-body-2 text-grey mt-2">{{ $t("diet-generator.fill-form-instructions") }}</p>
            </div>
          </v-card>
        </template>
      </v-col>
    </v-row>

    <!-- Error Snackbar -->
    <v-snackbar v-model="errorSnackbar" color="error" timeout="5000">
      {{ errorMessage }}
      <template #actions>
        <v-btn variant="text" @click="errorSnackbar = false">{{ $t("general.close") }}</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useUserApi } from "~/composables/api";
import DietInputForm from "~/components/Domain/Diet/DietInputForm.vue";
import DietPlanDisplay from "~/components/Domain/Diet/DietPlanDisplay.vue";
import WeeklyPlanDisplay from "~/components/Domain/Diet/WeeklyPlanDisplay.vue";
import NutritionSummary from "~/components/Domain/Diet/NutritionSummary.vue";
import type {
  DietInput,
  DietPlanResponse,
  WeeklyDietPlan,
  CalorieCalculation,
} from "~/lib/api/user/diet-generator";

const { $globals } = useNuxtApp();
const api = useUserApi();
const i18n = useI18n();

// State
const loading = ref(false);
const errorSnackbar = ref(false);
const errorMessage = ref("");

const dietInput = ref<DietInput>({
  current_weight: 80,
  target_weight: 75,
  maintenance_calories: 2200,
  timeline_weeks: 8,
  diet_preference: "non-vegetarian",
  meals_per_day: 4,
  allergies: [],
  cuisine_preference: "",
  protein_preference: "",
});

const calorieCalculation = ref<CalorieCalculation | null>(null);
const dietPlan = ref<DietPlanResponse | null>(null);
const weeklyPlan = ref<WeeklyDietPlan | null>(null);

const activePlan = computed(() => weeklyPlan.value || dietPlan.value);

// Methods
async function calculateCalories() {
  try {
    const { data } = await api.dietGenerator.calculateCalories(dietInput.value);
    if (data) {
      calorieCalculation.value = data;
    }
  } catch (error: any) {
    showError(error.message || i18n.t("diet-generator.error-calculating"));
  }
}

async function generateDailyPlan() {
  loading.value = true;
  weeklyPlan.value = null;
  dietPlan.value = null;

  try {
    const { data } = await api.dietGenerator.generateDailyPlan(dietInput.value);
    if (data) {
      dietPlan.value = data;
    }
  } catch (error: any) {
    showError(error.message || i18n.t("diet-generator.error-generating"));
  } finally {
    loading.value = false;
  }
}

async function generateWeeklyPlan() {
  loading.value = true;
  dietPlan.value = null;
  weeklyPlan.value = null;

  try {
    const { data } = await api.dietGenerator.generateWeeklyPlan(dietInput.value);
    if (data) {
      weeklyPlan.value = data;
    }
  } catch (error: any) {
    showError(error.message || i18n.t("diet-generator.error-generating"));
  } finally {
    loading.value = false;
  }
}

async function handleRegenerateMeal(mealType: string, excludeMeals: string[]) {
  try {
    loading.value = true;
    const { data } = await api.dietGenerator.regenerateMeal(dietInput.value, mealType, excludeMeals);
    if (data && dietPlan.value) {
      // Replace the meal in the current plan
      const index = dietPlan.value.meals.findIndex((m) => m.meal_type === mealType);
      if (index !== -1) {
        dietPlan.value.meals[index] = data;
      }
    }
  } catch (error: any) {
    showError(error.message || i18n.t("diet-generator.error-regenerating"));
  } finally {
    loading.value = false;
  }
}

function showError(message: string) {
  errorMessage.value = message;
  errorSnackbar.value = true;
}

// Initial calculation
onMounted(() => {
  calculateCalories();
});
</script>
