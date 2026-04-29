<template>
  <v-card-text class="pa-6">
    <v-row class="mb-6">
      <v-col cols="12" class="d-flex align-center justify-space-between flex-wrap gap-2">
        <h6 class="admin-section-title text-h6 font-weight-bold">Назначения преподавателей</h6>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
          Добавить назначение
        </v-btn>
      </v-col>
    </v-row>

    <!-- Фильтры -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6">
        <v-select
          v-model="filterTeacherId"
          :items="teachers"
          item-title="full_name"
          item-value="id"
          label="Фильтр по преподавателю"
          variant="outlined"
          clearable
          @update:model-value="loadAssignments"
        ></v-select>
      </v-col>
      <v-col cols="12" sm="6">
        <v-select
          v-model="filterGroupId"
          :items="groups"
          item-title="group_name"
          item-value="id"
          label="Фильтр по группе"
          variant="outlined"
          clearable
          @update:model-value="loadAssignments"
        ></v-select>
      </v-col>
    </v-row>

    <v-progress-linear v-if="loading" indeterminate class="mb-4"></v-progress-linear>

    <!-- Таблица -->
    <div v-if="!loading" class="rounded-lg overflow-hidden border">
      <v-table dense hover>
        <thead>
          <tr>
            <th class="text-left">Преподаватель</th>
            <th class="text-left">Предмет</th>
            <th class="text-left">Группа</th>
            <th class="text-left">Учебный период</th>
            <th class="text-left">Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in assignments" :key="a.id" class="assignment-row">
            <td class="text-body-2 font-weight-medium">{{ a.teacher_name }}</td>
            <td class="text-body-2">{{ a.subject.name }}</td>
            <td>
              <v-chip size="small" variant="tonal" color="primary">
                {{ a.group.group_name }}
              </v-chip>
            </td>
            <td class="text-body-2 text-medium-emphasis">{{ a.academic_period.name }}</td>
            <td>
              <v-btn
                icon
                size="small"
                variant="text"
                color="error"
                @click="openDeleteDialog(a)"
                title="Удалить назначение"
              >
                <v-icon size="18">mdi-delete</v-icon>
              </v-btn>
            </td>
          </tr>
          <tr v-if="assignments.length === 0">
            <td colspan="5" class="text-center py-6 text-medium-emphasis">
              Назначений нет. Нажмите "Добавить назначение" чтобы создать первое.
            </td>
          </tr>
        </tbody>
      </v-table>
    </div>

    <!-- Диалог создания -->
    <v-dialog v-model="showCreateDialog" width="500">
      <v-card class="rounded-lg" elevation="4">
        <v-card-title class="pa-4 text-h6 font-weight-bold">Добавить назначение</v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-6">
          <v-select
            v-model="form.teacher_id"
            :items="activeTeachers"
            item-title="full_name"
            item-value="id"
            label="Преподаватель"
            variant="outlined"
            class="mb-4"
            :error-messages="formErrors.teacher_id"
          ></v-select>

          <v-text-field
            v-model="form.subject_name"
            label="Предмет"
            variant="outlined"
            class="mb-4"
            hint="Введите название предмета. Если предмет уже есть у этого преподавателя — будет использован существующий."
            persistent-hint
            :error-messages="formErrors.subject_name"
          ></v-text-field>

          <v-select
            v-model="form.group_id"
            :items="groups"
            item-title="group_name"
            item-value="id"
            label="Группа"
            variant="outlined"
            class="mb-4"
            :error-messages="formErrors.group_id"
          ></v-select>

          <v-select
            v-model="form.academic_period_id"
            :items="periods"
            item-title="name"
            item-value="id"
            label="Учебный период"
            variant="outlined"
            :error-messages="formErrors.academic_period_id"
          ></v-select>
        </v-card-text>
        <v-card-actions class="pa-4 justify-end gap-2">
          <v-btn variant="outlined" @click="showCreateDialog = false">Отмена</v-btn>
          <v-btn color="primary" :loading="createLoading" @click="createAssignment">Сохранить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Диалог удаления -->
    <v-dialog v-model="showDeleteDialog" width="420">
      <v-card class="rounded-lg" elevation="4">
        <v-card-title class="pa-4 text-h6 font-weight-bold">Удалить назначение?</v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-6">
          <p>
            <strong>{{ deletingAssignment?.teacher_name }}</strong>
            будет отвязан от предмета
            <strong>{{ deletingAssignment?.subject.name }}</strong>
            в группе
            <strong>{{ deletingAssignment?.group.group_name }}</strong>.
          </p>
          <p class="text-body-2 text-medium-emphasis mt-2">
            Уже созданные уроки и оценки не удаляются.
          </p>
        </v-card-text>
        <v-card-actions class="pa-4 justify-end gap-2">
          <v-btn variant="outlined" @click="showDeleteDialog = false">Отмена</v-btn>
          <v-btn color="error" :loading="deleteLoading" @click="deleteAssignment">Удалить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-alert v-if="success" type="success" variant="tonal" class="mt-4" closable @click:close="success = ''">
      {{ success }}
    </v-alert>
    <v-alert v-if="error" type="error" variant="tonal" class="mt-4" closable @click:close="error = ''">
      {{ error }}
    </v-alert>
  </v-card-text>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../api/axios'

