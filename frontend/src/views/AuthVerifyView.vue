<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { NCard, NSpin, NResult, NButton, useMessage } from 'naive-ui'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const message = useMessage()

onMounted(async () => {
  const token = route.query.token as string

  if (!token) {
    message.error('No token provided')
    router.push('/login')
    return
  }

  const success = await authStore.verifyMagicLink(token)

  if (success) {
    message.success('Login successful!')
    // Redirect to home page
    setTimeout(() => {
      router.push('/')
    }, 1000)
  }
})
</script>

<template>
  <div class="verify-container">
    <n-card class="verify-card">
      <div v-if="authStore.isLoading" class="loading-state">
        <n-spin size="large" />
        <p style="margin-top: 16px">Verifying your magic link...</p>
      </div>

      <n-result
        v-else-if="authStore.error"
        status="error"
        title="Verification Failed"
        :description="authStore.error"
      >
        <template #footer>
          <n-button type="primary" @click="router.push('/login')">
            Back to Login
          </n-button>
        </template>
      </n-result>

      <n-result
        v-else-if="authStore.isAuthenticated"
        status="success"
        title="Login Successful"
        description="Redirecting you to the home page..."
      />
    </n-card>
  </div>
</template>

<style scoped>
.verify-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 24px;
}

.verify-card {
  width: 100%;
  max-width: 500px;
  text-align: center;
}

.loading-state {
  padding: 40px 20px;
}
</style>
