<template>
  <v-card-text class="pa-6">
    <!-- Кнопка создания преподавателя -->
    <v-row class="mb-6">
      <v-col cols="12" class="d-flex align-center justify-space-between">
        <h6 class="admin-section-title text-h6 font-weight-bold"> Управление преподавателями</h6>
        <v-btn 
          color="indigo-darken-2" 
          prepend-icon="mdi-plus"
          @click="showCreateDialog = true"
        >
          Добавить преподавателя
        </v-btn>
      </v-col>
    </v-row>

    <!-- Диалог создания преподавателя -->
    <v-dialog v-model="showCreateDialog" width="500">
      <v-card class="rounded-lg" elevation="4">
        <v-card-title class="bg-indigo-darken-2 text-white">
          Добавить нового преподавателя
        </v-card-title>
        <v-card-text class="pa-6">
          <v-form @submit.prevent="createTeacher">
            <v-text-field
              v-model="newTeacher.full_name"
              label="ФИО"
              variant="outlined"
              class="mb-4"
              prepend-inner-icon="mdi-account"
            ></v-text-field>

            <v-text-field
              v-model="newTeacher.email"
              label="Email"
              variant="outlined"
              class="mb-4"
              prepend-inner-icon="mdi-email"
              type="email"
            ></v-text-field>

            <v-select
              v-model="newTeacher.role"
              label="Роль"
              variant="outlined"
              :items="['teacher', 'admin']"
              class="mb-4"
              prepend-inner-icon="mdi-shield-account"
            ></v-select>

            <v-alert type="info" variant="tonal" class="mb-4">
               После создания будет сгенерирован временный пароль
            </v-alert>

            <v-btn 
              type="submit" 
              color="indigo-darken-2" 
              block 
              size="large"
              :loading="createLoading"
            >
              Создать
            </v-btn>
          </v-form>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Диалог с сгенерированным паролем -->
    <v-dialog v-model="showPasswordDialog" width="500">
      <v-card class="rounded-lg" elevation="4">
        <v-card-title class="bg-green-darken-2 text-white">
          ✅ Преподаватель создан
        </v-card-title>
        <v-card-text class="pa-6">
          <v-alert type="warning" variant="tonal" class="mb-4">
             Сохраните и сообщите временный пароль преподавателю!
          </v-alert>

          <div class="mb-4">
            <div class="text-body-2 text-grey-darken-2 mb-2">Email:</div>
            <v-text-field
              :model-value="createdTeacher.email"
              readonly
              variant="outlined"
            ></v-text-field>
          </div>

          <div class="mb-4">
            <div class="text-body-2 text-grey-darken-2 mb-2">Временный пароль:</div>
            <v-text-field
              :model-value="createdTeacher.password"
              readonly
              variant="outlined"
              append-inner-icon="mdi-content-copy"
              @click:append-inner="copyPassword"
            ></v-text-field>
          </div>

          <v-btn 
            color="indigo-darken-2" 
            block 
            size="large"
            @click="showPasswordDialog = false; loadTeachers()"
          >
            Понял
          </v-btn>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Таблица преподавателей -->
    <v-row class="mb-4">
      <v-col cols="12">
        <v-text-field
          v-model="searchQuery"
          label="Поиск по email или имени"
          variant="outlined"
          prepend-inner-icon="mdi-magnify"
          clearable
          class="mb-4"
        ></v-text-field>
      </v-col>
    </v-row>

    <v-progress-linear v-if="loading" indeterminate class="mb-4"></v-progress-linear>

    <v-data-table
      v-if="!loading"
      :headers="headers"
      :items="filteredTeachers"
      class="rounded-lg"
    >
      <template #item.is_active="{ item }">
        <v-chip 
          :color="item.is_active ? 'green' : 'red'" 
          text-color="white"
          size="small"
        >
          {{ item.is_active ? ' Активен' : ' Заблокирован' }}
        </v-chip>
      </template>

      <template #item.role="{ item }">
        <v-chip 
          :color="item.role === 'admin' ? 'indigo-darken-2' : 'blue'" 
          text-color="white"
          size="small"
        >
          {{ item.role === 'admin' ? ' Администратор' : ' Преподаватель' }}
        </v-chip>
      </template>

      <template #item.actions="{ item }">
        <v-menu>
          <template #activator="{ props }">
            <v-btn 
              icon="mdi-dots-vertical" 
              variant="text" 
              size="small"
              v-bind="props"
            ></v-btn>
          </template>
          <v-list>
            <v-list-item @click="editTeacher(item)">
              <template #prepend>
                <v-icon>mdi-pencil</v-icon>
              </template>
              <v-list-item-title>Редактировать</v-list-item-title>
            </v-list-item>

            <v-list-item @click="showResetPasswordDialog = true; selectedTeacherId = item.id">
              <template #prepend>
                <v-icon>mdi-lock-reset</v-icon>
              </template>
              <v-list-item-title>Сброс пароля</v-list-item-title>
            </v-list-item>

            <v-divider></v-divider>

            <v-list-item @click="toggleBlockTeacher(item)">
              <template #prepend>
                <v-icon :color="item.is_active ? 'red' : 'green'">
                  {{ item.is_active ? 'mdi-block-helper' : 'mdi-check-circle' }}
                </v-icon>
              </template>
              <v-list-item-title>
                {{ item.is_active ? 'Заблокировать' : 'Разблокировать' }}
              </v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </template>
    </v-data-table>

    <!-- Диалог сброса пароля -->
    <v-dialog v-model="showResetPasswordDialog" width="500">
      <v-card class="rounded-lg" elevation="4">
        <v-card-title class="bg-orange-darken-2 text-white">
           Сброс пароля
        </v-card-title>
        <v-card-text class="pa-6">
          <v-text-field
            v-model="newPassword"
            label="Новый пароль"
            type="password"
            variant="outlined"
            class="mb-4"
            hint="Минимум 8 символов"
            prepend-inner-icon="mdi-lock"
          ></v-text-field>

          <v-btn 
            color="orange-darken-2" 
            block 
            size="large"
            :loading="resetLoading"
            @click="resetPassword"
          >
            Сбросить пароль
          </v-btn>
        </v-card-text>
      </v-card>
    </v-dialog>

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

