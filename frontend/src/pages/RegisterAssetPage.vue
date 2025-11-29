<!-- File path: frontend/src/pages/RegisterAssetPage.vue -->
<template>
  <q-page padding>
    <q-card>
      <q-card-section class="row items-center justify-between">
        <div class="text-subtitle1">Đăng ký Tài sản Ra/Vào</div>
      </q-card-section>
      <q-separator />
      <q-card-section>
        <q-form @submit="onSubmit" class="q-gutter-y-md">

          <!-- Form đăng ký tài sản -->
          <div class="row q-col-gutter-md">
            <div class="col-12 col-md-4">
              <q-input 
                :model-value="auth.user?.full_name" 
                label="Họ tên NV" 
                dense 
                outlined 
                readonly 
              />
            </div>
            <div class="col-12 col-md-4">
              <q-input 
                :model-value="auth.user?.username" 
                label="Mã NV" 
                dense 
                outlined 
                readonly 
              />
            </div>
            <!-- === FIX (TASK 4): Cho phép chỉnh sửa Bộ phận === -->
            <div class="col-12 col-md-4">
              <q-input 
                v-model="form.department" 
                label="Bộ phận" 
                dense 
                outlined 
                required
              />
            </div>
            <!-- === KẾT THÚC FIX === -->
            
            <div class="col-12 col-md-6">
              <q-input 
                v-model="form.destination" 
                label="Chuyển đến (Nơi nhận/Công ty)" 
                dense 
                outlined 
                required 
              />
            </div>
            
            <div class="col-12 col-md-3">
              <q-input 
                v-model.number="form.quantity" 
                label="Số lượng" 
                type="number" 
                dense 
                outlined 
                required 
                :rules="[val => val > 0 || 'Số lượng phải lớn hơn 0']"
              />
            </div>

             <div class="col-12 col-md-3">
               <q-input 
                v-model="form.expected_return_date" 
                label="Ngày dự kiến hoàn trả" 
                dense 
                outlined 
                mask="date" 
                hint="Tùy chọn (để trống nếu không về)"
                clearable
              >
                <template v-slot:append>
                  <q-icon name="event" class="cursor-pointer">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-date v-model="form.expected_return_date">
                        <div class="row items-center justify-end">
                          <q-btn v-close-popup label="Đóng" color="primary" flat />
                        </div>
                      </q-date>
                    </q-popup-proxy>
                  </q-icon>
                </template>
               </q-input>
            </div>

            <div class="col-12">
              <q-input 
                type="textarea" 
                v-model="form.description_reason" 
                label="Mô tả Tài sản & Lý do mang ra *" 
                outlined 
                dense 
                required 
                :rules="[val => val && val.trim().length > 0 || 'Mô tả không được để trống']"
                hint="Vui lòng mô tả chi tiết tài sản"
              />
            </div>

            <!-- Image Upload Field -->
            <div class="col-12">
              <q-file 
                v-model="selectedImages" 
                label="Hình ảnh tài sản *" 
                outlined 
                dense
                multiple
                accept="image/*"
                max-files="5"
                counter
                required
                hint="Chọn tối đa 5 ảnh. Ảnh bắt buộc."
                :rules="[val => (val && val.length > 0) || 'Vui lòng chọn ít nhất 1 ảnh']"
              >
                <template v-slot:prepend>
                  <q-icon name="attach_file" />
                </template>
              </q-file>
            </div>

            <!-- Image Preview -->
            <div v-if="imagePreviews.length > 0" class="col-12">
              <div class="text-caption q-mb-sm">Xem trước:</div>
              <div class="row q-col-gutter-sm">
                <div v-for="(preview, index) in imagePreviews" :key="index" class="col-6 col-sm-4 col-md-3">
                  <q-card flat bordered>
                    <q-img :src="preview" ratio="1" />
                  </q-card>
                </div>
              </div>
            </div>
          </div>

          <div class="col-12">
            <q-btn 
              type="submit" 
              label="Đăng ký Tài sản" 
              color="primary" 
              :loading="isSubmitting"
              :disable="isSubmitting"
            />
          </div>
        </q-form>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup>
import { reactive, ref, computed, watch } from 'vue'
import { useQuasar, date as quasarDate } from 'quasar'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const $q = useQuasar()
const auth = useAuthStore()

// === FIX (TASK 4): Cập nhật logic form cho Bộ phận ===

// 1. Tính toán giá trị bộ phận mặc định
const departmentDisplay = computed(() => {
  if (auth.user?.department) return auth.user.department;
  if (auth.user?.full_name && auth.user.full_name.includes('-')) {
    return auth.user.full_name.split('-')[0].trim();
  }
  return ''; // Trả về rỗng nếu không có
})

// 2. Thêm 'department' vào trạng thái form ban đầu
const initialFormState = {
  destination: '',
  description_reason: '',
  quantity: 1,
  expected_return_date: null,
  department: departmentDisplay.value, // Gán giá trị mặc định
}

const form = reactive({ ...initialFormState })
const isSubmitting = ref(false)
const selectedImages = ref(null)
const imagePreviews = ref([])

// Watch for image selection changes to generate previews
watch(selectedImages, (newFiles) => {
  imagePreviews.value = []
  if (newFiles && newFiles.length > 0) {
    for (const file of newFiles) {
      const reader = new FileReader()
      reader.onload = (e) => {
        imagePreviews.value.push(e.target.result)
      }
      reader.readAsDataURL(file)
    }
  }
})

// (Xóa computed 'departmentDisplay' cũ ở đây nếu có)

async function onSubmit() {
  isSubmitting.value = true;
  try {
    // Validate quantity
    if (!form.quantity || form.quantity <= 0) {
        $q.notify({ type: 'negative', message: 'Số lượng phải lớn hơn 0.' });
        isSubmitting.value = false;
        return;
    }

    // Validate images
    if (!selectedImages.value || selectedImages.value.length === 0) {
        $q.notify({ type: 'negative', message: 'Vui lòng chọn ít nhất 1 ảnh.' });
        isSubmitting.value = false;
        return;
    }

    // Chuẩn bị payload
    const payload = {
      ...form, // 'department' đã có trong form
      // Chuyển đổi ngày (YYYY/MM/DD) sang (YYYY-MM-DD) cho backend
      expected_return_date: form.expected_return_date 
        ? quasarDate.formatDate(quasarDate.extractDate(form.expected_return_date, 'YYYY/MM/DD'), 'YYYY-MM-DD') 
        : null
    };
    
    // Step 1: Create asset
    const response = await api.post('/assets', payload); 
    const assetId = response.data.id;
    
    // Step 2: Upload images
    const uploadPromises = []
    for (const file of selectedImages.value) {
      const formData = new FormData()
      formData.append('file', file)
      uploadPromises.push(
        api.post(`/assets/${assetId}/upload-image`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      )
    }
    
    await Promise.all(uploadPromises)
    
    $q.notify({ type: 'positive', message: 'Đăng ký tài sản và tải ảnh thành công!' });
    resetForm();

  } catch (error) {
    console.error("Asset registration failed:", error);
    $q.notify({ type: 'negative', message: error.response?.data?.detail || 'Đăng ký thất bại.' })
  } finally {
    isSubmitting.value = false
  }
}

function resetForm() {
  Object.assign(form, initialFormState);
  form.quantity = 1;
  form.expected_return_date = null;
  form.department = departmentDisplay.value; // Reset lại bộ phận về mặc định
  selectedImages.value = null
  imagePreviews.value = []
}
</script>
