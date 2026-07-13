<template>
  <!-- 学习模式标签：仅当用户已选择模式时显示 -->
  <div class="mode-tag" v-if="session.learningMode">
    <div
      class="mode-tag-btn"
      :style="{ background: tagStyle.bg, color: tagStyle.color, borderColor: tagStyle.border }"
      @click="showDialog = true"
      :title="`当前：${tagStyle.label}｜点击切换`"
    >
      <span class="mode-tag-icon">{{ tagStyle.icon }}</span>
      <span class="mode-tag-label">{{ tagStyle.label }}</span>
      <span class="mode-tag-arrow">▾</span>
    </div>

    <!-- 切换弹窗 -->
    <transition name="dialog-fade">
      <div class="mode-dialog-overlay" v-if="showDialog" @click.self="showDialog = false">
        <div class="mode-dialog">
          <div class="dialog-header">
            <h3>切换学习模式</h3>
            <button class="dialog-close" @click="showDialog = false">✕</button>
          </div>

          <div class="dialog-current">
            当前模式：
            <span :style="{ color: tagStyle.color, fontWeight: 700 }">{{ tagStyle.label }}</span>
          </div>

          <div class="dialog-modes">
            <div
              v-for="m in modes"
              :key="m.value"
              class="dialog-mode-card"
              :class="{ active: m.value === currentMode }"
              :style="m.value === currentMode ? { borderColor: m.color, background: m.color + '10' } : {}"
              @click="currentMode = m.value"
            >
              <div class="dm-content">
                <span class="dm-icon">{{ m.icon }}</span>
                <div class="dm-text">
                  <span class="dm-label">{{ m.label }}</span>
                  <span class="dm-desc">{{ m.shortDesc }}</span>
                </div>
              </div>
              <span class="dm-check" v-if="m.value === currentMode">✓</span>
            </div>
          </div>

          <div class="dialog-actions">
            <button class="btn-cancel" @click="showDialog = false">取消</button>
            <button
              class="btn-confirm"
              :style="{ background: currentModeInfo.color || '#3b82f6' }"
              :disabled="!currentMode || currentMode === session.learningMode"
              @click="doSwitch"
            >
              切换到「{{ currentModeInfo.label || '...' }}」
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSessionStore } from '../store/session'
import { getStorage, STORAGE_KEYS } from '../utils/storage'

const MODE_STYLES = {
  basic:    { icon: '🌱', label: '基础模式', color: '#22c55e', bg: '#22c55e18', border: '#22c55e55' },
  beginner: { icon: '📘', label: '入门模式', color: '#3b82f6', bg: '#3b82f618', border: '#3b82f655' },
  exam:     { icon: '🚀', label: '考试模式', color: '#f97316', bg: '#f9731618', border: '#f9731655' },
}

const session = useSessionStore()
const showDialog = ref(false)
const currentMode = ref('')
const modes = ref([])

// 当前模式标签样式
const tagStyle = computed(() => {
  return MODE_STYLES[session.learningMode] || MODE_STYLES.basic
})

// 当前选中的模式信息
const currentModeInfo = computed(() => {
  return modes.value.find(m => m.value === currentMode.value) || {}
})

onMounted(async () => {
  currentMode.value = session.learningMode

  // 拉取模式列表
  try {
    const token = getStorage(STORAGE_KEYS.TOKEN) || session.token
    const headers = token ? { Authorization: `Bearer ${token}` } : {}
    const base = import.meta.env.VITE_API_BASE || '/api'
    const res = await fetch(`${base}/profile/learning-modes`, { headers })
    if (res.ok) {
      const data = await res.json()
      modes.value = data.modes || []
    }
  } catch (e) {
    console.warn('[ModeTag] 获取模式列表失败', e)
  }
})

