import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  requestMagicLinkApiV1AuthMagicLinkPost,
  verifyMagicLinkApiV1AuthVerifyPost,
  getCurrentUserProfileApiV1AuthMeGet,
} from '@/api/sdk.gen'
import type { UserResponse } from '@/api/types.gen'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<UserResponse | null>(null)
  const sessionToken = ref<string | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!user.value && !!sessionToken.value)

  // Actions
  async function requestMagicLink(email: string): Promise<{ success: boolean; message?: string }> {
    isLoading.value = true
    error.value = null

    try {
      const response = await requestMagicLinkApiV1AuthMagicLinkPost({
        body: { email },
      })

      if (response.data) {
        return { success: true, message: response.data.message }
      }
      return { success: false }
    } catch (err: unknown) {
      const errorMessage = (err as Error).message || 'Failed to send magic link'
      error.value = errorMessage
      return { success: false, message: errorMessage }
    } finally {
      isLoading.value = false
    }
  }

  async function verifyMagicLink(token: string): Promise<boolean> {
    isLoading.value = true
    error.value = null

    try {
      const response = await verifyMagicLinkApiV1AuthVerifyPost({
        body: { token },
      })

      if (response.data) {
        sessionToken.value = response.data.access_token
        user.value = response.data.user as UserResponse

        // Store session token in localStorage for persistence
        localStorage.setItem('session_token', response.data.access_token)

        return true
      }
      return false
    } catch (err: unknown) {
      error.value = (err as Error).message || 'Invalid or expired magic link'
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function fetchCurrentUser(): Promise<boolean> {
    if (!sessionToken.value) {
      return false
    }

    isLoading.value = true
    error.value = null

    try {
      const response = await getCurrentUserProfileApiV1AuthMeGet({
        headers: {
          authorization: sessionToken.value ? `Bearer ${sessionToken.value}` : undefined,
        },
      })

      if (response.data) {
        user.value = response.data
        return true
      }
      return false
    } catch (err: unknown) {
      error.value = (err as Error).message || 'Failed to fetch user profile'
      // If unauthorized, clear the session
      if ((err as { status?: number }).status === 401) {
        logout()
      }
      return false
    } finally {
      isLoading.value = false
    }
  }

  function logout() {
    user.value = null
    sessionToken.value = null
    error.value = null
    localStorage.removeItem('session_token')
  }

  function initializeSession() {
    const storedToken = localStorage.getItem('session_token')
    if (storedToken) {
      sessionToken.value = storedToken
      // Fetch user profile to validate session
      fetchCurrentUser()
    }
  }

  return {
    // State
    user,
    sessionToken,
    isLoading,
    error,
    // Getters
    isAuthenticated,
    // Actions
    requestMagicLink,
    verifyMagicLink,
    fetchCurrentUser,
    logout,
    initializeSession,
  }
})
