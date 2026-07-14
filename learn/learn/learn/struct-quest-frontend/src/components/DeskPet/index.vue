<template>
  <div
    ref="petEl"
    class="desk-pet"
    :class="[`mood-${petStore.currentMood}`, { 'is-dragging': petStore.isDragging }]"
    :style="petStyle"
    @mousedown.prevent="startDrag"
    @touchstart.prevent="startDrag"
    @mouseenter="onMouseEnter"
    @mouseleave="onMouseLeave"
  >
    <!-- Title Badge Above Pet -->
    <transition name="badge-pop">
      <div v-if="currentTitle && !petStore.isDragging" class="title-badge" @click.stop="togglePanel">
        <span class="title-badge-icon">🎖️</span>
        <span class="title-badge-text">{{ currentTitle }}</span>
      </div>
    </transition>

    <!-- Pet SVG -->
    <div class="pet-svg-wrapper" @click.stop="onClick">
      <svg
        ref="svgRef"
        viewBox="0 0 120 140"
        xmlns="http://www.w3.org/2000/svg"
        class="pet-svg"
      >
        <defs>
          <radialGradient id="bodyGrad" cx="40%" cy="35%" r="60%">
            <stop offset="0%" stop-color="#E8F4FF" />
            <stop offset="60%" stop-color="#C5DEFF" />
            <stop offset="100%" stop-color="#8BBCFF" />
          </radialGradient>
          <radialGradient id="bodyGradBright" cx="40%" cy="35%" r="60%">
            <stop offset="0%" stop-color="#F0F8FF" />
            <stop offset="60%" stop-color="#DAEFFF" />
            <stop offset="100%" stop-color="#A8D4FF" />
          </radialGradient>
          <radialGradient id="blushGrad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#FFB5B5" stop-opacity="0.6" />
            <stop offset="100%" stop-color="#FFB5B5" stop-opacity="0" />
          </radialGradient>
          <filter id="portGlow">
            <feGaussianBlur stdDeviation="2" result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>

        <!-- Shadow -->
        <ellipse ref="shadowRef" cx="60" cy="134" rx="24" ry="5" fill="rgba(0,0,0,0.12)"/>

        <!-- Left Arm -->
        <g ref="leftArmRef" class="pet-arm left-arm">
          <path d="M 34,70 Q 16,64 12,76" fill="none" stroke="#8BBCFF" stroke-width="4.5" stroke-linecap="round"/>
          <circle cx="12" cy="76" r="5" fill="#C5DEFF" stroke="#8BBCFF" stroke-width="1.5"/>
        </g>

        <!-- Right Arm -->
        <g ref="rightArmRef" class="pet-arm right-arm">
          <path d="M 86,70 Q 104,64 108,76" fill="none" stroke="#8BBCFF" stroke-width="4.5" stroke-linecap="round"/>
          <circle cx="108" cy="76" r="5" fill="#C5DEFF" stroke="#8BBCFF" stroke-width="1.5"/>
        </g>

        <!-- Ports -->
        <g ref="portsRef" class="pet-ports">
          <circle cx="31" cy="70" r="5" fill="white" stroke="#6366f1" stroke-width="1.5"/>
          <circle cx="31" cy="70" r="2" fill="#6366f1"/>
          <circle cx="89" cy="70" r="5" fill="white" stroke="#6366f1" stroke-width="1.5"/>
          <circle cx="89" cy="70" r="2" fill="#6366f1"/>
        </g>

        <!-- Body -->
        <circle ref="bodyRef" cx="60" cy="72" r="30" fill="url(#bodyGrad)" stroke="#6366f1" stroke-width="2.5" class="pet-body-circle"/>

        <!-- Blush -->
        <circle cx="44" cy="80" r="6" fill="url(#blushGrad)"/>
        <circle cx="76" cy="80" r="6" fill="url(#blushGrad)"/>

        <!-- Left Eye -->
        <g ref="leftEyeRef" class="pet-eye left-eye">
          <ellipse cx="48" cy="66" rx="6" ry="7" fill="white" stroke="#3B6CB7" stroke-width="1.5"/>
          <circle ref="leftPupilRef" cx="50" cy="67.5" r="3.2" fill="#2C3E50"/>
          <circle cx="49" cy="65" r="1.3" fill="white"/>
        </g>

        <!-- Right Eye -->
        <g ref="rightEyeRef" class="pet-eye right-eye">
          <ellipse cx="72" cy="66" rx="6" ry="7" fill="white" stroke="#3B6CB7" stroke-width="1.5"/>
          <circle ref="rightPupilRef" cx="74" cy="67.5" r="3.2" fill="#2C3E50"/>
          <circle cx="73" cy="65" r="1.3" fill="white"/>
        </g>

        <!-- Mouth -->
        <path ref="mouthRef" d="M 52,78 Q 60,85 68,78" fill="none" stroke="#2C3E50" stroke-width="2.2" stroke-linecap="round" class="pet-mouth"/>

        <!-- Head Leaf -->
        <g ref="leafRef" class="pet-leaf">
          <path d="M 60,44 Q 48,28 60,16 Q 72,28 60,44" fill="#22C55E" stroke="#16A34A" stroke-width="1.5"/>
          <line x1="60" y1="44" x2="60" y2="52" stroke="#16A34A" stroke-width="2.5"/>
        </g>

        <!-- Effects -->
        <g ref="thinkRef" class="pet-effect" style="display:none">
          <circle cx="60" cy="12" r="8" fill="white" stroke="#6366f1" stroke-width="1.5" stroke-dasharray="4 2">
            <animateTransform attributeName="transform" type="rotate" from="0 60 12" to="360 60 12" dur="4s" repeatCount="indefinite"/>
          </circle>
          <text x="57" y="15" font-size="11" fill="#6366f1" font-weight="bold">?</text>
        </g>
        <g ref="sleepRef" class="pet-effect" style="display:none">
          <text x="80" y="20" font-size="8" fill="#8BBCFF" font-weight="bold" opacity="0.4">z</text>
          <text x="88" y="8" font-size="10" fill="#8BBCFF" font-weight="bold" opacity="0.6">z</text>
          <text x="98" y="-2" font-size="12" fill="#8BBCFF" font-weight="bold" opacity="0.8">Z</text>
        </g>
        <g ref="sparkleRef" class="pet-effect" style="display:none">
          <text x="20" y="40" font-size="10" fill="#FFD700">*</text>
          <text x="95" y="45" font-size="8" fill="#FFB347">*</text>
        </g>
        <g ref="teachRef" class="pet-effect" style="display:none">
          <line x1="31" y1="70" x2="8" y2="90" stroke="#6366f1" stroke-width="1.5" stroke-dasharray="3 2" opacity="0.6"/>
          <line x1="89" y1="70" x2="112" y2="90" stroke="#6366f1" stroke-width="1.5" stroke-dasharray="3 2" opacity="0.6"/>
          <circle cx="8" cy="90" r="3" fill="#A8D4FF"/>
          <circle cx="112" cy="90" r="3" fill="#A8D4FF"/>
        </g>
      </svg>
    </div>

    <!-- Pet Shadow -->
    <div class="pet-shadow" :class="{ 'is-active': !['sleeping','thinking'].includes(petStore.currentMood) }"></div>

    <!-- Tooltip -->
    <transition name="bubble-pop">
      <div v-if="tooltipText && !petStore.isDragging && !showPanel" class="pet-tooltip">
        {{ tooltipText }}
      </div>
    </transition>

    <!-- ═══ ACHIEVEMENT PANEL ═══ -->
    <transition name="panel-slide">
      <div v-if="showPanel" class="achievement-panel" @click.stop>
        <div class="ap-header">
          <h3 class="ap-title">🏆 荣誉成就</h3>
          <button class="ap-close" @click="showPanel = false">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M4 12L12 4M12 12L4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          </button>
        </div>

        <div class="ap-current">
          <div class="ap-current-badge">
            <span class="ap-badge-emoji">🎖️</span>
            <div class="ap-badge-info">
              <span class="ap-badge-title">{{ currentTitle }}</span>
              <span class="ap-badge-sub">当前称号</span>
            </div>
          </div>
          <div class="ap-level-row">
            <span class="ap-level-label">学习等级</span>
            <span class="ap-level-value">Lv.{{ userLevel }}</span>
          </div>
        </div>

        <div class="ap-divider"></div>

        <h4 class="ap-section-title">已解锁成就</h4>
        <div class="ap-achievements">
          <div
            v-for="a in achievements"
            :key="a.id"
            :class="['ap-achievement', { unlocked: a.unlocked }]"
          >
            <span class="ap-ach-icon">{{ a.unlocked ? a.icon : '🔒' }}</span>
            <div class="ap-ach-info">
              <span class="ap-ach-name">{{ a.name }}</span>
              <span class="ap-ach-desc">{{ a.desc }}</span>
            </div>
            <span v-if="a.unlocked" class="ap-ach-date">{{ a.date }}</span>
          </div>
        </div>

        <div class="ap-divider"></div>

        <h4 class="ap-section-title">学习里程碑</h4>
        <div class="ap-milestones">
          <div v-for="m in milestones" :key="m.label" :class="['ap-milestone', { reached: m.reached }]">
            <div class="ap-ms-icon">{{ m.reached ? '✅' : '⭕' }}</div>
            <span class="ap-ms-label">{{ m.label }}</span>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import gsap from 'gsap'
