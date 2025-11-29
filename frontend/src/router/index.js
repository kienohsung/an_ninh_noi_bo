// File: frontend/src/router/index.js
// (FIXED: Đã sửa lỗi cú pháp khi thêm route)

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
import VehicleLogPage from '../pages/VehicleLogPage.vue'

// === CHECKLIST 2.9 (SỬA LỖI): Import 2 trang mới ===
import RegisterAssetPage from '../pages/RegisterAssetPage.vue'
import AssetManagementPage from '../pages/AssetManagementPage.vue'


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
      { path: 'vehicle-log', component: VehicleLogPage, meta: { roles: ['admin', 'manager'] } },
      { path: 'suppliers', component: SuppliersPage, meta: { roles: ['admin','manager'] } },
      { path: 'users', component: UsersPage, meta: { roles: ['admin','manager'] } }, // <-- (FIXED) Đã thêm dấu phẩy
      
      // === CHECKLIST 2.9 (SỬA LỖI): Thêm 2 route mới ===
      { 
        path: 'register-asset', 
        component: RegisterAssetPage, 
        meta: { roles: ['admin','manager','staff'] } 
      },
      { 
        path: 'asset-management', 
        component: AssetManagementPage, 
        meta: { roles: ['admin','manager'] } 
      }
      // === KẾT THÚC CHECKLIST 2.9 ===
    ]
  }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    auth.returnUrl = to.fullPath
    return next('/login')
  }

  // Kiểm tra role
  if (to.meta.roles) {
    if (!to.meta.roles.includes(auth.user?.role)) {
      // Nếu không có quyền, về trang mặc định
      return next(defaultRouteForRole(auth.user?.role))
    }
  }

  return next()
})

export default router