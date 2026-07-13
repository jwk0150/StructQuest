<template>
  <section id="ai-tutor" class="ai-section">
    <div class="section-inner">
      <!-- Section Header -->
      <div class="section-header" ref="headerRef">
        <span class="section-tag">AI 助教</span>
        <h2 class="section-title">你的<span class="title-accent">24/7</span>私人导师</h2>
        <p class="section-subtitle">
          融合讯飞虚拟人、Edge TTS 语音合成与流式 LLM 对话。支持自然语言提问，AI 将用费曼学习法为你拆解每一个复杂概念。
        </p>
      </div>

      <!-- ═══════════ 左右布局：数字人 + 对话 ═══════════ -->
      <div class="tutor-layout" ref="layoutRef">
        <!-- 左侧：数字人老师 -->
        <div class="tutor-left">
          <DigitalTeacher
            ref="digitalTeacherRef"
            :iflytek-config="iflytekConfig"
            @loaded="onTeacherLoaded"
            @error="onTeacherError"
          />

          <!-- TTS 模式切换 -->
          <div class="tts-bar">
            <button :class="['tts-btn', { active: ttsMode === 'edge_tts' }]" @click="setTtsMode('edge_tts')">
              🎵 Edge TTS
            </button>
            <button
              :class="['tts-btn', { active: ttsMode === 'iflytek' }]"
              :disabled="!iflytekAvailable"
              @click="setTtsMode('iflytek')"
            >
              🧑‍🏫 数字人{{ iflytekAvailable ? '' : '(未配置)' }}
            </button>
          </div>

          <!-- 音色选择 -->
          <div class="voice-row" v-if="ttsMode === 'edge_tts'">
            <span class="voice-label">音色</span>
            <select v-model="currentVoice" class="voice-select">
              <option value="xiaoxiao">温柔女声</option>
              <option value="yunxi">阳光男声</option>
              <option value="xiaoyi">知性女声</option>
              <option value="yunyang">沉稳男声</option>
            </select>
          </div>

          <!-- 状态 -->
          <div class="status-row">
            <span :class="['status-dot', isConnected ? 'online' : 'offline']"></span>
            <span class="status-text">{{ connectionLabel }}</span>
          </div>
        </div>

        <!-- 右侧：对话窗口 -->
        <div class="tutor-right">
          <div class="chat-window">
            <!-- 头部 -->
            <div class="chat-header">
              <div class="chat-header-left">
                <span :class="['dot', isConnected ? 'online' : 'offline']"></span>
                <span>AI 老师</span>
              </div>
              <div class="chat-header-right">
                <span v-if="isTyping" class="thinking-badge">思考中...</span>
                <span class="model-tag">StructQuest AI</span>
              </div>
            </div>

            <!-- 消息区 -->
            <div class="chat-messages" ref="msgRef">
              <!-- 离线演示 -->
              <template v-if="messages.length === 0 && !isConnected">
                <div class="chat-msg assistant">
                  <div class="msg-avatar">🤖</div>
                  <div class="msg-bubble">
                    你好！我是你的 AI 数据结构导师。有什么想了解的吗？
                    <div class="bubble-hint">你可以问我：数组的内存分配原理、二叉树的遍历方式、动态规划的思想……</div>
                  </div>
                </div>
                <div class="chat-msg user">
                  <div class="msg-bubble">什么是二叉搜索树？它和普通二叉树的区别在哪？</div>
                </div>
                <div class="chat-msg assistant">
                  <div class="msg-avatar">🤖</div>
                  <div class="msg-bubble">
                    <strong>二叉搜索树 (BST)</strong> 是一种特殊的二叉树，核心规则：
                    <ul>
                      <li><strong>左子树</strong>所有节点 &lt; 根节点</li>
                      <li><strong>右子树</strong>所有节点 &gt; 根节点</li>
                      <li>左右子树本身也是 BST</li>
                    </ul>
                    这使得<code>查找、插入、删除</code>的平均时间复杂度为 <strong>O(log n)</strong>。
                  </div>
                </div>
              </template>

              <!-- 实时消息 -->
              <div v-for="msg in messages" :key="msg.id" :class="['chat-msg', msg.role]">
                <div v-if="msg.role === 'assistant'" class="msg-avatar">🤖</div>
                <div class="msg-bubble" v-html="renderMd(msg.content)"></div>
              </div>

              <!-- AI 思考中 -->
              <div v-if="isTyping" class="chat-msg assistant">
                <div class="msg-avatar">🤖</div>
                <div class="msg-bubble typing">
                  <span class="t-dot"></span><span class="t-dot"></span><span class="t-dot"></span>
                </div>
              </div>
            </div>

            <!-- 输入区 -->
            <div class="chat-input-area">
              <input
                v-model="inputMsg"
                type="text"
                class="chat-input"
                placeholder="向 AI 老师提问…"
                :disabled="!isConnected"
                @keyup.enter="sendMessage"
              />
              <button
                class="send-btn"
                :disabled="!isConnected || isTyping || !inputMsg.trim()"
                @click="sendMessage"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M2 8l12-6L8 14l-2-6L2 8z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 隐藏音频 -->
      <audio ref="audioRef" @ended="audioEnded" @play="audioPlay"></audio>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import DigitalTeacher from '../../components/DigitalTeacher/index.vue'