import { usePetStore } from '@/store/pet'
import { useSessionStore } from '@/store/session'

const route = useRoute()
const petStore = usePetStore()
const sessionStore = useSessionStore()

// ── Achievement State ──
const showPanel = ref(false)

const currentTitle = computed(() => {
  const level = sessionStore.user?.level || 5
  if (level >= 20) return '知识大师'
  if (level >= 15) return '数据结构专家'
  if (level >= 10) return '算法能手'
  if (level >= 5) return '学习之星'
  return '初学者'
})

const userLevel = computed(() => sessionStore.user?.level || 5)

const achievements = ref([
  { id: 1, name: '初出茅庐', desc: '完成第一章学习', icon: '🌟', unlocked: true, date: '2026-07-01' },
  { id: 2, name: '坚持不懈', desc: '连续学习7天', icon: '🔥', unlocked: true, date: '2026-07-05' },
  { id: 3, name: '知识猎手', desc: '掌握10个知识点', icon: '🎯', unlocked: true, date: '2026-07-08' },
  { id: 4, name: '代码勇士', desc: '完成5道编程题', icon: '⚔️', unlocked: false },
  { id: 5, name: '学霸模式', desc: '单日学习超2小时', icon: '📚', unlocked: true, date: '2026-07-10' },
  { id: 6, name: '全栈探索者', desc: '学习全部8个章节', icon: '🗺️', unlocked: false },
])