const doSwitch = async () => {
  if (!currentMode.value || currentMode.value === session.learningMode) return
  try {
    const token = getStorage(STORAGE_KEYS.TOKEN) || session.token
    const headers = { 'Content-Type': 'application/json' }
    if (token) headers['Authorization'] = `Bearer ${token}`
    const base = import.meta.env.VITE_API_BASE || '/api'
    const res = await fetch(`${base}/profile/set-learning-mode`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ learning_mode: currentMode.value }),
    })
    if (!res.ok) {
      console.warn('[ModeTag] 后端保存失败，仅本地生效')
    } else {
      const data = await res.json()
      console.log('[ModeTag] 模式已保存到后端:', data.learning_mode)
    }
    let info = currentModeInfo.value
    session.setLearningMode(currentMode.value, info)
    showDialog.value = false
  } catch (e) {
    console.error('[ModeTag] 切换模式失败', e)
    // 本地兜底：仍允许切换
    session.setLearningMode(currentMode.value, currentModeInfo.value)
    showDialog.value = false
  }
}
</script>

<style lang="scss" scoped>
.mode-tag {
  display: inline-flex;
  align-items: center;
  margin-top: 2px;
}
.mode-tag-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 1px 10px;
  border-radius: 12px;
  border: 1px solid;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
  line-height: 1.6;
  &:hover { filter: brightness(0.95); transform: scale(1.03); }
}
.mode-tag-icon { font-size: 12px; }
.mode-tag-arrow { font-size: 8px; opacity: 0.6; margin-left: 1px; }

/* ── 弹窗 ── */
.mode-dialog-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.4);
  backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  z-index: 2000;
}
.mode-dialog {
  background: var(--bg-color);
  border-radius: 20px;
  width: 520px; max-width: 92vw;
  max-height: 85vh; overflow-y: auto;
  padding: 0 0 28px;
  box-shadow: 0 24px 64px rgba(0,0,0,0.15);
}
.dialog-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 24px 28px 16px;
  border-bottom: 1px solid var(--border-light);
  h3 { margin: 0; font-size: 18px; color: var(--text-main); }
}
.dialog-close {
  width: 32px; height: 32px; border-radius: 50%;
  border: none; background: var(--bg-secondary);
  color: var(--text-secondary); font-size: 15px;
  cursor: pointer; transition: background 0.2s;
  &:hover { background: var(--bg-tertiary); }
}
.dialog-current {
  padding: 16px 28px 8px;
  font-size: 13px;
  color: var(--text-tertiary);
}
.dialog-modes {
  display: flex; flex-direction: column; gap: 10px;
  padding: 12px 28px;
}
.dialog-mode-card {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 18px;
  border: 2px solid var(--border-color);
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  &:hover { border-color: var(--color-primary-light); }
  &.active { }
}
.dm-icon { font-size: 26px; flex-shrink: 0; }
.dm-label { font-size: 15px; font-weight: 700; color: var(--text-main); }
.dm-check {
  margin-left: auto;
  width: 26px; height: 26px; border-radius: 50%;
  background: var(--color-primary); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700;
}
.dm-desc { font-size: 12px; color: var(--text-tertiary); margin: 4px 0 0; width: 100%; }
.dialog-actions {
  display: flex; justify-content: flex-end; gap: 12px;
  padding: 8px 28px 0;
}
.btn-cancel {
  padding: 10px 20px; border-radius: 10px;
  border: 1px solid var(--border-color);
  background: var(--bg-color); color: var(--text-secondary);
  font-size: 14px; font-weight: 600; cursor: pointer;
  transition: all 0.2s;
  &:hover { border-color: var(--color-primary); color: var(--color-primary); }
}
.btn-confirm {
  padding: 10px 22px; border-radius: 10px;
  border: none; color: #fff;
  font-size: 14px; font-weight: 700; cursor: pointer;
  transition: opacity 0.2s;
  &:disabled { opacity: 0.4; cursor: not-allowed; }
  &:hover:not(:disabled) { opacity: 0.88; }
}

/* ── 动画 ── */
.dialog-fade-enter-active, .dialog-fade-leave-active { transition: opacity 0.22s; }
.dialog-fade-enter-from, .dialog-fade-leave-to { opacity: 0; }
</style>
