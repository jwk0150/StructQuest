<template>
  <div class="onboarding-container">
    <transition name="fade" mode="out-in">
      <!-- ═══════════ Step 1: 欢迎页 ═══════════ -->
      <div v-if="step === 'intro'" key="intro" class="intro-step">
        <div class="logo">◈ StructQuest</div>
        <h1>个性化学习之旅</h1>
        <p class="intro-desc">我们将通过 <strong>3 个简单步骤</strong>（约 2~3 分钟），全面了解你的学习背景和当前水平，为你生成 <strong>AI 初始学习画像</strong>。</p>

        <div class="step-preview-list">
          <div class="step-preview">
            <span class="sp-num">1</span>
            <div>
              <strong>学习需求问卷</strong>
              <p>了解你的学习目的和偏好</p>
            </div>
          </div>
          <div class="step-preview">
            <span class="sp-num">2</span>
            <div>
              <strong>能力诊断测试</strong>
              <p>24 道题评估你的知识掌握度</p>
            </div>
          </div>
          <div class="step-preview">
            <span class="sp-num">3</span>
            <div>
              <strong>AI 生成画像</strong>
              <p>综合数据生成初始学习画像</p>
            </div>
          </div>
        </div>

        <el-button type="primary" size="large" class="start-btn" @click="step = 'questionnaire'">
          开始 <el-icon class="el-icon--right"><Right /></el-icon>
        </el-button>
      </div>

      <!-- ═══════════ Step 2: 学习目标问卷 ═══════════ -->
      <div v-else-if="step === 'questionnaire'" key="questionnaire" class="questionnaire-step">
        <div class="step-header">
          <span class="step-badge">Step 1/3</span>
          <h2>学习需求问卷</h2>
          <p>了解你的学习目的，帮你匹配最合适的学习资源</p>
        </div>

        <el-card class="q-card" shadow="never">
          <!-- Q1: 学习目的（单选） -->
          <div class="q-section">
            <h3 class="q-title">① 你学习数据结构的主要目的是？</h3>
            <div class="q-options">
              <div
                v-for="opt in purposeOptions" :key="opt.value"
                class="q-option" :class="{ selected: questionnaire.learning_purpose === opt.value }"
                @click="questionnaire.learning_purpose = opt.value"
              >
                <span class="q-opt-icon">{{ opt.icon }}</span>
                <span class="q-opt-text">{{ opt.label }}</span>
                <span class="q-opt-desc">{{ opt.desc }}</span>
              </div>
            </div>
          </div>

          <!-- Q2: 学习方式偏好（多选） -->
          <div class="q-section">
            <h3 class="q-title">② 你更喜欢哪种学习方式？（可多选）</h3>
            <div class="q-options">
              <div
                v-for="opt in styleOptions" :key="opt.value"
                class="q-option q-option--multi"
                :class="{ selected: questionnaire.preferred_styles.includes(opt.value) }"
                @click="toggleStyle(opt.value)"
              >
                <span class="q-opt-icon">{{ opt.icon }}</span>
                <span class="q-opt-text">{{ opt.label }}</span>
              </div>
            </div>
          </div>

          <!-- Q3: 每天学习时间 -->
          <div class="q-section">
            <h3 class="q-title">③ 每天可以投入多少时间学习？</h3>
            <div class="q-options q-options--time">
              <div
                v-for="opt in timeOptions" :key="opt.value"
                class="q-option q-option--time"
                :class="{ selected: questionnaire.daily_study_time === opt.value }"
                @click="questionnaire.daily_study_time = opt.value"
              >
                <span class="q-opt-time">{{ opt.label }}</span>
                <span class="q-opt-time-desc">{{ opt.desc }}</span>
              </div>
            </div>
          </div>
        </el-card>

        <div class="step-actions">
          <el-button @click="step = 'intro'">返回</el-button>
          <el-button
            type="primary" size="large"
            :disabled="!canProceedToDiagnostic"
            :loading="submittingQuestionnaire"
            @click="submitQuestionnaire"
          >
            下一步：能力诊断测试 →
          </el-button>
        </div>
      </div>

      <!-- ═══════════ Step 3: 诊断测试 ═══════════ -->
      <div v-else-if="step === 'diagnostic'" key="diagnostic" class="diagnostic-step">
        <div class="diag-top-bar">
          <span class="step-badge">Step 2/3</span>
          <span class="diag-module-tag">{{ diagnostic.currentModuleName.value }}</span>
          <span class="diag-progress-text">{{ diagnostic.currentGlobalIndex.value + 1 }} / {{ diagnostic.totalQuestions.value }}</span>
        </div>

        <el-progress
          :percentage="diagnostic.progressPercent.value"
          :show-text="false" :stroke-width="6"
          color="#10a37f"
        />

        <transition name="slide-up" mode="out-in">
          <div v-if="diagnostic.currentQuestion.value" :key="diagnostic.currentQuestion.value.id" class="diag-question-area">
            <el-card class="diag-q-card" shadow="never">
              <div class="diag-q-header">
                <el-tag size="small" type="info">{{ diagnostic.currentModuleName.value }}</el-tag>
                <span class="diag-q-diff" v-if="diagnostic.currentQuestion.value.difficulty">
                  难度: {{ '★'.repeat(diagnostic.currentQuestion.value.difficulty) }}
                </span>
              </div>
              <h3 class="diag-q-text">{{ diagnostic.currentQuestion.value.question }}</h3>
              <div class="diag-q-options">
                <div
                  v-for="(opt, idx) in diagnostic.currentQuestion.value.options"
                  :key="idx"
                  class="diag-option"
                  :class="{ selected: getSelectedAnswer(diagnostic.currentQuestion.value.id) === idx }"
                  @click="diagnostic.selectAnswer(idx)"
                >
                  <span class="diag-opt-letter">{{ String.fromCharCode(65 + idx) }}</span>
                  <span class="diag-opt-text">{{ opt }}</span>
                </div>
              </div>

              <div class="diag-q-actions">
                <el-button text type="info" @click="diagnostic.goPrev()" :disabled="diagnostic.currentGlobalIndex.value === 0">
                  ← 上一题
                </el-button>
                <el-button text type="warning" @click="diagnostic.skipQuestion()" :disabled="!diagnostic.canSkip.value">
                  跳过 ⏭
                </el-button>
              </div>
            </el-card>
          </div>

          <!-- 加载中 -->
          <div v-else-if="diagnostic.loading.value" class="diag-loading">
            <div class="loading-spinner"></div>
            <p>正在加载诊断题目...</p>
          </div>
        </transition>
      </div>

      <!-- ═══════════ Step 4: AI 分析结果 ═══════════ -->
      <div v-else-if="step === 'result'" key="result" class="result-step">
        <el-card class="result-card" shadow="never">
          <div class="result-header">
            <el-tag type="success" effect="dark" round>画像生成完成</el-tag>
            <h1>你的初始学习画像</h1>
          </div>

          <!-- AI 画像 -->
          <div v-if="aiProfile.ability_level" class="ai-profile-box">
            <div class="profile-grid">
              <div class="profile-cell">
                <span class="cell-label">能力等级</span>
                <span class="cell-value primary">{{ levelLabel(aiProfile.ability_level) }}</span>
              </div>
              <div class="profile-cell">
                <span class="cell-label">学习风格</span>
                <span class="cell-value success">{{ styleLabel(aiProfile.learning_style) }}</span>
              </div>
              <div class="profile-cell">
                <span class="cell-label">学习节奏</span>
                <span class="cell-value warning">{{ aiProfile.learning_rhythm || aiProfile.pace || '适中' }}</span>
              </div>
              <div class="profile-cell">
                <span class="cell-label">信心指数</span>
                <span class="cell-value info">{{ aiProfile.confidence_score || '?' }}/100</span>
              </div>
            </div>

            <!-- 知识掌握度 -->
            <div v-if="Object.keys(knowledgeMastery).length > 0" class="mastery-section">
              <h4>📊 知识掌握度</h4>
              <div class="mastery-bars">
                <div v-for="(score, topic) in knowledgeMastery" :key="topic" class="mastery-bar-item">
                  <div class="mastery-bar-label">
                    <span>{{ topic }}</span>
                    <span :class="masteryClass(score)">{{ score }}%</span>
                  </div>
                  <div class="mastery-bar-track">
                    <div class="mastery-bar-fill" :class="masteryBarClass(score)" :style="{ width: score + '%' }"></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 资源偏好 -->
            <div v-if="aiProfile.resource_preferences" class="pref-section">
              <h4>🎯 初始资源偏好</h4>
              <div class="pref-tags">
                <el-tag
                  v-for="(score, type) in topPreferences" :key="type"
                  :type="score > 70 ? 'success' : score > 40 ? 'warning' : 'info'"
                  effect="plain" round
                >
                  {{ type }}: {{ score }}%
                </el-tag>
              </div>
            </div>

            <div v-if="aiProfile.weakness_summary" class="weakness-hint">
              <span class="hint-icon">⚡</span>
              短板聚焦：<strong>{{ aiProfile.weakness_summary }}</strong>
            </div>

            <div v-if="aiProfile.daily_strategy" class="strategy-box">
              <span class="hint-icon">💡</span>
              {{ aiProfile.daily_strategy }}
            </div>
          </div>

          <!-- 学习路径预览（Orchestrator 管线生成） -->
          <div v-if="orchestratedPath.length > 0" class="path-preview">
            <h4>📋 AI 为你规划的学习路径（{{ orchestratedPath.length }} 步）</h4>
            <div class="path-steps">
              <div v-for="(step, idx) in orchestratedPath.slice(0, 5)" :key="idx" class="path-step-item">
                <span class="step-num">{{ idx + 1 }}</span>
                <div class="step-body">
                  <span class="step-topic">{{ step.topic || step.title || '步骤 ' + (idx+1) }}</span>
                  <span class="step-diff" :class="'diff-' + (step.difficulty || 'medium')">
                    {{ step.difficulty === 'hard' ? '困难' : step.difficulty === 'easy' ? '简单' : '中等' }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- 首次资源推荐 -->
          <div v-if="orchestratedRecommendations.length > 0" class="first-recs">
            <h4>🎯 为你推荐的首批资源</h4>
            <div class="rec-items">
              <div v-for="rec in orchestratedRecommendations.slice(0, 4)" :key="rec.resource_id" class="rec-item">
                <span class="rec-type-tag">{{ rec.type || rec.resource_type }}</span>
                <span class="rec-title">{{ rec.title }}</span>
                <span v-if="rec.reason" class="rec-reason">{{ rec.reason }}</span>
              </div>
            </div>
          </div>

          <!-- AI 失败时的降级显示 -->
          <div v-else-if="aiError" class="ai-error-box">
            <p>AI 画像生成遇到问题，但已根据你的测试结果生成了基础画像。</p>
          </div>

          <div class="result-actions">
            <el-button type="primary" size="large" @click="finishOnboarding" :loading="isNavigating">
              进入我的学习空间
            </el-button>
          </div>
        </el-card>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Right } from '@element-plus/icons-vue'
