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
import MealCard from "./MealCard.vue";
import type { WeeklyDietPlan } from "~/lib/api/user/diet-generator";

const { $globals } = useNuxtApp();

const props = defineProps<{
  plan: WeeklyDietPlan;
}>();

defineEmits<{
  (e: "regenerate-meal", mealType: string, excludeMeals: string[]): void;
}>();

const selectedDay = ref(1);
const checkedItems = ref<string[]>([]);

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
}
</script>
