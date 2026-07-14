<template>
  <div class="sq-layout">
    <!-- ═══ TOP NAVIGATION ═══ -->
    <TopNav />

    <!-- ═══ MAIN CONTENT (Full Width) ═══ -->
    <main class="content-area">
      <router-view v-slot="{ Component, route: r }">
        <transition name="page-fade" mode="out-in">
          <keep-alive :include="['Dashboard', 'Map']">
            <component :is="Component" :key="r.path" />
          </keep-alive>
        </transition>
      </router-view>
    </main>

    <!-- ═══ DESK PET (Bottom-Right Fixed) ═══ -->
    <DeskPet />
  </div>
</template>

<script setup>
import { watch } from 'vue'
import { useRoute } from 'vue-router'
import { usePetStore } from '@/store/pet'
import TopNav from '@/components/common/TopNav.vue'
import DeskPet from '@/components/DeskPet/index.vue'

const route = useRoute()
const petStore = usePetStore()

// Track learning pages for pet mood
watch(() => route.path, (path) => {
  petStore.isLearningPage = path.startsWith('/app/learn/') || path.startsWith('/app/exam/')
}, { immediate: true })
</script>

<style scoped>
.sq-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--bg-page);
}

.content-area {
  flex: 1;
  min-height: 0;
}

/* Page transition */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.page-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