const milestones = ref([
  { label: '学习 1 小时', reached: true },
  { label: '学习 5 小时', reached: true },
  { label: '学习 20 小时', reached: false },
  { label: '学习 50 小时', reached: false },
  { label: '完成 10 个任务', reached: true },
  { label: '完成 50 个任务', reached: false },
])

function togglePanel() {
  showPanel.value = !showPanel.value
}

// ── Position ──
const petX = ref(parseFloat(localStorage.getItem('pet_x')) || window.innerWidth - 150)
const petY = ref(parseFloat(localStorage.getItem('pet_y')) || window.innerHeight - 220)
const dragStartX = ref(0)
const dragStartY = ref(0)
const petStartX = ref(0)
const petStartY = ref(0)
let hasMoved = false

// ── Refs ──
const petEl = ref(null)
const svgRef = ref(null)
const bodyRef = ref(null)
const shadowRef = ref(null)
const leftEyeRef = ref(null)
const rightEyeRef = ref(null)
const leftPupilRef = ref(null)
const rightPupilRef = ref(null)
const mouthRef = ref(null)
const leafRef = ref(null)
const leftArmRef = ref(null)
const rightArmRef = ref(null)
const portsRef = ref(null)
const thinkRef = ref(null)
const sleepRef = ref(null)
const sparkleRef = ref(null)
const teachRef = ref(null)
const isHovered = ref(false)
const isClicked = ref(false)
const autoTimer = ref(null)
const animations = ref([])

