<template>
  <div class="chat-page-container" :class="{ 'both-collapsed': leftCollapsed && rightCollapsed }">
    <!-- 折叠按钮（放在容器外，折叠后仍可见可点） -->
    <button class="collapse-btn left-toggle" :class="{ 'at-edge': leftCollapsed }" @click="leftCollapsed = !leftCollapsed" :title="leftCollapsed ? '展开侧栏' : '折叠侧栏'">
      <el-icon><ArrowLeft v-if="!leftCollapsed" /><ArrowRight v-else /></el-icon>
    </button>
    <button class="collapse-btn right-toggle" :class="{ 'at-edge': rightCollapsed }" @click="rightCollapsed = !rightCollapsed" :title="rightCollapsed ? '展开侧栏' : '折叠侧栏'">
      <el-icon><ArrowRight v-if="!rightCollapsed" /><ArrowLeft v-else /></el-icon>
    </button>

    <!-- ═══════ 左侧：数字人 + 状态卡 ═══════ -->
    <aside class="left-panel" :class="{ collapsed: leftCollapsed }">

      <transition name="fade">
        <div v-show="!leftCollapsed" class="left-content">
          <!-- 数字人区域 -->
          <div class="teacher-section">
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
            <!-- 语音气泡 -->
            <transition name="bubble">
              <div v-if="speechText" class="speech-bubble">{{ speechText }}</div>
            </transition>
          </div>

          <!-- 学习状态卡 -->
          <div class="stats-card">
            <div class="stats-head">
              <span class="online-dot"></span>
              <span>{{ connectionLabel }}</span>
              <button class="tts-pill" :class="{ active: ttsMode === 'iflytek' }" :disabled="!iflytekAvailable" @click="setTtsMode('iflytek')">🧑 讯飞</button>
            </div>
            <div class="stats-body">
              <div class="stats-label">今日陪伴</div>
              <div class="stats-value"><span class="big">{{ todayStudyMinutes }}</span><span class="unit">分钟</span></div>
              <div class="stats-tip">{{ statsTip }}</div>
            </div>
            <div class="stats-mascot">🐣</div>
          </div>
        </div>
      </transition>
    </aside>

    <!-- ═══════ 中间：聊天 ═══════ -->
    <main class="chat-main">
      <div class="messages-container" ref="messageBox">
        <!-- 欢迎屏（无消息时） -->
        <div v-if="messages.length === 0" class="welcome-screen">
          <h1 class="welcome-title">你好，{{ userName }} <span class="wave">✨</span></h1>
          <p class="welcome-sub">今天想学点什么呢？我可以帮你讲知识、写代码、分析问题、出题练习惯！</p>
          <div class="suggested-prompts">
            <div v-for="p in suggestedPrompts" :key="p" class="prompt-chip" @click="inputMsg = p; sendMsg()">
              {{ p }}
            </div>
            <button class="refresh-prompts" @click="refreshPrompts">
              <el-icon><Refresh /></el-icon> 换一换
            </button>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-for="(msg, i) in messages" :key="i" class="message-wrapper" :class="[msg.role, { 'both-collapsed': leftCollapsed && rightCollapsed }]" :data-msg-index="i">
          <div class="message-avatar">
            <div v-if="msg.role === 'ai'" class="ai-avatar">◈</div>
            <el-avatar v-else :size="32" src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" />
          </div>
          <div class="message-content">
            <div v-if="msg.role === 'user' || msg.content" class="bubble">
              <div v-if="msg.role === 'ai' && msg.content" class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
              <div v-else-if="msg.role === 'user'" class="text-content">{{ msg.content }}</div>
            </div>

            <!-- v5 结构化卡片 -->
            <div v-if="msg.role === 'ai' && msg.cards && msg.cards.length" class="message-cards-wrapper">
              <MessageCardRenderer
                :cards="msg.cards"
                @quiz-submit="(r) => onQuizSubmit(r)"
                @navigate="(n) => onCardNavigate(n)"
                @action="(a) => onCardAction(a)"
              />
            </div>

            <!-- 多模态资源卡片 -->
            <div v-if="msg.attachments && msg.attachments.length" class="resource-attachments">
              <div v-for="(att, ai2) in msg.attachments" :key="ai2" class="resource-card" :class="att.type">
                <div class="res-card-head" @click="toggleResource(att)">
                  <span class="res-icon">{{ resourceMeta[att.type]?.icon || '📎' }}</span>
                  <span class="res-title">{{ att.title || resourceMeta[att.type]?.label || att.type }}</span>
                  <span class="res-format-tag">{{ resourceMeta[att.type]?.label || att.format }}</span>
                  <button class="res-fullscreen-btn" title="全屏查看" @click.stop="openFullscreen(att)">
                    <el-icon><FullScreen /></el-icon>
                  </button>
                  <el-icon class="res-toggle" :class="{ expanded: att._expanded }"><ArrowDown /></el-icon>
                </div>
                <transition name="res-expand">
                  <div v-show="att._expanded" class="res-card-body">
                    <svg v-if="att.type === 'mindmap'" class="mindmap-container" :ref="el => setMindmapRef(el, att)"></svg>
                    <pre v-else-if="att.type === 'code_example'" class="code-block"><code>{{ att.content_text }}</code></pre>
                    <div v-else-if="att.type === 'quiz'" class="quiz-container">
                      <div v-for="(q, qi) in safeParseQuiz(att.content_text)" :key="qi" class="quiz-item">
                        <div class="quiz-q">第{{ q.id || qi+1 }}题：{{ q.question }}</div>
                        <div v-if="q.options && q.options.length" class="quiz-opts">
                          <div v-for="(opt, oi) in q.options" :key="oi" class="quiz-opt">{{ opt }}</div>
                        </div>
                        <el-collapse>
                          <el-collapse-item title="查看答案">
                            <p class="quiz-ans"><strong>答案：</strong>{{ q.answer }}</p>
                            <p v-if="q.explanation" class="quiz-exp">{{ q.explanation }}</p>
                          </el-collapse-item>
                        </el-collapse>
                      </div>
                    </div>
                    <div v-else-if="att.type === 'animation'" class="animation-container">
                      <video v-if="att.file_url || att.preview_url" :src="att.file_url || att.preview_url" controls class="anim-video"></video>
                      <div v-else class="anim-fallback">
                        <div class="anim-notice">⚠️ 视频渲染失败（服务端 Manim 环境异常）</div>
                        <div v-if="att.format === 'markdown' && att.content_text" class="markdown-body" v-html="renderMarkdown(att.content_text)"></div>
                        <pre v-else class="code-block"><code>{{ att.content_text }}</code></pre>
                      </div>
                    </div>
                    <div v-else-if="att.type === 'notes' || att.type === 'ppt_outline'" class="markdown-body" v-html="renderMarkdown(att.content_text)"></div>
                    <pre v-else class="code-block"><code>{{ att.content_text || JSON.stringify(att, null, 2) }}</code></pre>
                    <div class="res-actions">
                      <el-button link size="small" @click="copyText(att.content_text || '')">复制内容</el-button>
                      <span class="res-reason" v-if="att.generated_for">{{ att.generated_for }}</span>
                    </div>
                  </div>
                </transition>
              </div>
            </div>

            <!-- AI 消息操作 -->
            <div v-if="msg.role === 'ai' && msg.content" class="message-actions">
              <el-button link :icon="Pointer" @click="rateMessage(i, 'up')">有帮助</el-button>
              <el-button link :icon="CircleClose" @click="rateMessage(i, 'down')">没必要</el-button>
              <el-button link :icon="CopyDocument" @click="copyText(msg.content)">复制</el-button>
              <el-button link :icon="Refresh" @click="regenerate(i)">重新回答</el-button>
              <el-button link :icon="Star">收藏</el-button>
            </div>
          </div>
        </div>

        <!-- 打字指示器 -->
        <div v-if="isTyping && !pendingAiHasContent" class="message-wrapper ai" :class="{ 'both-collapsed': leftCollapsed && rightCollapsed }">
          <div class="message-avatar"><div class="ai-avatar">◈</div></div>
          <div class="message-content">
            <div class="bubble"><div class="typing-indicator"><span></span><span></span><span></span></div></div>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <footer class="chat-input-area">
        <div class="input-container">
          <el-input
            v-model="inputMsg"
            type="textarea"
            :rows="1"
            autosize
            placeholder="有问题尽管问我..."
            @keydown.enter.prevent="sendMsg"
          />
          <div class="input-toolbar">
            <button class="tool-btn" title="上传代码"><el-icon><Plus /></el-icon></button>
            <button class="tool-btn" title="语音输入"><el-icon><Microphone /></el-icon></button>
            <button class="send-btn" :disabled="!inputMsg.trim() || isTyping" @click="sendMsg">
              <el-icon><Top /></el-icon>
            </button>
          </div>
        </div>
      </footer>
    </main>

    <!-- ═══════ 右侧：历史 + 目录 ═══════ -->
    <aside class="right-panel" :class="{ collapsed: rightCollapsed }">

      <transition name="fade">
        <div v-show="!rightCollapsed" class="right-content">
          <!-- 对话历史 -->
          <section class="right-section history-section">
            <div class="section-head">
              <span class="section-title">对话历史</span>
              <button class="head-btn primary" @click="createNewChat">
                <el-icon><Plus /></el-icon> 新建对话
              </button>
            </div>
            <div class="section-body">
              <div v-if="isLoadingHistory" class="empty-hint">加载中…</div>
              <div v-else-if="chatHistory.length === 0" class="empty-hint">暂无记录</div>
              <div v-else class="hist-groups">
                <div v-for="group in groupedHistory" :key="group.label" class="hist-group">
                  <div class="group-label">{{ group.label }}</div>
                  <div
                    v-for="c in group.sessions"
                    :key="c.id"
                    class="hist-item"
                    :class="{ active: currentChatId === c.id }"
                    @click="selectChat(c.id)"
                  >
                    <div class="hist-info">
                      <div class="hist-title">{{ c.title }}</div>
                      <div class="hist-meta">
                        <span v-if="c.message_count">{{ c.message_count }}条对话</span>
                      </div>
                    </div>
                    <div class="hist-time">{{ formatTime(c.created_at) }}</div>
                    <el-button link size="small" class="del-btn" @click.stop="deleteChat(c.id, $event)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- 本次对话目录 -->
          <section class="right-section toc-section">
            <div class="section-head">
              <span class="section-title">本次对话目录</span>
            </div>
            <div class="section-body">
              <div v-if="currentToc.length === 0" class="empty-hint">对话进行时会自动生成</div>
              <div v-else class="toc-list">
                <div
                  v-for="(item, i) in currentToc"
                  :key="i"
                  class="toc-item"
                  :class="{ active: activeTocIdx === i }"
                  @click="scrollToTocItem(item)"
                >
                  <span class="toc-icon">{{ item.icon }}</span>
                  <span class="toc-title">{{ item.title }}</span>
                  <span class="toc-idx">{{ i + 1 }}</span>
                </div>
              </div>
            </div>
          </section>
        </div>
      </transition>
    </aside>

    <!-- ═══════ 全屏资源查看 ═══════ -->
    <teleport to="body">
      <transition name="fullscreen-fade">
        <div v-if="fullscreenAtt" class="fullscreen-overlay" @click.self="closeFullscreen">
          <div class="fullscreen-panel">
            <div class="fullscreen-head">
              <span class="fullscreen-icon">{{ resourceMeta[fullscreenAtt.type]?.icon || '📎' }}</span>
              <span class="fullscreen-title">{{ fullscreenAtt.title || resourceMeta[fullscreenAtt.type]?.label || fullscreenAtt.type }}</span>
              <button class="fullscreen-close" @click="closeFullscreen">
                <el-icon><CircleClose /></el-icon>
              </button>
            </div>
            <div class="fullscreen-body">
              <svg v-if="fullscreenAtt.type === 'mindmap'" class="mindmap-container fullscreen-mindmap" :ref="el => setMindmapRef(el, fullscreenAtt)"></svg>
              <pre v-else-if="fullscreenAtt.type === 'code_example'" class="code-block fullscreen-code"><code>{{ fullscreenAtt.content_text }}</code></pre>
              <video v-else-if="fullscreenAtt.type === 'animation' && (fullscreenAtt.file_url || fullscreenAtt.preview_url)" :src="fullscreenAtt.file_url || fullscreenAtt.preview_url" controls class="fullscreen-video"></video>
              <div v-else-if="fullscreenAtt.type === 'notes' || fullscreenAtt.type === 'ppt_outline'" class="markdown-body fullscreen-markdown" v-html="renderMarkdown(fullscreenAtt.content_text)"></div>
              <pre v-else class="code-block fullscreen-code"><code>{{ fullscreenAtt.content_text || JSON.stringify(fullscreenAtt, null, 2) }}</code></pre>
            </div>
            <div class="fullscreen-foot">
              <el-button @click="copyText(fullscreenAtt.content_text || '')">复制内容</el-button>
              <el-button @click="closeFullscreen">关闭</el-button>
            </div>
          </div>
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onUnmounted } from 'vue'
import {
  Plus, CopyDocument, Refresh, Top, Delete, ArrowDown,
  ArrowLeft, ArrowRight, Microphone, Pointer, CircleClose, Star, FullScreen,
} from '@element-plus/icons-vue'
import { useSessionStore } from '../../store/session'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import DOMPurify from 'dompurify'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getStorage, STORAGE_KEYS } from '../../utils/storage'
import DigitalTeacher from '../../components/DigitalTeacher/index.vue'
import MessageCardRenderer from '../../components/ChatCards/MessageCardRenderer.vue'

