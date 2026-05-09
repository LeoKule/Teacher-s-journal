<template>
  <v-card-text class="pa-6">
    <v-row class="mb-6">
      <v-col cols="12" class="d-flex align-center justify-space-between flex-wrap gap-2">
        <h6 class="admin-section-title text-h6 font-weight-bold">Управление группами</h6>
        <div class="d-flex flex-wrap" style="gap: 16px">
          <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
            Создать группу
          </v-btn>
          <v-btn color="warning" prepend-icon="mdi-arrow-up" @click="showPromotionDialog = true">
            Перевести на следующий курс
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- Диалог создания/редактирования группы -->
    <v-dialog v-model="showGroupDialog" width="440">
      <v-card class="rounded-lg" elevation="4">
        <v-card-title class="pa-4 text-h6 font-weight-bold">
          {{ editingGroup ? 'Редактировать группу' : 'Создать группу' }}
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-6">
          <v-text-field
            v-model="groupForm.group_name"
            label="Название группы"
            variant="outlined"
            class="mb-4"
            :error-messages="groupFormError"
          ></v-text-field>
          <v-select
            v-model="groupForm.course_year"
            label="Курс"
            variant="outlined"
            :items="[1, 2, 3, 4]"
          ></v-select>
        </v-card-text>
        <v-card-actions class="pa-4 justify-end gap-2">
          <v-btn variant="outlined" @click="showGroupDialog = false">Отмена</v-btn>
          <v-btn
            color="primary"
            :loading="groupSaveLoading"
            :disabled="!groupForm.group_name || !groupForm.course_year"
            @click="saveGroup"
          >
            Сохранить
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Диалог подтверждения удаления группы -->
    <v-dialog v-model="showDeleteDialog" width="420">
      <v-card class="rounded-lg" elevation="4">
        <v-card-title class="pa-4 text-h6 font-weight-bold">Удалить группу?</v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-6">
          <p>Группа <strong>{{ deletingGroup?.group_name }}</strong> будет удалена.</p>
          <p class="text-body-2 text-medium-emphasis mt-2">Удаление возможно только если в группе нет студентов.</p>
        </v-card-text>
        <v-card-actions class="pa-4 justify-end gap-2">
          <v-btn variant="outlined" @click="showDeleteDialog = false">Отмена</v-btn>
          <v-btn color="error" :loading="deleteLoading" @click="deleteGroup">Удалить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Диалог перевода групп -->
    <v-dialog v-model="showPromotionDialog" width="600">
      <v-card class="rounded-lg" elevation="4">
        <v-card-title class="pa-4 text-h6 font-weight-bold">
          Перевод групп на следующий курс
        </v-card-title>
        <v-divider></v-divider>
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
            color="warning"
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

    <!-- Поиск -->
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
          <v-card-title class="font-weight-bold">
            {{ course.year }} курс ({{ course.groups.length }} {{ pluralize(course.groups.length, 'группа', 'группы', 'групп') }})
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text class="pa-4">
            <v-row>
              <v-col
                v-for="group in course.groups"
                :key="group.id"
                cols="12"
                sm="6"
                md="4"
              >
                <v-card class="rounded-lg" variant="outlined">
                  <v-card-text class="pa-4">
                    <div class="d-flex align-center justify-space-between mb-1">
                      <div class="text-h6 font-weight-bold">{{ group.group_name }}</div>
                      <div class="d-flex gap-1">
                        <v-btn
                          icon
                          size="small"
                          variant="text"
                          color="primary"
                          @click="openStudentsDialog(group)"
                          title="Просмотр студентов"
                        >
                          <v-icon size="18">mdi-account-group</v-icon>
                        </v-btn>
                        <v-btn
                          icon
                          size="small"
                          variant="text"
                          @click="openEditDialog(group)"
                          title="Редактировать"
                        >
                          <v-icon size="18">mdi-pencil</v-icon>
                        </v-btn>
                        <v-btn
                          icon
                          size="small"
                          variant="text"
                          color="error"
                          :disabled="group.students_count > 0"
                          @click="openDeleteDialog(group)"
                          :title="group.students_count > 0 ? 'Нельзя удалить группу со студентами' : 'Удалить'"
                        >
                          <v-icon size="18">mdi-delete</v-icon>
                        </v-btn>
                      </div>
                    </div>
                    <div class="text-body-2 text-medium-emphasis">{{ group.course_year }} курс</div>
                    <v-chip size="small" variant="tonal" color="primary" class="mt-2">
                      {{ group.students_count }} {{ pluralize(group.students_count, 'студент', 'студента', 'студентов') }}
                    </v-chip>
                  </v-card-text>
                </v-card>
              </v-col>

              <v-col v-if="course.groups.length === 0" cols="12">
                <v-card variant="outlined" class="text-center pa-6">
                  <v-icon size="48" color="grey-lighten-1">mdi-folder-open-outline</v-icon>
                  <p class="text-medium-emphasis mt-3 mb-2">Нет групп на этом курсе</p>
                  <v-btn size="small" color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
                    Создать группу
                  </v-btn>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col v-if="courseGroups.length === 0" cols="12">
        <v-card variant="outlined" class="text-center pa-8">
          <v-icon size="56" color="grey-lighten-1">mdi-folder-multiple-outline</v-icon>
          <p class="text-h6 font-weight-medium mt-3 mb-1">Групп пока нет</p>
          <p class="text-body-2 text-medium-emphasis mb-3">Создайте первую группу, чтобы начать работу</p>
          <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
            Создать первую группу
          </v-btn>
        </v-card>
      </v-col>
    </v-row>

    <!-- Диалог просмотра студентов группы -->
    <v-dialog v-model="showStudentsDialog" width="560">
      <v-card class="rounded-lg" elevation="4">
        <v-card-title class="pa-4 text-h6 font-weight-bold d-flex align-center" style="gap: 12px">
          <span>Студенты группы {{ viewingGroup?.group_name }}</span>
          <v-chip size="small" variant="tonal" color="primary">{{ groupStudents.length }}</v-chip>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            size="small"
            prepend-icon="mdi-plus"
            @click="openAddStudentDialog"
          >
            Добавить
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-0">
          <v-progress-linear v-if="studentsLoading" indeterminate></v-progress-linear>
          <div v-if="!studentsLoading && groupStudents.length === 0" class="text-center text-medium-emphasis py-8">
            В группе нет студентов
          </div>
          <v-list v-if="!studentsLoading && groupStudents.length > 0" density="compact">
            <v-list-item
              v-for="(student, idx) in groupStudents"
              :key="student.id"
              :prepend-avatar="undefined"
            >
              <template #prepend>
                <span class="text-body-2 text-medium-emphasis mr-3" style="min-width:28px">{{ idx + 1 }}.</span>
              </template>
              <v-list-item-title class="text-body-2">{{ student.full_name }}</v-list-item-title>
              <template #append>
                <v-btn
                  icon
                  size="small"
                  variant="text"
                  color="error"
                  title="Удалить в корзину"
                  @click="confirmSoftDeleteStudent(student)"
                >
                  <v-icon size="18">mdi-delete</v-icon>
                </v-btn>
              </template>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions class="pa-4 justify-end">
          <v-btn variant="outlined" @click="showStudentsDialog = false">Закрыть</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Диалог быстрого добавления студента -->
    <v-dialog v-model="showAddStudentDialog" width="440">
      <v-card class="rounded-lg" elevation="4">
        <v-card-title class="pa-4 text-h6 font-weight-bold">
          Добавить студента в {{ viewingGroup?.group_name }}
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-6">
          <v-text-field
            v-model="newStudentLastName"
            label="Фамилия"
            variant="outlined"
            autofocus
            placeholder="Петров"
            class="mb-3"
            @keyup.enter="addStudent"
          ></v-text-field>
          <v-text-field
            v-model="newStudentFirstName"
            label="Имя"
            variant="outlined"
            placeholder="Иван"
            :error-messages="addStudentError"
            @keyup.enter="addStudent"
          ></v-text-field>
        </v-card-text>
        <v-card-actions class="pa-4 justify-end gap-2">
          <v-btn variant="outlined" @click="showAddStudentDialog = false">Отмена</v-btn>
          <v-btn
            color="primary"
            :loading="addStudentLoading"
            :disabled="!newStudentLastName.trim() || !newStudentFirstName.trim()"
            @click="addStudent"
          >
            Добавить
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Диалог подтверждения soft-delete студента -->
    <v-dialog v-model="showDeleteStudentDialog" width="440">
      <v-card class="rounded-lg" elevation="4">
        <v-card-title class="pa-4 text-h6 font-weight-bold">Удалить студента?</v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-6">
          <p>
            Студент <strong>{{ deletingStudent?.full_name }}</strong> будет перемещён в корзину.
          </p>
          <p class="text-body-2 text-medium-emphasis mt-2">
            Восстановить можно в разделе «Восстановить студентов». Оценки сохранятся.
          </p>
        </v-card-text>
        <v-card-actions class="pa-4 justify-end gap-2">
          <v-btn variant="outlined" @click="showDeleteStudentDialog = false">Отмена</v-btn>
          <v-btn color="error" :loading="deleteStudentLoading" @click="softDeleteStudent">Удалить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Алерты -->
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

