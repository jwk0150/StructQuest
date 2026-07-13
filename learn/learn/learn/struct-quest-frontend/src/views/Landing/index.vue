<template>
  <div class="landing" :class="{ 'menu-open': mobileMenuOpen }">
    <!-- ═══════════ Fixed Navbar ═══════════ -->
    <nav class="navbar" :class="{ scrolled: isScrolled }">
      <div class="navbar-inner">
        <!-- Logo -->
        <a href="#" class="nav-logo" @click.prevent="scrollToTop">
          <div class="logo-icon">
            <svg width="22" height="22" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="8" fill="#4F7CFF"/>
              <path d="M9 22V10l7 6 7-6v12" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <span class="logo-text">StructQuest</span>
        </a>

        <!-- Desktop Nav Links -->
        <div class="nav-links">
          <a v-for="link in navLinks" :key="link.id" :href="link.href" class="nav-link" @click.prevent="scrollToSection(link.id)">
            {{ link.label }}
          </a>
        </div>

        <!-- Right Actions -->
        <div class="nav-actions">
          <button class="btn-nav-login" @click="scrollToSection('login')">登录</button>
          <button class="btn-nav-start" @click="scrollToSection('login')">免费开始</button>
        </div>

        <!-- Mobile Menu Toggle -->
        <button class="mobile-toggle" @click="mobileMenuOpen = !mobileMenuOpen">
          <span></span><span></span><span></span>
        </button>
      </div>
    </nav>

    <!-- ═══════════ Main Content ═══════════ -->
    <main class="landing-main">
      <HeroSection />
      <PlatformIntro />
      <CoreFeatures />
      <LearningFlow />
      <DataVisualization />
      <AITutor />
      <Statistics />
      <LoginSection />
    </main>

    <!-- ═══════════ Footer ═══════════ -->
    <footer class="landing-footer">
      <div class="footer-inner">
        <div class="footer-brand">
          <div class="logo-icon">
            <svg width="20" height="20" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="8" fill="#4F7CFF"/>
              <path d="M9 22V10l7 6 7-6v12" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <span class="logo-text">StructQuest</span>
          <p class="footer-desc">AI 驱动的数据结构个性化学习平台</p>
        </div>
        <div class="footer-links">
          <div class="footer-col">
            <h4>产品</h4>
            <a href="#">首页</a><a href="#">学习路径</a><a href="#">可视化</a><a href="#">AI 助教</a>
          </div>
          <div class="footer-col">
            <h4>资源</h4>
            <a href="#">文档</a><a href="#">API</a><a href="#">博客</a><a href="#">社区</a>
          </div>
          <div class="footer-col">
            <h4>关于</h4>
            <a href="#">团队</a><a href="#">联系我们</a><a href="#">隐私政策</a><a href="#">服务条款</a>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <span>&copy; 2026 StructQuest. All rights reserved.</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import HeroSection from './HeroSection.vue'
import PlatformIntro from './PlatformIntro.vue'
import CoreFeatures from './CoreFeatures.vue'
import LearningFlow from './LearningFlow.vue'
import DataVisualization from './DataVisualization.vue'
import AITutor from './AITutor.vue'
import Statistics from './Statistics.vue'
import LoginSection from './LoginSection.vue'

gsap.registerPlugin(ScrollTrigger)

// ═══════ Navbar scroll state ═══════
const isScrolled = ref(false)
const mobileMenuOpen = ref(false)

const navLinks = [
  { id: 'hero', label: '首页' },
  { id: 'platform', label: '学习路径' },
  { id: 'features', label: '可视化' },
  { id: 'ai-tutor', label: 'AI 助教' },
  { id: 'login', label: '关于' },
]

function scrollToSection(id) {
  mobileMenuOpen.value = false
  const el = document.getElementById(id)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// ═══════ Scroll listener ═══════
let scrollHandler
onMounted(() => {
  scrollHandler = () => {
    isScrolled.value = window.scrollY > 20
  }
  window.addEventListener('scroll', scrollHandler, { passive: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', scrollHandler)
  ScrollTrigger.getAll().forEach(t => t.kill())
})
</script>

<style lang="scss">
/* ═══════════════════════════════════════════
   LANDING PAGE — Global Design Tokens
   ═══════════════════════════════════════════ */
:root {
  --lp-bg: #FFFFFF;
  --lp-bg-secondary: #F8F9FB;
  --lp-primary: #4F7CFF;
  --lp-primary-hover: #3B5FD9;
  --lp-primary-light: rgba(79, 124, 255, 0.08);
  --lp-primary-glow: rgba(79, 124, 255, 0.15);
  --lp-text: #111827;
  --lp-text-secondary: #6B7280;
  --lp-text-tertiary: #9CA3AF;
  --lp-border: #E5E7EB;
  --lp-border-light: #F3F4F6;
  --lp-radius-sm: 8px;
  --lp-radius-md: 12px;
  --lp-radius-lg: 16px;
  --lp-radius-xl: 20px;
  --lp-radius-2xl: 24px;
  --lp-radius-full: 9999px;
  --lp-shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.04);
  --lp-shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06);
  --lp-shadow-md: 0 4px 16px rgba(0, 0, 0, 0.04), 0 2px 4px rgba(0, 0, 0, 0.04);
  --lp-shadow-lg: 0 10px 40px rgba(0, 0, 0, 0.05), 0 2px 8px rgba(0, 0, 0, 0.04);
  --lp-shadow-xl: 0 20px 60px rgba(0, 0, 0, 0.06);
  --lp-font-display: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
  --lp-font-body: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --lp-font-mono: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;
  --lp-transition-fast: 0.15s cubic-bezier(0.4, 0, 0.2, 1);
  --lp-transition-base: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  --lp-transition-slow: 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  --lp-transition-spring: 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  --lp-max-width: 1440px;
  --lp-section-gap: 140px;
}

/* ═══════════════════════════════════════════
   BASE STYLES
   ═══════════════════════════════════════════ */
.landing {
  font-family: var(--lp-font-body);
  color: var(--lp-text);
  background: var(--lp-bg);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  overflow-x: hidden;
}

/* ═══════ NAVBAR ═══════ */
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  height: 64px;
  transition: all var(--lp-transition-base);
  background: transparent;

  &.scrolled {
    background: rgba(255, 255, 255, 0.82);
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border-bottom: 1px solid var(--lp-border-light);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  }
}