import { useSessionStore } from '../../store/session'
import { useDiagnostic } from '../../composables/useDiagnostic'
import { setStorage, STORAGE_KEYS } from '../../utils/storage'
import onboardingApi from '../../api/onboarding'
import { ElMessage } from 'element-plus'

const router = useRouter()
const sessionStore = useSessionStore()
const diagnostic = useDiagnostic()

// ── 步骤状态 ──
const step = ref('intro')
const submittingQuestionnaire = ref(false)
const submittingDiagnostic = ref(false)
const generatingProfile = ref(false)
const isNavigating = ref(false)
const aiError = ref(false)
const aiProfile = ref({})
const orchestratedPath = ref([])       // Orchestrator 返回的学习路径
const orchestratedResources = ref([])  // Orchestrator 返回的资源
const orchestratedRecommendations = ref([])  // Orchestrator 返回的推荐

// ── Step 2: 问卷数据 ──
const questionnaire = reactive({
  learning_purpose: '',
  preferred_styles: [],
  daily_study_time: '',
})

const purposeOptions = [
  { value: 'course_preview', label: '课程预习', icon: '📖', desc: '提前了解课程内容' },
  { value: 'daily_study', label: '日常学习', icon: '📚', desc: '配合课堂进度系统学习' },
  { value: 'final_exam', label: '期末考试', icon: '📝', desc: '重点复习、冲刺高分' },
  { value: 'postgraduate', label: '考研', icon: '🎓', desc: '系统备考研究生入学考试' },
  { value: 'project_practice', label: '项目实践', icon: '💻', desc: '动手做项目、积累代码经验' },
  { value: 'algorithm_contest', label: '算法竞赛', icon: '🏆', desc: 'LeetCode/ACM 竞赛训练' },
]