const sessionStore = useSessionStore()
const userName = computed(() => sessionStore.user?.username || 'master')

const inputMsg = ref('')
const isTyping = ref(false)
const currentChatId = ref(null)
const messageBox = ref(null)
const socket = ref(null)
let reconnectTimer = null
let manuallyClosedSocket = false

// ═══════ 数字人 ═══════
const digitalTeacherRef = ref(null)
const voiceKey = ref('xiaoxiao')
const avatarKey = ref('teacher_female')
const ttsMode = ref('iflytek')
const isSpeaking = ref(false)
const currentVolume = ref(0)
const iflytekAvailable = ref(false)
const iflytekConfig = ref({})
const isConnected = ref(false)
const speechText = ref('嗨~ 我是你的AI导师小灵，有什么问题都可以问我哦！')

const connectionLabel = computed(() => {
  if (isConnected.value && ttsMode.value === 'iflytek' && iflytekAvailable.value) return '数字人已连接'
  if (isConnected.value) return 'AI 已就绪'
  return '等待连接...'
})

// ═══════ 侧边栏折叠 ═══════
const leftCollapsed = ref(false)
const rightCollapsed = ref(false)

// ═══════ 今日学习统计（从 localStorage 取，没有则显示默认值）═══════
const todayStudyMinutes = ref(parseInt(localStorage.getItem('todayStudyMinutes') || '42', 10))
const statsTip = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深啦，早点休息哦~'
  if (h < 12) return '新的一天，加油！'
  if (h < 18) return '下午继续努力~'
  if (h < 22) return '学习路上，你并不孤单。'
  return '夜深啦，注意休息~'
})