const groups = ref([])
const loading = ref(false)
const error = ref('')
const success = ref('')
const searchQuery = ref('')

const showPromotionDialog = ref(false)
const promotionLoading = ref(false)
const selectedGroupsForPromotion = ref([])

const showGroupDialog = ref(false)
const editingGroup = ref(null)
const groupForm = ref({ group_name: '', course_year: 1 })
const groupFormError = ref('')
const groupSaveLoading = ref(false)

const showDeleteDialog = ref(false)
const deletingGroup = ref(null)
const deleteLoading = ref(false)

const showStudentsDialog = ref(false)
const viewingGroup = ref(null)
const groupStudents = ref([])
const studentsLoading = ref(false)

const showDeleteStudentDialog = ref(false)
const deletingStudent = ref(null)
const deleteStudentLoading = ref(false)

const showAddStudentDialog = ref(false)
const newStudentLastName = ref('')
const newStudentFirstName = ref('')
const addStudentLoading = ref(false)
const addStudentError = ref('')

const openAddStudentDialog = () => {
  newStudentLastName.value = ''
  newStudentFirstName.value = ''
  addStudentError.value = ''
  showAddStudentDialog.value = true
}

const addStudent = async () => {
  const lastName = newStudentLastName.value.trim()
  const firstName = newStudentFirstName.value.trim()
  if (!lastName || !firstName || !viewingGroup.value) return
  // Формат как в bulk-импорте: "Имя Фамилия"
  const fullName = `${firstName} ${lastName}`
  addStudentError.value = ''
  addStudentLoading.value = true
  try {
    const res = await api.post('/admin/students/', {
      full_name: fullName,
      group_id: viewingGroup.value.id,
    })
    groupStudents.value = [...groupStudents.value, res.data].sort((a, b) =>
      a.full_name.localeCompare(b.full_name, 'ru')
    )
    success.value = `Студент ${fullName} добавлен`
    showAddStudentDialog.value = false
  } catch (err) {
    addStudentError.value = err.response?.data?.detail || 'Ошибка при добавлении'
  } finally {
    addStudentLoading.value = false
  }
}

