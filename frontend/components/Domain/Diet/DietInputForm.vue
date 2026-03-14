<template>
  <v-card>
    <v-card-title>
      <v-icon start>{{ $globals.icons.accountCog }}</v-icon>
      {{ $t("diet-generator.input-form-title") }}
    </v-card-title>

    <v-card-text>
      <v-form ref="formRef" v-model="formValid">
        <!-- Personal Data Section -->
        <div class="text-subtitle-2 mb-2 mt-2">{{ $t("diet-generator.personal-data") }}</div>
        
        <v-text-field
          v-model.number="localInput.current_weight"
          :label="$t('diet-generator.current-weight')"
          type="number"
          suffix="kg"
          :rules="[rules.required, rules.positive]"
          variant="outlined"
          density="compact"
          class="mb-2"
        />

        <v-text-field
          v-model.number="localInput.target_weight"
          :label="$t('diet-generator.target-weight')"
          type="number"
          suffix="kg"
          :rules="[rules.required, rules.positive]"
          variant="outlined"
          density="compact"
          class="mb-2"
        />

        <v-text-field
          v-model.number="localInput.maintenance_calories"
          :label="$t('diet-generator.maintenance-calories')"
          type="number"
          suffix="kcal"
          :rules="[rules.required, rules.positive]"
          variant="outlined"
          density="compact"
          class="mb-2"
        />

        <v-text-field
          v-model.number="localInput.timeline_weeks"
          :label="$t('diet-generator.timeline-weeks')"
          type="number"
          suffix="weeks"
          :rules="[rules.required, rules.positiveInt, rules.maxWeeks]"
          variant="outlined"
          density="compact"
          class="mb-2"
        />

        <!-- Preferences Section -->
        <div class="text-subtitle-2 mb-2 mt-4">{{ $t("diet-generator.preferences") }}</div>

        <v-select
          v-model="localInput.diet_preference"
          :label="$t('diet-generator.diet-preference')"
          :items="dietPreferenceOptions"
          variant="outlined"
          density="compact"
          class="mb-2"
        />

        <v-select
          v-model.number="localInput.meals_per_day"
          :label="$t('diet-generator.meals-per-day')"
          :items="mealsPerDayOptions"
          variant="outlined"
          density="compact"
          class="mb-2"
        />

        <!-- Optional Inputs Section -->
        <v-expansion-panels class="mb-4">
          <v-expansion-panel>
            <v-expansion-panel-title>
              <v-icon start size="small">{{ $globals.icons.cog }}</v-icon>
              {{ $t("diet-generator.optional-inputs") }}
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-combobox
                v-model="localInput.allergies"
                :label="$t('diet-generator.allergies')"
                :items="commonAllergies"
                multiple
                chips
                closable-chips
                variant="outlined"
                density="compact"
                class="mb-2"
              />

              <v-text-field
                v-model="localInput.cuisine_preference"
                :label="$t('diet-generator.cuisine-preference')"
                :placeholder="$t('diet-generator.cuisine-placeholder')"
                variant="outlined"
                density="compact"
                class="mb-2"
              />

              <v-text-field
                v-model="localInput.protein_preference"
                :label="$t('diet-generator.protein-preference')"
                :placeholder="$t('diet-generator.protein-placeholder')"
                variant="outlined"
                density="compact"
              />
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>

        <!-- Calorie Preview -->
        <v-card v-if="calculation" variant="tonal" color="primary" class="mb-4">
          <v-card-text>
            <div class="text-subtitle-2 mb-2">{{ $t("diet-generator.calorie-preview") }}</div>
            <div class="d-flex justify-space-between mb-1">
              <span>{{ $t("diet-generator.daily-target") }}:</span>
              <strong>{{ calculation.daily_calories }} kcal</strong>
            </div>
            <div class="d-flex justify-space-between mb-1">
              <span>{{ $t("diet-generator.daily-adjustment") }}:</span>
              <strong :class="calculation.daily_adjustment < 0 ? 'text-error' : 'text-success'">
                {{ calculation.daily_adjustment > 0 ? '+' : '' }}{{ calculation.daily_adjustment }} kcal
              </strong>
            </div>
            <div class="d-flex justify-space-between mb-1">
              <span>{{ $t("diet-generator.goal") }}:</span>
              <strong>{{ calculation.summary.goal }}</strong>
            </div>
            <v-chip
              v-if="!calculation.summary.is_safe"
              color="warning"
              size="small"
              class="mt-2"
            >
              {{ $t("diet-generator.aggressive-goal-warning") }}
            </v-chip>
          </v-card-text>
        </v-card>

        <!-- Action Buttons -->
        <v-btn
          block
          color="secondary"
          variant="outlined"
          class="mb-2"
          :disabled="loading"
          @click="$emit('calculate')"
        >
          <v-icon start>{{ $globals.icons.calculator }}</v-icon>
          {{ $t("diet-generator.calculate-preview") }}
        </v-btn>

        <v-btn
          block
          color="primary"
          class="mb-2"
          :disabled="!formValid || loading"
          :loading="loading"
          @click="$emit('generate')"
        >
          <v-icon start>{{ $globals.icons.food }}</v-icon>
          {{ $t("diet-generator.generate-daily") }}
        </v-btn>

        <v-btn
          block
          color="primary"
          variant="outlined"
          :disabled="!formValid || loading"
          :loading="loading"
          @click="$emit('generate-weekly')"
        >
          <v-icon start>{{ $globals.icons.calendarMultiselect }}</v-icon>
          {{ $t("diet-generator.generate-weekly") }}
        </v-btn>
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import type { DietInput, CalorieCalculation } from "~/lib/api/user/diet-generator";

const { $globals } = useNuxtApp();
const i18n = useI18n();

const props = defineProps<{
  modelValue: DietInput;
  loading: boolean;
  calculation: CalorieCalculation | null;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: DietInput): void;
  (e: "calculate"): void;
  (e: "generate"): void;
  (e: "generate-weekly"): void;
}>();

const formRef = ref();
const formValid = ref(false);

const localInput = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
});

// Options
const dietPreferenceOptions = [
  { title: i18n.t("diet-generator.vegetarian"), value: "vegetarian" },
  { title: i18n.t("diet-generator.non-vegetarian"), value: "non-vegetarian" },
  { title: i18n.t("diet-generator.vegan"), value: "vegan" },
  { title: i18n.t("diet-generator.keto"), value: "keto" },
  { title: i18n.t("diet-generator.paleo"), value: "paleo" },
];

const mealsPerDayOptions = [
  { title: "3 meals", value: 3 },
  { title: "4 meals", value: 4 },
  { title: "5 meals", value: 5 },
  { title: "6 meals", value: 6 },
];

const commonAllergies = [
  "Peanuts",
  "Tree nuts",
  "Milk",
  "Eggs",
  "Wheat",
  "Soy",
  "Fish",
  "Shellfish",
  "Sesame",
  "Gluten",
];

// Validation rules
const rules = {
  required: (v: any) => !!v || i18n.t("diet-generator.field-required"),
  positive: (v: number) => v > 0 || i18n.t("diet-generator.must-be-positive"),
  positiveInt: (v: number) => (Number.isInteger(v) && v > 0) || i18n.t("diet-generator.must-be-positive-integer"),
  maxWeeks: (v: number) => v <= 52 || i18n.t("diet-generator.max-52-weeks"),
};

// Watch for input changes to recalculate
watch(localInput, () => {
  emit("calculate");
}, { deep: true });
</script>
