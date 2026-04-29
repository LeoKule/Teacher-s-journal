<template>
  <v-card-text class="pa-6">
    <v-row class="mb-4">
      <v-col cols="12" class="d-flex align-center justify-space-between flex-wrap gap-2">
        <h6 class="admin-section-title text-h6 font-weight-bold">Уведомления</h6>
      </v-col>
    </v-row>

    <v-tabs v-model="activeTab" color="primary" class="mb-6">
      <v-tab value="send">
        <v-icon start>mdi-send</v-icon>
        Отправить
      </v-tab>
      <v-tab value="history">
        <v-icon start>mdi-history</v-icon>
        История
      </v-tab>
    </v-tabs>

    <v-window v-model="activeTab">
      <!-- Вкладка: Отправить -->
      <v-window-item value="send">
        <v-row>
          <!-- Форма отправки -->
          <v-col cols="12" md="6">
            <v-card class="rounded-lg" elevation="2">
              <v-card-title class="text-h6">Новое уведомление</v-card-title>
              <v-card-text class="pa-6">
                <v-select
                  v-model="form.notificationType"
                  :items="notificationTypes"
                  label="Тип уведомления"
                  variant="outlined"
                  class="mb-4"
                ></v-select>

                <div class="mb-4">
                  <label class="text-body-2 font-weight-bold d-block mb-3">Получатели:</label>
                  <v-sheet border rounded="lg" class="pa-4">
                    <v-checkbox
                      v-model="selectAllTeachers"
                      label="Все преподаватели"
                      @update:model-value="toggleSelectAll"
                      class="mb-3"
                      hide-details
                    ></v-checkbox>
                    <div v-if="!selectAllTeachers" class="ml-6">
                      <v-checkbox
                        v-for="teacher in availableTeachers"
                        :key="teacher.id"
                        v-model="form.recipients"
                        :value="teacher.id"
                        :label="`${teacher.full_name} (${teacher.email})`"
                        class="mb-2"
                        hide-details
                      ></v-checkbox>
                    </div>
                  </v-sheet>
                </div>

                <v-text-field
                  v-model="form.title"
                  label="Заголовок"
                  variant="outlined"
                  class="mb-4"
                  maxlength="100"
                ></v-text-field>

                <v-textarea
                  v-model="form.message"
                  label="Текст уведомления"
                  variant="outlined"
                  rows="6"
                  class="mb-4"
                  counter
                  maxlength="1000"
                ></v-textarea>

                <v-row>
                  <v-col cols="6">
                    <v-btn variant="outlined" block @click="resetForm">Очистить</v-btn>
                  </v-col>
                  <v-col cols="6">
                    <v-btn
                      color="primary"
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

          <!-- Превью и результат -->
          <v-col cols="12" md="6">
            <v-card class="rounded-lg mb-4" elevation="2">
              <v-card-title class="text-h6">Превью</v-card-title>
              <v-card-text class="pa-6">
                <div v-if="form.title" class="mb-4">
                  <div class="text-h6 font-weight-bold">{{ form.title }}</div>
                </div>
                <div v-if="form.message" class="text-body-2 mb-4 pa-3 rounded-lg bg-surface-variant">
                  {{ form.message }}
                </div>
                <div v-if="form.recipients.length > 0 || selectAllTeachers" class="mt-4 pt-4 border-t">
                  <label class="text-body-2 font-weight-bold d-block mb-2">Получатели:</label>
                  <div v-if="selectAllTeachers" class="text-body-2 text-medium-emphasis">
                    Все {{ availableTeachers.length }} преподавателей
                  </div>
                  <div v-else class="text-body-2 text-medium-emphasis">
                    {{ form.recipients.length }} получателей выбрано
                  </div>
                </div>
                <div v-else class="text-body-2 text-warning">Получатели не выбраны</div>
              </v-card-text>
            </v-card>

            <v-alert
              v-if="sendResult"
              :type="sendResult.success ? 'success' : 'error'"
              variant="tonal"
              class="rounded-lg"
              closable
              @update:modelValue="(v) => { if (!v) sendResult = null }"
            >
              {{ sendResult.message }}
            </v-alert>

            <v-card v-if="!sendResult" class="rounded-lg" elevation="0" variant="tonal" color="info">
              <v-card-text class="pa-4 text-body-2">
                <strong>Информация:</strong>
                <ul class="pl-4 mt-2">
                  <li>Уведомления видны только в истории на этой странице</li>
                  <li>Максимальная длина заголовка: 100 символов</li>
                  <li>Максимальная длина сообщения: 1000 символов</li>
                </ul>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-window-item>

      <!-- Вкладка: История -->
      <v-window-item value="history">
        <div class="d-flex justify-end mb-4">
          <v-btn variant="outlined" prepend-icon="mdi-refresh" @click="loadHistory" :loading="loadingHistory">
            Обновить
          </v-btn>
        </div>

        <v-progress-linear v-if="loadingHistory" indeterminate class="mb-4"></v-progress-linear>

        <div v-if="!loadingHistory" class="rounded-lg overflow-hidden border">
          <v-table dense hover>
            <thead>
              <tr>
                <th class="text-left">Дата</th>
                <th class="text-left">Тип</th>
                <th class="text-left">Заголовок</th>
                <th class="text-left">Получатели</th>
                <th class="text-left">Сообщение</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="n in history" :key="n.id">
                <td class="text-body-2 text-medium-emphasis text-no-wrap">{{ formatDate(n.created_at) }}</td>
                <td>
                  <v-chip size="small" variant="tonal" :color="typeColor(n.notification_type)">
                    {{ typeLabel(n.notification_type) }}
                  </v-chip>
                </td>
                <td class="text-body-2 font-weight-medium">{{ n.title }}</td>
                <td class="text-body-2">{{ n.recipients_count }} чел.</td>
                <td class="text-body-2 text-medium-emphasis" style="max-width:300px; white-space:normal">
                  {{ n.message.length > 80 ? n.message.slice(0, 80) + '…' : n.message }}
                </td>
              </tr>
              <tr v-if="history.length === 0">
                <td colspan="5" class="text-center py-6 text-medium-emphasis">
                  История пуста. Отправьте первое уведомление.
                </td>
              </tr>
            </tbody>
          </v-table>
        </div>
      </v-window-item>
    </v-window>
  </v-card-text>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import api from '../../api/axios'

