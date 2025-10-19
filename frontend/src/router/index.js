// File: frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import MainLayout from '../layouts/MainLayout.vue'
import LoginPage from '../pages/LoginPage.vue'
import DashboardPage from '../pages/DashboardPage.vue'
import RegisterGuest from '../pages/RegisterGuest.vue'
import GuardGate from '../pages/GuardGate.vue'
import SuppliersPage from '../pages/SuppliersPage.vue'
import UsersPage from '../pages/UsersPage.vue'
import LongTermGuestsPage from '../pages/LongTermGuestsPage.vue'
// (BƯỚC 1) IMPORT TRANG MỚI
import VehicleLogPage from '../pages/VehicleLogPage.vue'

function defaultRouteForRole (role) {
  if (role === 'admin' || role === 'manager') return '/dashboard'
  if (role === 'guard') return '/guard-gate'
  return '/register-guest' // staff
}

const routes = [
  { path: '/login', component: LoginPage },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: (to) => {
        const auth = useAuthStore()
        if (auth.user) {
          return defaultRouteForRole(auth.user.role)
        }
        return '/login'
      }},
      { path: 'dashboard', component: DashboardPage, meta: { roles: ['admin','manager'] } },      
      { path: 'register-guest', component: RegisterGuest, meta: { roles: ['admin','manager','staff'] } },
      { path: 'long-term-guests', component: LongTermGuestsPage, meta: { roles: ['admin','manager','staff'] } },
      { path: 'guard-gate', component: GuardGate, meta: { roles: ['admin','guard'] } },
      // (BƯỚC 2) THÊM ĐỊNH NGHĨA ROUTE MỚI
      { path: 'vehicle-log', component: VehicleLogPage, meta: { roles: ['admin', 'manager'] } },
      { path: 'suppliers', component: SuppliersPage, meta: { roles: ['admin','manager'] } },
      { path: 'users', component: UsersPage, meta: { roles: ['admin','manager'] } }
    ]
  }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return next('/login')
  }
  if (to.meta.roles && auth.user && !to.meta.roles.includes(auth.user.role)) {
    return next(defaultRouteForRole(auth.user.role))
  }
  next()
})

export default router

