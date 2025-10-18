<!-- File: security_mgmt_dev/frontend/src/pages/LoginPage.vue -->
<template>
  <div class="fullscreen bg-grey-2 flex flex-center">
    <!-- 
      Sửa đổi: 
      - Bỏ style cố định `min-width: 360px`.
      - Sử dụng class "my-card" để định nghĩa chiều rộng linh hoạt, phù hợp với mọi màn hình.
    -->
    <q-card class="my-card">
      <q-card-section>
        <div class="text-h6">Đăng nhập</div>
        <div class="text-caption text-grey-7">Nhập mã nhân viên và mật khẩu</div>
      </q-card-section>
      <q-separator/>
      <q-card-section>
        <q-form @submit="onSubmit" class="q-gutter-md">
          <q-input v-model="username" label="Tên đăng nhập" dense outlined autofocus/>
          <q-input v-model="password" type="password" label="Mật khẩu" dense outlined/>
          <q-btn type="submit" label="Đăng nhập" color="primary" class="full-width"/>
        </q-form>
      </q-card-section>
    </q-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const username = ref('')
const password = ref('')
const auth = useAuthStore()
const router = useRouter()

async function onSubmit () {
  try {
    await auth.login(username.value, password.value)
    router.push('/')
  } catch (e) {
    console.error(e)
    // Thêm thông báo lỗi cho người dùng nếu cần
  }
}
</script>

<!-- Thêm style cho card để đảm bảo tính đáp ứng -->
<style lang="scss" scoped>
.my-card {
  width: 100%;
  max-width: 400px;
  margin: 16px;
}
</style>