const petStyle = computed(() => ({
  left: `${petX.value}px`,
  top: `${petY.value}px`,
}))

const tooltipText = computed(() => {
  if (petStore.isDragging || isClicked.value || showPanel.value) return ''
  const t = {
    idle: '查看成就',
    thinking: '让我想想...',
    teaching: '',
    happy: '',
    sad: '',
    waving: '嗨～',
    waiting: '开始学习吧',
    sleeping: 'zzz...',
  }
  return t[petStore.currentMood] || '查看成就'
})

// ── Drag ──
function clamp(x, y) {
  const w = 100, h = 120
  return {
    x: Math.max(0, Math.min(x, window.innerWidth - w - 20)),
    y: Math.max(0, Math.min(y, window.innerHeight - h - 20)),
  }
}

function startDrag(e) {
  hasMoved = false
  petStore.isDragging = true
  petStore.recordInteraction()
  const cx = e.touches ? e.touches[0].clientX : e.clientX
  const cy = e.touches ? e.touches[0].clientY : e.clientY
  dragStartX.value = cx; dragStartY.value = cy
  petStartX.value = petX.value; petStartY.value = petY.value
  window.addEventListener('mousemove', onDrag)
  window.addEventListener('mouseup', stopDrag)
  window.addEventListener('touchmove', onDrag, { passive: false })
  window.addEventListener('touchend', stopDrag)
}

function onDrag(e) {
  const cx = e.touches ? e.touches[0].clientX : e.clientX
  const cy = e.touches ? e.touches[0].clientY : e.clientY
  if (Math.abs(cx - dragStartX.value) > 3 || Math.abs(cy - dragStartY.value) > 3) hasMoved = true
  const pos = clamp(petStartX.value + cx - dragStartX.value, petStartY.value + cy - dragStartY.value)
  petX.value = pos.x; petY.value = pos.y
}

function stopDrag() {
  petStore.isDragging = false
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', stopDrag)
  window.removeEventListener('touchmove', onDrag)
  window.removeEventListener('touchend', stopDrag)
  localStorage.setItem('pet_x', petX.value)
  localStorage.setItem('pet_y', petY.value)
}

function onMouseEnter() { isHovered.value = true; petStore.setMood('waving') }
function onMouseLeave() { isHovered.value = false; petStore.resetMood() }

function onClick() {
  if (hasMoved) return
  isClicked.value = true
  petStore.triggerHappy()
  setTimeout(() => { isClicked.value = false }, 1200)
  togglePanel()
}

// ════════════════ GSAP Animations (same as original) ════════════════
function killAll() {
  animations.value.forEach(a => { try { a.kill() } catch(e) {} })
  animations.value = []
  gsap.killTweensOf('*')
}

function animateIdle() {
  killAll(); if (!petEl.value) return
  const el = petEl.value
  gsap.set(el, { clearProps: 'all' })
  gsap.set(svgRef.value, { clearProps: 'all' })
  gsap.set([leftArmRef.value, rightArmRef.value], { clearProps: 'all' })
  gsap.set([leftPupilRef.value, rightPupilRef.value], { clearProps: 'all' })
  gsap.set(mouthRef.value, { attr: { d: 'M 52,78 Q 60,85 68,78' } })
  gsap.set(leafRef.value, { clearProps: 'all' })
  gsap.set(bodyRef.value, { clearProps: 'all' })
  gsap.set([thinkRef.value, sleepRef.value, sparkleRef.value, teachRef.value], { display: 'none' })
  const float = gsap.timeline({ repeat: -1, yoyo: true }).to(el, { y: '-=6', duration: 1.8, ease: 'sine.inOut' }).to(el, { y: '+=6', duration: 1.8, ease: 'sine.inOut' })
  const blink = gsap.timeline({ repeat: -1, repeatDelay: 3 }).to([leftEyeRef.value, rightEyeRef.value], { scaleY: 0.1, duration: 0.1, transformOrigin: 'center center' }).to([leftEyeRef.value, rightEyeRef.value], { scaleY: 1, duration: 0.1 })
  const breathe = gsap.timeline({ repeat: -1, yoyo: true }).to(bodyRef.value, { scale: 1.02, duration: 1.8, ease: 'sine.inOut', transformOrigin: '60px 72px' })
  animations.value.push(float, blink, breathe)
}

