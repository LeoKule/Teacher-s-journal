<template>
  <v-card-text class="pa-6">
    <!-- Заголовок -->
    <h6 class="admin-section-title text-h6 font-weight-bold mb-4"> Отправка уведомлений преподавателям</h6>

    <v-row>
      <!-- Форма отправки -->
      <v-col cols="12" md="6">
        <v-card class="rounded-lg" elevation="2">
          <v-card-title class="text-h6">Новое уведомление</v-card-title>
          <v-card-text class="pa-6">
            <!-- Тип уведомления -->
            <v-select
              v-model="form.notificationType"
              :items="notificationTypes"
              label="Тип уведомления"
              variant="outlined"
              class="mb-4"
              @update:model-value="updateTypeDescription"
            ></v-select>

            <!-- Выбор получателей -->
            <div class="mb-4">
              <label class="text-body-2 font-weight-bold d-block mb-3">
                 Получатели:
              </label>
              <div class="border rounded-lg pa-4" style="background: rgba(0,0,0,0.02)">
                <v-checkbox
                  v-if="form.recipients.length === 0"
                  v-model="selectAllTeachers"
                  label="Все преподаватели"
                  @update:model-value="toggleSelectAll"
                  class="mb-3"
                ></v-checkbox>
                <template v-else>
                  <v-checkbox
                    v-model="selectAllTeachers"
                    label="Все преподаватели"
                    @update:model-value="toggleSelectAll"
                    class="mb-3"
                  ></v-checkbox>
                </template>
                
                <div v-if="!selectAllTeachers" class="ml-6">
                  <v-checkbox
                    v-for="teacher in availableTeachers"
                    :key="teacher.id"
                    v-model="form.recipients"
                    :value="teacher.id"
                    :label="`${teacher.full_name} (${teacher.email})`"
                    class="mb-2"
                  ></v-checkbox>
                </div>
              </div>
            </div>

            <!-- Заголовок уведомления -->
            <v-text-field
              v-model="form.title"
              label="Заголовок"
              variant="outlined"
              class="mb-4"
              maxlength="100"
            ></v-text-field>

            <!-- Текст уведомления -->
            <v-textarea
              v-model="form.message"
              label="Текст уведомления"
              variant="outlined"
              rows="6"
              class="mb-4"
              counter
              maxlength="1000"
            ></v-textarea>

            <!-- Кнопки действия -->
            <v-row>
              <v-col cols="6">
                <v-btn
                  variant="outlined"
                  block
                  @click="resetForm"
                >
                  Очистить
                </v-btn>
              </v-col>
              <v-col cols="6">
                <v-btn
                  color="blue-darken-2"
                  block
                  @click="sendNotification"
                  :loading="sending"
                  :disabled="!isFormValid"
                >
                  <v-icon start>mdi-send</v-icon>
                  Отправить
                </v-btn>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Превью и результаты -->
      <v-col cols="12" md="6">
        <!-- Превью сообщения -->
        <v-card class="rounded-lg mb-4" elevation="2">
          <v-card-title class="text-h6"> Превью</v-card-title>
          <v-card-text class="pa-6">
            <div v-if="form.title" class="mb-4">
              <div class="text-h6 font-weight-bold">{{ form.title }}</div>
            </div>
            <div v-if="form.message" class="text-body-2 mb-4 pa-3 rounded-lg" style="background: rgba(0,0,0,0.05)">
              {{ form.message }}
            </div>
            <div v-if="form.recipients.length > 0 || selectAllTeachers" class="mt-4 pt-4 border-t">
              <label class="text-body-2 font-weight-bold d-block mb-2">Получатели:</label>
              <div v-if="selectAllTeachers" class="text-body-2 text-grey-darken-1">
                 Все {{ availableTeachers.length }} преподавателей
              </div>
              <div v-else class="text-body-2 text-grey-darken-1">
                 {{ form.recipients.length }} получателей выбрано
              </div>
            </div>
            <div v-else class="text-body-2 text-orange-darken-2">
               Получатели не выбраны
            </div>
          </v-card-text>
        </v-card>

        <!-- Результат отправки -->
        <v-alert
          v-if="sendResult"
          :type="sendResult.success ? 'success' : 'error'"
          variant="tonal"
          class="rounded-lg"
          closable
          @input="(v) => { if (!v) sendResult = null }"
        >
          {{ sendResult.message }}
        </v-alert>

        <!-- Инструкции -->
        <v-card v-if="!sendResult" class="rounded-lg" elevation="1" style="background: rgba(0,0,0,0.02)">
          <v-card-text class="pa-4 text-body-2">
            <strong> Информация:</strong>
            <ul class="pl-4 mt-2">
              <li>Уведомления отправляются всем выбранным преподавателям</li>
              <li>Максимальная длина заголовка: 100 символов</li>
              <li>Максимальная длина сообщения: 1000 символов</li>
            </ul>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-card-text>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../../api/axios'

const sending = ref(false)
const selectAllTeachers = ref(false)
const availableTeachers = ref([])
const sendResult = ref(null)

const notificationTypes = [
  { title: ' Важное объявление', value: 'announcement' },
  { title: ' Напоминание о дедлайне', value: 'reminder' },
  { title: ' Завершение задачи', value: 'completion' },
  { title: ' Техническое уведомление', value: 'technical' },
  { title: ' Прочее', value: 'other' }
]

const form = ref({
  notificationType: 'announcement',
  recipients: [],
  title: '',
  message: ''
})

const typeDescriptions = {
  announcement: 'Важное объявление для всех преподавателей',
  reminder: 'Напоминание о важном дедлайне или событии',
  completion: 'Уведомление об успешном завершении операции',
  technical: 'Техническое уведомление системы',
  other: 'Прочее'
}

const isFormValid = computed(() => {
  return form.value.title.trim().length > 0 &&
         form.value.message.trim().length > 0 &&
         (form.value.recipients.length > 0 || selectAllTeachers.value)
})

onMounted(async () => {
  await loadTeachers()
})

const loadTeachers = async () => {
  try {
    const response = await api.get('/admin/teachers/')
    availableTeachers.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки преподавателей:', error)
    availableTeachers.value = []
  }
}

const updateTypeDescription = () => {
  // Description is shown in list, can be extended for more detailed UI
}

const toggleSelectAll = () => {
  if (selectAllTeachers.value) {
    form.value.recipients = []
  }
}

const resetForm = () => {
  form.value = {
    notificationType: 'announcement',
    recipients: [],
    title: '',
    message: ''
  }
  selectAllTeachers.value = false
  sendResult.value = null
}

const sendNotification = async () => {
  if (!isFormValid.value) return

  sending.value = true

  try {
    const recipients = selectAllTeachers.value
      ? availableTeachers.value.map(t => t.id)
      : form.value.recipients

    const response = await api.post('/admin/notifications/send', {
      notification_type: form.value.notificationType,
      title: form.value.title,
      message: form.value.message,
      recipient_teacher_ids: recipients
    })

    sendResult.value = {
      success: true,
      message: ` Уведомление успешно отправлено ${recipients.length} преподавателям`
    }

    resetForm()
  } catch (error) {
    sendResult.value = {
      success: false,
      message: ' Ошибка отправки: ' + (error.response?.data?.detail || error.message)
    }
  } finally {
    sending.value = false
  }
}
</script>