const activeTab = ref('send')
const sending = ref(false)
const loadingHistory = ref(false)
const selectAllTeachers = ref(false)
const availableTeachers = ref([])
const sendResult = ref(null)
const history = ref([])

const notificationTypes = [
  { title: 'Важное объявление', value: 'announcement' },
  { title: 'Напоминание о дедлайне', value: 'reminder' },
  { title: 'Завершение задачи', value: 'completion' },
  { title: 'Техническое уведомление', value: 'technical' },
  { title: 'Прочее', value: 'other' }
]

const form = ref({
  notificationType: 'announcement',
  recipients: [],
  title: '',
  message: ''
})

const isFormValid = computed(() =>
  form.value.title.trim().length > 0 &&
  form.value.message.trim().length > 0 &&
  (form.value.recipients.length > 0 || selectAllTeachers.value)
)

onMounted(async () => {
  await loadTeachers()
})

watch(activeTab, (tab) => {
  if (tab === 'history') loadHistory()
})

const loadTeachers = async () => {
  try {
    const res = await api.get('/admin/teachers/')
    availableTeachers.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const loadHistory = async () => {
  loadingHistory.value = true
  try {
    const res = await api.get('/admin/notifications/')
    history.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loadingHistory.value = false
  }
}

const toggleSelectAll = () => {
  if (selectAllTeachers.value) form.value.recipients = []
}

const resetForm = () => {
  form.value = { notificationType: 'announcement', recipients: [], title: '', message: '' }
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
    await api.post('/admin/notifications/send', {
      notification_type: form.value.notificationType,
      title: form.value.title,
      message: form.value.message,
      recipient_teacher_ids: recipients
    })
    sendResult.value = {
      success: true,
      message: `Уведомление успешно отправлено ${recipients.length} преподавателям`
    }
    resetForm()
  } catch (e) {
    sendResult.value = {
      success: false,
      message: 'Ошибка отправки: ' + (e.response?.data?.detail || e.message)
    }
  } finally {
    sending.value = false
  }
}

const formatDate = (iso) => {
  if (!iso) return ''
  return new Date(iso).toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

const TYPE_MAP = {
  announcement: { label: 'Объявление', color: 'primary' },
  reminder: { label: 'Напоминание', color: 'warning' },
  completion: { label: 'Завершение', color: 'success' },
  technical: { label: 'Техническое', color: 'info' },
  other: { label: 'Прочее', color: 'default' }
}

const typeLabel = (t) => TYPE_MAP[t]?.label || t
const typeColor = (t) => TYPE_MAP[t]?.color || 'default'
</script>

<style scoped>
:deep(.v-table thead th) {
  color: rgba(var(--v-theme-on-surface), var(--v-high-emphasis-opacity)) !important;
  background-color: rgb(var(--v-theme-surface-variant)) !important;
}
</style>