function animateThinking() {
  killAll(); if (!petEl.value) return
  gsap.set(mouthRef.value, { attr: { d: 'M 54,80 Q 60,84 66,80' } })
  gsap.set([thinkRef.value, sleepRef.value, sparkleRef.value, teachRef.value], { display: 'none' })
  const tilt = gsap.timeline({ repeat: -1, yoyo: true }).to(svgRef.value, { rotation: -4, duration: 1.2, ease: 'sine.inOut', transformOrigin: '60px 72px' }).to(svgRef.value, { rotation: 0, duration: 1.2 })
  gsap.to([leftPupilRef.value, rightPupilRef.value], { y: -1.5, duration: 0.4 })
  const portPulse = gsap.timeline({ repeat: -1, yoyo: true }).to(portsRef.value, { opacity: 0.5, scale: 0.9, duration: 0.6 }).to(portsRef.value, { opacity: 1, scale: 1.1, duration: 0.6 })
  gsap.set(thinkRef.value, { display: 'block', opacity: 0 })
  gsap.to(thinkRef.value, { opacity: 1, duration: 0.4, y: -8 })
  animations.value.push(tilt, portPulse)
}

function animateTeaching() {
  killAll(); if (!petEl.value) return
  gsap.set(mouthRef.value, { attr: { d: 'M 52,76 Q 60,82 68,76' } })
  gsap.set([thinkRef.value, sleepRef.value, sparkleRef.value], { display: 'none' })
  gsap.set(teachRef.value, { display: 'block', opacity: 0 })
  gsap.to(teachRef.value, { opacity: 1, duration: 0.5 })
  const linePulse = gsap.timeline({ repeat: -1, yoyo: true }).to(teachRef.value, { opacity: 0.6, duration: 1.2 }).to(teachRef.value, { opacity: 1, duration: 1.2 })
  animations.value.push(linePulse)
}

function animateHappy() {
  killAll(); if (!petEl.value) return
  gsap.set(mouthRef.value, { attr: { d: 'M 52,76 Q 60,68 68,76' } })
  gsap.set([thinkRef.value, sleepRef.value, teachRef.value], { display: 'none' })
  const bounce = gsap.timeline().to(petEl.value, { y: '-=15', duration: 0.2 }).to(petEl.value, { y: '+=15', duration: 0.3, ease: 'bounce.out' }).to(petEl.value, { y: '-=8', duration: 0.15 }).to(petEl.value, { y: '+=8', duration: 0.25 })
  gsap.set(sparkleRef.value, { display: 'block', opacity: 0, scale: 0 })
  gsap.to(sparkleRef.value, { opacity: 1, scale: 1, duration: 0.3 }).to(sparkleRef.value, { opacity: 0, duration: 0.3, delay: 1.5 })
  gsap.to(bodyRef.value, { attr: { fill: 'url(#bodyGradBright)' }, duration: 0.3 })
  gsap.to(bodyRef.value, { attr: { fill: 'url(#bodyGrad)' }, duration: 0.5, delay: 1.5 })
  gsap.fromTo(leafRef.value, { rotation: -15 }, { rotation: 10, duration: 0.2, yoyo: true, repeat: 2, transformOrigin: '60px 44px' })
  animations.value.push(bounce)
}

