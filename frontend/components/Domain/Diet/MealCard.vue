<template>
  <v-card 
    class="meal-card h-100" 
    :class="mealTypeClass"
    elevation="2"
  >
    <v-card-title class="d-flex align-center justify-space-between pb-1">
      <div class="d-flex align-center">
        <v-icon start size="small" :color="mealTypeColor">{{ mealIcon }}</v-icon>
        <span class="text-body-2 font-weight-medium">{{ meal.meal_type }}</span>
      </div>
      <v-chip size="x-small" :color="mealTypeColor" variant="flat">
        {{ meal.calories }} kcal
      </v-chip>
    </v-card-title>

    <v-card-text class="pt-0">
      <div class="text-h6 mb-2">{{ meal.name }}</div>
      
      <!-- Macros Row -->
      <div class="d-flex ga-2 mb-3">
        <v-chip size="x-small" color="blue" variant="tonal">
          P: {{ meal.protein }}g
        </v-chip>
        <v-chip size="x-small" color="orange" variant="tonal">
          C: {{ meal.carbs }}g
        </v-chip>
        <v-chip size="x-small" color="purple" variant="tonal">
          F: {{ meal.fat }}g
        </v-chip>
      </div>

      <!-- Ingredients -->
      <div class="mb-3">
        <div class="text-caption text-medium-emphasis mb-1">{{ $t("diet-generator.ingredients") }}</div>
        <div class="d-flex flex-wrap ga-1">
          <v-chip
            v-for="ingredient in meal.ingredients.slice(0, 5)"
            :key="ingredient"
            size="x-small"
            variant="outlined"
          >
            {{ ingredient }}
          </v-chip>
          <v-chip 
            v-if="meal.ingredients.length > 5"
            size="x-small"
            variant="text"
          >
            +{{ meal.ingredients.length - 5 }} more
          </v-chip>
        </div>
      </div>

      <!-- Instructions (collapsible) -->
      <v-expansion-panels variant="accordion" flat>
        <v-expansion-panel>
          <v-expansion-panel-title class="px-0 py-1" style="min-height: 32px;">
            <span class="text-caption">{{ $t("diet-generator.instructions") }}</span>
          </v-expansion-panel-title>
          <v-expansion-panel-text class="text-body-2">
            {{ meal.instructions }}
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-card-text>

    <v-card-actions>
      <v-btn
        size="small"
        variant="text"
        color="primary"
        @click="$emit('regenerate')"
      >
        <v-icon start size="small">{{ $globals.icons.refresh }}</v-icon>
        {{ $t("diet-generator.regenerate") }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { MealItem } from "~/lib/api/user/diet-generator";

const { $globals } = useNuxtApp();

const props = defineProps<{
  meal: MealItem;
}>();

defineEmits<{
  (e: "regenerate"): void;
}>();

const mealTypeColor = computed(() => {
  switch (props.meal.meal_type.toLowerCase()) {
    case "breakfast":
      return "amber";
    case "lunch":
      return "green";
    case "snack":
      return "blue";
    case "dinner":
      return "deep-purple";
    default:
      return "primary";
  }
});

const mealTypeClass = computed(() => {
  return `meal-${props.meal.meal_type.toLowerCase()}`;
});

const mealIcon = computed(() => {
  switch (props.meal.meal_type.toLowerCase()) {
    case "breakfast":
      return $globals.icons.weatherSunny;
    case "lunch":
      return $globals.icons.food;
    case "snack":
      return $globals.icons.bread;
    case "dinner":
      return $globals.icons.weatherNight;
    default:
      return $globals.icons.food;
  }
});
</script>

<style scoped>
.meal-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.meal-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
}
</style>
