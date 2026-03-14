<template>
  <v-card variant="tonal" color="primary" class="mb-4">
    <v-card-text>
      <div class="text-h6 mb-3">{{ $t("diet-generator.nutrition-summary") }}</div>
      
      <v-row>
        <v-col cols="6" sm="3">
          <div class="text-center">
            <div class="text-h5 font-weight-bold">{{ dailyCalories }}</div>
            <div class="text-caption">{{ $t("diet-generator.calories") }}</div>
          </div>
        </v-col>
        
        <v-col cols="6" sm="3">
          <div class="text-center">
            <div class="text-h5 font-weight-bold text-blue">{{ targetProtein }}g</div>
            <div class="text-caption">{{ $t("diet-generator.protein") }}</div>
          </div>
        </v-col>
        
        <v-col cols="6" sm="3">
          <div class="text-center">
            <div class="text-h5 font-weight-bold text-orange">{{ targetCarbs }}g</div>
            <div class="text-caption">{{ $t("diet-generator.carbs") }}</div>
          </div>
        </v-col>
        
        <v-col cols="6" sm="3">
          <div class="text-center">
            <div class="text-h5 font-weight-bold text-purple">{{ targetFat }}g</div>
            <div class="text-caption">{{ $t("diet-generator.fat") }}</div>
          </div>
        </v-col>
      </v-row>

      <!-- Macro Distribution Bar -->
      <div class="mt-4">
        <div class="text-caption mb-1">{{ $t("diet-generator.macro-distribution") }}</div>
        <div class="d-flex rounded overflow-hidden" style="height: 24px;">
          <div 
            class="bg-blue d-flex align-center justify-center text-white text-caption"
            :style="{ width: proteinPercentage + '%' }"
          >
            {{ proteinPercentage }}%
          </div>
          <div 
            class="bg-orange d-flex align-center justify-center text-white text-caption"
            :style="{ width: carbsPercentage + '%' }"
          >
            {{ carbsPercentage }}%
          </div>
          <div 
            class="bg-purple d-flex align-center justify-center text-white text-caption"
            :style="{ width: fatPercentage + '%' }"
          >
            {{ fatPercentage }}%
          </div>
        </div>
        <div class="d-flex justify-space-between mt-1">
          <span class="text-caption text-blue">{{ $t("diet-generator.protein") }}</span>
          <span class="text-caption text-orange">{{ $t("diet-generator.carbs") }}</span>
          <span class="text-caption text-purple">{{ $t("diet-generator.fat") }}</span>
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  dailyCalories: number;
  targetProtein: number;
  targetCarbs: number;
  targetFat: number;
}>();

// Calculate percentage distribution
const totalMacroCalories = computed(() => {
  return (props.targetProtein * 4) + (props.targetCarbs * 4) + (props.targetFat * 9);
});

const proteinPercentage = computed(() => {
  if (totalMacroCalories.value === 0) return 0;
  return Math.round((props.targetProtein * 4 / totalMacroCalories.value) * 100);
});

const carbsPercentage = computed(() => {
  if (totalMacroCalories.value === 0) return 0;
  return Math.round((props.targetCarbs * 4 / totalMacroCalories.value) * 100);
});

const fatPercentage = computed(() => {
  if (totalMacroCalories.value === 0) return 0;
  return Math.round((props.targetFat * 9 / totalMacroCalories.value) * 100);
});
</script>
