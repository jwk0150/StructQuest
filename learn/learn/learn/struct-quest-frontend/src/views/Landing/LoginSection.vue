<template>
  <section id="login" class="login-section">
    <div class="section-inner">
      <div class="login-grid" ref="loginGrid">
        <!-- Left: Platform Intro -->
        <div class="login-info">
          <div class="login-logo">
            <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="8" fill="#4F7CFF"/>
              <path d="M9 22V10l7 6 7-6v12" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>StructQuest</span>
          </div>

          <h2>准备好开始了吗？</h2>
          <p class="login-info-desc">
            加入 12,800+ 名学习者，通过 AI 驱动的可视化方式，
            真正理解数据结构与算法之美。
          </p>

          <div class="login-perks">
            <div v-for="perk in perks" :key="perk" class="login-perk">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <circle cx="9" cy="9" r="8" stroke="#4F7CFF" stroke-width="1.5"/>
                <path d="M5.5 9l2.5 2.5 4.5-5" stroke="#4F7CFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>{{ perk }}</span>
            </div>
          </div>
        </div>

        <!-- Right: Login Card -->
        <div class="login-card-wrapper">
          <div class="login-card">
            <!-- Tabs -->
            <div class="login-tabs">
              <button
                :class="['tab-btn', { active: loginMode === 'login' }]"
                @click="loginMode = 'login'"
              >登录</button>
              <button
                :class="['tab-btn', { active: loginMode === 'register' }]"
                @click="loginMode = 'register'"
              >注册</button>
            </div>

            <!-- Login Form -->
            <form v-if="loginMode === 'login'" class="login-form" @submit.prevent="handleLogin">
              <div class="form-group">
                <label class="form-label">用户名</label>
                <input
                  v-model="loginForm.username"
                  type="text"
                  class="form-input"
                  placeholder="请输入用户名"
                />
              </div>
              <div class="form-group">
                <label class="form-label">密码</label>
                <input
                  v-model="loginForm.password"
                  type="password"
                  class="form-input"
                  placeholder="••••••••"
                />
              </div>
              <div class="form-row">
                <label class="remember-me">
                  <input type="checkbox" v-model="loginForm.remember" />
                  <span>记住我</span>
                </label>
                <a href="#" class="forgot-link">忘记密码？</a>
              </div>
              <button type="submit" class="btn-login" :class="{ loading: isLoading }">
                {{ isLoading ? '登录中…' : '登 录' }}
              </button>
            </form>

            <!-- Register Form -->
            <form v-else class="login-form" @submit.prevent="handleRegister">
              <div class="form-group">
                <label class="form-label">用户名</label>
                <input
                  v-model="registerForm.username"
                  type="text"
                  class="form-input"
                  placeholder="请输入用户名"
                />
              </div>
              <div class="form-group">
                <label class="form-label">邮箱</label>
                <input
                  v-model="registerForm.email"
                  type="email"
                  class="form-input"
                  placeholder="your@email.com"
                />
              </div>
              <div class="form-group">
                <label class="form-label">密码</label>
                <input
                  v-model="registerForm.password"
                  type="password"
                  class="form-input"
                  placeholder="至少 6 个字符"
                />
              </div>
              <button type="submit" class="btn-login" :class="{ loading: isLoading }">
                {{ isLoading ? '注册中…' : '创建账号' }}
              </button>
            </form>

            <!-- Divider -->
            <div class="login-divider">
              <span>或</span>
            </div>

            <!-- Social Login -->
            <div class="social-btns">
              <button class="btn-social" @click="handleSocialLogin('github')">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
                </svg>
                GitHub 登录
              </button>
              <button class="btn-social" @click="handleSocialLogin('google')">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
                Google 登录
              </button>
            </div>

            <!-- Guest -->
            <button class="btn-guest" @click="handleGuest">
              游客体验
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useSessionStore } from '../../store/session'
import { ElMessage } from 'element-plus'
import authApi from '../../api/auth'

gsap.registerPlugin(ScrollTrigger)

const router = useRouter()
const sessionStore = useSessionStore()

const loginMode = ref('login')
const isLoading = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
  remember: false,
})

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  major: '',
  grade: '',
  course: '数据结构',
  learning_goal: '',
  daily_study_time: '',
})