// ═══════ 聊天历史 ═══════
const chatHistory = ref([])
const isLoadingHistory = ref(false)
const messages = ref([])

// 多模态资源元数据
const resourceMeta = {
  mindmap:      { icon: '🧠', label: '思维导图' },
  code_example: { icon: '💻', label: '代码案例' },
  quiz:         { icon: '✏️', label: '练习题' },
  animation:    { icon: '🎬', label: '动画演示' },
  notes:        { icon: '📖', label: '学习讲义' },
  ppt_outline:  { icon: '📊', label: 'PPT大纲' },
}

// 卡片类型 → 图标（用于目录）
const CARD_ICONS = {
  knowledge: '📘',
  code: '💻',
  complexity: '📊',
  quiz: '📝',
  suggestion: '🎯',
  knowledge_graph: '🗺️',
  comparison: '⚖️',
  debug: '🔧',
  mermaid: '📐',
}

function getCardIcon(type) {
  return CARD_ICONS[type] || '📌'
}

function toggleResource(att) {
  att._expanded = !att._expanded
  if (att._expanded && att.type === 'mindmap' && !att._rendered) {
    nextTick(() => renderMindmap(att))
  }
}

// ═══════ 全屏查看资源 ═══════
const fullscreenAtt = ref(null)
function openFullscreen(att) {
  fullscreenAtt.value = att
  if (att.type === 'mindmap' && !att._expanded) {
    att._expanded = true
    nextTick(() => {
      if (!att._rendered) renderMindmap(att)
    })
  }
}
function closeFullscreen() {
  fullscreenAtt.value = null
}

function safeParseQuiz(text) {
  if (!text) return []
  try {
    const data = typeof text === 'string' ? JSON.parse(text) : text
    if (Array.isArray(data)) return data
    if (data.quiz_items) return data.quiz_items
    return []
  } catch { return [] }
}

function extractCode(text) {
  if (!text) return ''
  const m = text.match(/```python\s*\n([\s\S]*?)\n```/)
  return m ? m[1] : text
}

// ═══════ 建议问题（多组，可"换一换"）═══════
const allPrompts = [
  ['请解释一下什么是时间复杂度？', '用比喻的方法讲讲栈和队列的区别', '如何判断一个链表是否有环？', '写一个冒泡排序的 Python 示例'],
  ['二叉树和二叉搜索树有什么区别？', '什么是红黑树？为什么要用它？', 'Dijkstra 算法是怎么工作的？', '哈希表是怎么解决冲突的？'],
  ['讲讲动态规划的核心思想', '什么是 B+ 树？为什么数据库用它？', '并查集可以用来解决什么问题？', '什么是跳表？Redis 为什么用它？'],
  ['快速排序的 partition 过程', '讲讲 KMP 字符串匹配算法', '什么是布隆过滤器？', 'LRU 缓存是怎么实现的？'],
]
const promptIdx = ref(0)
const suggestedPrompts = computed(() => allPrompts[promptIdx.value])
function refreshPrompts() {
  promptIdx.value = (promptIdx.value + 1) % allPrompts.length
}

function getAuthToken() {
  const token = getStorage(STORAGE_KEYS.TOKEN)
  return token ? `Bearer ${token}` : ''
}

const currentUserId = computed(() => sessionStore.user?.id || null)

// ═══════ 历史记录 API ═══════
async function loadChatSessions(autoSelect = false) {
  if (!sessionStore.isAuthenticated) return
  isLoadingHistory.value = true
  try {
    const r = await fetch('/api/chat/sessions', { headers: { 'Authorization': getAuthToken() } })
    if (r.ok) {
      const d = await r.json()
      chatHistory.value = d.map(s => ({
        id: s.id,
        title: s.title || '新对话',
        message_count: s.message_count,
        created_at: s.created_at,
      }))
      if (autoSelect && chatHistory.value.length > 0 && !currentChatId.value) {
        const lastSession = chatHistory.value[0]
        currentChatId.value = lastSession.id
        await loadMessages(lastSession.id)
        scrollToBottom()
      }
    }
  } catch (e) {
    console.error('[Chat] 加载会话列表失败:', e)
  } finally {
    isLoadingHistory.value = false
  }
}

