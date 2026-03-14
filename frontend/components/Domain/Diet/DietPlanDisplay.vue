<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      <v-icon start color="primary">{{ $globals.icons.food }}</v-icon>
      {{ $t("diet-generator.daily-plan") }}
    </v-card-title>

    <v-card-text>
      <v-row>
        <v-col 
          v-for="meal in plan.meals" 
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

      <!-- Notes -->
      <v-alert v-if="plan.notes" type="info" variant="tonal" class="mt-4">
        <div class="text-subtitle-2">{{ $t("diet-generator.tips") }}</div>
        <div class="text-body-2">{{ plan.notes }}</div>
      </v-alert>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import MealCard from "./MealCard.vue";
import type { DietPlanResponse } from "~/lib/api/user/diet-generator";

const { $globals } = useNuxtApp();

defineProps<{
  plan: DietPlanResponse;
}>();

defineEmits<{
  (e: "regenerate-meal", mealType: string, excludeMeals: string[]): void;
}>();
</script>
