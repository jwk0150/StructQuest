<template>
  <div class="exam-workspace" :class="{ 'is-coding': currentQuestion?.type === 'coding' }">
    <aside class="question-sidebar">
      <div class="sidebar-heading">
        <span class="sidebar-kicker">QUESTION SET</span>
        <h2>题目导航</h2>
        <p>选择题号切换作答，答案会自动保留。</p>
      </div>

      <div class="progress-card">
        <div class="progress-copy">
          <span>完成进度</span>
          <strong>{{ completedCount }}/{{ questions.length }}</strong>
        </div>
        <div class="progress-track">
          <span :style="{ width: `${progressPercent}%` }"></span>
        </div>
      </div>

      <div class="question-grid">
        <button
          v-for="(question, index) in questions"
          :key="question.id"
          type="button"
          class="question-nav-item"
          :class="{
            active: index === activeIndex,
            answered: isAnswered(question),
          }"
          @click="activeIndex = index"
        >
          <span class="nav-number">{{ index + 1 }}</span>
          <span class="nav-meta">{{ typeLabel(question.type) }}</span>
          <span v-if="isAnswered(question)" class="nav-check">✓</span>
        </button>
      </div>

      <div class="sidebar-legend">
        <span><i class="dot current"></i>当前</span>
        <span><i class="dot done"></i>已完成</span>
        <span><i class="dot todo"></i>未作答</span>
      </div>
    </aside>

    <main v-if="currentQuestion" class="question-stage">
      <header class="stage-toolbar">
        <div class="toolbar-tags">
          <span class="question-index">第 {{ activeIndex + 1 }} 题</span>
          <span class="type-chip" :class="`type-${currentQuestion.type || 'choice'}`">
            {{ typeLabel(currentQuestion.type) }}
          </span>
          <span class="difficulty-chip">{{ difficultyLabel(currentQuestion.difficulty) }}</span>
        </div>
        <span class="autosave-status"><i></i>答案自动保存</span>
      </header>

      <article class="problem-card">
        <div class="problem-heading">
          <span class="problem-label">题目要求</span>
          <h3>{{ currentQuestion.question }}</h3>
        </div>

        <div v-if="(currentQuestion.type || 'choice') === 'choice'" class="choice-board">
          <button
            v-for="(option, optionIndex) in currentQuestion.options"
            :key="optionIndex"
            type="button"
            class="choice-card"
            :class="{ selected: answers[currentQuestion.id] === optionIndex }"
            @click="updateAnswer(optionIndex)"
          >
            <span class="choice-letter">{{ String.fromCharCode(65 + optionIndex) }}</span>
            <span class="choice-text">{{ option }}</span>
            <span class="choice-state">{{ answers[currentQuestion.id] === optionIndex ? '✓' : '' }}</span>
          </button>
        </div>

        <div v-else-if="currentQuestion.type === 'blank'" class="blank-workbench">
          <label :for="`blank-${currentQuestion.id}`">填写答案</label>
          <input
            :id="`blank-${currentQuestion.id}`"
            :value="answers[currentQuestion.id] || ''"
            autocomplete="off"
            placeholder="在这里输入你的答案"
            @input="updateAnswer($event.target.value)"
          />
          <p>请填写关键概念或计算结果，无需重复题干。</p>
        </div>

        <div v-else-if="currentQuestion.type === 'coding'" class="coding-workbench">
          <section class="coding-brief">
            <div class="brief-section">
              <span class="brief-title">编写要求</span>
              <ul>
                <li>使用 Python 3 完成题目给出的函数。</li>
                <li>保留函数名与参数，不要只填写运行结果。</li>
                <li>考虑空输入、边界值和常见异常情况。</li>
              </ul>
            </div>
            <div class="brief-section judge-note">
              <span class="brief-title">评测说明</span>
              <p>提交后会检查函数结构、关键逻辑与返回值，并给出参考实现和解析。</p>
            </div>
          </section>

          <section class="editor-shell">
            <div class="editor-toolbar">
              <div class="editor-file">
                <span class="window-dots"><i></i><i></i><i></i></span>
                <span>main.py</span>
                <b>Python 3</b>
              </div>
              <button type="button" class="reset-code" @click="resetCode">重置代码</button>
            </div>
            <textarea
              :key="`${currentQuestion.id}-${editorVersion}`"
              class="code-editor"
              :value="codingValue"
              rows="18"
              spellcheck="false"
              aria-label="Python 代码编辑器"
              @input="updateAnswer($event.target.value)"
            ></textarea>
            <div class="editor-footer">
              <span>UTF-8</span>
              <span>Spaces: 4</span>
              <span>{{ codingLineCount }} 行</span>
            </div>
          </section>
        </div>
      </article>

      <footer class="stage-actions">
        <button type="button" class="nav-action" :disabled="activeIndex === 0" @click="previousQuestion">
          ← 上一题
        </button>
        <div class="answer-status" :class="{ complete: isAnswered(currentQuestion) }">
          <span>{{ isAnswered(currentQuestion) ? '本题已作答' : '本题尚未作答' }}</span>
          <small>{{ completedCount === questions.length ? '全部完成，可以交卷' : `还剩 ${questions.length - completedCount} 题` }}</small>
        </div>
        <button
          v-if="activeIndex < questions.length - 1"
          type="button"
          class="nav-action next"
          @click="nextQuestion"
        >
          下一题 →
        </button>
        <button
          type="button"
          class="submit-action"
          :disabled="completedCount < questions.length || submitting"
          @click="$emit('submit')"
        >
          {{ submitting ? '正在提交…' : '提交全部答案' }}
        </button>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  questions: { type: Array, default: () => [] },
  answers: { type: Object, required: true },
  submitting: { type: Boolean, default: false },
})

