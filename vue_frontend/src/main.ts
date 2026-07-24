import './assets/index.css'
import './styles/line-art/tokens.css'
import './styles/line-art/chrome.css'
import './styles/line-art/book-frame.css'
import './styles/line-art/home.css'
import './styles/line-art/login.css'
import './styles/line-art/auth-pages.css'
import './styles/line-art/library.css'
import './styles/line-art/game-setting.css'
import './styles/line-art/gameplay.css'
import './styles/line-art/document-pages.css'
import './styles/line-art/shadcn-bridge.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { useAuthStore } from '@/stores/auth'

// Add version from package.json
const version = __APP_VERSION__
console.log(`GenQuest Version: ${version}`)

const app = createApp(App)

app.use(createPinia())
app.use(router)

const authStore = useAuthStore()
authStore.initialize().then(() => {
  app.mount('#app')
})