async function loadMessages(sessionId) {
  if (!sessionId) { messages.value = []; return }
  try {
    const r = await fetch(`/api/chat/sessions/${sessionId}/messages`, {
      headers: { 'Authorization': getAuthToken() },
    })
    if (r.ok) {
      const d = await r.json()
      messages.value = d.map(m => ({
        id: m.id,
        role: m.role,
        content: m.content || '',
        attachments: (m.attachments || []).map(a => ({ ...a, _expanded: false, _rendered: false })),
        cards: m.cards || null,
        _completed: true,  // 标记为已完成，防止后续 chunk 误更新
      }))
    } else {
      messages.value = []
    }
  } catch (e) {
    console.error('[Chat] 加载消息失败:', e)
    messages.value = []
  }
}

// 按今天/昨天/更早分组
const groupedHistory = computed(() => {
  const today = []
  const yesterday = []
  const earlier = []
  const now = new Date()
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const yesterdayStart = todayStart - 86400000
  chatHistory.value.forEach(s => {
    const t = new Date(s.created_at).getTime()
    if (t >= todayStart) today.push(s)
    else if (t >= yesterdayStart) yesterday.push(s)
    else earlier.push(s)
  })
  const result = []
  if (today.length) result.push({ label: '今天', sessions: today })
  if (yesterday.length) result.push({ label: '昨天', sessions: yesterday })
  if (earlier.length) result.push({ label: '更早', sessions: earlier })
  return result
})

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const sameDay = d.toDateString() === now.toDateString()
  if (sameDay) {
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
  }
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function createNewChat() {
  currentChatId.value = null
  messages.value = []
}

