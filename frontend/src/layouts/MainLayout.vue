<!-- File: frontend/src/layouts/MainLayout.vue -->
<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn flat dense round icon="menu" @click="leftDrawerOpen = !leftDrawerOpen" aria-label="Menu"/>
        <q-toolbar-title>Ứng dụng an ninh nội bộ - Local Security App</q-toolbar-title>
        <div v-if="auth.user" class="row items-center q-gutter-sm">
          <q-chip :label="auth.user.full_name" icon="person" />
          <q-badge color="primary" :label="auth.user.role" />
          <q-btn flat icon="logout" label="Đăng xuất" @click="logout"/>
        </div>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" show-if-above bordered>
      <q-list>
        <q-item v-if="['admin','manager'].includes(auth.user?.role)" clickable v-ripple to="/dashboard">
          <q-item-section avatar><q-icon name="dashboard"/></q-item-section>
          <q-item-section>Dashboard</q-item-section>
        </q-item>

        <q-item v-if="['admin','manager','staff'].includes(auth.user?.role)" clickable v-ripple to="/register-guest">
          <q-item-section avatar><q-icon name="person_add"/></q-item-section>
          <q-item-section>Đăng ký khách</q-item-section>
        </q-item>
        
        <q-item v-if="['admin','manager','staff'].includes(auth.user?.role)" clickable v-ripple to="/long-term-guests">
          <q-item-section avatar><q-icon name="event_repeat"/></q-item-section>
          <q-item-section>Khách dài hạn</q-item-section>
        </q-item>

        <q-item v-if="['admin','guard'].includes(auth.user?.role)" clickable v-ripple to="/guard-gate">
          <q-item-section avatar><q-icon name="login"/></q-item-section>
          <q-item-section>Cổng bảo vệ</q-item-section>
        </q-item>

        <!-- MỤC MENU MỚI CHO NHẬT KÝ XE -->
        <q-item v-if="['admin','manager'].includes(auth.user?.role)" clickable v-ripple to="/vehicle-log">
          <q-item-section avatar><q-icon name="local_shipping" /></q-item-section>
          <q-item-section>Nhật ký xe</q-item-section>
        </q-item>

        <q-item v-if="['admin','manager'].includes(auth.user?.role)" clickable v-ripple to="/suppliers">
          <q-item-section avatar><q-icon name="store"/></q-item-section>
          <q-item-section>Nhà cung cấp</q-item-section>
        </q-item>

        <q-item v-if="['admin','manager'].includes(auth.user?.role)" clickable v-ripple to="/users">
          <q-item-section avatar><q-icon name="group"/></q-item-section>
          <q-item-section>Người dùng</q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view/>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()
const leftDrawerOpen = ref(true)

function logout () {
  auth.logout()
  router.push('/login')
}
</script>

