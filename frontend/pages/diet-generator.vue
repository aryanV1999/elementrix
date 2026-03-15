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

        <!-- Tab Navigation -->
        <v-tabs v-model="activeTab" color="primary" class="mb-4">
          <v-tab value="current">
            <v-icon start>{{ $globals.icons.calendar }}</v-icon>
            {{ $t("diet-generator.my-plan") }}
          </v-tab>
          <v-tab value="generate">
            <v-icon start>{{ $globals.icons.create }}</v-icon>
            {{ $t("diet-generator.generate-new") }}
          </v-tab>
          <v-tab value="history">
            <v-icon start>{{ $globals.icons.formatListBulleted }}</v-icon>
            {{ $t("diet-generator.history") }}
          </v-tab>
        </v-tabs>
      </v-col>
    </v-row>

    <!-- Current Plan Tab -->
    <v-window v-model="activeTab">
      <v-window-item value="current">
        <CurrentDietPlan
          v-if="savedPlan"
          :plan="savedPlan"
          :stats="planStats"
          :tracking="mealTracking"
          @toggle-meal="handleToggleMeal"
          @view-full-plan="viewFullPlan"
        />
        <v-card v-else class="d-flex justify-center align-center" style="min-height: 400px;">
          <div class="text-center pa-8">
            <v-icon size="80" color="grey-lighten-1">{{ $globals.icons.calendar }}</v-icon>
            <h3 class="mt-4 text-h6 text-grey">{{ $t("diet-generator.no-active-plan") }}</h3>
            <p class="text-body-2 text-grey mt-2">{{ $t("diet-generator.generate-and-save") }}</p>
            <v-btn color="primary" class="mt-4" @click="activeTab = 'generate'">
              {{ $t("diet-generator.generate-plan") }}
            </v-btn>
          </div>
        </v-card>
      </v-window-item>

      <!-- Generate New Tab -->
      <v-window-item value="generate">
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
              <!-- Save Plan Button -->
              <v-card class="mb-4 pa-4">
                <div class="d-flex align-center justify-space-between">
                  <div>
                    <h3 class="text-h6">{{ $t("diet-generator.like-this-plan") }}</h3>
                    <p class="text-body-2 text-grey">{{ $t("diet-generator.save-to-track") }}</p>
                  </div>
                  <v-btn
                    color="success"
                    :loading="savingPlan"
                    @click="openSavePlanDialog"
                  >
                    <v-icon start>{{ $globals.icons.save }}</v-icon>
                    {{ $t("diet-generator.follow-plan") }}
                  </v-btn>
                </div>
              </v-card>

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
      </v-window-item>

      <!-- History Tab -->
      <v-window-item value="history">
        <DietPlanHistory
          :plans="savedPlansList"
          :loading="loadingHistory"
          @activate="handleActivatePlan"
          @delete="handleDeletePlan"
          @view="handleViewPlan"
        />
      </v-window-item>
    </v-window>

    <!-- Save Plan Dialog -->
    <v-dialog v-model="savePlanDialog" max-width="500">
      <v-card>
        <v-card-title>{{ $t("diet-generator.save-plan") }}</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="planName"
            :label="$t('diet-generator.plan-name')"
            variant="outlined"
          />
          <v-textarea
            v-model="planDescription"
            :label="$t('diet-generator.plan-description')"
            variant="outlined"
            rows="2"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="savePlanDialog = false">{{ $t("general.cancel") }}</v-btn>
          <v-btn color="primary" :loading="savingPlan" @click="savePlan">
            {{ $t("diet-generator.save-and-follow") }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Error Snackbar -->
    <v-snackbar v-model="errorSnackbar" color="error" timeout="5000">
      {{ errorMessage }}
      <template #actions>
        <v-btn variant="text" @click="errorSnackbar = false">{{ $t("general.close") }}</v-btn>
      </template>
    </v-snackbar>

    <!-- Success Snackbar -->
    <v-snackbar v-model="successSnackbar" color="success" timeout="3000">
      {{ successMessage }}
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useUserApi } from "~/composables/api";
import { useMealieAuth } from "~/composables/use-mealie-auth";
import DietInputForm from "~/components/Domain/Diet/DietInputForm.vue";
import DietPlanDisplay from "~/components/Domain/Diet/DietPlanDisplay.vue";
import WeeklyPlanDisplay from "~/components/Domain/Diet/WeeklyPlanDisplay.vue";
import NutritionSummary from "~/components/Domain/Diet/NutritionSummary.vue";
import CurrentDietPlan from "~/components/Domain/Diet/CurrentDietPlan.vue";
import DietPlanHistory from "~/components/Domain/Diet/DietPlanHistory.vue";
import type {
  DietInput,
  DietPlanResponse,
  WeeklyDietPlan,
  CalorieCalculation,
  SavedDietPlan,
  SavedDietPlanSummary,
  MealTracking,
  PlanStats,
} from "~/lib/api/user/diet-generator";

