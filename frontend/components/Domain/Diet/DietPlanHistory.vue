<template>
  <div>
    <v-card v-if="loading" class="d-flex justify-center align-center" style="min-height: 300px;">
      <v-progress-circular indeterminate color="primary" />
    </v-card>

    <template v-else-if="plans.length > 0">
      <v-row>
        <v-col
          v-for="plan in plans"
          :key="plan.id"
          cols="12"
          md="6"
          lg="4"
        >
          <v-card>
            <v-card-title class="d-flex align-center">
              <span class="flex-grow-1">{{ plan.name }}</span>
              <v-chip v-if="plan.is_active" color="success" size="small">
                {{ $t("diet-generator.active") }}
              </v-chip>
            </v-card-title>

            <v-card-subtitle v-if="plan.description">
              {{ plan.description }}
            </v-card-subtitle>

            <v-card-text>
              <!-- Nutrition Summary -->
              <v-row dense class="mb-2">
                <v-col cols="6">
                  <div class="text-body-2">
                    <v-icon size="small" color="orange">{{ $globals.icons.fire }}</v-icon>
                    {{ plan.daily_calories }} {{ $t("diet-generator.cal-day") }}
                  </div>
                </v-col>
                <v-col cols="6">
                  <div class="text-body-2">
                    <v-icon size="small" color="red">{{ $globals.icons.food }}</v-icon>
                    {{ plan.target_protein?.toFixed(0) }}g {{ $t("diet-generator.protein") }}
                  </div>
                </v-col>
              </v-row>

              <!-- Date Info -->
              <div class="text-caption text-grey">
                {{ $t("diet-generator.created") }}: {{ formatDate(plan.created_at) }}
              </div>
              <div v-if="plan.start_date" class="text-caption text-grey">
                {{ $t("diet-generator.started") }}: {{ formatDate(plan.start_date) }}
              </div>
            </v-card-text>

            <v-card-actions>
              <v-btn
                v-if="!plan.is_active"
                color="primary"
                variant="text"
                size="small"
                @click="$emit('activate', plan.id)"
              >
                {{ $t("diet-generator.make-active") }}
              </v-btn>
              <v-btn
                color="info"
                variant="text"
                size="small"
                @click="$emit('view', plan.id)"
              >
                {{ $t("general.view") }}
              </v-btn>
              <v-spacer />
              <v-btn
                color="error"
                variant="text"
                size="small"
                icon
                @click="confirmDelete(plan)"
              >
                <v-icon>{{ $globals.icons.delete }}</v-icon>
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>
    </template>

    <v-card v-else class="d-flex justify-center align-center" style="min-height: 300px;">
      <div class="text-center pa-8">
        <v-icon size="80" color="grey-lighten-1">{{ $globals.icons.formatListBulleted }}</v-icon>
        <h3 class="mt-4 text-h6 text-grey">{{ $t("diet-generator.no-saved-plans") }}</h3>
        <p class="text-body-2 text-grey mt-2">{{ $t("diet-generator.generate-first") }}</p>
      </div>
    </v-card>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title>{{ $t("diet-generator.delete-plan") }}</v-card-title>
        <v-card-text>
          {{ $t("diet-generator.delete-confirm", { name: planToDelete?.name }) }}
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">{{ $t("general.cancel") }}</v-btn>
          <v-btn color="error" @click="handleDelete">{{ $t("general.delete") }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import type { SavedDietPlanSummary } from "~/lib/api/user/diet-generator";

const { $globals } = useNuxtApp();

interface Props {
  plans: SavedDietPlanSummary[];
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
});

const emit = defineEmits<{
  (e: "activate", planId: string): void;
  (e: "delete", planId: string): void;
  (e: "view", planId: string): void;
}>();

const deleteDialog = ref(false);
const planToDelete = ref<SavedDietPlanSummary | null>(null);

function formatDate(dateStr?: string): string {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleDateString();
}

function confirmDelete(plan: SavedDietPlanSummary) {
  planToDelete.value = plan;
  deleteDialog.value = true;
}

function handleDelete() {
  if (planToDelete.value) {
    emit("delete", planToDelete.value.id);
  }
  deleteDialog.value = false;
  planToDelete.value = null;
}
</script>