const confirmSoftDeleteStudent = (student) => {
  deletingStudent.value = student
  showDeleteStudentDialog.value = true
}

const softDeleteStudent = async () => {
  if (!deletingStudent.value) return
  deleteStudentLoading.value = true
  try {
    await api.post(`/admin/students/${deletingStudent.value.id}/soft-delete`)
    groupStudents.value = groupStudents.value.filter(s => s.id !== deletingStudent.value.id)
    success.value = `Студент ${deletingStudent.value.full_name} перемещён в корзину`
    showDeleteStudentDialog.value = false
    deletingStudent.value = null
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка при удалении студента'
    showDeleteStudentDialog.value = false
  } finally {
    deleteStudentLoading.value = false
  }
}

const pluralize = (count, one, few, many) => {
  if (count % 10 === 1 && count % 100 !== 11) return one
  if (count % 10 >= 2 && count % 10 <= 4 && (count % 100 < 10 || count % 100 >= 20)) return few
  return many
}

const availableGroups = computed(() => groups.value)

const courseGroups = computed(() => {
  const courses = {}
  filteredGroups.value.forEach(group => {
    if (!courses[group.course_year]) {
      courses[group.course_year] = { year: group.course_year, groups: [] }
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

const openStudentsDialog = async (group) => {
  viewingGroup.value = group
  groupStudents.value = []
  showStudentsDialog.value = true
  studentsLoading.value = true
  try {
    const res = await api.get('/students/', { params: { group_id: group.id } })
    groupStudents.value = res.data
  } catch (err) {
    console.error(err)
  } finally {
    studentsLoading.value = false
  }
}

const openCreateDialog = () => {
  editingGroup.value = null
  groupForm.value = { group_name: '', course_year: 1 }
  groupFormError.value = ''
  showGroupDialog.value = true
}

const openEditDialog = (group) => {
  editingGroup.value = group
  groupForm.value = { group_name: group.group_name, course_year: group.course_year }
  groupFormError.value = ''
  showGroupDialog.value = true
}

const saveGroup = async () => {
  groupFormError.value = ''
  groupSaveLoading.value = true
  try {
    if (editingGroup.value) {
      await api.patch(`/groups/${editingGroup.value.id}`, groupForm.value)
      success.value = `Группа ${groupForm.value.group_name} обновлена`
    } else {
      await api.post('/groups/', groupForm.value)
      success.value = `Группа ${groupForm.value.group_name} создана`
    }
    showGroupDialog.value = false
    await loadGroups()
  } catch (err) {
    groupFormError.value = err.response?.data?.detail || 'Ошибка при сохранении'
  } finally {
    groupSaveLoading.value = false
  }
}

const openDeleteDialog = (group) => {
  deletingGroup.value = group
  showDeleteDialog.value = true
}

const deleteGroup = async () => {
  deleteLoading.value = true
  try {
    await api.delete(`/groups/${deletingGroup.value.id}`)
    success.value = `Группа ${deletingGroup.value.group_name} удалена`
    showDeleteDialog.value = false
    await loadGroups()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка при удалении'
    showDeleteDialog.value = false
  } finally {
    deleteLoading.value = false
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
    const count = response.data.promoted_count
    success.value = `Переведено ${count} ${pluralize(count, 'группу', 'группы', 'групп')}. ${response.data.failed_count > 0 ? `Ошибок: ${response.data.failed_count}` : ''}`
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