gsap.registerPlugin(ScrollTrigger)

const headerRef = ref(null)
const layoutRef = ref(null)
const msgRef = ref(null)
const audioRef = ref(null)
const digitalTeacherRef = ref(null)

// ═══════ 状态 ═══════
const inputMsg = ref('')
const messages = ref([])
const isConnected = ref(false)
const isTyping = ref(false)
const ttsMode = ref('edge_tts')
const currentVoice = ref('xiaoxiao')
const iflytekAvailable = ref(false)
const iflytekConfig = ref({})

let ws = null
let msgId = 0

const connectionLabel = computed(() => {
  if (isConnected.value && ttsMode.value === 'iflytek') return '数字人已连接'
  if (isConnected.value) return 'AI 已就绪'
  return '等待连接...'
})

// ═══════ WebSocket ═══════
function connectWS() {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${proto}//${location.host}/ws/chat`)

  ws.onopen = () => {
    isConnected.value = true
    if (messages.value.length === 0) {
      messages.value.push({
        id: ++msgId, role: 'assistant',
        content: '你好！我是你的 AI 数据结构导师，有什么想了解的吗？',
      })
    }
  }
  ws.onclose = () => { isConnected.value = false; setTimeout(connectWS, 5000) }
  ws.onerror = () => { isConnected.value = false }

  ws.onmessage = async (e) => {
    try {
      const d = JSON.parse(e.data)
      if (d.type === 'chunk') {
        isTyping.value = true
        let last = [...messages.value].reverse().find(m => m.role === 'assistant')
        if (!last) { last = { id: ++msgId, role: 'assistant', content: '' }; messages.value.push(last) }
        last.content += d.content || ''
        scrollBottom()
      } else if (d.type === 'done') {
        isTyping.value = false
        scrollBottom()
        // 数字人朗读完整回复
        if (d.full_content && digitalTeacherRef.value?.speakText) {
          digitalTeacherRef.value.speakText(d.full_content)
        }
      } else if (d.type === 'tts_audio') {
        playAudio(d)
      } else if (d.type === 'error') {
        isTyping.value = false
        messages.value.push({ id: ++msgId, role: 'assistant', content: '⚠️ ' + (d.message || '服务异常') })
        scrollBottom()
      }
      // 转发给 DigitalTeacher
      if (digitalTeacherRef.value?.handleWsMessage) {
        digitalTeacherRef.value.handleWsMessage(d)
      }
    } catch {}
  }
}

function sendMessage() {
  const t = inputMsg.value.trim()
  if (!t || !isConnected.value || isTyping.value) return
  messages.value.push({ id: ++msgId, role: 'user', content: t })
  inputMsg.value = ''
  isTyping.value = true
  scrollBottom()

  const hist = messages.value
    .filter(m => m.id < msgId && !m.content.startsWith('⚠️'))
    .map(m => ({ role: m.role === 'user' ? 'user' : 'assistant', content: m.content }))

  ws.send(JSON.stringify({
    messages: [...hist, { role: 'user', content: t }],
    voice: currentVoice.value,
    enable_tts: true,
    tts_mode: ttsMode.value,
  }))
}

