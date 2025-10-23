<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { NCard, NForm, NFormItem, NInput, NButton, NSpace, NAlert, useMessage } from 'naive-ui'

const authStore = useAuthStore()
const message = useMessage()

const email = ref('')
const step = ref<'email' | 'success'>('email')

async function handleRequestMagicLink() {
  if (!email.value) {
    message.error('Please enter your email address')
    return
  }

  const result = await authStore.requestMagicLink(email.value)

  if (result.success) {
    step.value = 'success'
    message.success('Magic link sent! Check your email.')
  } else {
    message.error(result.message || 'Failed to send magic link')
  }
}
</script>

<template>
  <div class="login-container">
    <n-card class="login-card" title="Login">
      <n-space vertical :size="24">
        <!-- Email Step -->
        <div v-if="step === 'email'">
          <n-form>
            <n-form-item label="Email">
              <n-input
                v-model:value="email"
                type="text"
                name="email"
                placeholder="Enter your email"
                @keyup.enter="handleRequestMagicLink"
                :disabled="authStore.isLoading"
              />
            </n-form-item>

            <n-alert
              v-if="authStore.error"
              type="error"
              :title="authStore.error"
              closable
              @close="authStore.error = null"
            />

            <n-button
              type="primary"
              block
              :loading="authStore.isLoading"
              @click="handleRequestMagicLink"
            >
              Send Magic Link
            </n-button>
          </n-form>
        </div>

        <!-- Success Step -->
        <div v-else-if="step === 'success'">
          <n-alert type="success" title="Check your email!">
            We've sent you a magic link. Click the link in your email to complete login.
          </n-alert>

          <n-button
            text
            type="primary"
            @click="step = 'email'"
            style="margin-top: 16px"
          >
            Send another link
          </n-button>
        </div>
      </n-space>
    </n-card>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 24px;
}

.login-card {
  width: 100%;
  max-width: 400px;
}
</style>