const perks = [
  '免费开始，无需信用卡',
  'AI 驱动的个性化学习路径',
  '50+ 知识点全面覆盖',
  '交互式可视化 + AI 助教',
]

const loginGrid = ref(null)

// ═══════ Login logic ═══════
async function handleLogin() {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  isLoading.value = true
  try {
    const res = await authApi.login({
      username: loginForm.username,
      password: loginForm.password,
    })
    sessionStore.login(res.user, res.token)
    ElMessage.success(`欢迎回来，${res.user.username}！`)
    // Navigate to the app
    const target = res.user.has_completed_onboarding ? '/app' : '/onboarding'
    setTimeout(() => router.push(target), 500)
  } catch (err) {
    ElMessage.error(err?.detail || '登录失败')
  } finally {
    isLoading.value = false
  }
}

async function handleRegister() {
  if (!registerForm.username || !registerForm.password) {
    ElMessage.warning('请填写完整信息')
    return
  }
  isLoading.value = true
  try {
    const res = await authApi.register({
      username: registerForm.username,
      password: registerForm.password,
      email: registerForm.email || undefined,
      major: registerForm.major || undefined,
      grade: registerForm.grade || undefined,
      course: registerForm.course || undefined,
      learning_goal: registerForm.learning_goal || undefined,
      daily_study_time: registerForm.daily_study_time || undefined,
    })
    sessionStore.login(res.user, res.token)
    ElMessage.success('注册成功！')
    setTimeout(() => router.push('/onboarding'), 500)
  } catch (err) {
    ElMessage.error(err?.detail || '注册失败')
  } finally {
    isLoading.value = false
  }
}

function handleSocialLogin(provider) {
  ElMessage.info(`${provider} 登录功能即将上线`)
}

async function handleGuest() {
  isLoading.value = true
  try {
    const res = await authApi.guest()
    sessionStore.login(res.user, res.token)
    setTimeout(() => router.push('/onboarding'), 500)
  } catch {
    ElMessage.error('游客登录失败')
  } finally {
    isLoading.value = false
  }
}

// ═══════ Animations ═══════
onMounted(() => {
  if (loginGrid.value) {
    gsap.from(loginGrid.value.querySelector('.login-info'), {
      scrollTrigger: { trigger: loginGrid.value, start: 'top 75%' },
      opacity: 0, x: -30, duration: 0.8, ease: 'power3.out',
    })
    gsap.from(loginGrid.value.querySelector('.login-card-wrapper'), {
      scrollTrigger: { trigger: loginGrid.value, start: 'top 75%' },
      opacity: 0, x: 30, duration: 0.8, ease: 'power3.out', delay: 0.15,
    })
  }
})
</script>

<style lang="scss" scoped>
.login-section {
  padding: var(--lp-section-gap, 140px) 40px;
  background: var(--lp-bg);
}

.section-inner {
  max-width: var(--lp-max-width);
  margin: 0 auto;
}

.login-grid {
  display: grid;
  grid-template-columns: 1fr 440px;
  gap: 80px;
  align-items: center;
  max-width: 1000px;
  margin: 0 auto;
}

/* ── Left: Info ── */
.login-info {
  h2 {
    font-family: var(--lp-font-display);
    font-size: 36px;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: var(--lp-text);
    margin: 24px 0 16px;
    line-height: 1.15;
  }
}

.login-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--lp-font-display);
  font-weight: 700;
  font-size: 18px;
  color: var(--lp-text);
}

.login-info-desc {
  font-size: 16px;
  line-height: 1.65;
  color: var(--lp-text-secondary);
  margin: 0 0 32px;
}

