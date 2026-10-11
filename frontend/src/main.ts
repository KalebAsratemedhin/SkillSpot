import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import 'leaflet/dist/leaflet.css'
import './style.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Mount immediately so refresh isn't a blank white page while auth hydrates.
// Router beforeEach still awaits initialize() when a token is present.
app.mount('#app')

const authStore = useAuthStore()
void authStore.initialize()
