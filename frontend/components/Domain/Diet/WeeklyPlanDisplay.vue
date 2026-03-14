<template>
  <div>
    <!-- Day Tabs -->
    <v-tabs v-model="selectedDay" color="primary" class="mb-4">
      <v-tab v-for="day in plan.days" :key="day.day" :value="day.day">
        {{ $t("diet-generator.day") }} {{ day.day }}
      </v-tab>
    </v-tabs>

    <!-- Selected Day Content -->
    <v-window v-model="selectedDay">
      <v-window-item v-for="day in plan.days" :key="day.day" :value="day.day">
        <v-card class="mb-4">
          <v-card-title class="d-flex align-center justify-space-between">
            <span>
              <v-icon start color="primary">{{ $globals.icons.calendarDay }}</v-icon>
              {{ $t("diet-generator.day") }} {{ day.day }}
            </span>
            <div class="d-flex ga-2">
              <v-chip size="small" color="primary">{{ day.total_calories }} kcal</v-chip>
              <v-chip size="small" color="blue" variant="tonal">P: {{ day.total_protein }}g</v-chip>
              <v-chip size="small" color="orange" variant="tonal">C: {{ day.total_carbs }}g</v-chip>
              <v-chip size="small" color="purple" variant="tonal">F: {{ day.total_fat }}g</v-chip>
            </div>
          </v-card-title>

          <v-card-text>
            <v-row>
              <v-col 
                v-for="meal in day.meals" 
                :key="meal.meal_type + meal.name"
                cols="12"
                sm="6"
                lg="3"
              >
                <MealCard 
                  :meal="meal" 
                  @regenerate="$emit('regenerate-meal', meal.meal_type, [meal.name])"
                />
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-window-item>
    </v-window>

    <!-- Grocery List -->
    <v-card v-if="plan.grocery_list && plan.grocery_list.length > 0" class="mt-4">
      <v-card-title>
        <v-icon start color="primary">{{ $globals.icons.cartCheck }}</v-icon>
        {{ $t("diet-generator.grocery-list") }}
      </v-card-title>
      <v-card-text>
        <v-row>
          <v-col 
            v-for="(items, columnIndex) in groceryColumns" 
            :key="columnIndex"
            cols="12"
            sm="6"
            md="4"
          >
            <v-list density="compact">
              <v-list-item 
                v-for="item in items" 
                :key="item"
                :title="item"
              >
                <template #prepend>
                  <v-checkbox-btn 
                    :model-value="checkedItems.includes(item)"
                    @update:model-value="toggleItem(item)"
                  />
                </template>
              </v-list-item>
            </v-list>
          </v-col>
        </v-row>
      </v-card-text>
      <v-card-actions>
        <v-btn 
          color="primary" 
          variant="text"
          @click="copyGroceryList"
        >
          <v-icon start>{{ $globals.icons.contentCopy }}</v-icon>
          {{ $t("diet-generator.copy-list") }}
        </v-btn>
        
        <v-btn 
          color="success" 
          variant="text"
          :loading="savingRecipes"
          @click="saveAsRecipes"
        >
          <v-icon start>{{ $globals.icons.create }}</v-icon>
          {{ $t("diet-generator.save-as-recipes") }}
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- Notes -->
    <v-alert v-if="plan.notes" type="info" variant="tonal" class="mt-4">
      <div class="text-subtitle-2">{{ $t("diet-generator.tips") }}</div>
      <div class="text-body-2">{{ plan.notes }}</div>
    </v-alert>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useUserApi } from "~/composables/api";
import MealCard from "./MealCard.vue";
import type { WeeklyDietPlan } from "~/lib/api/user/diet-generator";

const { $globals } = useNuxtApp();
const { $toast } = useNuxtApp();
const userApi = useUserApi();

const props = defineProps<{
  plan: WeeklyDietPlan;
}>();

defineEmits<{
  (e: "regenerate-meal", mealType: string, excludeMeals: string[]): void;
}>();

const selectedDay = ref(1);
const checkedItems = ref<string[]>([]);
const savingRecipes = ref(false);

// Split grocery list into columns
const groceryColumns = computed(() => {
  const items = props.plan.grocery_list || [];
  const columnCount = 3;
  const itemsPerColumn = Math.ceil(items.length / columnCount);
  const columns: string[][] = [];
  
  for (let i = 0; i < columnCount; i++) {
    const start = i * itemsPerColumn;
    const end = start + itemsPerColumn;
    columns.push(items.slice(start, end));
  }
  
  return columns;
});

function toggleItem(item: string) {
  const index = checkedItems.value.indexOf(item);
  if (index === -1) {
    checkedItems.value.push(item);
  } else {
    checkedItems.value.splice(index, 1);
  }
}

async function copyGroceryList() {
  const list = props.plan.grocery_list?.join("\n") || "";
  await navigator.clipboard.writeText(list);
  $toast.success("Grocery list copied to clipboard!");
}

async function saveAsRecipes() {
  savingRecipes.value = true;
  let savedCount = 0;
  
  try {
    // Collect all unique meals from the weekly plan
    const uniqueMeals = new Map<string, any>();
    
    props.plan.days.forEach(day => {
      day.meals.forEach(meal => {
        const mealKey = `${meal.name}-${meal.meal_type}`;
        if (!uniqueMeals.has(mealKey)) {
          uniqueMeals.set(mealKey, meal);
        }
      });
    });
    
    // Save each unique meal as a recipe
    for (const meal of uniqueMeals.values()) {
      try {
        // Create recipe using Mealie's CreateRecipe format
        const recipeData = {
          name: meal.name,
          description: `Generated from diet plan - ${meal.meal_type}`,
          recipe_yield: meal.serving_size || "1 serving",
          prep_time: "PT15M", // Default 15 minutes prep
          cook_time: "PT30M", // Default 30 minutes cook
          recipe_ingredient: meal.ingredients?.map((ingredient, index) => ({
            note: ingredient,
            original_text: ingredient,
            position: index + 1
          })) || [],
          recipe_instructions: meal.instructions ? [{
            text: meal.instructions,
            position: 1
          }] : [],
          nutrition: {
            calories: meal.calories?.toString() || null,
            protein: meal.protein?.toString() || null,
            carbohydrate_content: meal.carbs?.toString() || null,
            fat_content: meal.fat?.toString() || null
          },
          tags: [{ name: "Diet Plan" }, { name: meal.meal_type }],
          recipe_category: [{ name: meal.meal_type }]
        };
        
        const { data } = await userApi.recipes.createOne(recipeData);
        if (data) {
          savedCount++;
        }
      } catch (error) {
        console.error(`Failed to save recipe for ${meal.name}:`, error);
      }
    }
    
    if (savedCount > 0) {
      $toast.success(`Successfully saved ${savedCount} recipes from your diet plan!`);
    } else {
      $toast.warning("No recipes were saved. Please try again.");
    }
  } catch (error) {
    console.error('Failed to save recipes:', error);
    $toast.error("Failed to save recipes. Please try again.");
  } finally {
    savingRecipes.value = false;
  }
}
</script>