const styleOptions = [
  { value: 'video', label: '视频讲解', icon: '🎬' },
  { value: 'diagram', label: '图解', icon: '📊' },
  { value: 'reading', label: '阅读讲义', icon: '📄' },
  { value: 'coding', label: '动手写代码', icon: '⌨️' },
  { value: 'practice', label: '刷题', icon: '✏️' },
]

const timeOptions = [
  { value: '15min', label: '15分钟', desc: '碎片化学习' },
  { value: '30min', label: '30分钟', desc: '每日一练' },
  { value: '1hour', label: '1小时', desc: '稳步推进' },
  { value: '2hours', label: '2小时以上', desc: '深度学习' },
]

const canProceedToDiagnostic = computed(() => {
  return questionnaire.learning_purpose
    && questionnaire.preferred_styles.length > 0
    && questionnaire.daily_study_time
})

function toggleStyle(value) {
  const idx = questionnaire.preferred_styles.indexOf(value)
  if (idx >= 0) {
    questionnaire.preferred_styles.splice(idx, 1)
  } else {
    questionnaire.preferred_styles.push(value)
  }
}

// ── Step 2 → Step 3 ──
async function submitQuestionnaire() {
  if (!canProceedToDiagnostic.value) return
  submittingQuestionnaire.value = true
  try {
    // 后端保存问卷
    await onboardingApi.submitQuestionnaire({
      learning_purpose: questionnaire.learning_purpose,
      preferred_styles: questionnaire.preferred_styles,
      daily_study_time: questionnaire.daily_study_time,
    }).catch(err => console.warn('[Onboarding] 问卷保存失败（非致命）:', err))

    // 加载诊断题目
    await diagnostic.loadQuestions(onboardingApi)
    step.value = 'diagnostic'
    diagnostic.startTest()
  } catch (err) {
    ElMessage.error('加载题目失败：' + (err.message || '请重试'))
  } finally {
    submittingQuestionnaire.value = false
  }
}

