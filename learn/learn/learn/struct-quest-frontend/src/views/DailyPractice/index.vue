<template>
  <div class="practice-view">
    <div class="practice-topbar">
      <button class="back-btn" @click="$router.push('/app/quest')">← 返回</button>
      <div>
        <h1 class="practice-title">📝 今日练习</h1>
        <p class="practice-subtitle">完成以下 3 道题目，检测知识掌握程度</p>
      </div>
    </div>

    <div v-if="loading" class="practice-loading">加载题目中...</div>

    <div v-else-if="!submitted" class="practice-body">
      <div v-for="(q, idx) in questions" :key="q.id" class="practice-question-card"
        :class="{ 'is-answered': answers[q.id] !== undefined }">
        <div class="q-header">
          <span class="q-number">第 {{ idx + 1 }} 题</span>
          <span v-if="answers[q.id] !== undefined" class="q-status">✅ 已作答</span>
        </div>
        <p class="q-text">{{ q.question }}</p>
        <div class="q-options">
          <div v-for="(opt, oi) in q.options" :key="oi" class="q-option"
            :class="{ selected: answers[q.id] === oi }" @click="selectOption(q.id, oi)">
            <span class="option-label">{{ ['A', 'B', 'C', 'D'][oi] }}</span>
            <span class="option-text">{{ opt }}</span>
          </div>
        </div>
      </div>

      <button class="practice-submit-btn" :disabled="!canSubmit || submitting" @click="submitAnswers">
        {{ submitting ? '提交中...' : '提交答案' }}
      </button>
    </div>

    <div v-else class="practice-result">
      <div class="result-circle">
        <svg width="80" height="80" viewBox="0 0 80 80">
          <circle cx="40" cy="40" r="36" fill="none" stroke="#e8e8e8" stroke-width="6"/>
          <circle cx="40" cy="40" r="36" fill="none" stroke="#22c55e" stroke-width="6"
            :stroke-dasharray="226" :stroke-dashoffset="226 - (score / 100 * 226)"
            transform="rotate(-90 40 40)" stroke-linecap="round"/>
        </svg>
        <div class="result-score">{{ score }}<span>分</span></div>
      </div>
      <p class="result-text">{{ correctCount }} / {{ total }} 题正确</p>

      <div class="result-actions">
        <button class="back-btn" @click="$router.push('/app/quest')">返回今日任务</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import dailyTaskApi from '../../api/dailyTask'
import { useAbilityStore } from '../../store/ability'

const abilityStore = useAbilityStore()
const loading = ref(true)
const submitting = ref(false)
const submitted = ref(false)
const questions = ref([])
const answers = ref({})
const correctCount = ref(0)
const scoreValue = ref(0)
const resultDetails = ref([])

const canSubmit = computed(() => Object.keys(answers.value).length === questions.value.length && questions.value.length > 0)
const total = computed(() => questions.value.length)
const score = computed(() => scoreValue.value)

onMounted(async () => {
  try {
    const res = await dailyTaskApi.getPracticeQuestions()
    questions.value = res.questions || []
  } catch (e) {
    console.warn('[DailyPractice] 加载题目失败:', e)
  } finally {
    loading.value = false
  }
})

function selectOption(qId, optionIndex) {
  if (submitted.value) return
  answers.value = { ...answers.value, [qId]: optionIndex }
}

async function submitAnswers() {
  submitting.value = true
  const answerList = questions.value.map(q => ({
    question_id: q.id,
    answer: answers.value[q.id],
    is_correct: false,
    question_text: q.question,
    options: q.options,
    question_type: 'choice',
  }))

  try {
    const res = await dailyTaskApi.submitPractice({ answers: answerList })
    scoreValue.value = res.score || 0
    correctCount.value = res.correct_count || 0
    submitted.value = true

    // 刷新能力值
    await abilityStore.refreshAbility()
  } catch (e) {
    console.warn('[DailyPractice] 提交失败:', e)
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
.practice-view { max-width: 720px; margin: 0 auto; padding: 24px 28px; }
.practice-topbar { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }
.back-btn { padding: 7px 16px; border: 1px solid rgba(0,0,0,0.1); border-radius: 8px; background: #f9f8f6; color: #666; font-size: 13px; cursor: pointer; white-space: nowrap; &:hover { background: #f0eee9; } }
.practice-title { font-size: 24px; font-weight: 700; color: #333; margin: 0 0 4px; }
.practice-subtitle { font-size: 14px; color: #999; margin: 0; }
.practice-loading { text-align: center; padding: 80px 0; color: #999; font-size: 15px; }
.practice-body { display: flex; flex-direction: column; gap: 16px; }
.practice-question-card { background: #fff; border-radius: 14px; border: 1px solid rgba(0,0,0,0.06); padding: 20px 24px; transition: all 0.2s; }
.practice-question-card.is-answered { border-color: rgba(34,197,94,0.25); background: rgba(240,253,244,0.3); }
.q-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.q-number { font-size: 13px; font-weight: 700; color: #3b82f6; }
.q-status { font-size: 12px; color: #22c55e; }
.q-text { font-size: 15px; color: #333; line-height: 1.6; margin: 0 0 14px; }
.q-options { display: flex; flex-direction: column; gap: 8px; }
.q-option { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 10px; border: 1px solid rgba(0,0,0,0.08); cursor: pointer; transition: all 0.2s; }
.q-option:hover { border-color: rgba(59,130,246,0.3); background: rgba(59,130,246,0.04); }
.q-option.selected { border-color: #3b82f6; background: rgba(59,130,246,0.08); }
.q-option.selected .option-label { background: #3b82f6; color: #fff; }
.option-label { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; color: #999; background: rgba(0,0,0,0.04); flex-shrink: 0; transition: all 0.2s; }
.option-text { font-size: 14px; color: #555; }
.practice-submit-btn { margin-top: 12px; padding: 14px 32px; border: none; border-radius: 12px; background: linear-gradient(135deg, #3b82f6, #6366f1); color: #fff; font-size: 15px; font-weight: 600; cursor: pointer; transition: all 0.2s; align-self: center; }
.practice-submit-btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none !important; }
.practice-submit-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(59,130,246,0.3); }
.practice-result { text-align: center; padding: 40px 0; }
.result-circle { position: relative; width: 80px; height: 80px; margin: 0 auto 16px; }
.result-score { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: 700; color: #22c55e; }
.result-score span { font-size: 14px; font-weight: 400; color: #999; margin-left: 2px; }
.result-text { font-size: 16px; color: #666; margin: 0 0 24px; }
.result-actions { display: flex; justify-content: center; gap: 12px; }
</style>