const { $globals } = useNuxtApp();
const api = useUserApi();
const i18n = useI18n();
const { user } = useMealieAuth();

// Tabs
const activeTab = ref("current");

// State
const loading = ref(false);
const loadingHistory = ref(false);
const errorSnackbar = ref(false);
const errorMessage = ref("");
const successSnackbar = ref(false);
const successMessage = ref("");

// Save Dialog
const savePlanDialog = ref(false);
const savingPlan = ref(false);
const planName = ref("My Diet Plan");
const planDescription = ref("");

// Diet Input
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

// Generated Plans
const calorieCalculation = ref<CalorieCalculation | null>(null);
const dietPlan = ref<DietPlanResponse | null>(null);
const weeklyPlan = ref<WeeklyDietPlan | null>(null);

// Saved Plans
const savedPlan = ref<SavedDietPlan | null>(null);
const savedPlansList = ref<SavedDietPlanSummary[]>([]);
const planStats = ref<PlanStats | null>(null);
const mealTracking = ref<MealTracking[]>([]);

const activePlan = computed(() => weeklyPlan.value || dietPlan.value);

// Methods
async function loadActivePlan() {
  if (!user.value?.id) {
    console.log('No user ID, skipping loadActivePlan');
    return;
  }
  
  console.log('Loading active plan for user:', user.value.id);
  try {
    const { data } = await api.dietGenerator.getActivePlan(user.value.id);
    console.log('Active plan response:', data);
    if (data) {
      savedPlan.value = data;
      mealTracking.value = data.meal_tracking || [];
      console.log('Loaded plan:', savedPlan.value);
      console.log('Meal tracking:', mealTracking.value);
      // Load stats
      const statsResponse = await api.dietGenerator.getStats(data.id);
      if (statsResponse.data) {
        planStats.value = statsResponse.data;
        console.log('Plan stats:', planStats.value);
      }
    } else {
      console.log('No active plan found');
    }
  } catch (error) {
    console.error("Error loading active plan:", error);
  }
}

async function loadPlanHistory() {
  if (!user.value?.id) return;
  
  loadingHistory.value = true;
  try {
    const { data } = await api.dietGenerator.getAllPlans(user.value.id);
    if (data) {
      savedPlansList.value = data;
    }
  } catch (error) {
    console.error("Error loading plan history:", error);
  } finally {
    loadingHistory.value = false;
  }
}

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

function openSavePlanDialog() {
  planName.value = `Diet Plan - ${new Date().toLocaleDateString()}`;
  planDescription.value = "";
  savePlanDialog.value = true;
}