const emit = defineEmits(['answer', 'submit'])
const activeIndex = ref(0)
const editorVersion = ref(0)

const currentQuestion = computed(() => props.questions[activeIndex.value] || null)

function isAnswered(question) {
  if (!question) return false
  const answer = props.answers[question.id]
  if (answer === undefined || answer === null) return false
  if (typeof answer === 'string') {
    const value = answer.trim()
    if (!value) return false
    if (question.type === 'coding' && value === String(question.coding_template || '').trim()) return false
  }
  return true
}

const completedCount = computed(() => props.questions.filter(isAnswered).length)
const progressPercent = computed(() => (
  props.questions.length ? Math.round((completedCount.value / props.questions.length) * 100) : 0
))
const codingValue = computed(() => {
  const question = currentQuestion.value
  if (!question) return ''
  return props.answers[question.id] ?? question.coding_template ?? ''
})
const codingLineCount = computed(() => String(codingValue.value || '').split('\n').length)

watch(() => props.questions, () => {
  activeIndex.value = 0
  editorVersion.value += 1
})

function typeLabel(type) {
  return ({ choice: '选择题', blank: '填空题', coding: '编程题' })[type || 'choice'] || '题目'
}

function difficultyLabel(difficulty) {
  return ({ easy: '基础', medium: '进阶', hard: '挑战' })[difficulty] || '综合'
}

function updateAnswer(value) {
  if (!currentQuestion.value) return
  emit('answer', { id: currentQuestion.value.id, value })
}

function resetCode() {
  updateAnswer(undefined)
  editorVersion.value += 1
}

function previousQuestion() {
  activeIndex.value = Math.max(0, activeIndex.value - 1)
}

function nextQuestion() {
  activeIndex.value = Math.min(props.questions.length - 1, activeIndex.value + 1)
}
</script>

<style scoped>
.exam-workspace {
  display: grid;
  grid-template-columns: 238px minmax(0, 1fr);
  min-height: 650px;
  overflow: hidden;
  border: 1px solid #e1e8f0;
  border-radius: 20px;
  background: #f6f8fb;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
}

.question-sidebar {
  padding: 25px 20px;
  border-right: 1px solid #e1e8f0;
  background: #fff;
}

.sidebar-kicker {
  color: #7c3aed;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.16em;
}

.sidebar-heading h2 {
  margin: 6px 0 5px;
  color: #172033;
  font-size: 21px;
}

.sidebar-heading p {
  margin: 0;
  color: #8490a3;
  font-size: 12px;
  line-height: 1.6;
}

.progress-card {
  margin: 22px 0;
  padding: 14px;
  border-radius: 12px;
  background: #f6f3ff;
}

.progress-copy {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #746988;
  font-size: 12px;
}

