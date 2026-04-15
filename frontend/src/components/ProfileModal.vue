<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-0 z-[100] flex items-center justify-center" @click.self="$emit('close')">
      <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="$emit('close')"></div>
      <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden animate-modal-in">
        <div class="px-8 pt-8 pb-4">
          <div class="flex items-center justify-between mb-1">
            <h2 class="text-xl font-bold text-text-primary">编辑个人资料</h2>
            <button @click="$emit('close')" class="p-1 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
              <svg class="w-5 h-5 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <p class="text-sm text-text-secondary">更新你的公开昵称、手机号和个人简介</p>
        </div>

        <form @submit.prevent="handleSubmit" class="px-8 pb-8">
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1.5">邮箱地址</label>
              <input
                v-model="form.email"
                type="email"
                readonly
                disabled
                class="w-full h-11 px-4 rounded-xl border border-border bg-gray-50 text-sm text-text-secondary placeholder:text-text-muted cursor-not-allowed"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-text-primary mb-1.5">昵称</label>
              <input
                v-model="form.nickname"
                type="text"
                placeholder="请输入昵称"
                class="w-full h-11 px-4 rounded-xl border border-border bg-white text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                :disabled="submitting"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-text-primary mb-1.5">手机号</label>
              <input
                v-model="form.phone"
                type="text"
                placeholder="请输入手机号"
                class="w-full h-11 px-4 rounded-xl border border-border bg-white text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                :disabled="submitting"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-text-primary mb-1.5">个人简介</label>
              <textarea
                v-model="form.bio"
                rows="4"
                placeholder="介绍一下你自己"
                class="w-full px-4 py-3 rounded-xl border border-border bg-white text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none"
                :disabled="submitting"
              ></textarea>
            </div>
          </div>

          <div v-if="error" class="mt-4 p-3 rounded-xl bg-red-50 border border-red-100">
            <p class="text-sm text-red-600">{{ error }}</p>
          </div>

          <button
            type="submit"
            :disabled="submitting"
            class="w-full h-11 mt-6 rounded-full bg-primary text-white text-sm font-semibold hover:bg-blue-600 transition-colors shadow-md disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer flex items-center justify-center gap-2"
          >
            <svg v-if="submitting" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {{ submitting ? '保存中...' : '保存资料' }}
          </button>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { updateProfile } from '../api/auth'

const props = defineProps({
  visible: Boolean,
  user: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['close', 'success'])

const form = reactive({
  email: '',
  nickname: '',
  phone: '',
  bio: '',
})

const submitting = ref(false)
const error = ref('')

function syncFromUser(user) {
  form.email = user?.email || ''
  form.nickname = user?.nickname || ''
  form.phone = user?.phone || ''
  form.bio = user?.bio || ''
}

watch(
  () => props.user,
  (nextUser) => {
    syncFromUser(nextUser)
    error.value = ''
  },
  { immediate: true, deep: true }
)

watch(
  () => props.visible,
  (isVisible) => {
    if (!isVisible) return
    syncFromUser(props.user)
    error.value = ''
  }
)

async function handleSubmit() {
  error.value = ''
  submitting.value = true
  try {
    const updatedUser = await updateProfile({
      nickname: form.nickname,
      phone: form.phone,
      bio: form.bio,
    })
    emit('success', updatedUser)
    emit('close')
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || '更新失败'
    error.value = typeof msg === 'string' ? msg : JSON.stringify(msg)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
@keyframes modal-in {
  from { opacity: 0; transform: scale(0.95) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
.animate-modal-in {
  animation: modal-in 0.2s ease-out;
}
</style>