// ── 监听诊断测试完成 ──
const diagnosticWatcher = ref(null)
function watchDiagnosticFinish() {
  diagnosticWatcher.value = setInterval(() => {
    if (diagnostic.finished.value) {
      clearInterval(diagnosticWatcher.value)
      submitDiagnosticAndGenerateProfile()
    }
  }, 500)
}

// 开始监听
const originalStartTest = diagnostic.startTest
diagnostic.startTest = function () {
  originalStartTest.call(diagnostic)
  watchDiagnosticFinish()
}

// ── Step 3 → Step 4: 提交诊断结果并生成画像 ──
async function submitDiagnosticAndGenerateProfile() {
  submittingDiagnostic.value = true
  step.value = 'result'
  generatingProfile.value = true
  aiError.value = false

  try {
    // 1. 提交诊断结果
    const diagResult = await diagnostic.submitDiagnostic(onboardingApi)
    console.log('[Onboarding] 诊断结果:', diagResult)

    // 2. 调用 AI 生成画像（含 Orchestrator 管线）
    const profileResult = await onboardingApi.generateProfile()
    aiProfile.value = profileResult.profile || {}
    orchestratedPath.value = profileResult.learning_path || []
    orchestratedResources.value = profileResult.resources || []
    orchestratedRecommendations.value = profileResult.recommendation?.items || []
    console.log('[Onboarding] AI 画像:', aiProfile.value, '路径:', orchestratedPath.value.length, '步')
  } catch (err) {
    console.error('[Onboarding] 画像生成失败:', err)
    aiError.value = true
    // 即使失败也展示已有的诊断数据
    aiProfile.value = {
      ability_level: 'beginner',
      learning_style: 'reading',
      knowledge_mastery: {},
      confidence_score: 50,
      summary: '画像生成遇到问题，你可以在学习过程中逐步完善。',
    }
  } finally {
    submittingDiagnostic.value = false
    generatingProfile.value = false
  }
}

