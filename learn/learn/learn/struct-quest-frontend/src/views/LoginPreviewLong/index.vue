<template>
  <div class="login-demo-host">
    <iframe
      ref="frameRef"
      class="login-demo-frame"
      src="/login-demo.html"
      title="StructQuest 登录"
    />
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import authApi from '../../api/auth'
import { useSessionStore } from '../../store/session'
import { getStorage, STORAGE_KEYS } from '../../utils/storage'

const router = useRouter()
const sessionStore = useSessionStore()
const frameRef = ref(null)

function hasLocalOnboardingDone() {
  if (getStorage(STORAGE_KEYS.ONBOARDING_DONE, false)) return true
  const profile = getStorage(STORAGE_KEYS.PROFILE)
  return !!(profile && (profile.persona_type || profile.ability_level))
}

function errorMessage(error) {
  return error?.detail || error?.error || error?.response?.data?.detail || error?.message || '操作失败，请稍后重试'
}

function notifyFrame(action, success, message) {
  frameRef.value?.contentWindow?.postMessage({
    source: 'structquest-login-parent', action, success, message
  }, window.location.origin)
}

async function finishLogin(response, action) {
  sessionStore.login(response.user, response.token)
  notifyFrame(action, true, action === 'register' ? '注册成功，正在创建学习画像' : action === 'guest' ? '游客体验已开启' : `欢迎回来，${response.user.username}`)
  await new Promise(resolve => setTimeout(resolve, 450))
  const onboardingDone = response.user.has_completed_onboarding || hasLocalOnboardingDone()
  await router.replace(response.user.is_admin ? '/admin/users' : onboardingDone ? '/app' : '/onboarding')
}

async function handleAuthMessage(event) {
  if (event.origin !== window.location.origin || event.source !== frameRef.value?.contentWindow) return
  const { source, action, payload = {} } = event.data || {}
  if (source !== 'structquest-login-demo') return

  try {
    if (action === 'login') {
      const response = await authApi.login(payload, { timeout: 10000 })
      await finishLogin(response, action)
    } else if (action === 'register') {
      const response = await authApi.register(payload)
      await finishLogin(response, action)
    } else if (action === 'guest') {
      const response = await authApi.guest()
      await finishLogin(response, action)
    } else if (action === 'forgot') {
      const response = await authApi.forgotPassword(payload.email)
      notifyFrame(action, true, response?.message || '如果该邮箱已注册，重置链接已发送')
    }
  } catch (error) {
    notifyFrame(action, false, errorMessage(error))
  }
}

onMounted(() => window.addEventListener('message', handleAuthMessage))
onBeforeUnmount(() => window.removeEventListener('message', handleAuthMessage))
</script>

<style scoped>
.login-demo-host {
  width: 100%;
  height: 100vh;
  overflow: hidden;
  background: oklch(0.985 0.005 90);
}

.login-demo-frame {
  display: block;
  width: 100%;
  height: 100%;
  border: 0;
  background: oklch(0.985 0.005 90);
}
</style>