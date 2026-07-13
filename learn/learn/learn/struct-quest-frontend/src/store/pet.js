 /**
  * 探探的情绪状态 Store
  * 其他组件可以通过此 store 触发宠物的表情/动画
  */
 import { defineStore } from 'pinia'
 import { ref, computed } from 'vue'
 
 export const usePetStore = defineStore('pet', () => {
   const moods = [
     'idle',       // 默认 - 悠闲漂浮
     'thinking',   // AI 思考中
     'teaching',   // 讲解知识
     'happy',      // 答对/完成
     'sad',        // 答错/失败
     'waving',     // 打招呼
     'waiting',    // 等待操作
     'sleeping',   // 长时间不活跃
   ]
 
   const currentMood = ref('idle')
   const lastInteraction = ref(Date.now())
   const isLearningPage = ref(false)
   const isAIChatting = ref(false)
   const isDragging = ref(false)
 
   const moodLabel = computed(() => {
     const labels = {
       idle: '悠闲中～',
       thinking: '思考中...',
       teaching: '讲解中',
       happy: '太棒了！',
       sad: '没关系再试试',
       waving: '嗨～',
       waiting: '快来学习啦',
       sleeping: 'zzz...',
     }
     return labels[currentMood.value] || '悠闲中～'
   })
 
   function setMood(mood) {
     if (moods.includes(mood)) {
       currentMood.value = mood
       lastInteraction.value = Date.now()
     }
   }
 
   function recordInteraction() {
     lastInteraction.value = Date.now()
     if (currentMood.value === 'sleeping') setMood('idle')
   }
 
   function resetMood() {
     setMood('idle')
   }
 
   function triggerHappy() {
     setMood('happy')
     setTimeout(() => { if (currentMood.value === 'happy') resetMood() }, 2500)
   }
 
   function triggerSad() {
     setMood('sad')
     setTimeout(() => { if (currentMood.value === 'sad') resetMood() }, 2500)
   }
 
   function triggerThinking() { setMood('thinking') }
   function stopThinking() { if (currentMood.value === 'thinking') setMood('idle') }
 
   return {
     moods, currentMood, lastInteraction,
     isLearningPage, isAIChatting, isDragging, moodLabel,
     setMood, recordInteraction, resetMood,
     triggerHappy, triggerSad, triggerThinking, stopThinking,
   }
 })
