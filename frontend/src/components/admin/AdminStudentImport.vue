<template>
  <v-card-text class="pa-6">
    <!-- Заголовок -->
    <h6 class="admin-section-title text-h6 font-weight-bold mb-6"> Импорт студентов из CSV</h6>

    <!-- Инструкция -->
    <v-alert type="info" variant="tonal" class="mb-6">
      <strong>Формат CSV:</strong> last_name, first_name, group_name, student_id (опционально)
      <br>
      <strong>Пример:</strong> Петров, Иван, 11-A, P001
    </v-alert>

    <!-- Drag & Drop зона -->
    <v-card
      class="mb-6 pa-8 text-center cursor-pointer border-2 rounded-lg"
      :class="dragover ? 'bg-blue-lighten-5 border-blue' : 'border-dashed border-grey'"
      @dragover.prevent="dragover = true"
      @dragleave="dragover = false"
      @drop.prevent="handleFileDrop"
      elevation="0"
    >
      <v-icon size="64" color="blue-darken-2" class="mb-4">mdi-cloud-upload</v-icon>
      <h5 class="text-h5 mb-2">Перетащите CSV файл сюда</h5>
      <p class="text-body-2 text-grey-darken-1">или нажмите для выбора файла</p>
      
      <input
        ref="fileInput"
        type="file"
        accept=".csv"
        hidden
        @change="handleFileSelect"
      />
      
      <v-btn
        color="blue-darken-2"
        variant="outlined"
        class="mt-4"
        @click="$refs.fileInput.click()"
      >
        <v-icon start>mdi-folder-open</v-icon>
        Выбрать файл
      </v-btn>
    </v-card>

    <!-- Опции импорта -->
    <v-card class="mb-6 pa-4" elevation="1">
      <v-checkbox
        v-model="dryRun"
        label="Dry Run - только проверить без сохранения"
        color="orange"
      ></v-checkbox>
    </v-card>

    <!-- Preview таблица -->
    <v-row v-if="previewData.length > 0" class="mb-6">
      <v-col cols="12">
        <h5 class="text-h6 mb-4"> Предпросмотр ({{ previewData.length }} строк)</h5>
        
        <v-data-table
          :headers="previewHeaders"
          :items="previewData"
          class="rounded-lg"
          density="compact"
        >
          <template #item.status="{ item }">
            <v-chip
              v-if="item.status === 'ok'"
              color="green"
              text-color="white"
              size="small"
            >
              ✓ OK
            </v-chip>
            <v-chip
              v-else
              color="red"
              text-color="white"
              size="small"
            >
              ✗ Ошибка
            </v-chip>
          </template>
        </v-data-table>
      </v-col>
    </v-row>

    <!-- Результат импорта -->
    <v-alert
      v-if="importResult"
      :type="importResult.success ? 'success' : 'error'"
      variant="tonal"
      class="mb-6"
    >
      <strong>{{ importResult.message }}</strong>
      <div v-if="importResult.error_count > 0" class="mt-3">
        <strong>Ошибки:</strong>
        <v-list density="compact" class="mt-2">
          <v-list-item
            v-for="(err, idx) in importResult.errors"
            :key="idx"
            prepend-icon="mdi-alert"
          >
            <v-list-item-title class="text-body-2">
              Строка {{ err.row_number }}: {{ err.error }}
            </v-list-item-title>
          </v-list-item>
        </v-list>
      </div>
    </v-alert>

    <!-- Кнопки действия -->
    <v-row v-if="previewData.length > 0" class="mb-6">
      <v-col cols="12" class="d-flex gap-2">
        <v-btn
          color="blue-darken-2"
          size="large"
          @click="performImport"
          :loading="importing"
          :disabled="importing || previewData.length === 0"
        >
          <v-icon start>mdi-check-all</v-icon>
          {{ dryRun ? 'Проверить' : 'Импортировать' }}
        </v-btn>
        
        <v-btn
          variant="outlined"
          size="large"
          @click="resetForm"
        >
          <v-icon start>mdi-refresh</v-icon>
          Сбросить
        </v-btn>
      </v-col>
    </v-row>
  </v-card-text>
</template>

<script setup>
import { ref } from 'vue'
import api from '../../api/axios'

const fileInput = ref(null)
const dragover = ref(false)
const dryRun = ref(false)
const importing = ref(false)
const previewData = ref([])
const importResult = ref(null)

const previewHeaders = [
  { title: 'Фамилия', key: 'last_name' },
  { title: 'Имя', key: 'first_name' },
  { title: 'Группа', key: 'group_name' },
  { title: 'ID студента', key: 'student_id' },
  { title: 'Статус', key: 'status' }
]

const handleFileDrop = (e) => {
  dragover.value = false
  const file = e.dataTransfer.files[0]
  if (file && file.type === 'text/csv') {
    parseCSV(file)
  } else {
    alert('Пожалуйста, выберите CSV файл')
  }
}

const handleFileSelect = (e) => {
  const file = e.target.files[0]
  if (file && file.type === 'text/csv') {
    parseCSV(file)
  } else {
    alert('Пожалуйста, выберите CSV файл')
  }
}

const parseCSV = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    const text = e.target.result
    const lines = text.split('\n').filter(line => line.trim())
    
    previewData.value = lines.map((line, idx) => {
      const parts = line.split(',').map(p => p.trim())
      return {
        row: idx + 1,
        last_name: parts[0] || '',
        first_name: parts[1] || '',
        group_name: parts[2] || '',
        student_id: parts[3] || '',
        status: parts[0] && parts[1] && parts[2] ? 'ok' : 'error'
      }
    })
  }
  reader.readAsText(file)
}

const performImport = async () => {
  importing.value = true
  importResult.value = null
  
  try {
    const rows = previewData.value.map(item => ({
      last_name: item.last_name,
      first_name: item.first_name,
      group_name: item.group_name,
      student_id: item.student_id || undefined
    }))
    
    const response = await api.post('/admin/students/bulk-import', {
      rows,
      dry_run: dryRun.value
    })
    
    importResult.value = response.data
  } catch (error) {
    importResult.value = {
      success: false,
      message: ' Ошибка при импорте: ' + (error.response?.data?.detail || error.message),
      error_count: 1,
      errors: []
    }
  } finally {
    importing.value = false
  }
}

const resetForm = () => {
  previewData.value = []
  importResult.value = null
  dryRun.value = false
}
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}
</style>
