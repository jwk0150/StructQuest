<template>
  <div class="chat-page-container">
    <!-- 左侧：数字人 -->
    <div class="teacher-panel">
      <div class="teacher-visual">
        <DigitalTeacher
          ref="digitalTeacherRef"
          :is-speaking="isSpeaking"
          :volume="currentVolume"
          :voice-key="voiceKey"
          :avatar-key="avatarKey"
          :is-processing="isTyping"
          :iflytek-config="iflytekConfig"
          @loaded="onTeacherLoaded"
          @error="onTeacherError"
        />
      </div>
      <div class="teacher-ctrls">
        <button :class="['ctrl-btn', { active: ttsMode === 'edge_tts' }]" @click="setTtsMode('edge_tts')">🎵 Edge</button>
        <button :class="['ctrl-btn', { active: ttsMode === 'iflytek' }]" :disabled="!iflytekAvailable" @click="setTtsMode('iflytek')">🧑 讯飞</button>
        <select v-if="ttsMode === 'edge_tts'" v-model="voiceKey" class="voice-sel">
          <option value="xiaoxiao">温柔女声</option>
          <option value="yunxi">阳光男声</option>
          <option value="xiaoyi">知性女声</option>
          <option value="yunyang">沉稳男声</option>
        </select>
        <span class="conn-status"><span :class="['s-dot', isConnected ? 'on' : 'off']"></span>{{ isConnected ? '已连接' : '等待' }}</span>
        <el-button link class="hist-btn" @click="showHistory = !showHistory">📋 历史</el-button>
      </div>
    </div>

    <!-- 右侧：聊天 -->
    <main class="chat-main">
      <div class="messages-container" ref="messageBox">
        <div v-if="messages.length === 0" class="welcome-screen">
          <div class="ai-logo">◈</div>
          <h2>有什么我可以帮你的吗？</h2>
          <div class="suggested-prompts">
            <div v-for="p in suggestedPrompts" :key="p" class="prompt-card" @click="inputMsg = p; sendMsg()">{{ p }}</div>
          </div>
        </div>

        <div v-for="(msg, i) in messages" :key="i" class="message-wrapper" :class="msg.role">
          <div class="message-avatar">
            <div v-if="msg.role === 'ai'" class="ai-avatar">◈</div>
            <el-avatar v-else :size="32" src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" />
          </div>
          <div class="message-content">
            <div class="sender-name">{{ msg.role === 'ai' ? 'StructQuest AI' : '你' }}</div>
            <div class="bubble">
              <div v-if="msg.role === 'ai'" class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
              <div v-else class="text-content">{{ msg.content }}</div>
            </div>
            <div v-if="msg.role === 'ai'" class="message-actions">
              <el-button link :icon="CopyDocument" @click="copyText(msg.content)">复制</el-button>
              <el-button link :icon="Refresh">重新生成</el-button>
            </div>
          </div>
        </div>
        <div v-if="isTyping" class="message-wrapper ai">
          <div class="message-avatar"><div class="ai-avatar">◈</div></div>
          <div class="message-content">
            <div class="sender-name">StructQuest AI</div>
            <div class="bubble"><div class="typing-indicator"><span></span><span></span><span></span></div></div>
          </div>
        </div>
      </div>

      <footer class="chat-input-area">
        <div class="input-container">
          <el-input v-model="inputMsg" type="textarea" :rows="1" autosize placeholder="问问 AI 关于数据结构的问题..." @keydown.enter.prevent="sendMsg" />
          <el-button type="primary" class="send-btn" :disabled="!inputMsg.trim() || isTyping" @click="sendMsg"><el-icon><Top /></el-icon></el-button>
        </div>
      </footer>
    </main>

    <!-- 聊天历史抽屉 -->
    <transition name="drawer">
      <div v-if="showHistory" class="history-drawer">
        <div class="hist-head">
          <span>聊天记录</span>
          <el-button link @click="createNewChat"><el-icon><Plus /></el-icon>新建</el-button>
          <el-button link @click="showHistory = false">✕</el-button>
        </div>
        <div class="hist-list">
          <div v-if="chatHistory.length === 0" class="empty-hint">暂无记录</div>
          <div v-for="c in chatHistory" :key="c.id" class="hist-item" :class="{ active: currentChatId === c.id }" @click="selectChat(c.id); showHistory = false">
            <span class="hist-title">{{ c.title }}</span>
            <el-button link size="small" @click.stop="deleteChat(c.id, $event)"><Delete /></el-button>
          </div>
        </div>
      </div>
    </transition>
    <div v-if="showHistory" class="drawer-mask" @click="showHistory = false"></div>

    <audio ref="audioRef" @ended="isSpeaking = false" @play="isSpeaking = true"></audio>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onUnmounted } from 'vue'