// ── 获取当前题目的已选答案 ──
function getSelectedAnswer(questionId) {
  const a = diagnostic.answers.value[questionId]
  if (!a || a.userAnswer === -1) return -1
  return a.userAnswer
}

// ── 知识掌握度 ──
const knowledgeMastery = computed(() => {
  return aiProfile.value.knowledge_mastery || {}
})

function masteryClass(score) {
  if (score >= 80) return 'mastery-high'
  if (score >= 50) return 'mastery-mid'
  return 'mastery-low'
}
function masteryBarClass(score) {
  if (score >= 80) return 'bar-high'
  if (score >= 50) return 'bar-mid'
  return 'bar-low'
}

// ── 资源偏好 Top3 ──
const topPreferences = computed(() => {
  const prefs = aiProfile.value.resource_preferences || {}
  const sorted = Object.entries(prefs).sort((a, b) => b[1] - a[1])
  return Object.fromEntries(sorted.slice(0, 4))
})

// ── 标签映射 ──
function levelLabel(level) {
  const map = { beginner: '初学者', intermediate: '中等', advanced: '进阶', expert: '专家' }
  return map[level] || level
}
function styleLabel(style) {
  const map = { visual: '视觉型', auditory: '听觉型', reading: '阅读型', hands_on: '实践型' }
  return map[style] || style
}

// ── 完成引导 ──
async function finishOnboarding() {
  isNavigating.value = true
  try {
    // 构建完整画像数据
    const profileData = {
      ...aiProfile.value,
      questionnaire: { ...questionnaire },
      generated_at: new Date().toISOString(),
    }

    // 保存到本地 store
    sessionStore.updateProfile(profileData)
    setStorage(STORAGE_KEYS.PROFILE, profileData)
    setStorage(STORAGE_KEYS.ONBOARDING_DONE, true)

    // 保存到后端
    try {
      const { profileApi } = await import('../../api/profile')
      await profileApi.save(profileData)
    } catch (err) {
      console.warn('[Onboarding] 后端保存画像失败（已用本地备份兜底）:', err.message || err)
    }

    router.push('/app')
  } catch (e) {
    isNavigating.value = false
    ElMessage.error('跳转失败，请手动刷新页面')
  }
}
</script>

<style lang="scss" scoped>
.onboarding-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-secondary);
  padding: 20px;
}

/* ═══════════ Step 1: 欢迎页 ═══════════ */
.intro-step {
  text-align: center;
  max-width: 560px;
  .logo { font-size: 32px; font-weight: 800; color: var(--color-primary); margin-bottom: 20px; }
  h1 { font-size: 36px; margin-bottom: 16px; }
  .intro-desc { font-size: 16px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 32px; }
}

.step-preview-list { display: flex; flex-direction: column; gap: 12px; margin-bottom: 36px; }
.step-preview {
  display: flex; align-items: center; gap: 14px; text-align: left;
  padding: 14px 18px; background: var(--bg-color); border-radius: 12px;
  border: 1px solid var(--border-color);
  .sp-num {
    width: 32px; height: 32px; border-radius: 50%;
    background: var(--color-primary); color: #fff;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 15px; flex-shrink: 0;
  }
  strong { display: block; font-size: 15px; margin-bottom: 2px; }
  p { font-size: 13px; color: var(--text-tertiary); margin: 0; }
}

.start-btn { height: 52px; padding: 0 40px; font-size: 17px; border-radius: 14px; }

/* ═══════════ Step 2: 问卷 ═══════════ */
.questionnaire-step { width: 100%; max-width: 680px; }
.step-header {
  text-align: center; margin-bottom: 28px;
  h2 { font-size: 26px; margin: 8px 0 4px; }
  p { color: var(--text-secondary); font-size: 14px; }
}
.step-badge {
  display: inline-block; padding: 4px 14px; background: var(--color-primary);
  color: #fff; border-radius: 20px; font-size: 12px; font-weight: 600;
}

