<template>
  <router-view></router-view>
</template>

<script setup>
import { useTheme } from './composables/useTheme'
import { useGlobalTimer } from './composables/useGlobalTimer'

// Initialize theme system
useTheme()

// ★ 启动全局在线计时器（跨所有页面追踪在线时长）
useGlobalTimer()
</script>

<style>
/* App global styles are in src/assets/styles/index.scss */
</style>