async function deleteChat(sessionId, event) {
  event.stopPropagation()
  try {
    await ElMessageBox.confirm('确定要删除这个会话吗？所有消息将被清除。', '确认删除', {
      confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning',
    })
    const r = await fetch(`/api/chat/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: { 'Authorization': getAuthToken() },
    })
    if (r.ok) {
      chatHistory.value = chatHistory.value.filter(c => c.id !== sessionId)
      if (currentChatId.value === sessionId) {
        currentChatId.value = null
        messages.value = []
      }
      ElMessage.success('已删除')
    } else {
      ElMessage.error('删除失败')
    }
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') ElMessage.error('删除失败')
  }
}

async function selectChat(sessionId) {
  currentChatId.value = sessionId
  await loadMessages(sessionId)
  scrollToBottom()
}

// ═══════ 本次对话目录（自动生成）═══════
const currentToc = computed(() => {
  const items = []
  messages.value.forEach((msg, mi) => {
    if (msg.role !== 'ai') return
    if (msg.cards && msg.cards.length) {
      msg.cards.forEach(card => {
        items.push({
          icon: card.icon || getCardIcon(card.type),
          title: card.title || '未命名',
          msgIndex: mi,
        })
      })
    } else if (msg.content) {
      const headings = msg.content.match(/^#{2,3}\s+(.+)$/gm) || []
      headings.forEach(h => {
        items.push({
          icon: '📌',
          title: h.replace(/^#+\s+/, '').trim(),
          msgIndex: mi,
        })
      })
    }
  })
  return items
})

const pendingAiHasContent = computed(() => {
  const last = messages.value[messages.value.length - 1]
  return !!(last?.role === 'ai' && !last._completed && last.content)
})

const activeTocIdx = ref(-1)
function scrollToTocItem(item) {
  // 找到对应的消息元素并滚动
  const el = messageBox.value?.querySelector(`[data-msg-index="${item.msgIndex}"]`)
  if (el && messageBox.value) {
    const boxTop = messageBox.value.getBoundingClientRect().top
    const elTop = el.getBoundingClientRect().top
    messageBox.value.scrollTo({ top: messageBox.value.scrollTop + (elTop - boxTop) - 20, behavior: 'smooth' })
  }
  const idx = currentToc.value.findIndex(t => t.msgIndex === item.msgIndex)
  activeTocIdx.value = idx
}

// ═══════ WebSocket ═══════
let currentRequestId = 0  // 用于防止重复 AI 消息：每次发送自增，chunk 只更新匹配 id 的占位

function getEventReqId(d) {
  const id = Number(d?.request_id ?? d?.req_id ?? currentRequestId)
  return Number.isFinite(id) && id > 0 ? id : currentRequestId
}

function isCurrentEvent(d) {
  const rawId = d?.request_id ?? d?.req_id
  return rawId == null || Number(rawId) === currentRequestId
}

function findAiMessage(reqId = currentRequestId, includeCompleted = true) {
  return [...messages.value].reverse().find(m => (
    m.role === 'ai' &&
    (m._reqId == null || m._reqId === reqId) &&
    (includeCompleted || !m._completed)
  ))
}

function ensureAiMessage(reqId = currentRequestId) {
  let msg = findAiMessage(reqId, false)
  if (!msg) {
    msg = { role: 'ai', content: '', _reqId: reqId, _completed: false }
    messages.value.push(msg)
  }
  return msg
}

function scheduleReconnect() {
  if (manuallyClosedSocket || reconnectTimer) return
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    initWebSocket()
  }, 5000)
}

function initWebSocket() {
  if (socket.value && [WebSocket.OPEN, WebSocket.CONNECTING].includes(socket.value.readyState)) return
  manuallyClosedSocket = false
  const p = location.protocol === 'https:' ? 'wss:' : 'ws:'
  socket.value = new WebSocket(`${p}//${location.host}/ws/chat`)

  socket.value.onopen = () => { isConnected.value = true }
  socket.value.onclose = () => {
    isConnected.value = false
    scheduleReconnect()
  }
  socket.value.onerror = () => { isConnected.value = false }

  socket.value.onmessage = async (e) => {
    let d
    try { d = JSON.parse(e.data) } catch { return }
    if (!isCurrentEvent(d)) return
    if (digitalTeacherRef.value?.handleWsMessage) digitalTeacherRef.value.handleWsMessage(d)

    const reqId = getEventReqId(d)
    if (d.type === 'chunk') {
      const target = ensureAiMessage(reqId)
      target.content += (d.content || '')
      scrollToBottom()
    } else if (d.type === 'done') {
      isTyping.value = false
      isSpeaking.value = false
      const target = findAiMessage(reqId, true)
      if (target) {
        target._completed = true
        if (d.full_content && (!target.content || target.content.length < d.full_content.length)) {
          target.content = d.full_content
        }
      }
      loadChatSessions()
      if (d.full_content && ttsMode.value === 'iflytek' && digitalTeacherRef.value?.speakText) {
        if (d.full_content.length >= 2000) {
          digitalTeacherRef.value.speakText(d.full_content)
        }
      }
    } else if (d.type === 'resource_done') {
      const res = d.resource || d.data || {}
      res._expanded = false
      res._rendered = false
      const target = findAiMessage(reqId, true) || ensureAiMessage(reqId)
      if (!target.attachments) target.attachments = []
      target.attachments.push(res)
      scrollToBottom()
    } else if (d.type === 'chat_session_created') {
      currentChatId.value = d.session_id
      await loadChatSessions()
    } else if (d.type === 'message_cards') {
      const cards = d.cards || []
      const target = findAiMessage(reqId, true) || ensureAiMessage(reqId)
      target.cards = cards
    } else if (d.type === 'error' || d.error) {
      isTyping.value = false
      isSpeaking.value = false
      const err = d.message || d.error || '未知错误'
      const target = findAiMessage(reqId, true) || ensureAiMessage(reqId)
      target.content = '⚠️ ' + err
      target._completed = true
    }
  }
}
async function sendMsg() {
  const text = inputMsg.value.trim()
  if (!text || isTyping.value) return
  if (!currentUserId.value) {
    ElMessage.warning('请先登录后再聊天')
    return
  }
  // 防御：若上一条是没填完的 AI 占位，先标完成，避免被本轮请求再次覆盖
  const last = messages.value[messages.value.length - 1]
  if (last?.role === 'ai' && !last._completed) {
    last._completed = true
  }
  // 自增请求 ID，标记本轮所有新消息
  const reqId = ++currentRequestId

  messages.value.push({ role: 'user', content: text, _reqId: reqId })
  inputMsg.value = ''
  isTyping.value = true
  const historyToSend = messages.value
    .filter(m => m.content && m.content.trim())
    .map(m => ({ role: m.role === 'ai' ? 'assistant' : 'user', content: m.content }))
  messages.value.push({ role: 'ai', content: '', _reqId: reqId })
  if (socket.value?.readyState === WebSocket.OPEN) {
    socket.value.send(JSON.stringify({
      request_id: reqId,
      session_id: currentChatId.value,
      user_id: currentUserId.value,
      messages: historyToSend,
      enable_tts: true,
      tts_mode: ttsMode.value,
      voice: voiceKey.value,
      avatar: avatarKey.value,
    }))
  } else {
    messages.value.pop()
    isTyping.value = false
    ElMessage.warning('连接断开，正在重连...')
    initWebSocket()
  }
  scrollToBottom()
}

function rateMessage(i, kind) {
  ElMessage.success(kind === 'up' ? '感谢反馈！' : '已收到，会继续优化')
}

function regenerate(i) {
  // 找到该 AI 消息之前最近的用户消息
  let userMsg = null
  for (let k = i - 1; k >= 0; k--) {
    if (messages.value[k].role === 'user') { userMsg = messages.value[k]; break }
  }
  if (!userMsg) return
  messages.value.splice(i, messages.value.length - i)  // 删除 AI + 之后所有
  inputMsg.value = userMsg.content
  sendMsg()
}

// ═══════ 数字人控制 ═══════
function setTtsMode(m) {
  ttsMode.value = m
  if (m === 'iflytek' && digitalTeacherRef.value?.startIflytek) digitalTeacherRef.value.startIflytek()
  else if (digitalTeacherRef.value?.stopIflytek) digitalTeacherRef.value.stopIflytek()
}
function onTeacherLoaded(ok) { console.log('[Chat] 数字人:', ok ? 'OK' : 'FAIL') }
function onTeacherError(err) { console.warn('[Chat] 数字人错误:', err) }

function scrollToBottom() {
  nextTick(() => { if (messageBox.value) messageBox.value.scrollTop = messageBox.value.scrollHeight })
}
function copyText(c) { navigator.clipboard.writeText(c).then(() => ElMessage.success('已复制')).catch(() => {}) }

function onQuizSubmit(result) {
  console.log('[Chat] 练习提交:', result)
  ElMessage.success(`得分: ${result.score}/${result.total}`)
}

function onCardNavigate(target) {
  if (!target?.topic) return
  inputMsg.value = `讲讲${target.topic}`
  sendMsg()
}

function onCardAction({ action, card }) {
  if (action?.action === 'copy' && action.target) {
    copyText(action.target)
  }
}

// 思维导图
const mindmapRefs = new Map()
function setMindmapRef(el, att) {
  if (el) {
    mindmapRefs.set(att, el)
    if (att._expanded && !att._rendered) {
      nextTick(() => renderMindmap(att))
    }
  }
}
function normalizeMindmapContent(raw, fallbackTitle = '思维导图') {
  let text = String(raw || '').trim()
  text = text.replace(/^```(?:markdown|markmap)?\s*/i, '').replace(/```$/i, '').trim()
  if (!text) return `# ${fallbackTitle}\n## 暂无内容`
  if (/^\s*#/m.test(text)) return text

  const lines = text.split(/\r?\n/).map(line => line.trim()).filter(Boolean)
  if (!lines.length) return `# ${fallbackTitle}\n## 暂无内容`

  const root = lines.shift().replace(/^[-*]\s*/, '') || fallbackTitle
  const md = [`# ${root}`]
  let hasSection = false

  lines.forEach((line) => {
    const clean = line.replace(/^[-*]\s*/, '')
    const pair = clean.match(/^(.{2,24})[：:]\s*(.+)$/)
    if (pair) {
      md.push(`## ${pair[1].trim()}`)
      md.push(`- ${pair[2].trim()}`)
      hasSection = true
    } else if (!hasSection || clean.length <= 16) {
      md.push(`## ${clean}`)
      hasSection = true
    } else {
      md.push(`- ${clean}`)
    }
  })

  return md.join('\n')
}

function escapeSvgText(text) {
  return String(text || '').replace(/[&<>"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]))
}

async function renderMindmap(att) {
  const el = mindmapRefs.get(att)
  if (!el || att._rendered) return
  att._rendered = true
  try {
    const { Transformer } = await import('markmap-lib')
    const { Markmap } = await import('markmap-view')
    const transformer = new Transformer()
    const markdown = normalizeMindmapContent(att.content_text, att.title || '思维导图')
    const { root, features } = transformer.transform(markdown)
    el.replaceChildren()
    if (features?.styles) transformer.getUsedAssets(features)
    const markmap = Markmap.create(el, { autoFit: true, duration: 300, maxWidth: 260, spacingHorizontal: 78, spacingVertical: 8 }, root)
    att._markmap = markmap
    setTimeout(() => markmap.fit(), 80)
  } catch (e) {
    el.innerHTML = `<text x="16" y="28" fill="#991b1b" font-size="13">导图渲染失败：${escapeSvgText(e.message || '未知错误')}</text>`
  }
}

// Markdown
try { marked.setOptions({ highlight(code, lang) { if (lang && hljs.getLanguage(lang)) return hljs.highlight(code, { language: lang }).value; return hljs.highlightAuto(code).value }, breaks: true }) } catch (e) {}
const renderMarkdown = (c) => c ? DOMPurify.sanitize(marked.parse(c)) : ''

// ═══════ Init ═══════
onMounted(async () => {
  initWebSocket()
  if (sessionStore.isAuthenticated) await loadChatSessions(true)
  scrollToBottom()
  fetch('/api/iflytek/status').then(r => r.json()).then(d => {
    iflytekAvailable.value = d.available === true
    if (d.config) iflytekConfig.value = d.config
  }).catch(() => {})
})
onUnmounted(() => {
  manuallyClosedSocket = true
  if (reconnectTimer) clearTimeout(reconnectTimer)
  reconnectTimer = null
  if (socket.value) socket.value.close()
})
</script>

<style lang="scss" scoped>
.chat-page-container {
  display: flex;
  height: calc(100vh - var(--topnav-height, 60px));
  background: #ffffff;
  overflow: hidden;
  position: relative;
}

/* ═══════════ 通用折叠按钮（容器级，折叠后仍可见可点） ═══════════ */
.collapse-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 22px; height: 56px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; z-index: 50;
  color: #9ca3af;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: left .3s ease, right .3s ease, color .2s, box-shadow .2s, border-color .2s;
  &:hover { color: #c84c5a; box-shadow: 0 2px 12px rgba(200,76,90,0.25); border-color: rgba(200,76,90,0.3); }
}
/* 展开时：紧贴面板外缘 */
.left-toggle { left: 280px; transform: translate(-50%, -50%); }
.right-toggle { right: 300px; transform: translate(50%, -50%); }
/* 折叠时：滑到 chat-main 边缘，始终可点 */
.left-toggle.at-edge { left: 0; }
.right-toggle.at-edge { right: 0; }

/* ═══════════ 左侧：数字人 ═══════════ */
.left-panel {
  width: 280px; min-width: 280px;
  display: flex; flex-direction: column;
  position: relative;
  transition: width .3s ease, min-width .3s ease;
  border-right: 1px solid #f3f4f6;
  &.collapsed { width: 0; min-width: 0; overflow: hidden; border-right: none; }
}
.left-content {
  flex: 1; display: flex; flex-direction: column;
  padding: 16px 12px 16px 16px;
  gap: 14px;
  overflow: hidden;
}
.teacher-section {
  flex: 1; position: relative;
  background: linear-gradient(180deg, #f5edff 0%, #e9deff 100%);
  border-radius: 16px;
  overflow: hidden;
  :deep(.digital-teacher) { position: absolute; inset: 0; }
}
.speech-bubble {
  position: absolute;
  top: 16px; right: 16px;
  max-width: 140px;
  padding: 10px 14px;
  background: white;
  border-radius: 12px;
  font-size: 12px;
  line-height: 1.5;
  color: #4b5563;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  z-index: 5;
  &::before {
    content: '';
    position: absolute;
    left: -6px; top: 16px;
    width: 0; height: 0;
    border-top: 6px solid transparent;
    border-bottom: 6px solid transparent;
    border-right: 6px solid white;
  }
}

.stats-card {
  background: white;
  border-radius: 16px;
  padding: 16px;
  position: relative;
  box-shadow: 0 2px 12px rgba(200,76,90,0.06);
}
.stats-head {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; color: #6b7280;
  margin-bottom: 12px;
}
.online-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 6px rgba(34,197,94,0.5);
}
.tts-pill {
  margin-left: auto;
  padding: 3px 10px; border-radius: 12px;
  background: #f3f4f6; border: 1px solid transparent;
  font-size: 11px; color: #6b7280; cursor: pointer;
  transition: all .2s;
  &.active { background: rgba(200,76,90,0.1); color: #c84c5a; border-color: rgba(200,76,90,0.3); }
  &:disabled { opacity: .4; cursor: not-allowed; }
}
.stats-label { font-size: 12px; color: #9ca3af; margin-bottom: 4px; }
.stats-value { display: flex; align-items: baseline; gap: 4px; margin-bottom: 6px;
  .big { font-size: 32px; font-weight: 700; color: #c84c5a; }
  .unit { font-size: 13px; color: #6b7280; }
}
.stats-tip { font-size: 11px; color: #9ca3af; line-height: 1.5; }
.stats-mascot {
  position: absolute; right: 12px; bottom: 8px;
  font-size: 40px; opacity: 0.6;
}

/* ═══════════ 中间：聊天 ═══════════ */
.chat-main {
  flex: 1; display: flex; flex-direction: column;
  background: transparent;
  min-width: 0;
  position: relative;
}
.messages-container {
  flex: 1; overflow-y: auto;
  padding: 28px 0 32px;
  display: flex; flex-direction: column; gap: 28px;
}

/* 欢迎屏 */
.welcome-screen {
  max-width: 1000px; margin: 40px auto 0; padding: 0 32px;
}
.welcome-title {
  font-size: 28px; font-weight: 700; color: #1f2937;
  margin: 0 0 8px;
  .wave { display: inline-block; animation: wave 2s infinite; transform-origin: 70% 70%; }
}
@keyframes wave {
  0%,60%,100% { transform: rotate(0); }
  10%,30% { transform: rotate(14deg); }
  20% { transform: rotate(-8deg); }
  40% { transform: rotate(-4deg); }
  50% { transform: rotate(10deg); }
}
.welcome-sub {
  font-size: 14px; color: #6b7280; line-height: 1.6;
  margin: 0 0 24px;
}
.suggested-prompts {
  display: flex; flex-wrap: wrap; gap: 10px;
  align-items: center;
}
.prompt-chip {
  padding: 8px 16px;
  background: rgba(200,76,90,0.08);
  border: 1px solid rgba(200,76,90,0.15);
  border-radius: 20px;
  font-size: 13px; color: #c84c5a;
  cursor: pointer; transition: all .2s;
  &:hover { background: rgba(200,76,90,0.15); transform: translateY(-1px); }
}
.refresh-prompts {
  margin-left: auto;
  background: transparent; border: none;
  font-size: 12px; color: #9ca3af; cursor: pointer;
  display: flex; align-items: center; gap: 4px;
  &:hover { color: #c84c5a; }
}

/* 消息 */
.message-wrapper {
  max-width: 1000px; margin: 0 auto; width: 96%;
  display: flex; gap: 16px;
  &.user { flex-direction: row-reverse;
    .bubble { background: linear-gradient(135deg, #c84c5a, #d97982); color: white; border-radius: 18px 4px 18px 18px; }
    .message-actions { display: none; }
  }
  .message-avatar { flex-shrink: 0;
    .ai-avatar { width: 32px; height: 32px; background: linear-gradient(135deg, #c84c5a, #d97982); color: white; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; }
  }
  .message-content { flex: 1; max-width: 82%;
    .bubble { padding: 14px 18px; border-radius: 4px 18px 18px 18px; font-size: 14px; line-height: 1.7; color: #1f2937; background: white; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
    .text-content { white-space: pre-wrap; word-break: break-word; }
    .message-actions { display: flex; gap: 14px; margin-top: 6px;
      .el-button { font-size: 11px; color: #9ca3af; padding: 0; &:hover { color: #c84c5a; } }
    }
  }
}

/* ═══ 两侧栏都收起时：加宽内容区，用户靠右 AI 靠左 ═══ */
.chat-page-container.both-collapsed {
  .message-wrapper {
    max-width: 1200px;
    width: 98%;
    .message-content { max-width: 78%; }
  }
  /* 收起时输入区和欢迎屏也更宽 */
  .welcome-screen { max-width: 1200px; }
  .chat-input-area { max-width: 1200px; }
}

/* 输入区 */
.chat-input-area {
  padding: 16px 32px 24px; max-width: 1000px; margin: 0 auto; width: 100%;
}
.input-container {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 10px 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
  display: flex; flex-direction: column; gap: 8px;
  :deep(.el-textarea__inner) { border: none; box-shadow: none !important; padding: 4px 8px; font-size: 14px; max-height: 180px; resize: none; }
}
.input-toolbar {
  display: flex; align-items: center; gap: 4px;
  .tool-btn {
    width: 32px; height: 32px; border-radius: 8px;
    background: transparent; border: none;
    color: #9ca3af; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: all .2s;
    &:hover { background: #f3f4f6; color: #c84c5a; }
  }
  .send-btn {
    margin-left: auto;
    width: 36px; height: 36px; border-radius: 50%;
    background: linear-gradient(135deg, #c84c5a, #d97982);
    color: white; border: none;
    cursor: pointer; display: flex; align-items: center; justify-content: center;
    transition: all .2s;
    &:hover:not(:disabled) { transform: scale(1.05); box-shadow: 0 4px 12px rgba(200,76,90,0.3); }
    &:disabled { opacity: .4; cursor: not-allowed; }
  }
}

.typing-indicator { display: flex; gap: 4px; padding: 4px 0;
  span { width: 6px; height: 6px; background: #9ca3af; border-radius: 50%; animation: typing 1.4s infinite ease-in-out;
    &:nth-child(1){animation-delay:0s} &:nth-child(2){animation-delay:.2s} &:nth-child(3){animation-delay:.4s}
  }
}
@keyframes typing { 0%,80%,100%{transform:scale(0);opacity:.3} 40%{transform:scale(1);opacity:1} }

/* ═══════════ 右侧：历史 + 目录 ═══════════ */
.right-panel {
  width: 300px; min-width: 300px;
  display: flex; flex-direction: column;
  position: relative;
  transition: width .3s ease, min-width .3s ease;
  border-left: 1px solid #f3f4f6;
  &.collapsed { width: 0; min-width: 0; overflow: hidden; border-left: none; }
}
.right-content {
  flex: 1; display: flex; flex-direction: column;
  padding: 16px 16px 16px 12px;
  gap: 14px;
  overflow: hidden;
}
.right-section {
  background: white;
  border-radius: 16px;
  display: flex; flex-direction: column;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(200,76,90,0.06);
}
.history-section { flex: 1.4; min-height: 0; }
.toc-section { flex: 1; min-height: 0; }

.section-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #f3f4f6;
}
.section-title { font-size: 14px; font-weight: 700; color: #1f2937; }
.head-btn {
  background: transparent; border: none;
  font-size: 12px; color: #c84c5a; cursor: pointer;
  display: flex; align-items: center; gap: 2px;
  padding: 4px 8px; border-radius: 6px;
  transition: all .2s;
  &:hover { background: rgba(200,76,90,0.08); }
}
.section-body { flex: 1; overflow-y: auto; padding: 8px; }

.empty-hint { text-align: center; color: #9ca3af; padding: 32px 12px; font-size: 13px; }

/* 历史列表 */
.hist-groups { display: flex; flex-direction: column; gap: 8px; }
.group-label {
  font-size: 11px; font-weight: 600; color: #9ca3af;
  padding: 4px 8px;
  text-transform: uppercase; letter-spacing: 0.5px;
}
.hist-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; border-radius: 8px;
  cursor: pointer; transition: all .2s;
  position: relative;
  &:hover { background: #f9fafb;
    .del-btn { opacity: 1; }
  }
  &.active { background: rgba(200,76,90,0.08);
    .hist-title { color: #c84c5a; font-weight: 600; }
  }
  &.active::before {
    content: ''; position: absolute; left: 0; top: 8px; bottom: 8px;
    width: 3px; background: #c84c5a; border-radius: 0 2px 2px 0;
  }
}
.hist-info { flex: 1; min-width: 0; }
.hist-title {
  font-size: 13px; color: #1f2937;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  margin-bottom: 2px;
}
.hist-meta { font-size: 11px; color: #9ca3af; }
.hist-time { font-size: 11px; color: #9ca3af; flex-shrink: 0; }
.del-btn {
  opacity: 0; padding: 2px; color: #9ca3af;
  transition: opacity .2s;
  &:hover { color: #ef4444; }
}

/* 目录 */
.toc-list { display: flex; flex-direction: column; gap: 2px; }
.toc-item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 12px; border-radius: 8px;
  cursor: pointer; transition: all .2s;
  font-size: 13px;
  &:hover { background: #f9fafb; }
  &.active { background: rgba(200,76,90,0.1); color: #c84c5a; }
}
.toc-icon { font-size: 14px; flex-shrink: 0; }
.toc-title { flex: 1; color: #4b5563; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.toc-idx { font-size: 11px; color: #d1d5db; flex-shrink: 0; }

/* ═══════════ 资源卡片（保留） ═══════════ */
.message-cards-wrapper { margin-top: 8px; }
.resource-attachments { display: flex; flex-direction: column; gap: 10px; margin-top: 10px; }
.resource-card {
  border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden;
  background: #fafafa; transition: box-shadow .2s;
  &:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
}
.res-card-head {
  display: flex; align-items: center; gap: 8px; padding: 10px 14px; cursor: pointer;
  user-select: none; transition: background .15s;
  &:hover { background: rgba(0,0,0,0.02); }
  .res-icon { font-size: 18px; }
  .res-title { flex: 1; font-size: 13px; font-weight: 600; color: #1f2937; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .res-format-tag { font-size: 11px; padding: 2px 8px; border-radius: 10px; background: rgba(200,76,90,0.1); color: #c84c5a; white-space: nowrap; }
  .res-toggle { transition: transform .25s; color: #9ca3af; &.expanded { transform: rotate(180deg); } }
}
.res-card-body { padding: 12px 14px; border-top: 1px solid #e5e7eb; }
.res-expand-enter-active, .res-expand-leave-active { transition: all .25s ease; overflow: hidden; }
.res-expand-enter-from, .res-expand-leave-to { max-height: 0; opacity: 0; }
.res-expand-enter-to, .res-expand-leave-from { max-height: 2000px; opacity: 1; }

.mindmap-container { display: block; width: 100%; height: 420px; min-height: 320px; background: #fafafa; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }

.code-block {
  background: #f0f1f3; color: #1f2937; padding: 14px 16px; border-radius: 8px;
  overflow-x: auto; font-size: 13px; line-height: 1.6; font-family: 'Fira Code', 'Consolas', monospace;
  max-height: 500px; overflow-y: auto; white-space: pre-wrap; word-break: break-word;
  code { background: none; padding: 0; color: inherit; }
}

.quiz-container { display: flex; flex-direction: column; gap: 14px; }
.quiz-item {
  padding: 12px; background: white; border-radius: 8px; border: 1px solid #e5e7eb;
  .quiz-q { font-size: 13px; font-weight: 600; margin-bottom: 8px; color: #1f2937; }
  .quiz-opts { display: flex; flex-direction: column; gap: 4px; margin: 8px 0; }
  .quiz-opt { font-size: 12px; padding: 4px 10px; background: #f9fafb; border-radius: 6px; color: #4b5563; }
  .quiz-ans { font-size: 12px; margin: 4px 0; }
  .quiz-exp { font-size: 12px; color: #9ca3af; margin: 4px 0; }
}

.animation-container { text-align: center; }
.anim-video { width: 100%; max-width: 640px; border-radius: 8px; }
.anim-fallback { text-align: left; }
.anim-notice { font-size: 12px; padding: 8px 12px; margin-bottom: 10px; background: rgba(245,158,11,0.1); border-left: 3px solid #f59e0b; border-radius: 4px; color: #92400e; }

.res-actions {
  display: flex; align-items: center; gap: 10px; margin-top: 10px; padding-top: 8px;
  border-top: 1px solid #e5e7eb;
  .res-reason { font-size: 11px; color: #9ca3af; margin-left: auto; }
}

/* 全屏按钮 */
.res-fullscreen-btn {
  width: 28px; height: 28px; border-radius: 6px;
  background: transparent; border: 1px solid transparent;
  color: #9ca3af; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all .2s; flex-shrink: 0;
  &:hover { background: rgba(200,76,90,0.08); color: #c84c5a; border-color: rgba(200,76,90,0.2); }
}

/* ═══════════ 全屏覆盖层 ═══════════ */
.fullscreen-overlay {
  position: fixed; inset: 0; z-index: 9999;
  background: rgba(0,0,0,0.55);
  display: flex; align-items: center; justify-content: center;
  padding: 32px;
}
.fullscreen-panel {
  width: 100%; max-width: 1100px; max-height: 90vh;
  background: white; border-radius: 16px;
  display: flex; flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
.fullscreen-head {
  display: flex; align-items: center; gap: 10px;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}
.fullscreen-icon { font-size: 20px; }
.fullscreen-title { flex: 1; font-size: 16px; font-weight: 700; color: #1f2937; }
.fullscreen-close {
  width: 32px; height: 32px; border-radius: 8px;
  background: transparent; border: none;
  color: #9ca3af; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all .2s;
  &:hover { background: #f3f4f6; color: #c84c5a; }
}
.fullscreen-body {
  flex: 1; overflow-y: auto; padding: 20px;
}
.fullscreen-mindmap { height: 70vh; min-height: 500px; }
.fullscreen-code {
  max-height: 70vh; overflow: auto; font-size: 14px;
}
.fullscreen-video { width: 100%; max-height: 70vh; border-radius: 8px; }
.fullscreen-markdown { max-height: 70vh; overflow-y: auto; padding: 0 8px; }
.fullscreen-foot {
  display: flex; align-items: center; justify-content: flex-end; gap: 10px;
  padding: 12px 20px; border-top: 1px solid #e5e7eb;
}

.fullscreen-fade-enter-active, .fullscreen-fade-leave-active { transition: opacity .25s; }
.fullscreen-fade-enter-from, .fullscreen-fade-leave-to { opacity: 0; }

/* 通用动效 */
.fade-enter-active, .fade-leave-active { transition: opacity .25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.bubble-enter-active, .bubble-leave-active { transition: all .3s ease; }
.bubble-enter-from, .bubble-leave-to { opacity: 0; transform: scale(0.9); }

/* 滚动条 */
.messages-container::-webkit-scrollbar,
.section-body::-webkit-scrollbar { width: 4px; }
.messages-container::-webkit-scrollbar-thumb,
.section-body::-webkit-scrollbar-thumb { background: rgba(200,76,90,0.2); border-radius: 2px; }
.messages-container::-webkit-scrollbar-track,
.section-body::-webkit-scrollbar-track { background: transparent; }
</style>