function animateSad() {
  killAll(); if (!petEl.value) return
  gsap.set(mouthRef.value, { attr: { d: 'M 54,84 Q 60,90 66,84' } })
  gsap.set([thinkRef.value, sleepRef.value, sparkleRef.value, teachRef.value], { display: 'none' })
  gsap.to(svgRef.value, { rotation: 3, duration: 0.4, transformOrigin: '60px 72px' })
  gsap.to([leftPupilRef.value, rightPupilRef.value], { y: 1.5, duration: 0.3 })
  gsap.to(leafRef.value, { rotation: -20, duration: 0.4, transformOrigin: '60px 44px' })
  gsap.to(leftArmRef.value, { y: 6, x: 2, duration: 0.4 })
  gsap.to(rightArmRef.value, { y: 6, x: -2, duration: 0.4 })
  gsap.to(bodyRef.value, { scaleY: 0.95, duration: 0.3, transformOrigin: '60px 72px' })
}

function animateWaving() {
  killAll(); if (!petEl.value) return
  gsap.set(mouthRef.value, { attr: { d: 'M 52,76 Q 60,82 68,76' } })
  gsap.set([thinkRef.value, sleepRef.value, sparkleRef.value, teachRef.value], { display: 'none' })
  const wave = gsap.timeline({ repeat: 2, yoyo: true }).to(rightArmRef.value, { rotation: -25, duration: 0.2, transformOrigin: '86px 70px' }).to(rightArmRef.value, { rotation: 5, duration: 0.2 }).to(rightArmRef.value, { rotation: -20, duration: 0.2 }).to(rightArmRef.value, { rotation: 0, duration: 0.2 })
  animations.value.push(wave)
}

function animateWaiting() {
  killAll(); if (!petEl.value) return
  gsap.set(mouthRef.value, { attr: { d: 'M 54,80 Q 60,83 66,80' } })
  gsap.set([thinkRef.value, sleepRef.value, sparkleRef.value, teachRef.value], { display: 'none' })
  gsap.to(petEl.value, { scaleY: 0.9, duration: 0.3, transformOrigin: 'bottom center' })
  const look = gsap.timeline({ repeat: -1, yoyo: true }).to([leftPupilRef.value, rightPupilRef.value], { x: -2, duration: 0.8 }).to([leftPupilRef.value, rightPupilRef.value], { x: 2, duration: 0.8 })
  animations.value.push(look)
}

function animateSleeping() {
  killAll(); if (!petEl.value) return
  gsap.set(mouthRef.value, { attr: { d: 'M 55,81 Q 60,83 65,81' } })
  gsap.set([thinkRef.value, sparkleRef.value, teachRef.value], { display: 'none' })
  gsap.to([leftEyeRef.value, rightEyeRef.value], { scaleY: 0.08, duration: 0.4, transformOrigin: 'center center' })
  gsap.to(svgRef.value, { rotation: 5, duration: 0.5, transformOrigin: '60px 72px' })
  gsap.to(bodyRef.value, { scale: 0.97, duration: 0.5, transformOrigin: '60px 72px' })
  gsap.to(leftArmRef.value, { y: 5, duration: 0.5 })
  gsap.to(rightArmRef.value, { y: 5, duration: 0.5 })
  gsap.set(sleepRef.value, { display: 'block', opacity: 0 })
  gsap.to(sleepRef.value, { opacity: 1, duration: 0.5 })
  const zFloat = gsap.timeline({ repeat: -1 }).to(sleepRef.value, { y: -12, duration: 2.5 }).to(sleepRef.value, { y: 0, duration: 0 })
  const breathe = gsap.timeline({ repeat: -1, yoyo: true }).to(bodyRef.value, { scale: 1.02, duration: 2.5, ease: 'sine.inOut', transformOrigin: '60px 72px' })
  const float = gsap.timeline({ repeat: -1, yoyo: true }).to(petEl.value, { y: '-=3', duration: 2.5, ease: 'sine.inOut' }).to(petEl.value, { y: '+=3', duration: 2.5, ease: 'sine.inOut' })
  animations.value.push(zFloat, breathe, float)
}

