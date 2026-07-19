<template>
  <div class="practice-page animate-in">
    <PracticeHero />
    <AIRecommendCard
      :recommend="aiRecommend"
      :loading="loadingRecommend"
      @start="handleStartRecommend"
    />
    <PracticeModeGrid :modes="practiceModes" />
    <RecentPractice
      :items="recentItems"
      @resume="handleResume"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PracticeHero from './PracticeHero.vue'
import AIRecommendCard from './AIRecommendCard.vue'
import PracticeModeGrid from './PracticeModeGrid.vue'
import RecentPractice from './RecentPractice.vue'
import { PRACTICE_MODES, DEFAULT_RECOMMEND } from './practiceData'
import { getAIRecommend, getRecentPractice } from '@/api/practice'

const router = useRouter()

const practiceModes = PRACTICE_MODES
const aiRecommend = ref({ ...DEFAULT_RECOMMEND })
const loadingRecommend = ref(true)
const recentItems = ref([])

onMounted(async () => {
  // parallel load
  const [recommend, recent] = await Promise.all([
    getAIRecommend().catch(() => DEFAULT_RECOMMEND),
    getRecentPractice().catch(() => []),
  ])
  aiRecommend.value = recommend || DEFAULT_RECOMMEND
  loadingRecommend.value = false
  recentItems.value = recent
})

function handleStartRecommend(rec) {
  if (rec?.nodeId) {
    router.push(`/app/exam/${rec.nodeId}`)
  }
}

function handleResume(item) {
  if (item?.nodeId) {
    router.push(`/app/exam/${item.nodeId}`)
  }
}
</script>

<style scoped>
.practice-page {
  max-width: 1280px;
  margin: 0 auto;
  padding: var(--space-6) var(--space-8) var(--space-12);
}

@media (max-width: 900px) {
  .practice-page { padding: var(--space-5) var(--space-4) var(--space-8); }
}

@media (max-width: 600px) {
  .practice-page { padding: var(--space-4) var(--space-3) var(--space-6); }
}
</style>
