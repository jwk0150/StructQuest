<template>
  <div class="exam-container">
    <!-- 加载中 -->
    <div v-if="loading" class="exam-loading">
      <div class="loading-spinner"></div>
      <p>正在加载章节测试...</p>
    </div>

    <!-- 考试页面 -->
    <div v-else-if="!submitted" class="exam-content">
      <div class="exam-header">
        <div class="exam-back">
          <router-link :to="'/map'" class="back-link">&larr; 返回知识图谱</router-link>
        </div>
        <h1>章节测试：{{ nodeTitle }}</h1>
        <p class="exam-desc">共 {{ questions.length }} 题，每题一个正确答案</p>
      </div>

      <!-- 错误提示 -->
      <div v-if="errorMsg" class="exam-error">
        <span class="error-icon">⚠️</span>
        <span>{{ errorMsg }}</span>
      </div>

      <div class="exam-body">
        <div
          v-for="(q, idx) in questions"
          :key="q.id"
          class="question-card"
          :class="{ 'has-answer': answers[q.id] !== undefined }"
        >
          <div class="question-num">第 {{ idx + 1 }} 题</div>
          <h3 class="question-text">{{ q.question }}</h3>
          <div class="option-list">
            <div
              v-for="(opt, oi) in q.options"
              :key="oi"
              class="option-item"
              :class="{ selected: answers[q.id] === oi }"
              @click="selectAnswer(q.id, oi)"
            >
              <span class="option-radio">{{ answers[q.id] === oi ? '●' : '○' }}</span>
              <span class="option-text">{{ String.fromCharCode(65 + oi) }}. {{ opt }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="exam-footer">
        <div class="progress-info">已完成 {{ answeredCount }} / {{ questions.length }} 题</div>
        <button
          class="submit-btn"
          :disabled="answeredCount < questions.length || submitting"
          @click="handleSubmit"
        >
          <span v-if="submitting" class="btn-loading"></span>
          {{ submitting ? '提交中...' : '提交测试' }}
        </button>
      </div>
    </div>

    <!-- 结果页面 -->
    <div v-else class="exam-result">
      <div class="result-card" :class="{ passed: result.passed, failed: !result.passed }">
        <div class="result-icon">{{ result.passed ? '🎉' : '📚' }}</div>
        <h2>{{ result.passed ? '恭喜通过！' : '继续加油！' }}</h2>
        <div class="score-circle">
          <svg width="120" height="120" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="54" fill="none" stroke="#e8e8e8" stroke-width="8"/>
            <circle cx="60" cy="60" r="54" fill="none" :stroke="result.passed ? '#22c55e' : '#f97316'" stroke-width="8"
              stroke-dasharray="339.292" :stroke-dashoffset="339.292 * (1 - result.score / 100)" stroke-linecap="round"
              transform="rotate(-90 60 60)"/>
            <text x="60" y="60" text-anchor="middle" dominant-baseline="central" font-size="28" font-weight="700"
              :fill="result.passed ? '#22c55e' : '#f97316'">{{ result.score }}分</text>
          </svg>
        </div>
        <p class="result-detail">正确 {{ result.correct_count }}/{{ result.total }} 题</p>
        <p v-if="result.chapter_completed" class="chapter-done">✅ 章节已完结</p>
        <p v-else class="chapter-hint">继续学习章节内容并通过测试以完结此章</p>

        <!-- 答题详情 -->
        <div class="answer-details">
          <div v-for="(d, idx) in result.details" :key="d.id" class="detail-item" :class="{ correct: d.is_correct, wrong: !d.is_correct }">
            <div class="detail-q">{{ idx + 1 }}. {{ d.question }}</div>
            <div class="detail-result">{{ d.is_correct ? '✅ 正确' : '❌ 错误' }}</div>
            <div v-if="!d.is_correct" class="detail-explanation">解析：{{ d.explanation }}</div>
          </div>
        </div>

        <div class="result-actions">
          <router-link to="/map" class="btn-back">返回知识图谱</router-link>
          <button class="btn-retake" @click="retryExam">重新测试</button>
          <router-link :to="'/learn/' + $route.params.nodeId" class="btn-retry">继续学习</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onActivated, watch } from 'vue'
