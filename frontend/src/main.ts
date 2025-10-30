import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { client } from '@/api/client.gen'

// Configure API client with environment-specific base URL
// In development: uses localhost from .env or defaults to localhost:8000
// In production: uses VITE_API_URL from Railway environment variables
const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
client.setConfig({
  baseUrl: apiUrl
})

// Set up request interceptor to automatically inject authorization headers
client.interceptors.request.use((request) => {
  // Get token from localStorage (persisted session)
  const token = localStorage.getItem('session_token')

  if (token) {
    // Add Authorization header if token exists
    request.headers.set('Authorization', `Bearer ${token}`)
  }

  return request
})

console.log('API configured with base URL:', apiUrl)

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