import {
  Plus, CopyDocument, Refresh,
  Top, Delete
} from '@element-plus/icons-vue'
import { useSessionStore } from '../../store/session'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import DOMPurify from 'dompurify'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getStorage, STORAGE_KEYS } from '../../utils/storage'
import DigitalTeacher from '../../components/DigitalTeacher/index.vue'

const sessionStore = useSessionStore()
const userName = computed(() => sessionStore.user?.username || '学霸同学')

const inputMsg = ref('')
const isTyping = ref(false)
const currentChatId = ref(null)
const messageBox = ref(null)
const audioRef = ref(null)
const socket = ref(null)

// ═══════ 数字人 ═══════
const showHistory = ref(false)
const showDigitalTeacher = ref(true)
const digitalTeacherRef = ref(null)
const voiceKey = ref('xiaoxiao')
const avatarKey = ref('teacher_female')
const ttsMode = ref('iflytek')
const isSpeaking = ref(false)
const currentVolume = ref(0)
const iflytekAvailable = ref(false)
const iflytekConfig = ref({})
const isConnected = ref(false)

const connectionLabel = computed(() => {
  if (isConnected.value && ttsMode.value === 'iflytek' && iflytekAvailable.value) return '数字人已连接'
  if (isConnected.value) return 'AI 已就绪'
  return '等待连接...'
})

const chatHistory = ref([])
const isLoadingHistory = ref(false)
const messages = ref([])

const suggestedPrompts = [
  '请解释一下什么是时间复杂度？',
  '用比喻的方法讲讲栈和队列的区别',
  '如何判断一个链表是否有环？',
  '写一个冒泡排序的 Python 示例'
]

function getAuthToken() {
  const token = getStorage(STORAGE_KEYS.TOKEN)
  return token ? `Bearer ${token}` : ''
}

// ═══════ 聊天 API ═══════
async function loadChatSessions() {
  if (!sessionStore.isAuthenticated) return
  isLoadingHistory.value = true
  try {
    const r = await fetch('/api/chat/sessions', { headers: { 'Authorization': getAuthToken() } })
    if (r.ok) {
      const d = await r.json()
      chatHistory.value = d.map(s => ({ id: s.id, title: s.title || '新对话', message_count: s.message_count, created_at: s.created_at }))
      if (d.length > 0 && !currentChatId.value) await selectChat(d[0].id)
    }
  } catch (e) { console.error(e)
  } finally { isLoadingHistory.value = false }
}

async function loadMessages(sessionId) {
  if (!sessionId) return
  try {
    const r = await fetch(`/api/chat/sessions/${sessionId}/messages`, { headers: { 'Authorization': getAuthToken() } })
    if (r.ok) {
      const d = await r.json()
      messages.value = d.map(m => ({ role: m.role === 'assistant' ? 'ai' : m.role, content: m.content, id: m.id }))
    } else messages.value = []
  } catch (e) { messages.value = [] }
}

async function saveMessageToDB(sessionId, content, role = 'user') {
  try {
    await fetch(`/api/chat/sessions/${sessionId}/messages`, {
      method: 'POST', headers: { 'Authorization': getAuthToken(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, role }),
    })
  } catch (e) {}
}