.navbar-inner {
  max-width: var(--lp-max-width);
  margin: 0 auto;
  padding: 0 40px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* Logo */
.nav-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: var(--lp-text);
  font-family: var(--lp-font-display);
  font-weight: 700;
  font-size: 18px;
  letter-spacing: -0.02em;
  flex-shrink: 0;

  .logo-icon {
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

/* Nav Links */
.nav-links {
  display: flex;
  align-items: center;
  gap: 4px;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.nav-link {
  padding: 8px 16px;
  border-radius: var(--lp-radius-md);
  font-size: 14px;
  font-weight: 500;
  color: var(--lp-text-secondary);
  text-decoration: none;
  transition: all var(--lp-transition-fast);

  &:hover {
    color: var(--lp-text);
    background: var(--lp-bg-secondary);
  }
}

/* Nav Actions */
.nav-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.btn-nav-login {
  padding: 8px 20px;
  border-radius: var(--lp-radius-lg);
  border: none;
  background: transparent;
  color: var(--lp-text);
  font-size: 14px;
  font-weight: 500;
  font-family: var(--lp-font-body);
  cursor: pointer;
  transition: all var(--lp-transition-fast);

  &:hover {
    background: var(--lp-bg-secondary);
  }
}

.btn-nav-start {
  padding: 8px 20px;
  border-radius: var(--lp-radius-lg);
  border: none;
  background: var(--lp-primary);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  font-family: var(--lp-font-body);
  cursor: pointer;
  transition: all var(--lp-transition-fast);

  &:hover {
    background: var(--lp-primary-hover);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px var(--lp-primary-glow);
  }
}

/* Mobile Toggle */
.mobile-toggle {
  display: none;
  flex-direction: column;
  gap: 5px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;

  span {
    display: block;
    width: 22px;
    height: 2px;
    background: var(--lp-text);
    border-radius: 2px;
    transition: all var(--lp-transition-fast);
  }
}

/* ═══════ MAIN ═══════ */
.landing-main {
  padding-top: 0;
}

/* ═══════ FOOTER ═══════ */
.landing-footer {
  background: var(--lp-bg-secondary);
  border-top: 1px solid var(--lp-border-light);
  padding: 80px 40px 40px;
}

.footer-inner {
  max-width: var(--lp-max-width);
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  gap: 80px;
}

.footer-brand {
  max-width: 280px;

  .logo-icon {
    display: inline-flex;
    margin-bottom: 16px;
  }

  .logo-text {
    display: block;
    font-family: var(--lp-font-display);
    font-weight: 700;
    font-size: 18px;
    color: var(--lp-text);
    margin-bottom: 8px;
  }
}

.footer-desc {
  font-size: 14px;
  color: var(--lp-text-secondary);
  line-height: 1.6;
  margin: 0;
}

.footer-links {
  display: flex;
  gap: 80px;
}

.footer-col {
  h4 {
    font-size: 13px;
    font-weight: 600;
    color: var(--lp-text);
    margin: 0 0 16px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  a {
    display: block;
    font-size: 14px;
    color: var(--lp-text-secondary);
    text-decoration: none;
    margin-bottom: 10px;
    transition: color var(--lp-transition-fast);

    &:hover {
      color: var(--lp-primary);
    }
  }
}

.footer-bottom {
  max-width: var(--lp-max-width);
  margin: 48px auto 0;
  padding-top: 24px;
  border-top: 1px solid var(--lp-border);
  text-align: center;

  span {
    font-size: 13px;
    color: var(--lp-text-tertiary);
  }
}

/* ═══════ RESPONSIVE ═══════ */
@media (max-width: 1024px) {
  .nav-links {
    display: none;
  }

  .nav-actions {
    .btn-nav-login { display: none; }
  }

  .mobile-toggle {
    display: flex;
  }

  .navbar-inner {
    padding: 0 20px;
  }

  .footer-inner {
    flex-direction: column;
    gap: 48px;
  }

  .footer-links {
    gap: 40px;
    flex-wrap: wrap;
  }
}
</style>
