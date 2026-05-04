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

const setupInput = (input) => {
  if (input.dataset.nkb) return
  input.dataset.nkb = '1'
  input.setAttribute('inputmode', 'none')
  input.addEventListener('focus', function () {
    window.requestAnimationFrame(() => this.blur())
  })
}

const applyToAll = () => {
  document.querySelectorAll('.v-select input').forEach(setupInput)
}

onMounted(() => {
  applyToAll()
  observer = new MutationObserver(applyToAll)
  observer.observe(document.body, { childList: true, subtree: true })
})

onUnmounted(() => {
  observer?.disconnect()
})
</script>