async function createNewChat() {
  try {
    const r = await fetch('/api/chat/sessions', {
      method: 'POST', headers: { 'Authorization': getAuthToken(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: '新对话' }),
    })
    if (r.ok) {
      const s = await r.json()
      chatHistory.value.unshift({ id: s.id, title: s.title, message_count: 0, created_at: s.created_at })
      currentChatId.value = s.id; messages.value = []
      ElMessage.success('新建对话成功')
    }
  } catch (e) { ElMessage.error('创建失败') }
}

async function deleteChat(sessionId, event) {
  event.stopPropagation()
  try {
    await ElMessageBox.confirm('确定要删除吗？', '确认', { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' })
    const r = await fetch(`/api/chat/sessions/${sessionId}`, { method: 'DELETE', headers: { 'Authorization': getAuthToken() } })
    if (r.ok) {
      chatHistory.value = chatHistory.value.filter(c => c.id !== sessionId)
      if (currentChatId.value === sessionId) {
        if (chatHistory.value.length > 0) await selectChat(chatHistory.value[0].id)
        else { currentChatId.value = null; messages.value = [] }
      }
      ElMessage.success('已删除')
    }
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}

async function selectChat(sessionId) { currentChatId.value = sessionId; await loadMessages(sessionId); scrollToBottom() }

// ═══════ WebSocket ═══════
function initWebSocket() {
  const p = location.protocol === 'https:' ? 'wss:' : 'ws:'
  socket.value = new WebSocket(`${p}//${location.host}/ws/chat`)
  socket.value.onopen = () => { isConnected.value = true }
  socket.value.onclose = () => { isConnected.value = false; setTimeout(initWebSocket, 5000) }
  socket.value.onerror = () => { isConnected.value = false }

  socket.value.onmessage = async (e) => {
    const d = JSON.parse(e.data)
    if (digitalTeacherRef.value?.handleWsMessage) digitalTeacherRef.value.handleWsMessage(d)

    if (d.type === 'chunk') {
      const last = messages.value[messages.value.length - 1]
      if (last?.role === 'ai') last.content += (d.content || '')
      else messages.value.push({ role: 'ai', content: d.content || '' })
      scrollToBottom()
    } else if (d.type === 'done') {
      isTyping.value = false; isSpeaking.value = false
      const last = messages.value[messages.value.length - 1]
      if (last?.role === 'ai' && currentChatId.value && last.content) await saveMessageToDB(currentChatId.value, last.content, 'ai')
      if (d.full_content && ttsMode.value === 'iflytek' && digitalTeacherRef.value?.speakText) digitalTeacherRef.value.speakText(d.full_content)
    } else if (d.type === 'tts_audio') playAudio(d)
    else if (d.type === 'error' || d.error) {
      isTyping.value = false; isSpeaking.value = false
      const err = d.message || d.error
      const last = messages.value[messages.value.length - 1]
      if (last?.role === 'ai') last.content = '⚠️ ' + err
      else messages.value.push({ role: 'ai', content: '⚠️ ' + err })
    }
  }
}

async function sendMsg() {
  if (!inputMsg.value.trim() || isTyping.value) return
  if (!currentChatId.value) { await createNewChat(); await new Promise(r => setTimeout(r, 300)) }
  const t = inputMsg.value
  messages.value.push({ role: 'user', content: t }); inputMsg.value = ''; isTyping.value = true
  await saveMessageToDB(currentChatId.value, t, 'user')
  if (socket.value?.readyState === WebSocket.OPEN) {
    socket.value.send(JSON.stringify({
      session_id: currentChatId.value,
      messages: messages.value.filter(m => m.content).map(m => ({ role: m.role === 'ai' ? 'assistant' : 'user', content: m.content })),
      enable_tts: true, tts_mode: ttsMode.value, voice: voiceKey.value, avatar: avatarKey.value,
    }))
    messages.value.push({ role: 'ai', content: '' })
  } else { isTyping.value = false; ElMessage.warning('连接断开，重连中...') }
  scrollToBottom()
}

// ═══════ 数字人控制 ═══════
function setTtsMode(m) {
  ttsMode.value = m
  if (m === 'iflytek' && digitalTeacherRef.value?.startIflytek) digitalTeacherRef.value.startIflytek()
  else if (digitalTeacherRef.value?.stopIflytek) digitalTeacherRef.value.stopIflytek()
}
function onTeacherLoaded(ok) { console.log('[Chat] 数字人:', ok ? 'OK' : 'FAIL') }
function onTeacherError(err) { console.warn('[Chat] 数字人错误:', err) }

function playAudio(d) {
  if (!audioRef.value) return
  let s = ''
  if (d.audio_url) s = d.audio_url.startsWith('http') ? d.audio_url : d.audio_url.startsWith('/') ? d.audio_url : `/static/${d.audio_url}`
  else if (d.audio_base64) s = `data:audio/mp3;base64,${d.audio_base64}`
  if (!s) return
  audioRef.value.src = s; audioRef.value.load(); audioRef.value.play().catch(() => {})
}

function scrollToBottom() { nextTick(() => { if (messageBox.value) messageBox.value.scrollTop = messageBox.value.scrollHeight }) }
function copyText(c) { navigator.clipboard.writeText(c).then(() => ElMessage.success('已复制')).catch(() => {}) }

// ═══════ Markdown ═══════
try { marked.setOptions({ highlight(code, lang) { if (lang && hljs.getLanguage(lang)) return hljs.highlight(code, { language: lang }).value; return hljs.highlightAuto(code).value }, breaks: true }) } catch (e) {}
const renderMarkdown = (c) => c ? DOMPurify.sanitize(marked.parse(c)) : ''

// ═══════ Init ═══════
onMounted(async () => {
  initWebSocket()
  if (sessionStore.isAuthenticated) await loadChatSessions()
  scrollToBottom()
  fetch('/api/iflytek/status').then(r => r.json()).then(d => {
    iflytekAvailable.value = d.available === true
    if (d.config) iflytekConfig.value = d.config
    ttsMode.value = iflytekAvailable.value ? 'iflytek' : 'edge_tts'
  }).catch(() => { ttsMode.value = 'edge_tts' })
})
onUnmounted(() => { if (socket.value) socket.value.close() })
</script>

<style lang="scss" scoped>
.chat-page-container {
  display: flex;
  height: calc(100vh - 64px);
  background: var(--bg-color);
  overflow: hidden;
}

/* ═══════════ 左侧：数字人 ═══════════ */
.teacher-panel {
  width: 280px; min-width: 280px;
  background: linear-gradient(180deg, #0f0f2e 0%, #1a1040 50%, #0d1b2a 100%);
  display: flex; flex-direction: column;
}
.teacher-visual {
  flex: 1; overflow: hidden; min-height: 0;
}
.teacher-ctrls {
  padding: 8px 10px;
  display: flex; flex-direction: column; gap: 5px;
  border-top: 1px solid rgba(255,255,255,0.08);
  .ctrl-btn {
    flex: 1; height: 28px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.12);
    background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.7); font-size: 11px; font-weight: 600; cursor: pointer;
    transition: all .2s; font-family: inherit;
    &:hover:not(:disabled) { background: rgba(255,255,255,0.12); color: #fff; }
    &.active { background: var(--color-primary); border-color: transparent; color: #fff; }
    &:disabled { opacity: .3; cursor: not-allowed; }
  }
  .voice-sel {
    height: 26px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.12);
    background: rgba(255,255,255,0.06); color: #fff; font-size: 11px; padding: 0 6px; outline: none;
    option { color: #333; }
  }
  .conn-status { display: flex; align-items: center; gap: 5px; font-size: 10px; color: rgba(255,255,255,0.5); }
  .s-dot { width: 6px; height: 6px; border-radius: 50%;
    &.on { background: #22c55e; box-shadow: 0 0 5px rgba(34,197,94,0.4); }
    &.off { background: #6b7280; }
  }
  .hist-btn { color: rgba(255,255,255,0.5); font-size: 12px; justify-content: flex-start; padding: 4px 0; }
}

/* ═══════════ 右侧：聊天 ═══════════ */
.chat-main {
  flex: 1; display: flex; flex-direction: column; background: white; min-width: 0;
}
.messages-container {
  flex: 1; overflow-y: auto; padding: 30px 0;
  display: flex; flex-direction: column; gap: 24px;
}
.welcome-screen {
  max-width: 560px; margin: 60px auto; text-align: center;
  .ai-logo { font-size: 44px; color: var(--color-primary); margin-bottom: 20px; }
  h2 { font-size: 22px; margin-bottom: 32px; }
  .suggested-prompts {
    display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
    .prompt-card { padding: 14px; border: 1px solid var(--border-color); border-radius: 10px; font-size: 13px; color: var(--text-secondary); cursor: pointer; transition: all .2s;
      &:hover { background: var(--bg-secondary); border-color: var(--color-primary); }
    }
  }
}
.message-wrapper {
  max-width: 760px; margin: 0 auto; width: 90%; display: flex; gap: 16px;
  &.user { flex-direction: row-reverse;
    .bubble { background: var(--bg-secondary); border-radius: 16px 4px 16px 16px; }
    .sender-name { text-align: right; }
  }
  .message-avatar { flex-shrink: 0;
    .ai-avatar { width: 30px; height: 30px; background: var(--color-primary); color: white; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; }
  }
  .message-content { flex: 1; max-width: 80%;
    .sender-name { font-size: 11px; font-weight: 600; color: var(--text-tertiary); margin-bottom: 4px; padding: 0 4px; }
    .bubble { padding: 10px 14px; border-radius: 4px 16px 16px 16px; font-size: 14px; line-height: 1.6; color: var(--text-main); }
    .message-actions { display: flex; gap: 10px; margin-top: 6px; .el-button { font-size: 11px; color: var(--text-tertiary); padding: 0; } }
  }
}
.chat-input-area {
  padding: 16px 24px 20px; max-width: 760px; margin: 0 auto; width: 100%;
  .input-container {
    background: white; border: 1px solid var(--border-color); border-radius: 16px; padding: 6px 10px;
    display: flex; align-items: flex-end; gap: 8px; box-shadow: var(--shadow-md);
    :deep(.el-textarea__inner) { border: none; box-shadow: none !important; padding: 8px; font-size: 14px; max-height: 180px; }
    .send-btn { width: 34px; height: 34px; border-radius: 8px; padding: 0; flex-shrink: 0; margin-bottom: 2px; }
  }
}
.typing-indicator { display: flex; gap: 4px; padding: 4px 0;
  span { width: 6px; height: 6px; background: var(--text-tertiary); border-radius: 50%; animation: typing 1.4s infinite ease-in-out;
    &:nth-child(1){animation-delay:0s} &:nth-child(2){animation-delay:.2s} &:nth-child(3){animation-delay:.4s}
  }
}
@keyframes typing { 0%,80%,100%{transform:scale(0);opacity:.3} 40%{transform:scale(1);opacity:1} }

/* ═══════════ 聊天历史抽屉 ═══════════ */
.history-drawer {
  position: fixed; top: 0; right: 0; width: 320px; height: 100vh;
  background: var(--bg-color); box-shadow: -4px 0 24px rgba(0,0,0,0.12);
  z-index: 100; display: flex; flex-direction: column;
}
.hist-head {
  display: flex; align-items: center; gap: 8px; padding: 16px 20px;
  border-bottom: 1px solid var(--border-color); font-weight: 700; font-size: 15px;
  .el-button { margin-left: auto; }
}
.hist-list {
  flex: 1; overflow-y: auto; padding: 8px;
  .empty-hint { text-align: center; color: var(--text-tertiary); padding: 40px; font-size: 13px; }
  .hist-item {
    display: flex; align-items: center; gap: 8px; padding: 10px 12px; border-radius: 8px; cursor: pointer; transition: all .2s;
    .hist-title { flex: 1; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text-secondary); }
    &:hover { background: var(--bg-secondary); }
    &.active { background: rgba(var(--color-primary-rgb), 0.06); .hist-title { color: var(--color-primary); font-weight: 600; } }
  }
}
.drawer-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.3); z-index: 99; }
.drawer-enter-active, .drawer-leave-active { transition: transform .3s ease; }
.drawer-enter-from, .drawer-leave-to { transform: translateX(100%); }
</style>