function scrollBottom() {
  nextTick(() => {
    const el = msgRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

// ═══════ TTS / 数字人 ═══════
function setTtsMode(mode) {
  ttsMode.value = mode
  if (mode === 'iflytek' && digitalTeacherRef.value?.startIflytek) {
    digitalTeacherRef.value.startIflytek()
  } else if (digitalTeacherRef.value?.stopIflytek) {
    digitalTeacherRef.value.stopIflytek()
  }
}

function onTeacherLoaded(ok) {
  console.log('[AITutor] 数字人加载:', ok)
}
function onTeacherError(err) {
  console.warn('[AITutor] 数字人错误:', err)
}

// ═══════ 音频 ═══════
function playAudio(data) {
  if (!audioRef.value) return
  let src = ''
  if (data.audio_url) {
    src = data.audio_url.startsWith('http') ? data.audio_url
      : data.audio_url.startsWith('/') ? data.audio_url
      : `/static/${data.audio_url}`
  } else if (data.audio_base64) {
    src = `data:audio/mp3;base64,${data.audio_base64}`
  }
  if (!src) return
  audioRef.value.src = src
  audioRef.value.load()
  audioRef.value.play().catch(() => {})
}
function audioEnded() {}
function audioPlay() {}

// ═══════ Markdown 渲染 ═══════
function renderMd(c) {
  if (!c) return ''
  return c
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}

// ═══════ 初始化 ═══════
onMounted(() => {
  connectWS()

  fetch('/api/iflytek/status')
    .then(r => r.json())
    .then(d => {
      iflytekAvailable.value = d.available === true
      if (d.config) iflytekConfig.value = d.config
      if (iflytekAvailable.value) ttsMode.value = 'iflytek'
    }).catch(() => {})

  // GSAP
  if (headerRef.value) {
    gsap.from(headerRef.value.querySelector('.section-tag'), {
      scrollTrigger: { trigger: headerRef.value, start: 'top 80%' },
      opacity: 0, y: 16, duration: 0.5,
    })
    gsap.from(headerRef.value.querySelector('.section-title'), {
      scrollTrigger: { trigger: headerRef.value, start: 'top 80%' },
      opacity: 0, y: 24, duration: 0.6, delay: 0.1,
    })
  }
  if (layoutRef.value) {
    gsap.from(layoutRef.value.querySelector('.tutor-left'), {
      scrollTrigger: { trigger: layoutRef.value, start: 'top 75%' },
      opacity: 0, x: -30, duration: 0.8, ease: 'power3.out',
    })
    gsap.from(layoutRef.value.querySelector('.tutor-right'), {
      scrollTrigger: { trigger: layoutRef.value, start: 'top 75%' },
      opacity: 0, x: 30, duration: 0.8, ease: 'power3.out', delay: 0.15,
    })
  }
})

onBeforeUnmount(() => {
  if (ws) { ws.close(); ws = null }
})
</script>

<style lang="scss" scoped>
.ai-section {
  padding: var(--lp-section-gap, 140px) 40px;
  background: var(--lp-bg);
}
.section-inner { max-width: var(--lp-max-width); margin: 0 auto; }

.section-header { text-align: center; max-width: 640px; margin: 0 auto 60px; }
.section-tag {
  display: inline-block; font-size: 13px; font-weight: 600;
  color: var(--lp-primary); background: var(--lp-primary-light);
  padding: 5px 14px; border-radius: var(--lp-radius-full);
  margin-bottom: 20px; text-transform: uppercase;
}
.section-title {
  font-family: var(--lp-font-display);
  font-size: clamp(32px, 4vw, 48px); font-weight: 800;
  letter-spacing: -0.03em; color: var(--lp-text); margin: 0 0 20px; line-height: 1.15;
}
.title-accent { color: var(--lp-primary); }
.section-subtitle {
  font-size: 17px; line-height: 1.7; color: var(--lp-text-secondary); max-width: 500px; margin: 0 auto;
}

/* ═══════════ 左右布局 ═══════════ */
.tutor-layout {
  display: flex; gap: 0;
  max-width: 1000px; margin: 0 auto;
  background: #fff; border-radius: 20px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.12);
  overflow: hidden; min-height: 540px;
}

/* ── 左侧：数字人 ── */
.tutor-left {
  width: 280px; min-width: 280px;
  background: linear-gradient(180deg, #0f0f2e 0%, #1a1040 50%, #0d1b2a 100%);
  display: flex; flex-direction: column;
  position: relative;
  :deep(.digital-teacher) {
    flex: 1; min-height: 340px;
  }
}

.tts-bar {
  display: flex; gap: 6px; padding: 10px 12px 6px;
}
.tts-btn {
  flex: 1; height: 32px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.15);
  background: rgba(255,255,255,0.06); color: rgba(255,255,255,0.7);
  font-size: 11px; font-weight: 600; cursor: pointer; font-family: inherit;
  transition: all 0.2s;
  &:hover:not(:disabled) { background: rgba(255,255,255,0.12); color: #fff; }
  &.active { background: var(--lp-primary); border-color: var(--lp-primary); color: #fff; }
  &:disabled { opacity: 0.3; cursor: not-allowed; }
}

.voice-row {
  display: flex; align-items: center; gap: 8px; padding: 6px 12px;
}
.voice-label { color: rgba(255,255,255,0.5); font-size: 11px; }
.voice-select {
  flex: 1; height: 28px; border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.15);
  background: rgba(255,255,255,0.08); color: #fff;
  font-size: 11px; padding: 0 6px; outline: none; font-family: inherit;
  option { color: #333; }
}

.status-row {
  display: flex; align-items: center; gap: 6px; padding: 6px 12px 10px;
}
.status-dot { width: 7px; height: 7px; border-radius: 50%;
  &.online { background: #22c55e; box-shadow: 0 0 6px rgba(34,197,94,0.5); }
  &.offline { background: #6b7280; }
}
.status-text { color: rgba(255,255,255,0.5); font-size: 11px; }

/* ── 右侧：对话 ── */
.tutor-right {
  flex: 1; display: flex; flex-direction: column; min-width: 0;
}
.chat-window {
  flex: 1; display: flex; flex-direction: column; height: 540px;
}

.chat-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px; border-bottom: 1px solid #f0f0f0;
}
.chat-header-left { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 600; color: var(--lp-text); }
.dot { width: 8px; height: 8px; border-radius: 50%;
  &.online { background: #22c55e; }
  &.offline { background: #d1d5db; }
}
.chat-header-right { display: flex; align-items: center; gap: 10px; }
.thinking-badge { font-size: 11px; color: var(--lp-primary); animation: blink 1s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.4} }
.model-tag { font-size: 11px; color: var(--lp-text-tertiary); background: var(--lp-bg-secondary); padding: 2px 10px; border-radius: 999px; }

/* 消息区 */
.chat-messages {
  flex: 1; overflow-y: auto; padding: 20px;
  display: flex; flex-direction: column; gap: 14px;
  background: #f8f9fb;
}
.chat-msg {
  display: flex; gap: 10px;
  &.user { justify-content: flex-end;
    .msg-bubble { background: var(--lp-primary); color: #fff; border-bottom-right-radius: 4px; }
  }
  &.assistant {
    .msg-bubble { border-bottom-left-radius: 4px; }
  }
}
.msg-avatar {
  width: 30px; height: 30px; border-radius: 50%;
  background: linear-gradient(135deg, var(--lp-primary), #818CF8);
  display: flex; align-items: center; justify-content: center;
  font-size: 15px; flex-shrink: 0; align-self: flex-end;
}
.msg-bubble {
  max-width: 82%; padding: 12px 16px; background: #fff;
  border-radius: 16px; font-size: 13.5px; line-height: 1.55;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04); border: 1px solid #eee;
  .bubble-hint { font-size: 11px; color: #9ca3af; margin-top: 6px; }
  ul { margin: 6px 0; padding-left: 18px; li { margin: 3px 0; line-height: 1.5; color: var(--lp-text-secondary); } }
  :deep(code) { background: var(--lp-primary-light); color: var(--lp-primary); padding: 1px 5px; border-radius: 4px; font-size: 12px; }
  :deep(strong) { color: var(--lp-text); }
}
.msg-bubble.typing { display: flex; align-items: center; gap: 4px; padding: 14px 18px !important; }
.t-dot { width: 6px; height: 6px; border-radius: 50%; background: #cbd5e1; animation: bounce 1.4s infinite both;
  &:nth-child(2){animation-delay:.16s} &:nth-child(3){animation-delay:.32s}
}
@keyframes bounce { 0%,80%,100%{transform:scale(.5);opacity:.35} 40%{transform:scale(1);opacity:1} }

/* 输入区 */
.chat-input-area { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border-top: 1px solid #f0f0f0; }
.chat-input {
  flex: 1; height: 42px; padding: 0 16px; border: 1.5px solid #e5e7eb;
  border-radius: 999px; font-size: 13.5px; font-family: inherit; color: var(--lp-text);
  outline: none; background: #f8f9fb; transition: all 0.2s;
  &::placeholder { color: #b0b7c3; }
  &:focus { border-color: var(--lp-primary); box-shadow: 0 0 0 3px var(--lp-primary-light); }
}
.send-btn {
  width: 42px; height: 42px; border-radius: 50%; border: none;
  background: var(--lp-primary); color: #fff;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all 0.2s; flex-shrink: 0;
  &:hover:not(:disabled) { transform: scale(1.05); box-shadow: 0 4px 12px var(--lp-primary-glow); }
  &:disabled { opacity: 0.3; cursor: not-allowed; }
}

/* ── 响应式 ── */
@media (max-width: 900px) {
  .tutor-layout { flex-direction: column; }
  .tutor-left { width: 100%; min-width: auto; max-height: 300px; }
  .chat-window { height: 400px; }
}
@media (max-width: 640px) {
  .ai-section { padding: 60px 16px; }
}
</style>