const assignments = ref([])
const teachers = ref([])
const groups = ref([])
const periods = ref([])
const loading = ref(false)
const error = ref('')
const success = ref('')

const filterTeacherId = ref(null)
const filterGroupId = ref(null)

const showCreateDialog = ref(false)
const createLoading = ref(false)
const form = ref({ teacher_id: null, subject_name: '', group_id: null, academic_period_id: null })
const formErrors = ref({})

const showDeleteDialog = ref(false)
const deleteLoading = ref(false)
const deletingAssignment = ref(null)

const activeTeachers = computed(() => teachers.value.filter(t => t.is_active))

onMounted(async () => {
  await Promise.all([loadTeachers(), loadGroups(), loadPeriods()])
  await loadAssignments()
})

const loadTeachers = async () => {
  try {
    const res = await api.get('/admin/teachers/')
    teachers.value = res.data
  } catch (err) {
    console.error(err)
  }
}

const loadGroups = async () => {
  try {
    const res = await api.get('/groups/')
    groups.value = res.data
  } catch (err) {
    console.error(err)
  }
}

const loadPeriods = async () => {
  try {
    const res = await api.get('/academic-periods/')
    periods.value = res.data
  } catch (err) {
    console.error(err)
  }
}

const loadAssignments = async () => {
  loading.value = true
  try {
    const params = {}
    if (filterTeacherId.value) params.teacher_id = filterTeacherId.value
    if (filterGroupId.value) params.group_id = filterGroupId.value
    const res = await api.get('/admin/assignments/', { params })
    assignments.value = res.data
  } catch (err) {
    error.value = 'Ошибка при загрузке назначений'
    console.error(err)
  } finally {
    loading.value = false
  }
}

const openCreateDialog = async () => {
  form.value = { teacher_id: null, subject_name: '', group_id: null, academic_period_id: null }
  formErrors.value = {}
  await Promise.all([loadGroups(), loadPeriods()])
  showCreateDialog.value = true
}

const createAssignment = async () => {
  formErrors.value = {}
  const errs = {}
  if (!form.value.teacher_id) errs.teacher_id = 'Выберите преподавателя'
  if (!form.value.subject_name?.trim()) errs.subject_name = 'Введите название предмета'
  if (!form.value.group_id) errs.group_id = 'Выберите группу'
  if (!form.value.academic_period_id) errs.academic_period_id = 'Выберите период'
  if (Object.keys(errs).length) { formErrors.value = errs; return }

  createLoading.value = true
  try {
    const res = await api.post('/admin/assignments/', {
      teacher_id: form.value.teacher_id,
      subject_name: form.value.subject_name.trim(),
      group_id: form.value.group_id,
      academic_period_id: form.value.academic_period_id,
    })
    assignments.value.unshift(res.data)
    showCreateDialog.value = false
    success.value = 'Назначение добавлено'
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка при создании назначения'
  } finally {
    createLoading.value = false
  }
}

const openDeleteDialog = (assignment) => {
  deletingAssignment.value = assignment
  showDeleteDialog.value = true
}

const deleteAssignment = async () => {
  deleteLoading.value = true
  try {
    await api.delete(`/admin/assignments/${deletingAssignment.value.id}`)
    assignments.value = assignments.value.filter(a => a.id !== deletingAssignment.value.id)
    showDeleteDialog.value = false
    success.value = 'Назначение удалено'
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка при удалении'
    showDeleteDialog.value = false
  } finally {
    deleteLoading.value = false
  }
}
</script>

<style scoped>
.assignment-row:hover {
  background-color: rgba(var(--v-theme-on-surface), 0.06);
}

:deep(.v-table thead th) {
  color: rgba(var(--v-theme-on-surface), var(--v-high-emphasis-opacity)) !important;
  background-color: rgb(var(--v-theme-surface-variant)) !important;
}
</style>