.q-card { border-radius: 18px; padding: 28px; border: none; box-shadow: var(--shadow-md) !important; margin-bottom: 24px; }
.q-section { margin-bottom: 28px; &:last-child { margin-bottom: 0; } }
.q-title { font-size: 16px; margin-bottom: 14px; color: var(--text-main); }
.q-options { display: flex; flex-wrap: wrap; gap: 10px; }

.q-option {
  padding: 14px 16px; background: var(--bg-secondary);
  border: 2px solid var(--border-color); border-radius: 12px;
  cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 10px;
  flex: 1; min-width: 160px;
  &:hover { border-color: var(--color-primary); transform: translateY(-1px); }
  &.selected { border-color: var(--color-primary); background: rgba(16,163,127,0.06); }
  .q-opt-icon { font-size: 20px; flex-shrink: 0; }
  .q-opt-text { font-weight: 600; font-size: 14px; white-space: nowrap; }
  .q-opt-desc { font-size: 12px; color: var(--text-tertiary); margin-left: auto; }
}

.q-option--multi { flex: 0 0 auto; min-width: auto; }
.q-option--time { flex-direction: column; align-items: center; gap: 4px; min-width: 100px;
  .q-opt-time { font-size: 18px; font-weight: 700; }
  .q-opt-time-desc { font-size: 12px; color: var(--text-tertiary); }
}

.step-actions { display: flex; justify-content: space-between; align-items: center; }

/* ═══════════ Step 3: 诊断测试 ═══════════ */
.diagnostic-step { width: 100%; max-width: 700px; }
.diag-top-bar {
  display: flex; align-items: center; gap: 14px; margin-bottom: 16px;
  .diag-module-tag {
    padding: 3px 10px; background: rgba(16,163,127,0.1);
    color: var(--color-primary); border-radius: 6px; font-size: 13px; font-weight: 600;
  }
  .diag-progress-text { margin-left: auto; font-size: 14px; color: var(--text-secondary); font-weight: 600; }
}