const teachers = ref([])
const loading = ref(false)
const error = ref('')
const success = ref('')
const searchQuery = ref('')

const showCreateDialog = ref(false)
const showPasswordDialog = ref(false)
const showResetPasswordDialog = ref(false)
const createLoading = ref(false)
const resetLoading = ref(false)
const selectedTeacherId = ref(null)
const newPassword = ref('')

const newTeacher = ref({
  full_name: '',
  email: '',
  role: 'teacher'
})

const createdTeacher = ref({
  email: '',
  password: ''
})

const headers = [
  { title: 'ФИО', key: 'full_name' },
  { title: 'Email', key: 'email' },
  { title: 'Роль', key: 'role' },
  { title: 'Статус', key: 'is_active' },
  { title: 'Последний вход', key: 'last_login' },
  { title: 'Действия', key: 'actions', sortable: false }
]

const filteredTeachers = computed(() => {
  if (!searchQuery.value) return teachers.value
  const query = searchQuery.value.toLowerCase()
  return teachers.value.filter(t =>
    t.email.toLowerCase().includes(query) ||
    t.full_name.toLowerCase().includes(query)
  )
})

const loadTeachers = async () => {
  try {
    loading.value = true
    const response = await api.get('/admin/teachers/')
    teachers.value = response.data
  } catch (err) {
    error.value = 'Ошибка при загрузке преподавателей'
    console.error(err)
  } finally {
    loading.value = false
  }
}

const createTeacher = async () => {
  if (!newTeacher.value.full_name || !newTeacher.value.email) {
    error.value = 'Заполните все поля'
    return
  }

  try {
    createLoading.value = true
    const response = await api.post('/admin/teachers/', newTeacher.value)
    createdTeacher.value = {
      email: response.data.email,
      password: response.data.temporary_password
    }
    showCreateDialog.value = false
    showPasswordDialog.value = true
    newTeacher.value = { full_name: '', email: '', role: 'teacher' }
    success.value = response.data.message
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка при создании преподавателя'
  } finally {
    createLoading.value = false
  }
}

const resetPassword = async () => {
  if (!newPassword.value || newPassword.value.length < 8) {
    error.value = 'Пароль должен быть не менее 8 символов'
    return
  }

  try {
    resetLoading.value = true
    const response = await api.post(
      `/admin/teachers/${selectedTeacherId.value}/reset-password`,
      { teacher_id: selectedTeacherId.value, new_password: newPassword.value }
    )
    success.value = response.data.message
    showResetPasswordDialog.value = false
    newPassword.value = ''
    await loadTeachers()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка при сбросе пароля'
  } finally {
    resetLoading.value = false
  }
}

const toggleBlockTeacher = async (teacher) => {
  try {
    const response = await api.post(
      `/admin/teachers/${teacher.id}/toggle-status`,
      { teacher_id: teacher.id, is_active: !teacher.is_active }
    )
    success.value = response.data.message
    await loadTeachers()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка при изменении статуса'
  }
}

const copyPassword = () => {
  navigator.clipboard.writeText(createdTeacher.value.password)
  success.value = 'Пароль скопирован в буфер обмена'
}

const editTeacher = (teacher) => {
  // TODO: Реализовать редактирование преподавателя
  console.log('Редактирование преподавателя:', teacher)
}

onMounted(() => {
  loadTeachers()
})
</script>

<style scoped>
</style>