.login-perks {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.login-perk {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14.5px;
  color: var(--lp-text-secondary);

  svg { flex-shrink: 0; }
}

/* ── Right: Login Card ── */
.login-card-wrapper {
  display: flex;
  justify-content: center;
}

.login-card {
  width: 100%;
  max-width: 440px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid var(--lp-border-light);
  border-radius: var(--lp-radius-2xl);
  padding: 40px;
  box-shadow: var(--lp-shadow-lg);
}

/* Tabs */
.login-tabs {
  display: flex;
  gap: 4px;
  background: var(--lp-bg-secondary);
  border-radius: var(--lp-radius-lg);
  padding: 4px;
  margin-bottom: 32px;
}

.tab-btn {
  flex: 1;
  height: 40px;
  border-radius: var(--lp-radius-md);
  border: none;
  background: transparent;
  font-size: 14px;
  font-weight: 600;
  color: var(--lp-text-secondary);
  cursor: pointer;
  transition: all var(--lp-transition-fast);
  font-family: var(--lp-font-body);

  &.active {
    background: #fff;
    color: var(--lp-text);
    box-shadow: var(--lp-shadow-sm);
  }

  &:hover:not(.active) {
    color: var(--lp-text);
  }
}

/* Form */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--lp-text);
}

.form-input {
  height: 44px;
  padding: 0 14px;
  border: 1.5px solid var(--lp-border);
  border-radius: var(--lp-radius-lg);
  font-size: 14px;
  font-family: var(--lp-font-body);
  color: var(--lp-text);
  outline: none;
  background: var(--lp-bg);
  transition: all var(--lp-transition-fast);

  &::placeholder {
    color: var(--lp-text-tertiary);
  }

  &:focus {
    border-color: var(--lp-primary);
    box-shadow: 0 0 0 3px var(--lp-primary-light);
  }
}

.form-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--lp-text-secondary);
  cursor: pointer;

  input[type="checkbox"] {
    accent-color: var(--lp-primary);
  }
}

.forgot-link {
  font-size: 13px;
  color: var(--lp-primary);
  text-decoration: none;
  font-weight: 500;

  &:hover {
    text-decoration: underline;
  }
}

.btn-login {
  width: 100%;
  height: 48px;
  border-radius: var(--lp-radius-lg);
  border: none;
  background: var(--lp-primary);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  font-family: var(--lp-font-body);
  cursor: pointer;
  transition: all var(--lp-transition-base);
  letter-spacing: 0.02em;
  margin-top: 4px;

  &:hover:not(:disabled) {
    background: var(--lp-primary-hover);
    transform: translateY(-2px);
    box-shadow: 0 8px 24px var(--lp-primary-glow);
  }

  &:active:not(:disabled) {
    transform: translateY(0) scale(0.98);
  }

  &.loading {
    opacity: 0.7;
    cursor: wait;
  }
}

/* Divider */
.login-divider {
  text-align: center;
  margin-bottom: 20px;
  position: relative;

  &::before {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    top: 50%;
    height: 1px;
    background: var(--lp-border-light);
  }

  span {
    position: relative;
    display: inline-block;
    padding: 0 16px;
    background: #fff;
    font-size: 13px;
    color: var(--lp-text-tertiary);
  }
}

/* Social Buttons */
.social-btns {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.btn-social {
  flex: 1;
  height: 44px;
  border-radius: var(--lp-radius-lg);
  border: 1.5px solid var(--lp-border);
  background: var(--lp-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--lp-text);
  cursor: pointer;
  transition: all var(--lp-transition-fast);
  font-family: var(--lp-font-body);

  &:hover {
    border-color: var(--lp-text);
    background: var(--lp-bg-secondary);
  }
}

.btn-guest {
  width: 100%;
  height: 44px;
  border-radius: var(--lp-radius-lg);
  border: none;
  background: transparent;
  color: var(--lp-text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all var(--lp-transition-fast);
  font-family: var(--lp-font-body);

  &:hover {
    color: var(--lp-primary);

    svg {
      transform: translateX(3px);
    }
  }

  svg {
    transition: transform var(--lp-transition-fast);
  }
}

/* ── Responsive ── */
@media (max-width: 1024px) {
  .login-grid {
    grid-template-columns: 1fr;
    gap: 48px;
  }

  .login-info {
    text-align: center;
    max-width: 440px;
    margin: 0 auto;

    .login-logo {
      justify-content: center;
    }

    .login-perks {
      align-items: flex-start;
      text-align: left;
      max-width: 360px;
      margin: 0 auto;
    }
  }

  .login-card-wrapper {
    max-width: 440px;
    margin: 0 auto;
  }
}

@media (max-width: 640px) {
  .login-section {
    padding: 80px 24px;
  }

  .login-card {
    padding: 28px 20px;
  }
}
</style>
