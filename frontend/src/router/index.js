import { createRouter, createWebHistory } from 'vue-router'
import { getCurrentUser } from 'vuefire'
import { collection, doc, getDoc } from 'firebase/firestore'
import { db } from '@/main'

import LoginView from '@/views/LoginView.vue'
const ScoreView = () => import('@/views/ScoreView.vue')
const AdminView = () => import('@/views/AdminView.vue')
const MainView = () => import('@/views/MainView.vue')

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/score',
      name: 'score',
      component: ScoreView,
      meta: { requiresAuth: true },
    },

    {
      path: '/admin',
      name: 'admin',
      component: AdminView,
      meta: { requiresAuth: true },
    },

    {
      path: '/main',
      name: 'main',
      component: MainView,
      meta: { requiresAuth: true },
    },

  ],
})

router.beforeEach(async (to) => {
  if (to.meta.requiresAuth) {
    const currentUser = await getCurrentUser()
    const currentUserAuthorization = await getDoc(doc(collection(db, 'authorization'), currentUser.uid))

    const isUserDefined = currentUserAuthorization.exists()
    const isUserFullAdmin = isUserDefined ? currentUserAuthorization.get('level') == 'full' : false
    const isUserAdmin = isUserDefined ? currentUserAuthorization.get('level') == 'admin' : false

    if (!currentUser || !isUserDefined) {
      return {
        path: '/',
      }
    }

    if ((!isUserAdmin && !isUserFullAdmin) && to.fullPath == '/admin') {
      return {
        path: '/score',
      }
    }

    if (!isUserFullAdmin && to.fullPath == '/main') {
      return {
        path: '/admin',
      }
    }
  }
})

export default router