.diag-question-area { margin-top: 24px; }
.diag-q-card { border-radius: 18px; padding: 28px; border: none; box-shadow: var(--shadow-md) !important; }
.diag-q-header { display: flex; align-items: center; gap: 10px; margin-bottom: 20px; }
.diag-q-diff { font-size: 12px; color: #f59e0b; }
.diag-q-text { font-size: 20px; line-height: 1.5; margin-bottom: 28px; }

.diag-q-options { display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px; }
.diag-option {
  display: flex; align-items: center; gap: 14px;
  padding: 16px 18px; background: var(--bg-secondary);
  border: 2px solid var(--border-color); border-radius: 12px;
  cursor: pointer; transition: all 0.2s;
  &:hover { border-color: var(--color-primary); }
  &.selected { border-color: var(--color-primary); background: rgba(16,163,127,0.06); }
}
.diag-opt-letter {
  width: 30px; height: 30px; border-radius: 8px;
  background: var(--bg-color); border: 1px solid var(--border-color);
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 14px; flex-shrink: 0;
  .selected & { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }
}
.diag-opt-text { font-size: 15px; }

.diag-q-actions { display: flex; justify-content: space-between; padding-top: 8px; border-top: 1px solid var(--border-light); }

.diag-loading { text-align: center; padding: 60px 0; }
.loading-spinner {
  width: 36px; height: 36px; border: 3px solid var(--border-color);
  border-top-color: var(--color-primary); border-radius: 50%;
  animation: spin 0.8s linear infinite; margin: 0 auto 16px;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ═══════════ Step 4: 结果 ═══════════ */
.result-step { width: 100%; max-width: 680px; }
.result-card {
  border-radius: 22px; padding: 36px; text-align: center;
  border: none; box-shadow: var(--shadow-lg) !important;
  .result-header {
    margin-bottom: 24px;
    h1 { font-size: 30px; margin-top: 12px; }
  }
}

.ai-profile-box {
  text-align: left;
  .profile-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }
  .profile-cell {
    background: var(--bg-secondary); border-radius: 12px; padding: 14px 10px; text-align: center;
    .cell-label { display: block; font-size: 11px; color: var(--text-tertiary); margin-bottom: 6px; text-transform: uppercase; }
    .cell-value { display: block; font-size: 15px; font-weight: 700;
      &.primary { color: var(--color-primary); }
      &.success { color: #10a37f; }
      &.warning { color: #E6A23C; }
      &.info { color: #409EFF; }
    }
  }
}

/* 知识掌握度条 */
.mastery-section {
  margin-bottom: 20px;
  h4 { font-size: 14px; margin: 0 0 12px; }
}
.mastery-bars { display: flex; flex-direction: column; gap: 10px; }
.mastery-bar-item { }
.mastery-bar-label {
  display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;
  .mastery-high { color: #22c55e; font-weight: 700; }
  .mastery-mid { color: #f59e0b; font-weight: 700; }
  .mastery-low { color: #ef4444; font-weight: 700; }
}
.mastery-bar-track { height: 8px; border-radius: 4px; background: var(--border-color); overflow: hidden; }
.mastery-bar-fill { height: 100%; border-radius: 4px; transition: width 0.8s ease;
  &.bar-high { background: linear-gradient(90deg, #22c55e, #4ade80); }
  &.bar-mid { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
  &.bar-low { background: linear-gradient(90deg, #ef4444, #f87171); }
}

.pref-section {
  margin-bottom: 16px;
  h4 { font-size: 14px; margin: 0 0 10px; }
}
.pref-tags { display: flex; gap: 8px; flex-wrap: wrap; }

.weakness-hint {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 16px; background: rgba(230,162,60,0.08);
  border-radius: 10px; font-size: 13px; color: var(--text-secondary); margin-bottom: 12px;
  .hint-icon { font-size: 16px; }
  strong { color: #E6A23C; }
}

.strategy-box {
  padding: 12px 16px; background: rgba(16,163,127,0.06);
  border-radius: 10px; font-size: 13px; color: var(--text-secondary);
  display: flex; align-items: flex-start; gap: 8px;
}

.ai-error-box {
  padding: 24px; background: rgba(239,68,68,0.06); border-radius: 12px;
  margin-bottom: 20px; font-size: 14px; color: var(--text-secondary);
}

.result-actions { display: flex; justify-content: center; margin-top: 28px; }

/* ── 学习路径预览 ── */
.path-preview {
  text-align: left; margin-bottom: 20px;
  h4 { font-size: 14px; margin: 0 0 12px; }
}
.path-steps { display: flex; flex-direction: column; gap: 6px; }
.path-step-item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 12px; background: var(--bg-secondary); border-radius: 8px;
  .step-num {
    width: 24px; height: 24px; border-radius: 50%;
    background: var(--color-primary); color: #fff;
    font-size: 12px; font-weight: 700;
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  }
  .step-body { flex: 1; display: flex; justify-content: space-between; align-items: center; }
  .step-topic { font-size: 13px; font-weight: 500; }
  .step-diff {
    font-size: 11px; padding: 2px 8px; border-radius: 10px;
    &.diff-easy { background: #dcfce7; color: #16a34a; }
    &.diff-medium { background: #fef3c7; color: #d97706; }
    &.diff-hard { background: #fee2e2; color: #dc2626; }
  }
}

/* ── 首批推荐 ── */
.first-recs {
  text-align: left; margin-bottom: 20px;
  h4 { font-size: 14px; margin: 0 0 10px; }
}
.rec-items { display: flex; flex-direction: column; gap: 8px; }
.rec-item {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px; background: var(--bg-secondary); border-radius: 8px;
}
.rec-type-tag {
  padding: 2px 8px; background: rgba(16,163,127,0.1);
  color: var(--color-primary); border-radius: 4px;
  font-size: 11px; font-weight: 600; white-space: nowrap;
}
.rec-title { font-size: 13px; font-weight: 500; flex: 1; }
.rec-reason { font-size: 11px; color: var(--text-tertiary); white-space: nowrap; }

/* Transitions */
.fade-enter-active, .fade-leave-active { transition: opacity 0.4s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-up-enter-active, .slide-up-leave-active { transition: all 0.35s ease-out; }
.slide-up-enter-from { transform: translateY(24px); opacity: 0; }
.slide-up-leave-to { transform: translateY(-24px); opacity: 0; }
</style>
