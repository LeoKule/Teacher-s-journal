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
    <v-skeleton-loader
      v-if="loading"
      type="table-thead, table-tbody"
      class="mb-4"
    ></v-skeleton-loader>

    <v-card
      v-if="!loading && deletedStudents.length === 0"
      class="text-center pa-8 mb-4"
      variant="outlined"
    >
      <v-icon size="56" color="success">mdi-check-circle-outline</v-icon>
      <p class="text-medium-emphasis mt-3">Нет удалённых студентов</p>
      <p class="text-caption text-medium-emphasis">Все студенты активны</p>
    </v-card>

    <div style="overflow-x: auto">
    <v-data-table
      v-if="!loading && deletedStudents.length > 0"
      :headers="headers"
      :items="deletedStudents"
      class="rounded-lg"
    >
      <template #item.actions="{ item }">
        <div class="d-flex" style="gap: 12px">
          <v-btn
            color="success"
            size="small"
            variant="tonal"
            icon
            title="Восстановить"
            @click="openRestoreDialog(item)"
            :loading="restoring === item.id"
          >
            <v-icon>mdi-restore</v-icon>
          </v-btn>
          <v-btn
            color="error"
            size="small"
            variant="outlined"
            icon
            title="Удалить навсегда"
            @click="openHardDeleteDialog(item)"
          >
            <v-icon>mdi-delete-forever</v-icon>
          </v-btn>
        </div>
      </template>
    </v-data-table>
    </div>

    <!-- Диалог подтверждения -->
    <v-dialog v-model="showConfirmDialog" width="400">
      <v-card class="rounded-lg" elevation="4">
        <v-card-title class="pa-4 text-h6 font-weight-bold">
          Подтверждение восстановления
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-6">
          <p class="mb-4">
            Вы действительно хотите восстановить студента 
            <strong>{{ selectedStudent?.full_name }}</strong>?
          </p>
          <p class="text-body-2 text-medium-emphasis">
            Все данные студента будут восстановлены и станут видны в системе.
          </p>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-btn variant="outlined" @click="showConfirmDialog = false">
            Отмена
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn
            color="success"
            @click="confirmRestore(selectedStudent)"
            :loading="restoring > 0"
          >
            Восстановить
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Диалог жёсткого удаления (двойное подтверждение) -->
    <v-dialog v-model="showHardDeleteDialog" width="500" persistent>
      <v-card class="rounded-lg" elevation="4">
        <v-card-title class="pa-4 text-h6 font-weight-bold text-error">
          <v-icon color="error" class="mr-2">mdi-alert-circle</v-icon>
          Удалить навсегда?
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-6">
          <v-alert type="error" variant="tonal" class="mb-4" density="compact">
            Это действие <strong>необратимо</strong>. Студент и все его оценки будут удалены из базы данных.
          </v-alert>
          <p class="mb-1"><strong>{{ hardDeleteTarget?.full_name }}</strong></p>
          <p class="text-body-2 text-medium-emphasis mb-3">Группа: {{ hardDeleteTarget?.group_name }}</p>

          <v-alert
            v-if="hardDeleteImpact"
            :type="hardDeleteImpact.grades_count > 0 ? 'warning' : 'info'"
            variant="tonal"
            density="compact"
            class="mb-3"
          >
            Будет удалено оценок: <strong>{{ hardDeleteImpact.grades_count }}</strong>
          </v-alert>

          <p class="text-body-2 mb-2">
            Чтобы подтвердить, введите <code>удалить</code>:
          </p>
          <v-text-field
            v-model="hardDeleteConfirmText"
            placeholder="удалить"
            density="compact"
            hide-details
            autofocus
          ></v-text-field>
        </v-card-text>
        <v-card-actions class="pa-4 justify-end gap-2">
          <v-btn variant="outlined" @click="closeHardDeleteDialog">Отмена</v-btn>
          <v-btn
            color="error"
            :loading="hardDeleteLoading"
            :disabled="hardDeleteConfirmText.trim().toLowerCase() !== 'удалить'"
            @click="hardDeleteStudent(hardDeleteTarget)"
          >
            Удалить навсегда
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
      @update:modelValue="(v) => { if (!v) restoreResult = null }"
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

const showHardDeleteDialog = ref(false)
const hardDeleteTarget = ref(null)
const hardDeleteLoading = ref(false)
const hardDeleteImpact = ref(null)
const hardDeleteConfirmText = ref('')

const headers = [
  { title: 'ФИО', key: 'full_name' },
  { title: 'Группа', key: 'group_name' },
  { title: 'Действия', key: 'actions', sortable: false, width: '100px' }
]

onMounted(async () => {
  await loadGroups()
  await loadDeletedStudents()
})

const loadGroups = async () => {
  try {
    const response = await api.get('/groups/')
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

const openRestoreDialog = (student) => {
  selectedStudent.value = student
  showConfirmDialog.value = true
}

const closeHardDeleteDialog = () => {
  showHardDeleteDialog.value = false
  hardDeleteImpact.value = null
  hardDeleteConfirmText.value = ''
  hardDeleteTarget.value = null
}

const openHardDeleteDialog = async (student) => {
  hardDeleteTarget.value = student
  hardDeleteImpact.value = null
  hardDeleteConfirmText.value = ''
  showHardDeleteDialog.value = true
  try {
    const res = await api.get(`/admin/students/${student.id}/delete-impact`)
    hardDeleteImpact.value = res.data
  } catch (err) {
    console.error('Не удалось получить данные о влиянии удаления:', err)
  }
}

// Принимает студента аргументом — защита от race
const hardDeleteStudent = async (student) => {
  if (!student) return
  hardDeleteLoading.value = true
  try {
    const res = await api.delete(`/admin/students/${student.id}`)
    deletedStudents.value = deletedStudents.value.filter(s => s.id !== student.id)
    closeHardDeleteDialog()
    restoreResult.value = {
      success: true,
      message: `Студент ${student.full_name} удалён навсегда (оценок удалено: ${res.data.grades_deleted ?? 0})`
    }
  } catch (err) {
    restoreResult.value = {
      success: false,
      message: 'Ошибка при удалении: ' + (err.response?.data?.detail || err.message)
    }
    closeHardDeleteDialog()
  } finally {
    hardDeleteLoading.value = false
  }
}

// Принимаем студента аргументом, чтобы избежать race condition если selectedStudent
// сменится между открытием диалога и нажатием "Восстановить"
const confirmRestore = async (student) => {
  if (!student) return
  restoring.value = student.id

  try {
    const response = await api.post(`/admin/students/${student.id}/restore`)
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