.progress-copy strong { color: #6d28d9; font-size: 15px; }
.progress-track { height: 6px; margin-top: 10px; overflow: hidden; border-radius: 99px; background: #e5dcfa; }
.progress-track span { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #8b5cf6, #6d28d9); transition: width .25s ease; }

.question-grid { display: grid; gap: 9px; }

.question-nav-item {
  position: relative;
  display: grid;
  grid-template-columns: 34px 1fr 18px;
  align-items: center;
  min-height: 48px;
  padding: 7px 9px;
  border: 1px solid #e6eaf0;
  border-radius: 11px;
  background: #fff;
  color: #718096;
  text-align: left;
  cursor: pointer;
  transition: .18s ease;
}

.question-nav-item:hover { border-color: #c4b5fd; transform: translateY(-1px); }
.question-nav-item.active { border-color: #7c3aed; background: #f8f5ff; color: #5b21b6; box-shadow: 0 0 0 3px rgba(124, 58, 237, .08); }
.question-nav-item.answered:not(.active) { border-color: #bbf7d0; background: #f2fdf6; }
.nav-number { display: grid; width: 30px; height: 30px; place-items: center; border-radius: 8px; background: #edf1f6; color: #334155; font-weight: 800; }
.active .nav-number { background: #7c3aed; color: #fff; }
.answered:not(.active) .nav-number { background: #dcfce7; color: #15803d; }
.nav-meta { padding-left: 8px; font-size: 12px; font-weight: 700; }
.nav-check { color: #16a34a; font-weight: 900; }

.sidebar-legend { display: flex; flex-wrap: wrap; gap: 10px 13px; margin-top: 20px; color: #94a0b2; font-size: 11px; }
.sidebar-legend span { display: inline-flex; align-items: center; gap: 5px; }
.dot { width: 7px; height: 7px; border-radius: 50%; background: #d8dee8; }
.dot.current { background: #7c3aed; }
.dot.done { background: #22c55e; }

.question-stage { display: flex; min-width: 0; flex-direction: column; padding: 22px; }
.stage-toolbar { display: flex; align-items: center; justify-content: space-between; min-height: 36px; margin-bottom: 14px; }
.toolbar-tags { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.question-index { color: #334155; font-size: 14px; font-weight: 800; }
.type-chip, .difficulty-chip { padding: 5px 9px; border-radius: 99px; font-size: 11px; font-weight: 700; }
.type-chip { background: #ede9fe; color: #6d28d9; }
.type-chip.type-coding { background: #dbeafe; color: #1d4ed8; }
.type-chip.type-blank { background: #fef3c7; color: #b45309; }
.difficulty-chip { background: #edf1f5; color: #64748b; }
.autosave-status { display: flex; align-items: center; gap: 7px; color: #8b97a8; font-size: 11px; }
.autosave-status i { width: 7px; height: 7px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 0 4px #dcfce7; }

.problem-card { flex: 1; min-height: 470px; padding: 30px; border: 1px solid #e4e9f0; border-radius: 16px; background: #fff; }
.problem-heading { padding-bottom: 24px; border-bottom: 1px solid #edf0f4; }
.problem-label, .brief-title { color: #8b5cf6; font-size: 11px; font-weight: 800; letter-spacing: .08em; }
.problem-heading h3 { max-width: 920px; margin: 10px 0 0; color: #182235; font-size: 20px; line-height: 1.65; }

.choice-board { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 13px; padding-top: 26px; }
.choice-card { display: grid; grid-template-columns: 38px 1fr 22px; align-items: center; min-height: 76px; padding: 14px 16px; border: 1px solid #e1e7ef; border-radius: 13px; background: #fbfcfe; color: #344054; text-align: left; cursor: pointer; transition: .18s ease; }
.choice-card:hover { border-color: #a78bfa; background: #faf8ff; transform: translateY(-1px); }
.choice-card.selected { border-color: #7c3aed; background: #f5f1ff; box-shadow: 0 0 0 3px rgba(124, 58, 237, .08); }
.choice-letter { display: grid; width: 32px; height: 32px; place-items: center; border-radius: 9px; background: #edf1f6; color: #475569; font-weight: 800; }
.selected .choice-letter { background: #7c3aed; color: #fff; }
.choice-text { padding: 0 12px; line-height: 1.55; }
.choice-state { color: #7c3aed; font-size: 18px; font-weight: 900; }

.blank-workbench { max-width: 700px; padding-top: 30px; }
.blank-workbench label { display: block; margin-bottom: 10px; color: #334155; font-size: 13px; font-weight: 800; }
.blank-workbench input { width: 100%; height: 52px; padding: 0 16px; border: 1px solid #d8e0e9; border-radius: 11px; outline: none; color: #172033; font-size: 15px; box-sizing: border-box; transition: .18s ease; }
.blank-workbench input:focus { border-color: #7c3aed; box-shadow: 0 0 0 4px rgba(124, 58, 237, .09); }
.blank-workbench p { color: #98a2b3; font-size: 12px; }

.coding-workbench { display: grid; grid-template-columns: minmax(210px, 28%) minmax(0, 1fr); gap: 18px; padding-top: 22px; }
.coding-brief { padding: 20px; border: 1px solid #e4e9ef; border-radius: 13px; background: #f8fafc; }
.brief-section + .brief-section { margin-top: 25px; padding-top: 20px; border-top: 1px solid #e4e9ef; }
.brief-section ul { margin: 12px 0 0; padding-left: 18px; color: #5d6878; font-size: 12px; line-height: 1.9; }
.brief-section p { margin: 11px 0 0; color: #5d6878; font-size: 12px; line-height: 1.75; }
.judge-note { padding: 14px; border: 0 !important; border-radius: 10px; background: #eef6ff; }
.judge-note .brief-title { color: #2563eb; }

.editor-shell { min-width: 0; overflow: hidden; border: 1px solid #263244; border-radius: 13px; background: #111827; box-shadow: 0 12px 30px rgba(15, 23, 42, .18); }
.editor-toolbar, .editor-footer { display: flex; align-items: center; justify-content: space-between; color: #9aa8bb; font-size: 11px; }
.editor-toolbar { height: 42px; padding: 0 13px; border-bottom: 1px solid #293548; background: #182235; }
.editor-file { display: flex; align-items: center; gap: 11px; }
.editor-file b { padding: 3px 7px; border-radius: 5px; background: #243854; color: #93c5fd; font-size: 10px; }
.window-dots { display: flex; gap: 5px; }
.window-dots i { width: 7px; height: 7px; border-radius: 50%; background: #64748b; }
.window-dots i:first-child { background: #f87171; }
.window-dots i:nth-child(2) { background: #fbbf24; }
.window-dots i:nth-child(3) { background: #4ade80; }
.reset-code { border: 0; background: transparent; color: #a5b4fc; font-size: 11px; cursor: pointer; }
.reset-code:hover { color: #fff; }
.code-editor { display: block; width: 100%; min-height: 340px; padding: 20px; resize: vertical; border: 0; outline: none; box-sizing: border-box; background: #111827; color: #dbeafe; font: 13px/1.75 "Cascadia Code", "JetBrains Mono", Consolas, monospace; tab-size: 4; }
.editor-footer { justify-content: flex-end; gap: 17px; height: 29px; padding: 0 13px; border-top: 1px solid #263244; background: #182235; }

.stage-actions { display: flex; align-items: center; gap: 10px; padding-top: 16px; }
.nav-action, .submit-action { height: 42px; padding: 0 17px; border-radius: 10px; font-weight: 700; cursor: pointer; transition: .18s ease; }
.nav-action { border: 1px solid #dce2ea; background: #fff; color: #526074; }
.nav-action:hover:not(:disabled) { border-color: #a78bfa; color: #6d28d9; }
.nav-action:disabled { opacity: .4; cursor: not-allowed; }
.answer-status { display: flex; min-width: 150px; flex: 1; flex-direction: column; padding: 0 8px; color: #9a6700; font-size: 12px; }
.answer-status.complete { color: #16803d; }
.answer-status small { margin-top: 2px; color: #98a2b3; }
.submit-action { border: 0; background: linear-gradient(135deg, #7c3aed, #5b21b6); color: #fff; box-shadow: 0 8px 18px rgba(109, 40, 217, .22); }
.submit-action:disabled { background: #c9cdd5; box-shadow: none; cursor: not-allowed; }

@media (max-width: 980px) {
  .exam-workspace { grid-template-columns: 1fr; }
  .question-sidebar { border-right: 0; border-bottom: 1px solid #e1e8f0; }
  .sidebar-heading p, .sidebar-legend { display: none; }
  .progress-card { margin: 14px 0; }
  .question-grid { display: flex; overflow-x: auto; padding-bottom: 3px; }
  .question-nav-item { min-width: 108px; }
  .coding-workbench { grid-template-columns: 1fr; }
}

@media (max-width: 680px) {
  .question-stage { padding: 12px; }
  .problem-card { min-height: 420px; padding: 20px; }
  .choice-board { grid-template-columns: 1fr; }
  .autosave-status, .answer-status { display: none; }
  .stage-actions { flex-wrap: wrap; }
  .submit-action { margin-left: auto; }
}
</style>
