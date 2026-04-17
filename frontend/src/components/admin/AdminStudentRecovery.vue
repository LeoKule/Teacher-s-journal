<template>
  <v-card-text class="pa-6">
    <!-- Заголовок -->
    <h6 class="admin-section-title text-h6 font-weight-bold mb-4"> Восстановление удаленных студентов</h6>

    <!-- Фильтр по группе -->
    <v-row class="mb-6">
      <v-col cols="12" md="6">
        <v-select
          v-model="selectedGroupFilter"
          :items="groups"
          item-title="group_name"
          item-value="id"
          label="Фильтр по группе (опционально)"
          variant="outlined"
          clearable
          @update:model-value="loadDeletedStudents"
        ></v-select>
      </v-col>
    </v-row>

    <!-- Таблица удаленных студентов -->
    <v-progress-linear v-if="loading" indeterminate class="mb-4"></v-progress-linear>

    <v-alert v-if="!loading && deletedStudents.length === 0" type="info" variant="tonal">
      ✓ Нет удаленных студентов
    </v-alert>

    <v-data-table
      v-if="!loading && deletedStudents.length > 0"
      :headers="headers"
      :items="deletedStudents"
      class="rounded-lg"
    >
      <template #item.actions="{ item }">
        <v-btn
          color="green-darken-2"
          size="small"
          @click="restoreStudent(item.id)"
          :loading="restoring === item.id"
        >
          <v-icon start>mdi-restore</v-icon>
          Восстановить
        </v-btn>
      </template>
    </v-data-table>

    <!-- Диалог подтверждения -->
    <v-dialog v-model="showConfirmDialog" width="400">
      <v-card class="rounded-lg" elevation="4">
        <v-card-title class="bg-orange-darken-2 text-white">
           Подтверждение восстановления
        </v-card-title>
        <v-card-text class="pa-6">
          <p class="mb-4">
            Вы действительно хотите восстановить студента 
            <strong>{{ selectedStudent?.full_name }}</strong>?
          </p>
          <p class="text-body-2 text-grey-darken-1">
            Все данные студента будут восстановлены и станут видны в системе.
          </p>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-btn variant="outlined" @click="showConfirmDialog = false">
            Отмена
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn
            color="green-darken-2"
            @click="confirmRestore"
            :loading="restoring > 0"
          >
            Восстановить
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Результат -->
    <v-alert
      v-if="restoreResult"
      :type="restoreResult.success ? 'success' : 'error'"
      variant="tonal"
      class="mt-6"
      closable
      @input="(v) => { if (!v) restoreResult = null }"
    >
      {{ restoreResult.message }}
    </v-alert>
  </v-card-text>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api/axios'

const loading = ref(false)
const restoring = ref(null)
const deletedStudents = ref([])
const groups = ref([])
const selectedGroupFilter = ref(null)
const showConfirmDialog = ref(false)
const selectedStudent = ref(null)
const restoreResult = ref(null)

const headers = [
  { title: 'ФИО', key: 'full_name' },
  { title: 'Группа', key: 'group_name' },
  { title: 'Действия', key: 'actions', sortable: false }
]

onMounted(async () => {
  await loadGroups()
  await loadDeletedStudents()
})

const loadGroups = async () => {
  try {
    const response = await api.get('/curriculum/groups/')
    groups.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки групп:', error)
  }
}

const loadDeletedStudents = async () => {
  loading.value = true
  try {
    const params = selectedGroupFilter.value ? { group_id: selectedGroupFilter.value } : {}
    const response = await api.get('/admin/students/deleted', { params })
    deletedStudents.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки удаленных студентов:', error)
  } finally {
    loading.value = false
  }
}

const restoreStudent = (studentId) => {
  selectedStudent.value = deletedStudents.value.find(s => s.id === studentId)
  showConfirmDialog.value = true
}

const confirmRestore = async () => {
  restoring.value = selectedStudent.value.id
  
  try {
    const response = await api.post(
      `/admin/students/${selectedStudent.value.id}/restore`
    )
    
    restoreResult.value = {
      success: true,
      message: response.data.message
    }
    
    showConfirmDialog.value = false
    await loadDeletedStudents()
  } catch (error) {
    restoreResult.value = {
      success: false,
      message: ' Ошибка восстановления: ' + (error.response?.data?.detail || error.message)
    }
  } finally {
    restoring.value = null
  }
}
</script>
