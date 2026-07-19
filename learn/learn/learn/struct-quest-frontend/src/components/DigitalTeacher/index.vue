<template>
  <div class="digital-teacher">
    <!-- 讯飞虚拟人 SDK 渲染容器 — 充满整个区域 -->
    <div v-show="iflytekActive && !iflytekError" ref="iflytekContainer" class="iflytek-container"></div>

    <!-- 讯飞错误 -->
    <div v-if="iflytekError" class="error-overlay">
      <span class="error-emoji">⚠️</span>
      <p class="error-title">讯飞虚拟人异常</p>
      <p class="error-detail">{{ iflytekError }}</p>
      <button class="retry-btn" @click="retryIflytek">🔄 重试</button>
    </div>

    <!-- 初始化中 -->
    <div v-else-if="iflytekActive && !iflytekReady" class="loading-overlay">
      <div class="loading-spinner"></div>
      <p class="loading-text">数字人初始化中...</p>
    </div>

    <!-- 待机 -->
    <div v-else-if="!iflytekActive && !iflytekError" class="standby-overlay">
      <span class="standby-emoji">🧑‍🏫</span>
      <p class="standby-text">{{ iflytekConfig?.appId ? '点击连接数字人' : '等待配置...' }}</p>
    </div>

    <!-- 状态条（绝对定位浮层） -->
    <transition name="fade">
      <div v-if="statusText" class="status-toast" :class="statusType">
        {{ statusText }}
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, watch, onBeforeUnmount, nextTick } from 'vue'
import AvatarPlatform from '@/lib/avatar-sdk-web/index.js'