const moodAnimations = {
  idle: animateIdle, thinking: animateThinking, teaching: animateTeaching,
  happy: animateHappy, sad: animateSad, waving: animateWaving,
  waiting: animateWaiting, sleeping: animateSleeping,
}

watch(() => petStore.currentMood, (newMood) => {
  const fn = moodAnimations[newMood]
  if (fn) fn()
})

function startAutoTimer() {
  clearInterval(autoTimer.value)
  autoTimer.value = setInterval(() => {
    if (petStore.isDragging) return
    if (petStore.currentMood === 'sleeping') return
    const elapsed = (Date.now() - petStore.lastInteraction) / 1000
    if (elapsed > 60 && petStore.currentMood !== 'waiting') petStore.setMood('waiting')
    if (elapsed > 120) petStore.setMood('sleeping')
  }, 5000)
}

onMounted(() => {
  petStore.recordInteraction()
  startAutoTimer()
  if (route.path.startsWith('/learn/')) {
    petStore.isLearningPage = true
    petStore.setMood('teaching')
  }
  nextTick(() => animateIdle())
})

onBeforeUnmount(() => {
  killAll()
  clearInterval(autoTimer.value)
})
</script>

<style scoped>
.desk-pet {
  position: fixed;
  z-index: 1001;
  cursor: grab;
  user-select: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: filter 0.25s;
}
.desk-pet.is-dragging { cursor: grabbing; }
.desk-pet.is-dragging .pet-svg-wrapper { transform: scale(0.92); transition: transform 0.2s; }

/* ── Title Badge ── */
.title-badge {
  position: absolute;
  bottom: 130px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 12px 4px 8px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.12);
  white-space: nowrap;
  cursor: pointer;
  transition: all var(--transition-fast);
  z-index: 10;
}
.title-badge:hover {
  transform: translateX(-50%) translateY(-2px);
  box-shadow: 0 6px 22px rgba(139, 92, 246, 0.18);
}
.title-badge-icon {
  font-size: 14px;
}
.title-badge-text {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-accent-purple);
  letter-spacing: 0.02em;
}
.badge-pop-enter-active { animation: badgeIn 0.3s ease-out; }
.badge-pop-leave-active { animation: badgeIn 0.2s ease-in reverse; }
@keyframes badgeIn {
  from { opacity: 0; transform: translateX(-50%) translateY(6px) scale(0.85); }
  to { opacity: 1; transform: translateX(-50%) translateY(0) scale(1); }
}

/* ── SVG ── */
.pet-svg-wrapper {
  width: 110px;
  height: auto;
  cursor: pointer;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), filter 0.3s ease;
}
.desk-pet:hover .pet-svg-wrapper {
  transform: scale(1.12);
  filter: brightness(1.08) drop-shadow(0 6px 20px rgba(99,102,241,0.3));
}
.pet-svg { display: block; width: 100%; height: auto; overflow: visible; }

.pet-shadow {
  width: 44px; height: 10px;
  background: rgba(0, 0, 0, 0.12);
  border-radius: 50%;
  filter: blur(4px);
  transition: all 0.4s ease;
  margin-top: -2px;
}
.pet-shadow.is-active { animation: shadowPulse 3.5s ease-in-out infinite; }
@keyframes shadowPulse {
  0%,100%{transform:scale(1);opacity:.4;width:44px}
  25%{transform:scale(.85);opacity:.3;width:38px}
  55%{transform:scale(1.1);opacity:.55;width:50px}
  75%{transform:scale(.92);opacity:.4;width:42px}
}
.desk-pet:hover .pet-shadow { width: 56px; opacity: 0.55; }
.desk-pet.is-dragging .pet-shadow { width: 50px; opacity: 0.45; }

.pet-tooltip {
  position: absolute;
  top: -32px; left: 50%;
  transform: translateX(-50%);
  padding: 4px 12px;
  background: rgba(99, 102, 241, 0.92);
  color: #fff;
  font-size: 11px;
  font-weight: 500;
  border-radius: 10px;
  white-space: nowrap;
  pointer-events: none;
  box-shadow: 0 3px 14px rgba(99,102,241,0.25);
}
.pet-tooltip::after {
  content: '';
  position: absolute;
  bottom: -5px; left: 50%;
  transform: translateX(-50%);
  width: 0; height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: 5px solid rgba(99, 102, 241, 0.92);
}

