<template>
  <v-app>
    <v-main>
      <router-view></router-view>
    </v-main>
  </v-app>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'

let observer = null

onMounted(() => {
  const applyInputMode = () => {
    document.querySelectorAll('.v-select input:not([inputmode])').forEach(input => {
      input.setAttribute('inputmode', 'none')
    })
  }
  applyInputMode()
  observer = new MutationObserver(applyInputMode)
  observer.observe(document.body, { childList: true, subtree: true })
})

onUnmounted(() => {
  observer?.disconnect()
})
</script>
