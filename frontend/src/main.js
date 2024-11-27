import './assets/main.css'
import { VueFire, VueFireAuth } from 'vuefire'
import { initializeApp } from 'firebase/app'

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { getFirestore } from 'firebase/firestore'


// Firebase initialization
const firebaseApp = initializeApp({
    apiKey: import.meta.env.VITE_APIKEY,
    authDomain: import.meta.env.VITE_AUTHDOMAIN,
    databaseURL: import.meta.env.VITE_DATABASEURL,
    projectId: import.meta.env.VITE_PROJECTID,
    storageBucket: import.meta.env.VITE_STORAGEBUCKET,
    messagingSenderId: import.meta.env.VITE_MESSAGINGSENDERID,
    appId: import.meta.env.VITE_APPID,
})

export const db = getFirestore(firebaseApp)

const app = createApp(App)
app.use(router)
app.use(VueFire, {
    firebaseApp,
    modules: [VueFireAuth()],
})
app.mount('#app')
