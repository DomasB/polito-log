<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { NButton, NAvatar, NDropdown, NSpace } from 'naive-ui'
import type { DropdownOption } from 'naive-ui'

const router = useRouter()
const authStore = useAuthStore()

const userInitial = computed(() => {
  if (authStore.user?.username) {
    return authStore.user.username.charAt(0).toUpperCase()
  }
  return '?'
})

const dropdownOptions = computed<DropdownOption[]>(() => [
  {
    label: authStore.user?.email || '',
    key: 'email',
    disabled: true,
  },
  {
    type: 'divider',
    key: 'divider',
  },
  {
    label: 'Logout',
    key: 'logout',
  },
])

function handleDropdownSelect(key: string) {
  if (key === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}

function handleLoginClick() {
  router.push('/login')
}
</script>

<template>
  <header class="app-header">
    <div class="header-content">
      <div class="logo">
        <h2>Polito Log</h2>
      </div>

      <div class="user-section">
        <n-space v-if="authStore.isAuthenticated" align="center">
          <n-dropdown
            :options="dropdownOptions"
            @select="handleDropdownSelect"
            trigger="click"
          >
            <n-avatar
              round
              class="user-avatar"
              style="cursor: pointer"
            >
              {{ userInitial }}
            </n-avatar>
          </n-dropdown>
        </n-space>

        <n-button
          v-else
          type="primary"
          @click="handleLoginClick"
        >
          Login
        </n-button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  width: 100%;
  background-color: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.09);
  padding: 12px 24px;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #fff;
}

.user-section {
  display: flex;
  align-items: center;
}

.user-avatar {
  background-color: #18a058;
  color: #fff;
  font-weight: 600;
}
</style>