const props = defineProps({
  iflytekConfig: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['loaded', 'error'])

// ═══ 讯飞 SDK 状态 ═══
const iflytekContainer = ref(null)
const iflytekActive = ref(false)
const iflytekReady = ref(false)
const iflytekError = ref('')
let avatarPlatform = null
const textQueue = []

const statusText = ref('')
const statusType = ref('info')

// ═══ 讯飞 SDK 初始化 ═══
async function initAvatarPlatform() {
  const cfg = props.iflytekConfig || {}
  if (!cfg.appId || !cfg.apiKey || !cfg.apiSecret) {
    iflytekError.value = '讯飞虚拟人未配置：缺少 APPID/APIKey/APISecret，请检查 .env 配置'
    statusText.value = '讯飞配置不完整'
    statusType.value = 'error'
    return
  }

  iflytekError.value = ''

  try {
    avatarPlatform = new AvatarPlatform({ logLevel: 2 })

    avatarPlatform.setApiInfo({
      appId: cfg.appId,
      apiKey: cfg.apiKey,
      apiSecret: cfg.apiSecret,
    })

    avatarPlatform.setGlobalParams({
      stream: { protocol: 'xrtc', fps: 25, alpha: 0 },
      avatar: {
        avatar_id: cfg.avatarId || '201165002',
        width: 1080,
        height: 1920,
      },
      tts: {
        vcn: 'x4_lingxiaoxuan_oral',
        speed: 50,
        pitch: 50,
        volume: 50,
      },
    })

    await nextTick()
    const wrapper = iflytekContainer.value
    if (!wrapper) {
      iflytekError.value = '渲染容器未就绪'
      return
    }

    await avatarPlatform.start({ wrapper })
    iflytekReady.value = true
    console.log('[DigitalTeacher] 讯飞 AvatarPlatform 已就绪')

    // 发送排队的文本
    if (textQueue.length > 0) {
      for (const t of textQueue) {
        await avatarPlatform.writeText(t, {})
      }
      textQueue.length = 0
    }
    emit('loaded', true)
  } catch (err) {
    console.error('[DigitalTeacher] 讯飞 SDK 初始化失败:', err)
    iflytekError.value = '讯飞 SDK 初始化失败: ' + (err.message || '未知错误')
    statusText.value = '讯飞初始化失败'
    statusType.value = 'error'
    emit('error', err)
  }
}

async function startIflytek() {
  iflytekActive.value = true
  iflytekError.value = ''
  await nextTick()
  initAvatarPlatform()
}

function stopIflytek() {
  iflytekActive.value = false
  iflytekReady.value = false
  iflytekError.value = ''
  if (avatarPlatform) {
    try { avatarPlatform.destroy() } catch (e) {}
    avatarPlatform = null
  }
}

async function retryIflytek() {
  stopIflytek()
  await nextTick()
  startIflytek()
}

async function speakText(text) {
  if (!text) return
  if (iflytekReady.value && avatarPlatform) {
    try {
      await avatarPlatform.writeText(text, {})
      console.log('[DigitalTeacher] 讯飞 speakText:', text.substring(0, 30) + '...')
    } catch (err) {
      console.error('[DigitalTeacher] writeText 失败:', err)
      statusText.value = '讯飞语音输出失败: ' + (err.message || '')
      statusType.value = 'error'
    }
  } else if (iflytekActive.value) {
    // SDK 还没就绪，排队
    textQueue.push(text)
  } else {
    // 讯飞未激活，直接报错
    statusText.value = '讯飞虚拟人未激活，请先选择讯飞模式'
    statusType.value = 'error'
  }
}

// ═══ WebSocket 消息处理 ═══
function handleWsMessage(data) {
  // 保留以兼容外部调用，但当前只需处理 done 事件
  if (data.type === 'tts_error') {
    statusText.value = data.message || '语音处理出错'
    statusType.value = 'error'
    setTimeout(() => { statusText.value = '' }, 3000)
  }
}

function resetState() {
  statusText.value = ''
}

function clearAll() {
  statusText.value = ''
}

// ═══ 监听 iflytekConfig 变化自动初始化 ═══
watch(() => props.iflytekConfig, (cfg) => {
  if (cfg && cfg.appId && !iflytekActive.value) {
    console.log('[DigitalTeacher] 检测到讯飞配置，自动初始化')
    startIflytek()
  }
}, { immediate: true, deep: true })

onBeforeUnmount(() => {
  if (avatarPlatform) {
    try { avatarPlatform.destroy() } catch (e) {}
    avatarPlatform = null
  }
  iflytekReady.value = false
})

defineExpose({
  handleWsMessage, resetState, clearAll,
  startIflytek, stopIflytek, speakText
})
</script>

<style scoped>
.digital-teacher {
  position: relative;
  width: 100%; height: 100%;
  overflow: hidden;
  background: linear-gradient(180deg, #0f0f2e 0%, #1a1040 50%, #0d1b2a 100%);
}

/* 讯飞 SDK 容器 — 满铺 */
.iflytek-container {
  width: 100%; height: 100%;
}
.iflytek-container :deep(canvas),
.iflytek-container :deep(video) {
  width: 100%; height: 100%;
  object-fit: contain;
}

/* 错误 */
.error-overlay {
  position: absolute; inset: 0;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 10px;
  background: linear-gradient(160deg, #1a0a0a, #2d1111);
  padding: 16px;
}
.error-emoji { font-size: 32px; }
.error-title { color: #fca5a5; font-size: 14px; font-weight: 600; margin: 0; }
.error-detail { color: rgba(248,113,113,0.65); font-size: 11px; margin: 0; text-align: center; max-width: 90%; }
.retry-btn {
  padding: 6px 18px; border: 1px solid rgba(239,68,68,0.35); border-radius: 14px;
  background: rgba(239,68,68,0.12); color: #fca5a5; font-size: 12px; cursor: pointer;
  transition: all 0.2s;
  &:hover { background: rgba(239,68,68,0.25); color: #fff; }
}

/* 加载 */
.loading-overlay {
  position: absolute; inset: 0;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 12px;
}
.loading-spinner {
  width: 36px; height: 36px;
  border: 3px solid rgba(200,76,90,0.15);
  border-top-color: #d86b76; border-right-color: #c84c5a;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.loading-text { color: #e7b9bd; font-size: 13px; margin: 0; }

/* 待机 */
.standby-overlay {
  position: absolute; inset: 0;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 12px;
}
.standby-emoji { font-size: 48px; opacity: 0.6; }
.standby-text { color: rgba(167,139,250,0.6); font-size: 13px; margin: 0; }

/* 状态浮层 */
.status-toast {
  position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%);
  padding: 5px 14px; z-index: 20;
  font-size: 11px; font-weight: 500; border-radius: 10px;
  white-space: nowrap; max-width: 90%;
  backdrop-filter: blur(12px);
  box-shadow: 0 4px 15px rgba(0,0,0,0.2);
  &.info { background: rgba(200,76,90,0.9); color: #fff; }
  &.success { background: rgba(16,185,129,0.9); color: #fff; }
  &.error { background: rgba(239,68,68,0.9); color: #fff; }
  &.warning { background: rgba(245,158,11,0.9); color: #fff; }
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>

