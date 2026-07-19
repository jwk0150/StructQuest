<template>
  <div class="quiz-card">
    <div v-if="submitted" class="quiz-result">
      <div class="result-header" :class="{ correct: isAllCorrect, wrong: !isAllCorrect }">
        <span class="result-icon">{{ isAllCorrect ? '✅' : '❌' }}</span>
        <span>{{ isAllCorrect ? '回答正确！' : `得分: ${score}/${totalQuestions}` }}</span>
      </div>
      <!-- 逐题解析 -->
      <div v-for="(q, qi) in questions" :key="qi" class="result-item">
        <div class="result-q">{{ qi + 1 }}. {{ q.question }}</div>
        <div class="result-user">
          你的答案: <strong>{{ getUserAnswer(qi) }}</strong>
          <span v-if="isCorrect(qi)" class="correct-tag">✓</span>
          <span v-else class="wrong-tag">✗</span>
        </div>
        <div v-if="!isCorrect(qi) && q.explanation" class="result-explain">
          {{ q.explanation }}
        </div>
      </div>
      <el-button size="small" type="primary" link @click="reset" style="margin-top:8px">重新作答</el-button>
    </div>

    <div v-else class="quiz-questions">
      <div v-for="(q, qi) in questions" :key="qi" class="quiz-item">
        <div class="quiz-q">
          <span class="q-num">{{ qi + 1 }}.</span>
          <span>{{ q.question }}</span>
        </div>
        <!-- 单选题 -->
        <div v-if="q.type === 'single_choice'" class="quiz-options">
          <label
            v-for="(opt, oi) in (q.options || [])"
            :key="oi"
            class="quiz-option"
            :class="{ selected: userAnswers[qi] === oi }"
          >
            <input
              type="radio"
              :name="'q' + qi"
              :value="oi"
              v-model="userAnswers[qi]"
            />
            <span>{{ opt.label }}. {{ opt.text }}</span>
          </label>
        </div>
        <!-- 判断题 -->
        <div v-else-if="q.type === 'true_false'" class="quiz-options">
          <label class="quiz-option" :class="{ selected: userAnswers[qi] === true }">
            <input type="radio" :name="'q' + qi" :value="true" v-model="userAnswers[qi]" /> 正确
          </label>
          <label class="quiz-option" :class="{ selected: userAnswers[qi] === false }">
            <input type="radio" :name="'q' + qi" :value="false" v-model="userAnswers[qi]" /> 错误
          </label>
        </div>
      </div>

      <el-button type="primary" size="small" @click="submitAnswers" :disabled="!canSubmit" style="margin-top:10px">
        提交答案
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  data: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['submit'])

const questions = computed(() => {
  const qs = props.data.questions || []
  return qs.map((q) => ({
    ...q,
    type: q.type || 'single_choice',
    options: q.options || [],
  }))
})

const totalQuestions = computed(() => questions.value.length)
const userAnswers = ref({})
const submitted = ref(false)
const score = ref(0)

const canSubmit = computed(() => {
  const qs = questions.value
  if (!qs.length) return false
  return qs.every((_, i) => userAnswers.value[i] !== undefined)
})

function isCorrect(qi) {
  const q = questions.value[qi]
  if (!q) return false
  const userAns = userAnswers.value[qi]
  const correct = q.correct !== undefined ? q.correct : q.answer
  if (correct === undefined) return false
  return String(userAns) === String(correct)
}

const isAllCorrect = computed(() => {
  return questions.value.every((_, i) => isCorrect(i))
})

function getUserAnswer(qi) {
  const q = questions.value[qi]
  if (!q) return ''
  const userAns = userAnswers.value[qi]
  const options = q.options || []
  const opt = options.find((o) => String(o.label) === String(userAns) || userAns === true || userAns === false)
  if (opt) return `${opt.label}. ${opt.text}`
  return String(userAns)
}

function submitAnswers() {
  let correct = 0
  questions.value.forEach((_, i) => {
    if (isCorrect(i)) correct++
  })
  score.value = correct
  submitted.value = true
  emit('submit', { score: correct, total: totalQuestions.value, answers: { ...userAnswers.value } })
}

function reset() {
  submitted.value = false
  userAnswers.value = {}
  score.value = 0
}
</script>

<style scoped>
.quiz-card {
  font-size: 14px;
}

.quiz-item {
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}
.quiz-item:last-child {
  border-bottom: none;
}

.quiz-q {
  font-weight: 600;
  margin-bottom: 8px;
  color: #1e293b;
}
.q-num {
  color: #c84c5a;
  margin-right: 6px;
}

.quiz-options {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.quiz-option {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  border: 1px solid transparent;
}
.quiz-option:hover {
  background: #f8fafc;
}
.quiz-option.selected {
  background: #fbf0f1;
  border-color: #c7d2fe;
}

.quiz-option input[type="radio"] {
  margin-top: 3px;
  accent-color: #c84c5a;
}

.quiz-result {
  font-size: 14px;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 8px;
  margin-bottom: 12px;
  font-weight: 600;
}
.result-header.correct { background: #ecfdf5; color: #065f46; }
.result-header.wrong { background: #fef2f2; color: #991b1b; }

.result-item {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}
.result-q { font-weight: 500; color: #333; }
.result-user { margin: 4px 0; color: #555; font-size: 13px; }
.result-explain {
  font-size: 12px;
  color: #6b7280;
  background: #f9fafb;
  padding: 6px 10px;
  border-radius: 4px;
  margin: 4px 0;
}
.correct-tag { color: #10b981; font-weight: 700; }
.wrong-tag { color: #ef4444; font-weight: 700; }
</style>

