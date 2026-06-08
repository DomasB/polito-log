<script setup lang="ts">
import { NConfigProvider, NMessageProvider } from 'naive-ui'
import { darkTheme } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'
import { useRoute } from 'vue-router'
import { onMounted, computed } from 'vue'
import AppHeader from '@/components/AppHeader.vue'

const authStore = useAuthStore()
const route = useRoute()

const showHeader = computed(() => {
  // Hide header on login and auth verify pages
  return route.path !== '/login' && !route.path.startsWith('/auth/')
})

onMounted(() => {
  authStore.initializeSession()
})
</script>

<template>
  <n-config-provider :theme="darkTheme">
    <n-message-provider>
      <div class="app-container">
        <app-header v-if="showHeader" />
        <main class="main-content">
          <router-view />
        </main>
      </div>
    </n-message-provider>
  </n-config-provider>
</template>

<style>
body {
  margin: 0;
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #121212;
  height: 100vh;
}

.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-content {
  flex: 1;
}
</style>
