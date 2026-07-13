<template>
  <div class="mode-choice-page">
    <!-- 顶部标题 -->
    <div class="page-header">
      <h1 class="page-title">选择你的学习模式</h1>
      <p class="page-subtitle">不同模式将为你提供差异化的学习内容和任务难度</p>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- 模式卡片区 -->
    <template v-else>
      <div v-if="modeList.length === 0" class="empty-state">
        <span class="empty-icon">📋</span>
        <h3>暂无可用学习模式</h3>
        <p>请刷新页面或稍后再试</p>
      </div>

      <div v-else class="mode-cards">
        <div
          v-for="mode in modeList"
          :key="mode.value"
          class="mode-card"
          :class="{ active: selectedMode === mode.value, [`mode-${mode.value}`]: true }"
          @click="selectedMode = mode.value"
        >
          <div class="mode-card-icon">{{ mode.icon }}</div>
          <h3 class="mode-card-title">{{ mode.label }}</h3>
          <p class="mode-card-desc">{{ mode.shortDesc }}</p>
          <ul class="mode-card-features">
            <li v-for="f in mode.features" :key="f">{{ f }}</li>
          </ul>
          <div class="mode-card-meta">
            <span>每日任务：{{ mode.dailyTasks }}</span>
            <span>学习时长：{{ mode.studyDuration }}</span>
          </div>
          <div class="mode-card-check" v-if="selectedMode === mode.value">✓</div>
        </div>
      </div>

      <!-- 底部操作 -->
      <div class="page-actions">
        <button class="btn-detail" @click="showDetail = true" :disabled="!selectedMode">
          查看「{{ selectedModeInfo.label || '...' }}」详情
        </button>
        <button
          class="btn-confirm"
          :style="{ background: selectedModeInfo.color || '#3b82f6' }"
          :disabled="!selectedMode || submitting"
          @click="confirmSelect(selectedMode)"
        >
          <span v-if="submitting" class="btn-loading"></span>
          {{ submitting ? '设置中...' : '确认选择，开始学习 →' }}
        </button>
      </div>
    </template>

    <!-- 模式详情弹窗 -->
    <transition name="fade">
      <div class="mode-detail-overlay" v-if="showDetail" @click.self="showDetail = false">
        <div class="mode-detail-dialog">
          <button class="detail-close" @click="showDetail = false">✕</button>
          <div class="detail-header" :style="{ background: currentModeDetail.color + '18', borderColor: currentModeDetail.color }">
            <span class="detail-icon">{{ currentModeDetail.icon }}</span>
            <h2 class="detail-title">{{ currentModeDetail.label }}</h2>
          </div>
          <div class="detail-body">
            <div class="detail-section">
              <h4>适合人群</h4>
              <div class="detail-tags">
                <span v-for="s in currentModeDetail.suitable_for" :key="s" class="detail-tag">{{ s }}</span>
              </div>
            </div>
            <div class="detail-section">
              <h4>特点</h4>
              <ul class="detail-features">
                <li v-for="f in currentModeDetail.features" :key="f">{{ f }}</li>
              </ul>
            </div>
            <div class="detail-section">
              <h4>内容推荐示例</h4>
              <p class="detail-example">「{{ currentModeDetail.example }}」</p>
            </div>
          </div>
          <button class="detail-select-btn" :style="{ background: currentModeDetail.color }" @click="confirmSelect(currentModeDetail.value); showDetail = false">
            选择此模式
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onErrorCaptured } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '../../store/session'
import { getStorage, STORAGE_KEYS } from '../../utils/storage'

const router = useRouter()
const session = useSessionStore()

const selectedMode = ref('')
const showDetail = ref(false)
const loading = ref(true)
const submitting = ref(false)

// 从后端拉取模式列表
const modeList = ref([])

// 全局错误捕获，防止渲染错误导致空白页
onErrorCaptured((err) => {
  console.error('[ModeChoice] 渲染错误:', err)
  return false
})