import { useRoute } from 'vue-router'
import { http } from '../../utils/request'

const route = useRoute()

const loading = ref(true)
const nodeTitle = ref('')
const questions = ref([])
const answers = reactive({})
const submitted = ref(false)
const result = ref({})
const submitting = ref(false)
const errorMsg = ref('')

const answeredCount = computed(() => Object.keys(answers).length)

// ★ 清理所有答案和错误
function resetAnswers() {
  Object.keys(answers).forEach(k => delete answers[k])
  errorMsg.value = ''
}

// ★ 选择答案
function selectAnswer(qId, optionIndex) {
  errorMsg.value = ''
  answers[qId] = optionIndex
}

// ★ 加载题目
async function loadQuestions(nodeId) {
  loading.value = true
  try {
    const res = await http.get(`/exam/${nodeId}/questions`)
    nodeTitle.value = res.node_title || nodeId
    questions.value = res.questions || []
  } catch (e) {
    console.error('[Exam] 加载失败:', e)
  } finally {
    loading.value = false
  }
}

// ★ 初次进入
onMounted(() => {
  loadQuestions(route.params.nodeId)
})

// ★ keep-alive 重新激活：重置所有状态，重新加载题目
onActivated(() => {
  submitted.value = false
  result.value = {}
  resetAnswers()
  loadQuestions(route.params.nodeId)
})

// ★ 路由参数变化（同一组件跳到不同的 nodeId）
watch(() => route.params.nodeId, (newId) => {
  if (newId) {
    submitted.value = false
    result.value = {}
    resetAnswers()
    loadQuestions(newId)
  }
})

// ★ 重新测试：重置状态回到答题页
function retryExam() {
  submitted.value = false
  result.value = {}
  errorMsg.value = ''
  resetAnswers()
}