async function savePlan() {
  if (!user.value?.id || !user.value?.groupId) {
    showError("User not logged in or missing group information");
    return;
  }

  const planToSave = weeklyPlan.value || dietPlan.value;
  if (!planToSave) {
    showError("No plan to save");
    return;
  }

  savingPlan.value = true;
  try {
    const { data } = await api.dietGenerator.savePlan(user.value.id, user.value.groupId, {
      name: planName.value,
      description: planDescription.value,
      is_active: true,
      plan_data: JSON.stringify(planToSave),
      daily_calories: planToSave.daily_calories,
      target_protein: planToSave.target_protein,
      target_carbs: planToSave.target_carbs,
      target_fat: planToSave.target_fat,
    });

    if (data) {
      savedPlan.value = data;
      savePlanDialog.value = false;
      showSuccess(i18n.t("diet-generator.plan-saved"));
      activeTab.value = "current";
      // Reload plan data
      await loadActivePlan();
      await loadPlanHistory();
    }
  } catch (error: any) {
    showError(error.message || i18n.t("diet-generator.error-saving"));
  } finally {
    savingPlan.value = false;
  }
}

async function handleToggleMeal(dayNumber: number, mealType: string, mealName: string, isCompleted: boolean) {
  if (!savedPlan.value) return;

  try {
    const { data } = await api.dietGenerator.toggleMealCompletion(savedPlan.value.id, {
      day_number: dayNumber,
      meal_type: mealType,
      meal_name: mealName,
      is_completed: isCompleted,
    });

    if (data) {
      // Update local tracking
      const index = mealTracking.value.findIndex(
        t => t.day_number === dayNumber && t.meal_type === mealType && t.meal_name === mealName
      );
      if (index !== -1) {
        mealTracking.value[index] = data;
      } else {
        mealTracking.value.push(data);
      }

      // Refresh stats
      const statsResponse = await api.dietGenerator.getStats(savedPlan.value.id);
      if (statsResponse.data) {
        planStats.value = statsResponse.data;
      }
    }
  } catch (error: any) {
    showError(error.message || i18n.t("diet-generator.error-tracking"));
  }
}

async function handleActivatePlan(planId: string) {
  if (!user.value?.id) return;

  try {
    const { data } = await api.dietGenerator.activatePlan(planId, user.value.id);
    if (data) {
      savedPlan.value = data;
      showSuccess(i18n.t("diet-generator.plan-activated"));
      await loadActivePlan();
      await loadPlanHistory();
      activeTab.value = "current";
    }
  } catch (error: any) {
    showError(error.message || i18n.t("diet-generator.error-activating"));
  }
}

async function handleDeletePlan(planId: string) {
  if (!user.value?.id) return;

  try {
    await api.dietGenerator.deletePlan(planId, user.value.id);
    showSuccess(i18n.t("diet-generator.plan-deleted"));
    await loadPlanHistory();
    if (savedPlan.value?.id === planId) {
      savedPlan.value = null;
      await loadActivePlan();
    }
  } catch (error: any) {
    showError(error.message || i18n.t("diet-generator.error-deleting"));
  }
}

async function handleViewPlan(planId: string) {
  console.log("Viewing plan:", planId);
  try {
    const { data } = await api.dietGenerator.getPlan(planId);
    if (data) {
      // Set as current viewed plan
      savedPlan.value = data;
      mealTracking.value = data.meal_tracking || [];
      
      // Load stats
      const statsResponse = await api.dietGenerator.getStats(data.id);
      if (statsResponse.data) {
        planStats.value = statsResponse.data;
      }
      
      // Switch to current tab to view
      activeTab.value = "current";
    }
  } catch (error: any) {
    showError(error.message || i18n.t("diet-generator.error-loading-plan"));
  }
}

function viewFullPlan() {
  // Could expand a dialog or navigate
  console.log("View full plan clicked");
}

function showError(message: string) {
  errorMessage.value = message;
  errorSnackbar.value = true;
}

function showSuccess(message: string) {
  successMessage.value = message;
  successSnackbar.value = true;
}

// Initial load
onMounted(async () => {
  await calculateCalories();
  await loadActivePlan();
  await loadPlanHistory();
});
</script>