.bubble-pop-enter-active { animation: bubbleIn 0.25s ease-out; }
.bubble-pop-leave-active { animation: bubbleIn 0.15s ease-in reverse; }
@keyframes bubbleIn {
  from { opacity: 0; transform: translateX(-50%) translateY(6px) scale(0.85); }
  to { opacity: 1; transform: translateX(-50%) translateY(0) scale(1); }
}

.mood-happy .pet-svg-wrapper { filter: brightness(1.1); }
.mood-sad .pet-svg-wrapper { filter: brightness(0.85) saturate(0.7); }
.mood-sleeping .pet-shadow { animation: none; opacity: 0.2; width: 38px; }

/* ════════════════ ACHIEVEMENT PANEL ════════════════ */
.achievement-panel {
  position: absolute;
  bottom: 0;
  left: 120px;
  width: 300px;
  max-height: 460px;
  overflow-y: auto;
  background: var(--bg-color);
  border: 1px solid var(--border-light);
  border-radius: 16px;
  box-shadow: 0 12px 40px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.06);
  padding: 20px;
  z-index: 20;
}
.achievement-panel::-webkit-scrollbar { width: 4px; }
.achievement-panel::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 2px; }

.ap-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.ap-title {
  font-size: 15px;
  font-weight: 800;
  color: var(--text-main);
  margin: 0;
}
.ap-close {
  width: 28px; height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: var(--bg-secondary);
  border-radius: 8px;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.ap-close:hover { background: var(--bg-tertiary); color: var(--text-main); }

.ap-current {
  margin-bottom: 12px;
}
.ap-current-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  background: var(--hero-gradient-soft);
  border-radius: 12px;
  margin-bottom: 10px;
}
.ap-badge-emoji {
  font-size: 28px;
}
.ap-badge-info {
  display: flex;
  flex-direction: column;
}
.ap-badge-title {
  font-size: 15px;
  font-weight: 800;
  color: var(--color-accent-purple);
}
.ap-badge-sub {
  font-size: 11px;
  color: var(--text-tertiary);
}
.ap-level-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
}
.ap-level-label {
  font-size: 12px;
  color: var(--text-secondary);
}
.ap-level-value {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-primary);
}

.ap-divider {
  height: 1px;
  background: var(--border-light);
  margin: 14px 0;
}

.ap-section-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin: 0 0 10px;
}

.ap-achievements {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.ap-achievement {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 10px;
  transition: background var(--transition-fast);
}
.ap-achievement.unlocked { opacity: 1; }
.ap-achievement:not(.unlocked) { opacity: 0.5; filter: grayscale(0.5); }

.ap-ach-icon { font-size: 18px; flex-shrink: 0; }
.ap-ach-info { flex: 1; display: flex; flex-direction: column; gap: 1px; }
.ap-ach-name { font-size: 12.5px; font-weight: 600; color: var(--text-main); }
.ap-ach-desc { font-size: 10.5px; color: var(--text-tertiary); }
.ap-ach-date { font-size: 10px; color: var(--text-tertiary); flex-shrink: 0; }

.ap-milestones {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.ap-milestone {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 4px;
}
.ap-milestone.reached { opacity: 1; }
.ap-milestone:not(.reached) { opacity: 0.4; }
.ap-ms-icon { width: 20px; text-align: center; font-size: 14px; flex-shrink: 0; }
.ap-ms-label { font-size: 12.5px; color: var(--text-secondary); }

/* Panel slide animation */
.panel-slide-enter-active { animation: panelSlideIn 0.3s cubic-bezier(0.16,1,0.3,1); }
.panel-slide-leave-active { animation: panelSlideIn 0.2s ease-in reverse; }
@keyframes panelSlideIn {
  from { opacity: 0; transform: translateY(12px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
</style>
