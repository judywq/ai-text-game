import './assets/index.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { useAuthStore } from '@/stores/auth'

// Add version from package.json
const version = __APP_VERSION__
console.log(`ATG Version: ${version}`)

const app = createApp(App)

app.use(createPinia())
app.use(router)

const authStore = useAuthStore()
authStore.initialize().then(() => {
  app.mount('#app')
})
