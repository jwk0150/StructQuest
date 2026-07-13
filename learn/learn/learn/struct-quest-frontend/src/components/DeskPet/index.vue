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
     <!-- SVG 角色 -->
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
 
         <!-- 阴影 -->
         <ellipse ref="shadowRef" cx="60" cy="134" rx="24" ry="5" fill="rgba(0,0,0,0.12)"/>
 
         <!-- 左臂 -->
         <g ref="leftArmRef" class="pet-arm left-arm">
           <path d="M 34,70 Q 16,64 12,76" fill="none" stroke="#8BBCFF" stroke-width="4.5" stroke-linecap="round"/>
           <circle cx="12" cy="76" r="5" fill="#C5DEFF" stroke="#8BBCFF" stroke-width="1.5"/>
         </g>
 
         <!-- 右臂 -->
         <g ref="rightArmRef" class="pet-arm right-arm">
           <path d="M 86,70 Q 104,64 108,76" fill="none" stroke="#8BBCFF" stroke-width="4.5" stroke-linecap="round"/>
           <circle cx="108" cy="76" r="5" fill="#C5DEFF" stroke="#8BBCFF" stroke-width="1.5"/>
         </g>
 
         <!-- 连接端口 -->
         <g ref="portsRef" class="pet-ports">
           <circle cx="31" cy="70" r="5" fill="white" stroke="#4F8CF7" stroke-width="1.5"/>
           <circle cx="31" cy="70" r="2" fill="#4F8CF7"/>
           <circle cx="89" cy="70" r="5" fill="white" stroke="#4F8CF7" stroke-width="1.5"/>
           <circle cx="89" cy="70" r="2" fill="#4F8CF7"/>
         </g>
 
         <!-- 身体 -->
         <circle ref="bodyRef" cx="60" cy="72" r="30" fill="url(#bodyGrad)" stroke="#4F8CF7" stroke-width="2.5" class="pet-body-circle"/>
 
         <!-- 腮红 -->
         <circle cx="44" cy="80" r="6" fill="url(#blushGrad)"/>
         <circle cx="76" cy="80" r="6" fill="url(#blushGrad)"/>
 
         <!-- 左眼 -->
         <g ref="leftEyeRef" class="pet-eye left-eye">
           <ellipse cx="48" cy="66" rx="6" ry="7" fill="white" stroke="#3B6CB7" stroke-width="1.5"/>
           <circle ref="leftPupilRef" cx="50" cy="67.5" r="3.2" fill="#2C3E50"/>
           <circle cx="49" cy="65" r="1.3" fill="white"/>
         </g>
 
         <!-- 右眼 -->
         <g ref="rightEyeRef" class="pet-eye right-eye">
           <ellipse cx="72" cy="66" rx="6" ry="7" fill="white" stroke="#3B6CB7" stroke-width="1.5"/>
           <circle ref="rightPupilRef" cx="74" cy="67.5" r="3.2" fill="#2C3E50"/>
           <circle cx="73" cy="65" r="1.3" fill="white"/>
         </g>
 
         <!-- 嘴巴 -->
         <path ref="mouthRef" d="M 52,78 Q 60,85 68,78" fill="none" stroke="#2C3E50" stroke-width="2.2" stroke-linecap="round" class="pet-mouth"/>
 
         <!-- 头顶小叶子 -->
         <g ref="leafRef" class="pet-leaf">
           <path d="M 60,44 Q 48,28 60,16 Q 72,28 60,44" fill="#22C55E" stroke="#16A34A" stroke-width="1.5"/>
           <line x1="60" y1="44" x2="60" y2="52" stroke="#16A34A" stroke-width="2.5"/>
         </g>
 
         <!-- 思考气泡 -->
         <g ref="thinkRef" class="pet-effect think-effect" style="display:none">
           <circle cx="60" cy="12" r="8" fill="white" stroke="#4F8CF7" stroke-width="1.5" stroke-dasharray="4 2">
             <animateTransform attributeName="transform" type="rotate" from="0 60 12" to="360 60 12" dur="4s" repeatCount="indefinite"/>
           </circle>
           <text x="57" y="15" font-size="11" fill="#4F8CF7" font-weight="bold">?</text>
         </g>
 
         <!-- 睡眠 Z -->
         <g ref="sleepRef" class="pet-effect sleep-effect" style="display:none">
           <text x="80" y="20" font-size="8" fill="#8BBCFF" font-weight="bold" opacity="0.4">z</text>
           <text x="88" y="8" font-size="10" fill="#8BBCFF" font-weight="bold" opacity="0.6">z</text>
           <text x="98" y="-2" font-size="12" fill="#8BBCFF" font-weight="bold" opacity="0.8">Z</text>
         </g>
 
         <!-- 开心星星 -->
         <g ref="sparkleRef" class="pet-effect sparkle-effect" style="display:none">
           <text x="20" y="40" font-size="10" fill="#FFD700">*</text>
           <text x="95" y="45" font-size="8" fill="#FFB347">*</text>
         </g>
 
         <!-- 教学连线 -->
         <g ref="teachRef" class="pet-effect teach-effect" style="display:none">
           <line x1="31" y1="70" x2="8" y2="90" stroke="#4F8CF7" stroke-width="1.5" stroke-dasharray="3 2" opacity="0.6"/>
           <line x1="89" y1="70" x2="112" y2="90" stroke="#4F8CF7" stroke-width="1.5" stroke-dasharray="3 2" opacity="0.6"/>
           <circle cx="8" cy="90" r="3" fill="#A8D4FF"/>
           <circle cx="112" cy="90" r="3" fill="#A8D4FF"/>
         </g>
       </svg>
     </div>
 
     <!-- 阴影 -->
     <div class="pet-shadow" :class="{ 'is-active': !['sleeping','thinking'].includes(petStore.currentMood) }"></div>
 
     <!-- 对话气泡 -->
     <transition name="bubble-pop">
       <div v-if="tooltipText && !petStore.isDragging" class="pet-tooltip">
         {{ tooltipText }}
       </div>
     </transition>
   </div>
 </template>
 
 <script setup>
 import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
 import { useRoute } from 'vue-router'
 import gsap from 'gsap'
 import { usePetStore } from '@/store/pet'
 
 const emit = defineEmits(['click'])
 const route = useRoute()
 const petStore = usePetStore()
 
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
 
 // ── Position ──
 const petX = ref(parseFloat(localStorage.getItem('pet_x')) || window.innerWidth - 140)
 const petY = ref(parseFloat(localStorage.getItem('pet_y')) || window.innerHeight - 240)
 const dragStartX = ref(0)
 const dragStartY = ref(0)
 const petStartX = ref(0)
 const petStartY = ref(0)
 let hasMoved = false
 
 // ── Interaction state ──
 const isHovered = ref(false)
 const isClicked = ref(false)
 const autoTimer = ref(null)
 const animations = ref([])
 
 // ── Computed ──
 const petStyle = computed(() => ({
   left: `${petX.value}px`,
   top: `${petY.value}px`,
 }))
 
 const tooltipText = computed(() => {
   if (petStore.isDragging || isClicked.value) return ''
   const t = {
     idle: '点我聊天',
     thinking: '让我想想...',
     teaching: '',
     happy: '',
     sad: '',
     waving: '嗨～',
     waiting: '开始学习吧',
     sleeping: 'zzz...',
   }
   return t[petStore.currentMood] || '点我聊天'
 })
 
 // ── Drag ──
 function clamp(x, y) {
   const w = 100, h = 120
   return {
     x: Math.max(0, Math.min(x, window.innerWidth - w)),
     y: Math.max(0, Math.min(y, window.innerHeight - h)),
   }
 }
 
 function startDrag(e) {
   hasMoved = false
   petStore.isDragging = true
   petStore.recordInteraction()
   const cx = e.touches ? e.touches[0].clientX : e.clientX
   const cy = e.touches ? e.touches[0].clientY : e.clientY
   dragStartX.value = cx
   dragStartY.value = cy
   petStartX.value = petX.value
   petStartY.value = petY.value
   window.addEventListener('mousemove', onDrag)
   window.addEventListener('mouseup', stopDrag)
   window.addEventListener('touchmove', onDrag, { passive: false })
   window.addEventListener('touchend', stopDrag)
 }
 
 function onDrag(e) {
   const cx = e.touches ? e.touches[0].clientX : e.clientX
   const cy = e.touches ? e.touches[0].clientY : e.clientY
   const dx = cx - dragStartX.value
   const dy = cy - dragStartY.value
   if (Math.abs(dx) > 3 || Math.abs(dy) > 3) hasMoved = true
   const pos = clamp(petStartX.value + dx, petStartY.value + dy)
   petX.value = pos.x
   petY.value = pos.y
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
 
 // ── Interaction ──
 function onMouseEnter() { isHovered.value = true; petStore.setMood('waving') }
 function onMouseLeave() { isHovered.value = false; petStore.resetMood() }
 
 function onClick() {
   if (hasMoved) return
   isClicked.value = true
   petStore.triggerHappy()
   setTimeout(() => { isClicked.value = false }, 1200)
   emit('click')
 }
 
 // ══════════════════════════════════════════
 // GSAP Animations
 // ══════════════════════════════════════════
 
 function killAll() {
   animations.value.forEach(a => { try { a.kill() } catch(e) {} })
   animations.value = []
   gsap.killTweensOf('*')
 }
 
 function animateIdle() {
   killAll()
   if (!petEl.value) return
   const el = petEl.value
   gsap.set(el, { clearProps: 'all' })
   gsap.set(svgRef.value, { clearProps: 'all' })
   gsap.set([leftArmRef.value, rightArmRef.value], { clearProps: 'all' })
   gsap.set([leftPupilRef.value, rightPupilRef.value], { clearProps: 'all' })
   gsap.set(mouthRef.value, { attr: { d: 'M 52,78 Q 60,85 68,78' } })
   gsap.set(leafRef.value, { clearProps: 'all' })
   gsap.set(bodyRef.value, { clearProps: 'all' })
   gsap.set([thinkRef.value, sleepRef.value, sparkleRef.value, teachRef.value], { display: 'none' })
 
   // 漂浮
   const float = gsap.timeline({ repeat: -1, yoyo: true })
     .to(el, { y: '-=6', duration: 1.8, ease: 'sine.inOut' }, 0)
     .to(el, { y: '+=6', duration: 1.8, ease: 'sine.inOut' }, 1.8)
   // 眨眼
   const blink = gsap.timeline({ repeat: -1, repeatDelay: 3 })
     .to([leftEyeRef.value, rightEyeRef.value], { scaleY: 0.1, duration: 0.1, transformOrigin: 'center center' })
     .to([leftEyeRef.value, rightEyeRef.value], { scaleY: 1, duration: 0.1, transformOrigin: 'center center' })
   // 呼吸
   const breathe = gsap.timeline({ repeat: -1, yoyo: true })
     .to(bodyRef.value, { scale: 1.02, duration: 1.8, ease: 'sine.inOut', transformOrigin: '60px 72px' })
   animations.value.push(float, blink, breathe)
 }
 
 function animateThinking() {
   killAll()
   if (!petEl.value) return
   const el = petEl.value
   gsap.set(el, { clearProps: 'all' })
   gsap.set(mouthRef.value, { attr: { d: 'M 54,80 Q 60,84 66,80' } })
   gsap.set([thinkRef.value, sleepRef.value, sparkleRef.value, teachRef.value], { display: 'none' })
 
   // 身体倾斜
   const tilt = gsap.timeline({ repeat: -1, yoyo: true })
     .to(svgRef.value, { rotation: -4, duration: 1.2, ease: 'sine.inOut', transformOrigin: '60px 72px' })
     .to(svgRef.value, { rotation: 0, duration: 1.2, ease: 'sine.inOut' })
   // 瞳孔上移
   gsap.to([leftPupilRef.value, rightPupilRef.value], { y: -1.5, duration: 0.4 })
   // 端口脉冲
   const portPulse = gsap.timeline({ repeat: -1, yoyo: true })
     .to(portsRef.value, { opacity: 0.5, scale: 0.9, duration: 0.6, transformOrigin: '60px 72px' })
     .to(portsRef.value, { opacity: 1, scale: 1.1, duration: 0.6, transformOrigin: '60px 72px' })
   // 显示思考气泡
   gsap.set(thinkRef.value, { display: 'block', opacity: 0 })
   gsap.to(thinkRef.value, { opacity: 1, duration: 0.4, y: -8, ease: 'back.out' })
   // 轻浮
   const float = gsap.timeline({ repeat: -1, yoyo: true })
     .to(el, { y: '-=8', duration: 1.5, ease: 'sine.inOut' })
     .to(el, { y: '+=8', duration: 1.5, ease: 'sine.inOut' })
   animations.value.push(tilt, portPulse, float)
 }
 
 function animateTeaching() {
   killAll()
   if (!petEl.value) return
   gsap.set(petEl.value, { clearProps: 'all' })
   gsap.set(mouthRef.value, { attr: { d: 'M 52,76 Q 60,82 68,76' } })
   gsap.set([thinkRef.value, sleepRef.value, sparkleRef.value], { display: 'none' })
   // 显示连线
   gsap.set(teachRef.value, { display: 'block', opacity: 0 })
   gsap.to(teachRef.value, { opacity: 1, duration: 0.5 })
   // 连线呼吸
   const linePulse = gsap.timeline({ repeat: -1, yoyo: true })
     .to(teachRef.value, { opacity: 0.6, duration: 1.2 })
     .to(teachRef.value, { opacity: 1, duration: 1.2 })
   animations.value.push(linePulse)
 }
 
 function animateHappy() {
   killAll()
   if (!petEl.value) return
   const el = petEl.value
   gsap.set(el, { clearProps: 'all' })
   gsap.set(mouthRef.value, { attr: { d: 'M 52,76 Q 60,68 68,76' } })
   gsap.set([thinkRef.value, sleepRef.value, teachRef.value], { display: 'none' })
 
   // 弹跳
   const bounce = gsap.timeline()
     .to(el, { y: '-=15', duration: 0.2, ease: 'power2.out' })
     .to(el, { y: '+=15', duration: 0.3, ease: 'bounce.out' })
     .to(el, { y: '-=8', duration: 0.15, ease: 'power2.out' })
     .to(el, { y: '+=8', duration: 0.25, ease: 'bounce.out' })
   // 星星
   gsap.set(sparkleRef.value, { display: 'block', opacity: 0, scale: 0 })
   gsap.to(sparkleRef.value, { opacity: 1, scale: 1, duration: 0.3, ease: 'back.out' })
   gsap.to(sparkleRef.value, { opacity: 0, duration: 0.3, delay: 1.5 })
   // 身体发光
   gsap.to(bodyRef.value, { attr: { fill: 'url(#bodyGradBright)' }, duration: 0.3 })
   gsap.to(bodyRef.value, { attr: { fill: 'url(#bodyGrad)' }, duration: 0.5, delay: 1.5 })
   // 叶子弹动
   gsap.fromTo(leafRef.value, { rotation: -15 }, { rotation: 10, duration: 0.2, yoyo: true, repeat: 2, transformOrigin: '60px 44px' })
   animations.value.push(bounce)
 }
 
 function animateSad() {
   killAll()
   if (!petEl.value) return
   gsap.set(petEl.value, { clearProps: 'all' })
   gsap.set(mouthRef.value, { attr: { d: 'M 54,84 Q 60,90 66,84' } })
   gsap.set([thinkRef.value, sleepRef.value, sparkleRef.value, teachRef.value], { display: 'none' })
 
   // 垂头
   gsap.to(svgRef.value, { rotation: 3, duration: 0.4, ease: 'power2.out', transformOrigin: '60px 72px' })
   // 瞳孔下移
   gsap.to([leftPupilRef.value, rightPupilRef.value], { y: 1.5, duration: 0.3 })
   // 叶子下垂
   gsap.to(leafRef.value, { rotation: -20, duration: 0.4, transformOrigin: '60px 44px' })
   // 垂肩
   gsap.to(leftArmRef.value, { y: 6, x: 2, duration: 0.4 })
   gsap.to(rightArmRef.value, { y: 6, x: -2, duration: 0.4 })
   // 身体微微压缩
   gsap.to(bodyRef.value, { scaleY: 0.95, duration: 0.3, transformOrigin: '60px 72px' })
   // 2.5s 后回到 idle
   gsap.to({}, { duration: 2, onComplete: () => {
     if (petStore.currentMood === 'sad') petStore.resetMood()
   }})
 }
 
 function animateWaving() {
   killAll()
   if (!petEl.value) return
   gsap.set(petEl.value, { clearProps: 'all' })
   gsap.set(mouthRef.value, { attr: { d: 'M 52,76 Q 60,82 68,76' } })
   gsap.set([thinkRef.value, sleepRef.value, sparkleRef.value, teachRef.value], { display: 'none' })
 
   // 右臂挥手
   const wave = gsap.timeline({ repeat: 2, yoyo: true })
     .to(rightArmRef.value, { rotation: -25, duration: 0.2, ease: 'power2.out', transformOrigin: '86px 70px' })
     .to(rightArmRef.value, { rotation: 5, duration: 0.2, ease: 'power2.out', transformOrigin: '86px 70px' })
     .to(rightArmRef.value, { rotation: -20, duration: 0.2, ease: 'power2.out', transformOrigin: '86px 70px' })
     .to(rightArmRef.value, { rotation: 0, duration: 0.2, ease: 'power2.out', transformOrigin: '86px 70px' })
   const float = gsap.timeline({ repeat: -1, yoyo: true })
     .to(petEl.value, { y: '-=4', duration: 0.6, ease: 'sine.inOut' })
     .to(petEl.value, { y: '+=4', duration: 0.6, ease: 'sine.inOut' })
   animations.value.push(wave, float)
 }
 
 function animateWaiting() {
   killAll()
   if (!petEl.value) return
   gsap.set(petEl.value, { clearProps: 'all' })
   gsap.set(mouthRef.value, { attr: { d: 'M 54,80 Q 60,83 66,80' } })
   gsap.set([thinkRef.value, sleepRef.value, sparkleRef.value, teachRef.value], { display: 'none' })
 
   // 坐下
   gsap.to(petEl.value, { scaleY: 0.9, duration: 0.3, transformOrigin: 'bottom center' })
   // 左右张望
   const look = gsap.timeline({ repeat: -1, yoyo: true })
     .to([leftPupilRef.value, rightPupilRef.value], { x: -2, duration: 0.8, ease: 'sine.inOut' })
     .to([leftPupilRef.value, rightPupilRef.value], { x: 2, duration: 0.8, ease: 'sine.inOut' })
   animations.value.push(look)
 }
 
 function animateSleeping() {
   killAll()
   if (!petEl.value) return
   gsap.set(petEl.value, { clearProps: 'all' })
   gsap.set(mouthRef.value, { attr: { d: 'M 55,81 Q 60,83 65,81' } })
   gsap.set([thinkRef.value, sparkleRef.value, teachRef.value], { display: 'none' })
 
   // 闭眼
   gsap.to([leftEyeRef.value, rightEyeRef.value], {
     scaleY: 0.08, duration: 0.4, ease: 'power2.in', transformOrigin: 'center center'
   })
   // 倾斜 + 放松
   gsap.to(svgRef.value, { rotation: 5, duration: 0.5, transformOrigin: '60px 72px' })
   gsap.to(bodyRef.value, { scale: 0.97, duration: 0.5, transformOrigin: '60px 72px' })
   gsap.to(leftArmRef.value, { y: 5, duration: 0.5 })
   gsap.to(rightArmRef.value, { y: 5, duration: 0.5 })
   // 显示 Z
   gsap.set(sleepRef.value, { display: 'block', opacity: 0 })
   gsap.to(sleepRef.value, { opacity: 1, duration: 0.5 })
   // Z 浮动
   const zFloat = gsap.timeline({ repeat: -1, delay: 0.5 })
     .to(sleepRef.value, { y: -12, duration: 2.5, ease: 'power1.out' })
     .to(sleepRef.value, { y: 0, duration: 0 })
   // 缓慢呼吸
   const breathe = gsap.timeline({ repeat: -1, yoyo: true })
     .to(bodyRef.value, { scale: 1.02, duration: 2.5, ease: 'sine.inOut', transformOrigin: '60px 72px' })
   const float = gsap.timeline({ repeat: -1, yoyo: true })
     .to(petEl.value, { y: '-=3', duration: 2.5, ease: 'sine.inOut' })
     .to(petEl.value, { y: '+=3', duration: 2.5, ease: 'sine.inOut' })
   animations.value.push(zFloat, breathe, float)
 }
 
 // ══════════════════════════════════════════
 // State machine
 // ══════════════════════════════════════════
 
 const moodAnimations = {
   idle: animateIdle,
   thinking: animateThinking,
   teaching: animateTeaching,
   happy: animateHappy,
   sad: animateSad,
   waving: animateWaving,
   waiting: animateWaiting,
   sleeping: animateSleeping,
 }
 
 watch(() => petStore.currentMood, (newMood) => {
   const fn = moodAnimations[newMood]
   if (fn) fn()
 })
 
 // 空闲超时进入 waiting -> sleeping
 function startAutoTimer() {
   clearInterval(autoTimer.value)
   autoTimer.value = setInterval(() => {
     const elapsed = (Date.now() - petStore.lastInteraction) / 1000
     if (petStore.isDragging) return
     if (petStore.currentMood === 'sleeping') return
     if (elapsed > 60 && petStore.currentMood !== 'waiting') petStore.setMood('waiting')
     if (elapsed > 120) petStore.setMood('sleeping')
   }, 5000)
 }
 
 // ── Lifecycle ──
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
 
 .pet-svg-wrapper {
   width: 110px;
   height: auto;
   cursor: pointer;
   transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), filter 0.3s ease;
 }
 .desk-pet:hover .pet-svg-wrapper {
   transform: scale(1.12);
   filter: brightness(1.08) drop-shadow(0 6px 20px rgba(79,140,247,0.3));
 }
 
 .pet-svg {
   display: block;
   width: 100%;
   height: auto;
   overflow: visible;
 }
 
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
   0%, 100% { transform: scale(1); opacity: 0.4; width: 44px; }
   25%  { transform: scale(0.85); opacity: 0.3; width: 38px; }
   55%  { transform: scale(1.1); opacity: 0.55; width: 50px; }
   75%  { transform: scale(0.92); opacity: 0.4; width: 42px; }
 }
 .desk-pet:hover .pet-shadow { width: 56px; opacity: 0.55; }
 .desk-pet.is-dragging .pet-shadow { width: 50px; opacity: 0.45; }
 
 .pet-tooltip {
   position: absolute;
   top: -32px; left: 50%;
   transform: translateX(-50%);
   padding: 4px 12px;
   background: rgba(79, 140, 247, 0.92);
   color: #fff;
   font-size: 11px;
   font-weight: 500;
   border-radius: 10px;
   white-space: nowrap;
   pointer-events: none;
   box-shadow: 0 3px 14px rgba(79,140,247,0.25);
 }
 .pet-tooltip::after {
   content: '';
   position: absolute;
   bottom: -5px; left: 50%;
   transform: translateX(-50%);
   width: 0; height: 0;
   border-left: 5px solid transparent;
   border-right: 5px solid transparent;
   border-top: 5px solid rgba(79, 140, 247, 0.92);
 }
 
 .bubble-pop-enter-active { animation: bubbleIn 0.25s ease-out; }
 .bubble-pop-leave-active { animation: bubbleIn 0.15s ease-in reverse; }
 @keyframes bubbleIn {
   from { opacity: 0; transform: translateX(-50%) translateY(6px) scale(0.85); }
   to   { opacity: 1; transform: translateX(-50%) translateY(0) scale(1); }
 }
 
 .mood-happy .pet-svg-wrapper { filter: brightness(1.1); }
 .mood-sad .pet-svg-wrapper { filter: brightness(0.85) saturate(0.7); }
 .mood-sleeping .pet-shadow { animation: none; opacity: 0.2; width: 38px; }
 </style>