async function handleSubmit() {
  if (submitting.value) return
  errorMsg.value = ''

  // 校验：是否所有题目都已作答
  if (answeredCount.value < questions.value.length) {
    errorMsg.value = `还有 ${questions.value.length - answeredCount.value} 道题未作答，请完成所有题目`
    return
  }

  submitting.value = true
  try {
    const nodeId = route.params.nodeId
    const answerList = Object.entries(answers).map(([id, answer]) => ({
      id, answer
    }))
    const res = await http.post(`/exam/${nodeId}/submit`, {
      node_id: nodeId,
      answers: answerList,
    })
    result.value = res
    submitted.value = true
    // ★ 考试完成后，全局刷新能力值（无需刷新页面，雷达图自动更新）
    try {
      const { useAbilityStore } = await import('../../store/ability')
      const abilityStore = useAbilityStore()
      await abilityStore.refreshAbility()
    } catch (_) { /* 能力刷新非关键路径，失败不影响主流程 */ }
  } catch (e) {
    const detail = e?.detail || e?.message || ''
    const status = e?.status || ''
    console.error('[Exam] 提交失败:', e)
    if (!detail && !status) {
      errorMsg.value = '网络错误，请检查网络连接后重试'
    } else if (status === 401) {
      errorMsg.value = '登录已过期，请重新登录'
    } else if (status === 500 || detail.includes('500')) {
      errorMsg.value = '服务器异常，请稍后重试'
    } else {
      errorMsg.value = detail || '提交失败，请重试'
    }
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
.exam-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 32px 24px 48px;
  min-height: 100vh;
}

.exam-loading {
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

.exam-header {
  margin-bottom: 32px;
  .back-link { font-size: 14px; color: var(--color-primary); text-decoration: none; &:hover { text-decoration: underline; } }
  h1 { font-size: 28px; margin: 16px 0 8px; }
  .exam-desc { color: var(--text-tertiary); font-size: 14px; margin: 0; }
}

.question-card {
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 20px;
  transition: border-color 0.2s;
  &.has-answer { border-color: var(--color-primary-light); }

  .question-num {
    font-size: 12px;
    font-weight: 700;
    color: var(--color-primary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 12px;
  }
  .question-text {
    font-size: 17px;
    font-weight: 600;
    color: var(--text-main);
    margin: 0 0 20px;
    line-height: 1.4;
  }
}

.option-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.option-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1.5px solid var(--border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  &:hover { border-color: var(--color-primary-light); background: rgba(16,163,127,0.03); }
  &.selected {
    border-color: var(--color-primary);
    background: rgba(16,163,127,0.06);
  }
  .option-radio {
    font-size: 18px;
    color: var(--color-primary);
    width: 20px; text-align: center;
  }
  .option-text {
    font-size: 15px;
    color: var(--text-main);
    font-weight: 500;
  }
}

/* ── 错误提示 ── */
.exam-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 10px;
  margin-bottom: 16px;
  font-size: 14px;
  color: #dc2626;
  .error-icon { font-size: 16px; }
}

.exam-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
  margin-top: 20px;
  border-top: 1px solid var(--border-light);
  .progress-info { font-size: 14px; color: var(--text-secondary); }
  .submit-btn {
    padding: 14px 40px;
    border: none;
    border-radius: 12px;
    background: linear-gradient(135deg, var(--color-primary), #0d8c6d);
    color: #fff;
    font-size: 16px;
    font-weight: 700;
    cursor: pointer;
    transition: opacity 0.2s;
    display: flex;
    align-items: center;
    gap: 8px;
    &:disabled { opacity: 0.4; cursor: not-allowed; }
    &:hover:not(:disabled) { opacity: 0.9; }
    .btn-loading {
      width: 16px; height: 16px;
      border: 2px solid rgba(255,255,255,0.3);
      border-top-color: #fff;
      border-radius: 50%;
      animation: btn-spin 0.6s linear infinite;
    }
  }
  @keyframes btn-spin { to { transform: rotate(360deg); } }
}

.exam-result {
  padding: 40px 0;
}
.result-card {
  text-align: center;
  padding: 40px 32px;
  border-radius: 24px;
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-lg);
  &.passed { border-left: 6px solid #22c55e; }
  &.failed { border-left: 6px solid #f97316; }
  .result-icon { font-size: 48px; margin-bottom: 16px; }
  h2 { font-size: 28px; margin: 0 0 24px; }
}
.score-circle { margin: 0 auto 24px; }
.result-detail { font-size: 16px; color: var(--text-secondary); margin: 0 0 8px; }
.chapter-done { color: #22c55e; font-weight: 700; font-size: 16px; }
.chapter-hint { color: #f97316; font-size: 14px; }

.answer-details {
  text-align: left;
  margin: 32px 0;
}
.detail-item {
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 12px;
  &.correct { background: rgba(34,197,94,0.06); }
  &.wrong { background: rgba(249,115,22,0.06); }
  .detail-q { font-weight: 600; margin-bottom: 6px; font-size: 14px; }
  .detail-result { font-size: 13px; margin-bottom: 6px; }
  .detail-explanation { font-size: 13px; color: var(--text-tertiary); padding: 8px 12px; background: rgba(0,0,0,0.03); border-radius: 8px; }
}

.result-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-top: 24px;
  a {
    padding: 12px 28px;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s;
  }
  .btn-back {
    background: var(--bg-secondary);
    color: var(--text-secondary);
    border: 1px solid var(--border-color);
    &:hover { border-color: var(--color-primary); color: var(--color-primary); }
  }
  .btn-retake {
    padding: 12px 28px;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    border: 1.5px solid #f97316;
    background: #fff;
    color: #f97316;
    transition: all 0.2s;
    &:hover { background: rgba(249,115,22,0.06); border-color: #ea580c; color: #ea580c; }
  }
  .btn-retry {
    background: linear-gradient(135deg, var(--color-primary), #0d8c6d);
    color: #fff;
    &:hover { opacity: 0.9; }
  }
}
</style>