onMounted(async () => {
  // 设置初始 loading 状态
  loading.value = true
  try {
    const token = getStorage(STORAGE_KEYS.TOKEN) || session.token
    const headers = token ? { Authorization: `Bearer ${token}` } : {}
    const base = import.meta.env.VITE_API_BASE || '/api'
    const res = await fetch(`${base}/profile/learning-modes`, { headers })
    if (res.ok) {
      const data = await res.json()
      modeList.value = data.modes || []
    }
  } catch (e) {
    console.warn('[ModeChoice] 获取模式列表失败，使用默认配置', e)
  } finally {
    loading.value = false
  }

  // 兜底默认配置（API 返回空或失败时使用）
  if (!modeList.value || modeList.value.length === 0) {
    modeList.value = [
      {
        value: 'basic',
        label: '基础模式',
        icon: '🌱',
        color: '#22c55e',
        shortDesc: '轻松入门，激发兴趣',
        features: ['内容简单易懂', '学习压力低', '注重兴趣激发', '每日任务量较少'],
        dailyTasks: '1~3个',
        studyDuration: '10~20分钟',
        suitable_for: ['零基础用户', '初次接触该领域用户', '学习兴趣培养阶段'],
        example: '3分钟看懂什么是AI',
      },
      {
        value: 'beginner',
        label: '入门模式',
        icon: '📚',
        color: '#3b82f6',
        shortDesc: '系统学习，建立体系',
        features: ['内容具有一定深度', '开始建立知识体系', '任务难度中等', '增加实践训练'],
        dailyTasks: '3~5个',
        studyDuration: '20~40分钟',
        suitable_for: ['已具备基础认知', '希望系统学习用户'],
        example: 'DeepSeek如何实现推理能力',
      },
      {
        value: 'exam',
        label: '考试模式',
        icon: '🎯',
        color: '#f97316',
        shortDesc: '高强度冲刺，高效提分',
        features: ['高强度学习', '重点考点覆盖', '高频真题训练', '强化知识点记忆'],
        dailyTasks: '5~8个',
        studyDuration: '40~90分钟',
        suitable_for: ['备考用户', '需要快速提升成绩用户'],
        example: '近三年考试中出现频率最高的知识点',
      },
    ]
  }

  // 如果已设置过模式，预选
  if (session.learningMode) {
    selectedMode.value = session.learningMode
  }
})

const selectedModeInfo = computed(() => {
  return modeList.value.find(m => m.value === selectedMode.value) || {}
})

const currentModeDetail = computed(() => {
  return selectedMode.value
    ? modeList.value.find(m => m.value === selectedMode.value) || {}
    : (modeList.value[0] || {})
})

const confirmSelect = async (modeValue) => {
  if (!modeValue) return
  loading.value = true
  try {
    const token = getStorage(STORAGE_KEYS.TOKEN) || session.token
    const headers = { 'Content-Type': 'application/json' }
    if (token) headers['Authorization'] = `Bearer ${token}`
    const base = import.meta.env.VITE_API_BASE || '/api'
    const res = await fetch(`${base}/profile/set-learning-mode`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ learning_mode: modeValue }),
    })

    let modeInfo = selectedModeInfo.value
    if (!res.ok) {
      console.warn('[ModeChoice] 后端保存失败，仅本地生效')
    } else {
      const data = await res.json()
      modeInfo = data.learning_mode_info || selectedModeInfo.value
    }

    // 保存到 store + localStorage
    session.setLearningMode(modeValue, modeInfo)

    // 跳转首页
    router.push('/app')
  } catch (e) {
    console.error('[ModeChoice] 设置模式失败', e)
    // 本地兜底：仍允许进入
    session.setLearningMode(modeValue, selectedModeInfo.value)
    router.push('/app')
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
/* ═════════════════════════════
   MODE CHOICE PAGE
   ═════════════════════════════ */
.mode-choice-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 48px 24px 64px;
  min-height: 100vh;
}

.page-header {
  text-align: center;
  margin-bottom: 48px;
}
.page-title {
  font-size: 32px;
  font-weight: 800;
  color: var(--text-main);
  margin: 0 0 12px;
}
.page-subtitle {
  font-size: 16px;
  color: var(--text-tertiary);
  margin: 0;
}

/* ── 卡片网格 ── */
.mode-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 28px;
  margin-bottom: 48px;
}
@media (max-width: 900px) {
  .mode-cards { grid-template-columns: 1fr; max-width: 420px; margin: 0 auto 48px; }
}

