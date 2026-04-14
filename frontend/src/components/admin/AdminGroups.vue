<template>
  <v-card-text class="pa-6">
    <v-row class="mb-6">
      <v-col cols="12" class="d-flex align-center justify-space-between">
        <h6 class="text-h6 font-weight-bold"> Управление группами</h6>
        <v-btn 
          color="orange-darken-2" 
          prepend-icon="mdi-arrow-up"
          @click="showPromotionDialog = true"
        >
          Перевести на следующий курс
        </v-btn>
      </v-col>
    </v-row>

    <!-- Диалог перевода групп -->
    <v-dialog v-model="showPromotionDialog" width="600">
      <v-card class="rounded-lg" elevation="4">
        <v-card-title class="bg-orange-darken-2 text-white">
           Перевод групп на следующий курс
        </v-card-title>
        <v-card-text class="pa-6">
          <v-alert type="warning" variant="tonal" class="mb-4">
             Это действие переведет выбранные группы на следующий курс!
            <br/>
            Например: 1 курс → 2 курс
          </v-alert>

          <v-select
            v-model="selectedGroupsForPromotion"
            label="Выберите группы для перевода"
            variant="outlined"
            :items="availableGroups"
            item-title="group_name"
            item-value="id"
            multiple
            chips
            class="mb-4"
          ></v-select>

          <v-btn 
            color="orange-darken-2" 
            block 
            size="large"
            :loading="promotionLoading"
            @click="promoteGroups"
            :disabled="selectedGroupsForPromotion.length === 0"
          >
            Перевести {{ selectedGroupsForPromotion.length > 0 ? selectedGroupsForPromotion.length : '' }} груп{{ selectedGroupsForPromotion.length === 1 ? 'пу' : 'п' }}
          </v-btn>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Таблица групп по курсам -->
    <v-row class="mb-4">
      <v-col cols="12">
        <v-text-field
          v-model="searchQuery"
          label="Поиск по названию группы"
          variant="outlined"
          prepend-inner-icon="mdi-magnify"
          clearable
        ></v-text-field>
      </v-col>
    </v-row>

    <v-progress-linear v-if="loading" indeterminate class="mb-4"></v-progress-linear>

    <v-row v-if="!loading">
      <v-col 
        v-for="course in courseGroups" 
        :key="course.year"
        cols="12"
        class="mb-4"
      >
        <v-card class="rounded-lg" elevation="1">
          <v-card-title class="bg-indigo-lighten-4">
             {{ course.year }} курс ({{ course.groups.length }} {{ pluralize(course.groups.length, 'группа') }})
          </v-card-title>
          <v-card-text class="pa-4">
            <v-row>
              <v-col 
                v-for="group in course.groups" 
                :key="group.id"
                cols="12"
                sm="6"
                md="4"
              >
                <v-card 
                  class="rounded-lg cursor-pointer transition-all"
                  :class="{ 'bg-indigo-lighten-5': selectedGroupsForPromotion.includes(group.id) }"
                  @click="toggleGroupSelection(group.id)"
                >
                  <v-card-text class="pa-4">
                    <div class="text-h6 font-weight-bold">{{ group.group_name }}</div>
                    <div class="text-body-2 text-grey-darken-2 mt-2">
                       {{ group.course_year }} курс
                    </div>
                    <v-checkbox
                      :model-value="selectedGroupsForPromotion.includes(group.id)"
                      class="mt-2"
                      hide-details
                      @click.stop="toggleGroupSelection(group.id)"
                    ></v-checkbox>
                  </v-card-text>
                </v-card>
              </v-col>

              <v-col v-if="course.groups.length === 0" cols="12">
                <div class="text-center text-grey-darken-2 py-8">
                  Нет групп на этом курсе
                </div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Алерты -->
    <v-alert v-if="success" type="success" variant="tonal" class="mt-4" closable @click="success = ''">
      {{ success }}
    </v-alert>
    <v-alert v-if="error" type="error" variant="tonal" class="mt-4" closable @click="error = ''">
      {{ error }}
    </v-alert>
  </v-card-text>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../api/axios'

const groups = ref([])
const loading = ref(false)
const error = ref('')
const success = ref('')
const searchQuery = ref('')

const showPromotionDialog = ref(false)
const promotionLoading = ref(false)
const selectedGroupsForPromotion = ref([])

const pluralize = (count, word) => {
  if (count % 10 === 1 && count % 100 !== 11) return word
  if (count % 10 >= 2 && count % 10 <= 4 && (count % 100 < 10 || count % 100 >= 20)) return word + 'ы'
  return word + ''
}

const availableGroups = computed(() => {
  return groups.value
})

const courseGroups = computed(() => {
  const courses = {}
  
  filteredGroups.value.forEach(group => {
    if (!courses[group.course_year]) {
      courses[group.course_year] = {
        year: group.course_year,
        groups: []
      }
    }
    courses[group.course_year].groups.push(group)
  })

  return Object.values(courses).sort((a, b) => a.year - b.year)
})

const filteredGroups = computed(() => {
  if (!searchQuery.value) return groups.value
  const query = searchQuery.value.toLowerCase()
  return groups.value.filter(g => g.group_name.toLowerCase().includes(query))
})

const loadGroups = async () => {
  try {
    loading.value = true
    error.value = ''
    const response = await api.get('/groups/')
    groups.value = response.data
  } catch (err) {
    error.value = 'Ошибка при загрузке групп'
    console.error(err)
  } finally {
    loading.value = false
  }
}

const toggleGroupSelection = (groupId) => {
  const index = selectedGroupsForPromotion.value.indexOf(groupId)
  if (index > -1) {
    selectedGroupsForPromotion.value.splice(index, 1)
  } else {
    selectedGroupsForPromotion.value.push(groupId)
  }
}

const promoteGroups = async () => {
  if (selectedGroupsForPromotion.value.length === 0) {
    error.value = 'Выберите хотя бы одну группу'
    return
  }

  try {
    promotionLoading.value = true
    const response = await api.post('/admin/groups/promote-year/', {
      group_ids: selectedGroupsForPromotion.value
    })
    
    success.value = ` Переведено ${response.data.promoted_count} гру${response.data.promoted_count === 1 ? 'пп' : 'пп'}. ${response.data.failed_count > 0 ? `Ошибок: ${response.data.failed_count}` : ''}`
    showPromotionDialog.value = false
    selectedGroupsForPromotion.value = []
    
    await loadGroups()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка при переводе групп'
  } finally {
    promotionLoading.value = false
  }
}

onMounted(() => {
  loadGroups()
})
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}

.transition-all {
  transition: all 0.3s ease;
}
</style>
