 <template>
   <div class="sq-layout" :class="{ 'chat-open': isChatExpanded }">
     <!-- ═══ SIDEBAR ═══ -->
     <aside class="sidebar" :class="{ 'is-collapsed': isCollapsed }">
       <!-- Brand -->
       <div class="sidebar-brand">
         <router-link to="/app" class="brand-link">
           <span class="brand-icon">
             <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
               <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
             </svg>
           </span>
           <transition name="brand-text">
             <span v-if="!isCollapsed" class="brand-name">StructQuest</span>
           </transition>
         </router-link>
         <button class="collapse-btn" @click="toggleCollapse" :title="isCollapsed ? '展开' : '折叠'">
           <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
             <path v-if="!isCollapsed" d="M6 3L11 8L6 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
             <path v-else d="M10 3L5 8L10 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
           </svg>
         </button>
       </div>
 
       <!-- New Chat -->
       <button class="new-chat-btn" @click="openNewChat">
         <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
           <path d="M8 2V14M2 8H14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
         </svg>
         <transition name="btn-text"><span v-if="!isCollapsed">新对话</span></transition>
       </button>
 
       <!-- Navigation -->
       <nav class="sidebar-nav">
         <div v-if="!isCollapsed" class="nav-label">导航</div>
         <router-link
           v-for="item in mainNav" :key="item.path"
           :to="item.path"
           class="nav-item"
           :class="{ 'is-active': isActive(item.path) }"
         >
           <component :is="item.icon" class="nav-icon" />
           <transition name="nav-text">
             <span v-if="!isCollapsed" class="nav-text">{{ item.label }}</span>
           </transition>
           <span v-if="item.badge && !isCollapsed" class="nav-badge">{{ item.badge }}</span>
         </router-link>
 
         <template v-if="!isCollapsed">
           <div class="nav-label recent-label">最近</div>
           <router-link
             v-for="item in recentItems" :key="item.path"
             :to="item.path"
             class="nav-item nav-item--recent"
           >
             <Message class="nav-icon nav-icon--sm" />
             <span class="nav-text nav-text--recent">{{ item.label }}</span>
           </router-link>
         </template>
       </nav>
 
       <!-- User -->
       <div class="sidebar-footer">
         <div class="user-card" @click="goToProfile">
           <div class="user-avatar">{{ userName.charAt(0) }}</div>
           <transition name="user-info">
             <div v-if="!isCollapsed" class="user-info">
               <span class="user-name">{{ userName }}</span>
               <span class="user-role">学习者</span>
             </div>
           </transition>
         </div>
       </div>
       <div class="active-indicator" :style="indicatorStyle"></div>
     </aside>
 
     <!-- ═══ MAIN CONTENT ═══ -->
     <div class="main-area">
       <!-- Top Bar -->
       <header class="top-bar">
         <div class="top-bar-left">
           <button class="top-bar-collapse" @click="toggleCollapse">
             <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 12h18M3 6h18M3 18h18"/></svg>
           </button>
           <div class="breadcrumb">
             <span v-for="(crumb, i) in breadcrumbs" :key="i" class="crumb">
               <span v-if="i > 0" class="crumb-sep">/</span>
               <span :class="{ 'crumb-current': i === breadcrumbs.length - 1 }">{{ crumb }}</span>
             </span>
           </div>
         </div>
         <div class="top-bar-right">
           <div class="search-box">
             <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
             <input v-model="searchQuery" class="search-input" placeholder="搜索知识点..." @keyup.enter="handleSearch" />
           </div>
           <button class="top-icon-btn" title="通知">
             <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>
           </button>
           <div class="top-bar-avatar" @click="goToProfile">{{ userName.charAt(0) }}</div>
         </div>
       </header>
 
       <!-- Content -->
       <main class="content-area" :class="{ 'is-dimmed': isChatExpanded }">
         <router-view v-slot="{ Component, route: r }">
           <transition name="page-fade" mode="out-in">
             <keep-alive>
               <component :is="Component" :key="r.path" />
             </keep-alive>
           </transition>
         </router-view>
       </main>
     </div>
 
     <!-- ═══ DESK PET ═══ -->
     <template v-if="!isChatExpanded">
       <DeskPet @click="toggleChat" />
     </template>
 
     <!-- ═══ AI CHAT PANEL ═══ -->
     <template v-else>
       <div
         class="chat-panel"
         :class="{ 'is-dragging': isPanelDragging, 'is-resizing': isPanelResizing }"
         :style="panelStyle"
       >
         <!-- Header -->
         <div class="chat-header" @mousedown.prevent="startPanelDrag" @touchstart.prevent="startPanelDrag">
           <div class="chat-header-left">
             <span class="chat-header-icon">
               <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
             </span>
             <span class="chat-header-title">AI 老师</span>
             <span class="ws-dot" :class="wsConnected ? 'connected' : ''"></span>
           </div>
           <div class="chat-header-actions">
             <button class="chat-btn" @click.stop="clearChat" title="清空对话">
               <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M3 5h10M5 5V3.5A1.5 1.5 0 016.5 2h3A1.5 1.5 0 0111 3.5V5M6.5 7.5v4M9.5 7.5v4M4 5l.75 8.25A1.5 1.5 0 006.25 14.5h3.5a1.5 1.5 0 001.5-1.5L12 5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
             </button>
             <button class="chat-btn" @click.stop="toggleChat" title="关闭">
               <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M4 12L12 4M12 12L4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
             </button>
           </div>
         </div>
 
         <!-- Body -->
         <div class="chat-body">
           <div class="chat-teacher">
             <DigitalTeacher ref="digitalTeacherRef" :iflytek-config="iflytekConfig" @loaded="onTeacherLoaded" />
           </div>
           <div ref="chatAreaRef" class="chat-messages">
             <div v-if="chatMessages.length === 0 && !isLoading" class="chat-empty">
               <span class="chat-empty-icon">
                 <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
               </span>
               <p>向 AI 老师提问</p>
             </div>
             <template v-else>
               <div v-for="(msg, i) in chatMessages" :key="i" :class="['chat-msg', msg.role]">
                 <div v-if="msg.role === 'assistant'" class="chat-msg-avatar">
                   <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
                 </div>
                 <div :class="['chat-msg-bubble', { 'markdown-body': msg.role === 'assistant' }]" v-html="msg.role === 'assistant' ? renderMarkdown(msg.content) : escapeHtml(msg.content)"></div>
               </div>
               <div v-if="isLoading" class="chat-msg assistant">
                 <div class="chat-msg-avatar">
                   <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
                 </div>
                 <div class="chat-msg-bubble typing">
                   <span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>
                 </div>
               </div>
             </template>
           </div>
         </div>
 
         <!-- Input -->
         <div class="chat-input-area">
           <input
             v-model="chatInput"
             class="chat-input"
             placeholder="输入你的问题..."
             @keydown.enter="sendMsg"
             :disabled="!wsConnected || isLoading"
           />
           <button class="chat-send-btn" @click="sendMsg" :disabled="!chatInput.trim() || isLoading">
             <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
           </button>
         </div>
 
         <!-- Resize Handle -->
         <div class="chat-resize-handle" @mousedown.prevent="startPanelResize" @touchstart.prevent="startPanelResize">
           <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M8 2V8H2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
         </div>
       </div>
     </template>
   </div>
 </template>
 
 <script setup>
 import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
 import { useRoute, useRouter } from 'vue-router'
 import { useSessionStore } from '@/store/session'
 import { usePetStore } from '@/store/pet'
 import { ElMessage } from 'element-plus'
 import { marked } from 'marked'
 import hljs from 'highlight.js'
 import 'highlight.js/styles/github-dark.css'
 import DOMPurify from 'dompurify'
 import { HomeFilled, Grid, Calendar, ChatDotRound, TrendCharts, User, Message } from '@element-plus/icons-vue'
 import DigitalTeacher from '@/components/DigitalTeacher/index.vue'
 import DeskPet from '@/components/DeskPet/index.vue'
 
 const route = useRoute()
 const router = useRouter()
 const sessionStore = useSessionStore()
 const petStore = usePetStore()
 const searchQuery = ref('')
 
 const userName = computed(() => sessionStore.user?.username || '学生')
 
 // ── Sidebar ──
 const isCollapsed = ref(localStorage.getItem('sq_sidebar_collapsed') === 'true')
 function toggleCollapse() {
   isCollapsed.value = !isCollapsed.value
   localStorage.setItem('sq_sidebar_collapsed', isCollapsed.value)
 }
 
 const mainNav = [
   { path: '/app', icon: HomeFilled, label: '首页', badge: null },
   { path: '/app/map', icon: Grid, label: '知识图谱', badge: null },
   { path: '/app/quest', icon: Calendar, label: '学习任务', badge: 2 },
   { path: '/app/chat', icon: ChatDotRound, label: 'AI 对话', badge: null },
   { path: '/app/analysis', icon: TrendCharts, label: '学习报告', badge: null },
 ]
 
 const recentItems = [
   { path: '/app/learn/ch01_data_concept', label: '数据结构基本概念' },
   { path: '/app/learn/ch02_linked_list', label: '链表' },
 ]
 
 function isActive(path) {
   if (path === '/app') return route.path === '/app' || route.path.startsWith('/app/dashboard')
   return route.path.startsWith(path)
 }
 
 const indicatorStyle = computed(() => {
   const idx = mainNav.findIndex(n => isActive(n.path))
   if (idx < 0) return {}
   const h = 100 / mainNav.length
   return { top: `${242 + idx * h}%`, height: `${h}%` }
 })
 
 // ── Breadcrumb ──
 const breadcrumbs = computed(() => {
   const path = route.path
   if (path === '/app' || path === '/app/dashboard') return ['首页']
   if (path.startsWith('/app/map')) return ['知识图谱']
   if (path.startsWith('/app/quest')) return ['学习任务']
   if (path.startsWith('/app/chat')) return ['AI 对话']
   if (path.startsWith('/app/analysis')) return ['学习报告']
   if (path.startsWith('/app/learn/')) return ['学习', '知识点']
   if (path.startsWith('/app/exam/')) return ['学习', '考试']
   if (path.startsWith('/app/profile')) return ['个人中心']
   if (path.startsWith('/app/admin')) return ['管理后台']
   return ['首页']
 })
 
 function handleSearch() {
   const q = searchQuery.value.trim()
   if (!q) return
   router.push(`/app/learn/search?q=${encodeURIComponent(q)}`)
 }
 
 function goToProfile() {
   router.push('/app/profile')
 }
 
 function openNewChat() {
   if (!isChatExpanded.value) toggleChat()
   clearChat()
 }
 
 // ── Pet Store Integration ──
 watch(() => route.path, (path) => {
   petStore.isLearningPage = path.startsWith('/app/learn/') || path.startsWith('/app/exam/')
 })
 
 // ── Chat Panel ──
 const isChatExpanded = ref(false)
 function toggleChat() { isChatExpanded.value = !isChatExpanded.value }
 
 const panelWidth = ref(620)
 const panelHeight = ref(580)
 const panelX = ref(80)
 const panelY = ref(60)
 const isPanelDragging = ref(false)
 const isPanelResizing = ref(false)
 
 const panelStyle = computed(() => ({
   left: `${panelX.value}px`,
   top: `${panelY.value}px`,
   width: `${panelWidth.value}px`,
   height: `${panelHeight.value}px`,
 }))
 
 function clampPanel(x, y, w, h) {
   return {
     x: Math.max(-w + 80, Math.min(x, window.innerWidth - w - 60)),
     y: Math.max(0, Math.min(y, window.innerHeight - 48)),
     w: Math.max(380, Math.min(w, window.innerWidth - 100)),
     h: Math.max(380, Math.min(h, window.innerHeight - 40)),
   }
 }
 
 let panelDragStartX = 0, panelDragStartY = 0, panelOrigX = 0, panelOrigY = 0
 function startPanelDrag(e) {
   isPanelDragging.value = true
   const cx = e.touches ? e.touches[0].clientX : e.clientX
   const cy = e.touches ? e.touches[0].clientY : e.clientY
   panelDragStartX = cx; panelDragStartY = cy
   panelOrigX = panelX.value; panelOrigY = panelY.value
   window.addEventListener('mousemove', onPanelDrag)
   window.addEventListener('mouseup', stopPanelDrag)
   window.addEventListener('touchmove', onPanelDrag, { passive: false })
   window.addEventListener('touchend', stopPanelDrag)
 }
 function onPanelDrag(e) {
   const cx = e.touches ? e.touches[0].clientX : e.clientX
   const cy = e.touches ? e.touches[0].clientY : e.clientY
   const pos = clampPanel(panelOrigX + cx - panelDragStartX, panelOrigY + cy - panelDragStartY, panelWidth.value, panelHeight.value)
   panelX.value = pos.x; panelY.value = pos.y
 }
 function stopPanelDrag() {
   isPanelDragging.value = false
   window.removeEventListener('mousemove', onPanelDrag)
   window.removeEventListener('mouseup', stopPanelDrag)
   window.removeEventListener('touchmove', onPanelDrag)
   window.removeEventListener('touchend', stopPanelDrag)
 }
 
 let resizeStartX = 0, resizeStartY = 0, resizeW = 0, resizeH = 0
 function startPanelResize(e) {
   isPanelResizing.value = true
   const cx = e.touches ? e.touches[0].clientX : e.clientX
   const cy = e.touches ? e.touches[0].clientY : e.clientY
   resizeStartX = cx; resizeStartY = cy
   resizeW = panelWidth.value; resizeH = panelHeight.value
   window.addEventListener('mousemove', onPanelResize)
   window.addEventListener('mouseup', stopPanelResize)
   window.addEventListener('touchmove', onPanelResize, { passive: false })
   window.addEventListener('touchend', stopPanelResize)
 }
 function onPanelResize(e) {
   const cx = e.touches ? e.touches[0].clientX : e.clientX
   const cy = e.touches ? e.touches[0].clientY : e.clientY
   const pos = clampPanel(panelX.value, panelY.value, resizeW + cx - resizeStartX, resizeH + cy - resizeStartY)
   panelWidth.value = pos.w; panelHeight.value = pos.h
 }
 function stopPanelResize() {
   isPanelResizing.value = false
   window.removeEventListener('mousemove', onPanelResize)
   window.removeEventListener('mouseup', stopPanelResize)
   window.removeEventListener('touchmove', onPanelResize)
   window.removeEventListener('touchend', stopPanelResize)
 }
 
 // ── Chat Messages ──
 const chatMessages = ref([])
 const chatInput = ref('')
 const isLoading = ref(false)
 const wsConnected = ref(false)
 let ws = null
 const chatAreaRef = ref(null)
 const digitalTeacherRef = ref(null)
 const iflytekConfig = ref({})
 
 function escapeHtml(text) {
   const div = document.createElement('div')
   div.textContent = text
   return div.innerHTML
 }
 
 function renderMarkdown(text) {
   if (!text) return ''
   const raw = marked.parse(text, { breaks: true })
   const clean = DOMPurify.sanitize(raw, {
     ALLOWED_TAGS: ['p','br','strong','em','code','pre','a','ul','ol','li','h1','h2','h3','h4','h5','h6','blockquote','hr','table','thead','tbody','tr','th','td','span','div','img','input'],
     ALLOWED_ATTR: ['class','href','target','src','alt','checked','type','id'],
   })
   return clean
 }
 
 // Highlight code blocks after render
 function highlightCode() {
   nextTick(() => {
     document.querySelectorAll('.chat-msg-bubble pre code').forEach(el => {
       hljs.highlightElement(el)
     })
   })
 }
 
 function connectWebSocket() {
   const token = localStorage.getItem('token') || ''
   const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
   const url = `${protocol}//${location.host}/ws/chat?token=${encodeURIComponent(token)}`
 
   try {
     ws = new WebSocket(url)
     ws.onopen = () => { wsConnected.value = true }
     ws.onmessage = (e) => {
       try {
         const data = JSON.parse(e.data)
         if (data.type === 'chunk') {
           const last = chatMessages.value[chatMessages.value.length - 1]
           if (last && last.role === 'assistant' && last._streaming) {
             last.content += data.content
             highlightCode()
           }
         } else if (data.type === 'done') {
           isLoading.value = false
           petStore.stopThinking()
           if (data.tts_audio) {
             // Handle TTS
           }
           highlightCode()
         } else if (data.type === 'error') {
           ElMessage.error(data.content || 'AI 回复出错')
           isLoading.value = false
           petStore.stopThinking()
         }
       } catch (err) {
         // text message
       }
     }
     ws.onclose = () => {
       wsConnected.value = false
       setTimeout(connectWebSocket, 3000)
     }
     ws.onerror = () => {
       wsConnected.value = false
     }
   } catch (err) {
     wsConnected.value = false
   }
 }
 
 function sendMsg() {
   const text = chatInput.value.trim()
   if (!text || isLoading.value || !wsConnected.value) return
   chatInput.value = ''
   chatMessages.value.push({ role: 'user', content: text })
   isLoading.value = true
   petStore.triggerThinking()
 
   const msg = {
     messages: chatMessages.value.map(m => ({
       role: m.role === 'assistant' ? 'assistant' : 'user',
       content: m._streaming ? m.content : m.content,
     })),
   }
 
   chatMessages.value.push({ role: 'assistant', content: '', _streaming: true })
 
   if (ws && ws.readyState === WebSocket.OPEN) {
     ws.send(JSON.stringify(msg))
   }
 
   nextTick(() => {
     if (chatAreaRef.value) {
       chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight
     }
   })
 }
 
 function clearChat() {
   chatMessages.value = []
   chatInput.value = ''
 }
 
 function onTeacherLoaded() {}
 
 // ── Lifecycle ──
 onMounted(() => {
   petStore.recordInteraction()
   connectWebSocket()
   if (route.path.startsWith('/app/learn/') || route.path.startsWith('/app/exam/')) {
     petStore.isLearningPage = true
     petStore.setMood('teaching')
   }
 })
 
 onBeforeUnmount(() => {
   if (ws) { ws.close(); ws = null }
 })
 </script>
 
 <style scoped>
 .sq-layout {
   display: flex;
   height: 100vh;
   overflow: hidden;
   background: #f5f6fa;
 }
 
 /* ═══ SIDEBAR ═══ */
 .sidebar {
   width: 240px;
   min-width: 240px;
   background: linear-gradient(180deg, #1a1d2e 0%, #141724 100%);
   display: flex;
   flex-direction: column;
   position: relative;
   transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
   z-index: 100;
   overflow: hidden;
 }
 .sidebar.is-collapsed {
   width: 64px;
   min-width: 64px;
 }
 
 .sidebar-brand {
   display: flex;
   align-items: center;
   justify-content: space-between;
   padding: 18px 16px 12px;
   border-bottom: 1px solid rgba(255,255,255,0.06);
 }
 .brand-link {
   display: flex;
   align-items: center;
   gap: 10px;
   text-decoration: none;
   color: #fff;
 }
 .brand-icon {
   width: 34px; height: 34px;
   display: flex; align-items: center; justify-content: center;
   background: linear-gradient(135deg, #4F8CF7, #6C5CE7);
   border-radius: 10px;
   color: #fff;
   flex-shrink: 0;
 }
 .brand-name {
   font-size: 16px;
   font-weight: 700;
   letter-spacing: -0.3px;
   white-space: nowrap;
 }
 .collapse-btn {
   width: 28px; height: 28px;
   display: flex; align-items: center; justify-content: center;
   background: rgba(255,255,255,0.06);
   border: none; border-radius: 8px;
   color: rgba(255,255,255,0.5);
   cursor: pointer;
   transition: all 0.2s;
   flex-shrink: 0;
 }
 .collapse-btn:hover { background: rgba(255,255,255,0.12); color: #fff; }
 
 .new-chat-btn {
   display: flex;
   align-items: center;
   gap: 8px;
   margin: 12px 16px;
   padding: 8px 14px;
   background: rgba(79, 140, 247, 0.15);
   border: 1px solid rgba(79, 140, 247, 0.25);
   border-radius: 10px;
   color: #7BA7F7;
   font-size: 13px;
   cursor: pointer;
   transition: all 0.2s;
   white-space: nowrap;
   flex-shrink: 0;
 }
 .new-chat-btn:hover {
   background: rgba(79, 140, 247, 0.25);
   border-color: rgba(79, 140, 247, 0.4);
 }
 .is-collapsed .new-chat-btn { justify-content: center; padding: 8px; }
 
 .sidebar-nav {
   flex: 1;
   overflow-y: auto;
   padding: 8px 12px;
   display: flex;
   flex-direction: column;
   gap: 2px;
 }
 .nav-label {
   font-size: 10px;
   font-weight: 600;
   text-transform: uppercase;
   letter-spacing: 1px;
   color: rgba(255,255,255,0.3);
   padding: 12px 12px 6px;
 }
 .recent-label { margin-top: 8px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.06); }
 
 .nav-item {
   display: flex;
   align-items: center;
   gap: 10px;
   padding: 9px 12px;
   border-radius: 8px;
   text-decoration: none;
   color: rgba(255,255,255,0.55);
   font-size: 13.5px;
   font-weight: 500;
   transition: all 0.15s;
   position: relative;
   white-space: nowrap;
 }
 .nav-item:hover { color: rgba(255,255,255,0.85); background: rgba(255,255,255,0.06); }
 .nav-item.is-active { color: #fff; background: rgba(79, 140, 247, 0.2); }
 .nav-item--recent { font-size: 12.5px; color: rgba(255,255,255,0.4); padding: 6px 12px; }
 .nav-icon { width: 18px; height: 18px; flex-shrink: 0; }
 .nav-icon--sm { width: 14px; height: 14px; }
 .nav-text { white-space: nowrap; }
 .nav-text--recent { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
 .nav-badge {
   margin-left: auto;
   background: #4F8CF7;
   color: #fff;
   font-size: 10px;
   font-weight: 700;
   padding: 1px 7px;
   border-radius: 10px;
 }
 
 .active-indicator {
   position: absolute;
   right: 0;
   width: 3px;
   background: #4F8CF7;
   border-radius: 3px 0 0 3px;
   transition: top 0.25s ease, height 0.25s ease;
 }
 
 .sidebar-footer {
   padding: 12px;
   border-top: 1px solid rgba(255,255,255,0.06);
   flex-shrink: 0;
 }
 .user-card {
   display: flex;
   align-items: center;
   gap: 10px;
   padding: 8px 10px;
   border-radius: 10px;
   cursor: pointer;
   transition: background 0.15s;
 }
 .user-card:hover { background: rgba(255,255,255,0.06); }
 .user-avatar {
   width: 32px; height: 32px;
   border-radius: 50%;
   background: linear-gradient(135deg, #4F8CF7, #6C5CE7);
   display: flex; align-items: center; justify-content: center;
   color: #fff; font-size: 13px; font-weight: 700;
   flex-shrink: 0;
 }
 .user-info {
   display: flex;
   flex-direction: column;
   gap: 1px;
   overflow: hidden;
 }
 .user-name { font-size: 13px; font-weight: 600; color: #fff; white-space: nowrap; }
 .user-role { font-size: 11px; color: rgba(255,255,255,0.4); white-space: nowrap; }
 
 /* ═══ MAIN AREA ═══ */
 .main-area {
   flex: 1;
   display: flex;
   flex-direction: column;
   min-width: 0;
   overflow: hidden;
 }
 
 .top-bar {
   display: flex;
   align-items: center;
   justify-content: space-between;
   height: 52px;
   padding: 0 20px;
   background: #fff;
   border-bottom: 1px solid #eef0f4;
   flex-shrink: 0;
   z-index: 50;
 }
 .top-bar-left {
   display: flex;
   align-items: center;
   gap: 12px;
 }
 .top-bar-collapse {
   width: 32px; height: 32px;
   display: none; align-items: center; justify-content: center;
   background: none; border: none; border-radius: 8px;
   color: #555; cursor: pointer;
   transition: background 0.15s;
 }
 .top-bar-collapse:hover { background: #f0f2f5; }
 @media (max-width: 768px) { .top-bar-collapse { display: flex; } }
 
 .breadcrumb {
   display: flex;
   align-items: center;
   gap: 8px;
   font-size: 13px;
   color: #888;
 }
 .crumb-sep { color: #ccc; }
 .crumb-current { color: #222; font-weight: 600; }
 
 .top-bar-right {
   display: flex;
   align-items: center;
   gap: 12px;
 }
 .search-box {
   display: flex;
   align-items: center;
   gap: 8px;
   padding: 6px 12px;
   background: #f5f6fa;
   border-radius: 8px;
   color: #999;
   transition: all 0.2s;
 }
 .search-box:focus-within {
   background: #fff;
   box-shadow: 0 0 0 2px rgba(79,140,247,0.15);
   color: #4F8CF7;
 }
 .search-input {
   border: none;
   background: transparent;
   outline: none;
   font-size: 13px;
   width: 160px;
   color: #333;
 }
 .search-input::placeholder { color: #aaa; }
 
 .top-icon-btn {
   width: 34px; height: 34px;
   display: flex; align-items: center; justify-content: center;
   background: none; border: none; border-radius: 8px;
   color: #666; cursor: pointer;
   transition: all 0.15s;
 }
 .top-icon-btn:hover { background: #f0f2f5; color: #333; }
 
 .top-bar-avatar {
   width: 32px; height: 32px;
   border-radius: 50%;
   background: linear-gradient(135deg, #4F8CF7, #6C5CE7);
   display: flex; align-items: center; justify-content: center;
   color: #fff; font-size: 12px; font-weight: 700;
   cursor: pointer;
   transition: transform 0.15s;
 }
 .top-bar-avatar:hover { transform: scale(1.08); }
 
 .content-area {
   flex: 1;
   overflow-y: auto;
   transition: opacity 0.3s;
   background: #f5f6fa;
 }
 .content-area.is-dimmed { opacity: 0.7; }
 
 /* ═══ CHAT PANEL ═══ */
 .chat-panel {
   position: fixed;
   z-index: 1002;
   background: #fff;
   border-radius: 14px;
   box-shadow: 0 8px 40px rgba(0,0,0,0.12), 0 2px 10px rgba(0,0,0,0.06);
   display: flex;
   flex-direction: column;
   overflow: hidden;
   cursor: default;
   border: 1px solid rgba(0,0,0,0.04);
 }
 .chat-panel.is-dragging { cursor: grabbing; }
 .chat-panel.is-dragging .chat-header { cursor: grabbing; }
 
 .chat-header {
   display: flex;
   align-items: center;
   justify-content: space-between;
   padding: 12px 16px;
   background: linear-gradient(135deg, #4F8CF7, #6C5CE7);
   color: #fff;
   cursor: grab;
   flex-shrink: 0;
   border-radius: 14px 14px 0 0;
   user-select: none;
 }
 .chat-header-left { display: flex; align-items: center; gap: 8px; }
 .chat-header-icon { display: flex; }
 .chat-header-title { font-size: 14px; font-weight: 600; }
 
 .ws-dot {
   width: 7px; height: 7px;
   border-radius: 50%;
   background: #ff6b6b;
   transition: background 0.3s;
 }
 .ws-dot.connected { background: #51cf66; box-shadow: 0 0 6px rgba(81,207,102,0.4); }
 
 .chat-header-actions { display: flex; gap: 6px; }
 .chat-btn {
   width: 28px; height: 28px;
   display: flex; align-items: center; justify-content: center;
   background: rgba(255,255,255,0.1);
   border: none; border-radius: 6px;
   color: rgba(255,255,255,0.7);
   cursor: pointer;
   transition: all 0.15s;
 }
 .chat-btn:hover { background: rgba(255,255,255,0.2); color: #fff; }
 
 .chat-body {
   flex: 1;
   display: flex;
   flex-direction: column;
   overflow: hidden;
 }
 .chat-teacher {
   height: 120px;
   background: #f8f9fb;
   border-bottom: 1px solid #eef0f4;
   flex-shrink: 0;
 }
 
 .chat-messages {
   flex: 1;
   overflow-y: auto;
   padding: 16px;
   display: flex;
   flex-direction: column;
   gap: 12px;
 }
 .chat-empty {
   flex: 1;
   display: flex;
   flex-direction: column;
   align-items: center;
   justify-content: center;
   color: #bbb;
   gap: 8px;
 }
 .chat-empty-icon { opacity: 0.4; }
 .chat-empty p { font-size: 13px; margin: 0; }
 
 .chat-msg { display: flex; gap: 8px; max-width: 90%; }
 .chat-msg.user { align-self: flex-end; }
 .chat-msg.assistant { align-self: flex-start; }
 .chat-msg-avatar {
   width: 28px; height: 28px;
   border-radius: 50%;
   background: linear-gradient(135deg, #4F8CF7, #6C5CE7);
   display: flex; align-items: center; justify-content: center;
   color: #fff; font-size: 12px;
   flex-shrink: 0;
   align-self: flex-end;
 }
 .chat-msg-bubble {
   padding: 10px 14px;
   border-radius: 14px;
   font-size: 13px;
   line-height: 1.55;
   word-break: break-word;
 }
 .chat-msg.user .chat-msg-bubble {
   background: #4F8CF7;
   color: #fff;
   border-bottom-right-radius: 4px;
 }
 .chat-msg.assistant .chat-msg-bubble {
   background: #f0f2f5;
   color: #333;
   border-bottom-left-radius: 4px;
 }
 
 .typing {
   display: flex;
   align-items: center;
   gap: 4px;
   padding: 12px 16px !important;
 }
 .typing-dot {
   width: 7px; height: 7px;
   border-radius: 50%;
   background: #999;
   animation: dotBounce 1.4s infinite ease-in-out both;
 }
 .typing-dot:nth-child(2) { animation-delay: 0.16s; }
 .typing-dot:nth-child(3) { animation-delay: 0.32s; }
 @keyframes dotBounce {
   0%,80%,100% { transform: scale(0.5); opacity: 0.3; }
   40% { transform: scale(1); opacity: 1; }
 }
 
 .chat-input-area {
   display: flex;
   align-items: center;
   gap: 8px;
   padding: 10px 14px;
   border-top: 1px solid #eef0f4;
   background: #fafbfc;
   flex-shrink: 0;
 }
 .chat-input {
   flex: 1;
   height: 36px;
   padding: 0 14px;
   border: 1.5px solid #e0e2e6;
   border-radius: 18px;
   font-size: 13px;
   outline: none;
   background: #fff;
   transition: border-color 0.2s;
 }
 .chat-input:focus { border-color: #4F8CF7; box-shadow: 0 0 0 3px rgba(79,140,247,0.08); }
 .chat-input:disabled { background: #f5f6fa; opacity: 0.6; }
 
 .chat-send-btn {
   width: 36px; height: 36px;
   border-radius: 50%;
   border: none;
   background: #4F8CF7;
   color: #fff;
   cursor: pointer;
   display: flex; align-items: center; justify-content: center;
   flex-shrink: 0;
   transition: all 0.15s;
   box-shadow: 0 4px 12px rgba(79,140,247,0.25);
 }
 .chat-send-btn:hover:not(:disabled) { transform: scale(1.06); }
 .chat-send-btn:disabled { opacity: 0.35; cursor: not-allowed; box-shadow: none; }
 
 .chat-resize-handle {
   position: absolute;
   bottom: 0; right: 0;
   width: 22px; height: 22px;
   cursor: nwse-resize;
   display: flex; align-items: flex-end; justify-content: flex-end;
   padding: 0 4px 4px 0;
   color: #bbb;
   z-index: 5;
 }
 .chat-resize-handle:hover { color: #4F8CF7; }
 
 /* Page transition */
 .page-fade-enter-active,
 .page-fade-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
 .page-fade-enter-from { opacity: 0; transform: translateY(8px); }
 .page-fade-leave-to { opacity: 0; transform: translateY(-8px); }
 
 /* Sidebar transitions */
 .brand-text-enter-active, .brand-text-leave-active,
 .btn-text-enter-active, .btn-text-leave-active,
 .nav-text-enter-active, .nav-text-leave-active,
 .user-info-enter-active, .user-info-leave-active {
   transition: opacity 0.2s ease, transform 0.2s ease;
 }
 .brand-text-enter-from, .btn-text-enter-from,
 .nav-text-enter-from, .user-info-enter-from {
   opacity: 0; transform: translateX(-8px);
 }
 .brand-text-leave-to, .btn-text-leave-to,
 .nav-text-leave-to, .user-info-leave-to {
   opacity: 0; transform: translateX(-8px);
 }
 
 /* Scrollbar */
 .sidebar-nav::-webkit-scrollbar { width: 3px; }
 .sidebar-nav::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }
 .chat-messages::-webkit-scrollbar { width: 4px; }
 .chat-messages::-webkit-scrollbar-thumb { background: #ddd; border-radius: 2px; }
 
 /* Markdown inside chat */
 :deep(.markdown-body p) { margin: 4px 0; }
 :deep(.markdown-body p:first-child) { margin-top: 0; }
 :deep(.markdown-body p:last-child) { margin-bottom: 0; }
 :deep(.markdown-body code) { background: rgba(0,0,0,0.06); padding: 1px 5px; border-radius: 4px; font-size: 12px; color: #e06c75; }
 :deep(.markdown-body pre) { background: #282c34; border-radius: 8px; padding: 10px 14px; overflow-x: auto; margin: 8px 0; }
 :deep(.markdown-body pre code) { background: none; color: #abb2bf; font-size: 12.5px; padding: 0; }
 </style>