.mode-card {
  position: relative;
  background: var(--bg-color);
  border: 2px solid var(--border-color);
  border-radius: 20px;
  padding: 36px 28px 32px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: center;

  &:hover {
    transform: translateY(-6px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.1);
  }

  &.active {
    border-width: 2.5px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.12);
  }

  &.mode-basic.active  { border-color: #22c55e; box-shadow: 0 8px 30px rgba(34,197,94,0.18); }
  &.mode-beginner.active { border-color: #3b82f6; box-shadow: 0 8px 30px rgba(59,130,246,0.18); }
  &.mode-exam.active    { border-color: #f97316; box-shadow: 0 8px 30px rgba(249,115,22,0.18); }
}

.mode-card-icon {
  font-size: 48px;
  margin-bottom: 16px;
}
.mode-card-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0 0 8px;
}
.mode-card-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 20px;
}
.mode-card-features {
  list-style: none;
  padding: 0;
  margin: 0 0 20px;
  text-align: left;
  li {
    font-size: 13px;
    color: var(--text-secondary);
    padding: 5px 0;
    padding-left: 20px;
    position: relative;
    &::before {
      content: '✓';
      position: absolute;
      left: 0;
      color: var(--color-primary);
      font-weight: 700;
    }
  }
}
.mode-card-meta {
  display: flex;
  justify-content: center;
  gap: 16px;
  font-size: 12px;
  color: var(--text-tertiary);
  padding-top: 16px;
  border-top: 1px solid var(--border-light);
}

.mode-card-check {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
}

/* ── 详情弹窗 ── */
.mode-detail-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.45);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.mode-detail-dialog {
  background: var(--bg-color);
  border-radius: 20px;
  width: 560px;
  max-width: 92vw;
  max-height: 85vh;
  overflow-y: auto;
  padding: 0 0 32px;
  position: relative;
  box-shadow: 0 24px 64px rgba(0,0,0,0.18);
}
.detail-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: rgba(0,0,0,0.08);
  color: var(--text-secondary);
  font-size: 18px;
  cursor: pointer;
  z-index: 1;
  transition: background 0.2s;
  &:hover { background: rgba(0,0,0,0.15); }
}
.detail-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 32px 32px 24px;
  border-bottom: 2px solid transparent;
  border-radius: 20px 20px 0 0;
}
.detail-icon { font-size: 40px; }
.detail-title { font-size: 26px; font-weight: 800; color: var(--text-main); margin: 0; }

.detail-body { padding: 24px 32px; }
.detail-section {
  margin-bottom: 24px;
  h4 { font-size: 14px; font-weight: 700; color: var(--text-main); margin: 0 0 10px; }
}
.detail-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.detail-tag {
  font-size: 12px;
  padding: 5px 14px;
  border-radius: 20px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-weight: 600;
}
.detail-features {
  list-style: none; padding: 0; margin: 0;
  li { font-size: 14px; color: var(--text-secondary); padding: 4px 0; padding-left: 18px; position: relative;
    &::before { content: '•'; position: absolute; left: 0; color: var(--color-primary); font-weight: 700; }
  }
}
.detail-example {
  font-size: 14px;
  color: var(--text-tertiary);
  background: var(--bg-secondary);
  padding: 12px 16px;
  border-radius: 10px;
  margin: 0;
  font-style: italic;
}

.detail-select-btn {
  display: block;
  margin: 0 32px;
  padding: 14px;
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.2s;
  &:hover { opacity: 0.88; }
}

/* ── 底部操作 ── */
.page-actions {
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}
.btn-detail {
  padding: 14px 28px;
  border: 1.5px solid var(--border-color);
  border-radius: 12px;
  background: var(--bg-color);
  color: var(--text-secondary);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  &:hover:not(:disabled) { border-color: var(--color-primary); color: var(--color-primary); }
  &:disabled { opacity: 0.4; cursor: not-allowed; }
}
.btn-confirm {
  padding: 14px 36px;
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.2s;
  &:hover:not(:disabled) { opacity: 0.88; }
  &:disabled { opacity: 0.4; cursor: not-allowed; }
}

/* ── 加载状态 ── */
.loading-state {
  text-align: center;
  padding: 80px 0;
  color: var(--text-secondary);
}
.loading-spinner {
  width: 40px; height: 40px;
  border: 3px solid var(--border-color);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── 空状态 ── */
.empty-state {
  text-align: center;
  padding: 80px 0;
  .empty-icon { font-size: 48px; }
  h3 { margin: 12px 0 8px; font-size: 20px; }
  p { color: var(--text-tertiary); font-size: 14px; }
}

.btn-loading {
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: btn-spin 0.6s linear infinite;
  display: inline-block;
  vertical-align: middle;
  margin-right: 6px;
}
@keyframes btn-spin { to { transform: rotate(360deg); } }

/* ── 动画 ── */
.fade-enter-active, .fade-leave-active { transition: opacity 0.25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
