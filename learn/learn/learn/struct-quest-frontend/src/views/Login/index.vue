<template>
  <div class="login-container" @mousemove="onMouseMove">
    <!-- 左侧：卡通角色区域（保持不变） -->
    <div class="brand-section">
      <!-- 背景装饰 -->
      <div class="bg-decor">
        <div class="decor-circle decor-circle--1"></div>
        <div class="decor-circle decor-circle--2"></div>
        <div class="decor-dots"></div>
      </div>

      <!-- 角色舞台 -->
      <div class="characters-stage" ref="stageRef">
        <!-- 角色1：橙色半圆 — 活泼开朗 -->
        <div
          class="character char-orange"
          :class="{
            'has-entered': hasEntered,
            'focus-email': charState === 'email',
            'focus-password': charState === 'password',
            'peeking': isPeeking,
            'login-fail': charState === 'fail',
            'login-success': charState === 'success'
          }"
        >
          <div class="character-body char-orange-body">
            <div class="eyes eyes-pair">
              <div class="eye-wrapper">
                <div v-if="!(isPeeking && peekingChar !== 'orange')" class="eye" :style="charState === 'email' ? eyeBigStyle : ''">
                  <div class="pupil" :style="orangePupilStyle">
                    <span class="pupil-highlight"></span>
                  </div>
                </div>
                <div v-else class="eye eye-closed eye-closed--peek"></div>
              </div>
              <div class="eye-wrapper">
                <div v-if="!(isPeeking && peekingChar !== 'orange')" class="eye" :style="charState === 'email' ? eyeBigStyle : ''">
                  <div class="pupil" :style="orangePupil2Style">
                    <span class="pupil-highlight"></span>
                  </div>
                </div>
                <div v-else class="eye eye-closed eye-closed--peek"></div>
              </div>
            </div>
            <div class="mouth" :class="mouthClass('orange')"></div>
            <div class="blush blush--orange" :class="{ show: charState === 'success' }">
              <span></span><span></span>
            </div>
          </div>
        </div>

        <!-- 角色2：紫色矩形 — 傲娇丰富 -->
        <div
          class="character char-purple"
          :class="{
            'has-entered': hasEntered,
            'focus-email': charState === 'email',
            'focus-password': charState === 'password',
            'peeking': isPeeking,
            'login-fail': charState === 'fail',
            'login-success': charState === 'success'
          }"
        >
          <div class="character-body char-purple-body">
            <div class="blush blush--purple" :class="{ show: charState === 'email' || isPeeking }">
              <span></span><span></span>
            </div>
            <div class="eyes eyes-pair">
              <div class="eye-wrapper">
                <div v-if="!isPeeking" class="eye eye--narrow" :style="charState === 'email' ? eyeBigStyle : ''">
                  <div class="pupil pupil--slit" :style="purplePupilStyle">
                    <span class="pupil-highlight"></span>
                  </div>
                </div>
                <div v-else class="eye eye-closed eye-closed--angry"></div>
              </div>
              <div class="eye-wrapper">
                <div v-if="!isPeeking" class="eye eye--narrow" :style="charState === 'email' ? eyeBigStyle : ''">
                  <div class="pupil pupil--slit" :style="purplePupil2Style">
                    <span class="pupil-highlight"></span>
                  </div>
                </div>
                <div v-else class="eye eye-closed eye-closed--angry"></div>
              </div>
            </div>
            <div class="mouth mouth--purple" :class="mouthClass('purple')"></div>
          </div>
        </div>

        <!-- 角色3：黑色竖矩形 — 冷静呆萌 -->
        <div
          class="character char-black"
          :class="{
            'has-entered': hasEntered,
            'focus-email': charState === 'email',
            'focus-password': charState === 'password',
            'peeking': isPeeking,
            'login-fail': charState === 'fail',
            'login-success': charState === 'success'
          }"
        >
          <div class="character-body char-black-body">
            <div class="eyes eyes-pair eyes--wide">
              <div class="eye-wrapper">
                <div v-if="!isPeeking" class="eye eye--round" :style="charState === 'email' ? eyeBigStyle : ''">
                  <div class="pupil pupil--large" :style="blackPupilStyle">
                    <span class="pupil-highlight"></span>
                  </div>
                </div>
                <div v-else class="eye eye-closed eye-closed--flat"></div>
              </div>
              <div class="eye-wrapper">
                <div v-if="!isPeeking" class="eye eye--round" :style="charState === 'email' ? eyeBigStyle : ''">
                  <div class="pupil pupil--large" :style="blackPupil2Style">
                    <span class="pupil-highlight"></span>
                  </div>
                </div>
                <div v-else class="eye eye-closed eye-closed--flat"></div>
              </div>
            </div>
            <div class="mouth mouth--black" :class="mouthClass('black')"></div>
          </div>
        </div>

        <!-- 角色4：黄色圆角矩形 — 温和内敛 -->
        <div
          class="character char-yellow"
          :class="{
            'has-entered': hasEntered,
            'focus-email': charState === 'email',
            'focus-password': charState === 'password',
            'peeking': isPeeking,
            'login-fail': charState === 'fail',
            'login-success': charState === 'success'
          }"
        >
          <div class="character-body char-yellow-body">
            <div class="eyes eyes-pair">
              <div class="eye-wrapper">
                <div v-if="!isPeeking" class="eye eye--gentle" :style="charState === 'email' ? eyeBigStyle : ''">
                  <div class="pupil" :style="yellowPupilStyle">
                    <span class="pupil-highlight"></span>
                  </div>
                </div>
                <div v-else class="eye eye-closed eye-closed--gentle"></div>
              </div>
              <div class="eye-wrapper">
                <div v-if="!isPeeking" class="eye eye--gentle" :style="charState === 'email' ? eyeBigStyle : ''">
                  <div class="pupil" :style="yellowPupil2Style">
                    <span class="pupil-highlight"></span>
                  </div>
                </div>
                <div v-else class="eye eye-closed eye-closed--gentle"></div>
              </div>
            </div>
            <div class="mouth mouth--yellow" :class="mouthClass('yellow')"></div>
            <div class="blush blush--yellow" :class="{ show: charState === 'success' }">
              <span></span><span></span>
            </div>
          </div>
        </div>

        <!-- 地面阴影 -->
        <div class="ground-shadows" :class="{ 'has-entered': hasEntered }">
          <span class="shadow shadow--1"></span>
          <span class="shadow shadow--2"></span>
          <span class="shadow shadow--3"></span>
          <span class="shadow shadow--4"></span>
        </div>
      </div>

      <!-- 品牌文字 -->
      <div class="brand-content" :class="{ 'content-visible': brandVisible }">
        <div class="logo">StructQuest</div>
        <h1>AI 驱动的数据结构<br>个性化学习平台</h1>
        <p class="subtitle">摆脱枯燥的死记硬背，通过多智能体协同与动态画像，为你量身定制最适合的学习路径。</p>

        <div class="features">
          <div class="feature-item">
            <el-icon><DataLine /></el-icon>
            <span>MBTI式动态学习画像</span>
          </div>
          <div class="feature-item">
            <el-icon><Connection /></el-icon>
            <span>多智能体协同规划路径</span>
          </div>
          <div class="feature-item">
            <el-icon><ChatDotRound /></el-icon>
            <span>费曼学习法深度交互</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧：登录/注册/忘记密码 表单 -->
    <div class="form-section">
      <div class="form-wrapper">

        <!-- ═══ 登录模式 ═══ -->
        <template v-if="formMode === 'login'">
          <div class="form-header">
            <h2>欢迎回来</h2>
            <p>登录以继续你的数据结构探索之旅</p>
          </div>

          <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" class="modern-form" @submit.prevent>
            <el-form-item prop="username">
              <label class="field-label">用户名</label>
              <el-input
                ref="accountInputRef"
                v-model="loginForm.username"
                placeholder="请输入用户名"
                size="large"
                :prefix-icon="User"
                clearable
                @focus="onEmailFocus"
                @blur="onEmailBlur"
              />
            </el-form-item>

            <el-form-item prop="password">
              <label class="field-label">密码</label>
              <el-input
                ref="passwordInputRef"
                v-model="loginForm.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="请输入密码"
                size="large"
                :prefix-icon="Lock"
                show-password
                @focus="onPasswordFocus"
                @blur="onPasswordBlur"
                @keyup.enter="handleLogin"
              />
            </el-form-item>

            <!-- 记住我 + 忘记密码 -->
            <div class="form-options-row">
              <el-checkbox v-model="rememberMe" class="remember-check">记住我</el-checkbox>
              <a href="#" class="forgot-link" @click.prevent="formMode = 'forgot'">忘记密码？</a>
            </div>

            <el-button
              type="primary"
              size="large"
              class="submit-btn"
              :loading="loading"
              @click="handleLogin"
            >
              {{ loading ? '登录中...' : '登 录' }}
            </el-button>

            <div class="divider-row"><span>或</span></div>

            <el-button
              size="large"
              class="guest-btn"
              @click="handleGuestLogin"
            >
              游客体验
            </el-button>

            <div class="switch-mode">
              还没有账号？<a href="#" @click.prevent="switchToRegister">立即注册</a>
            </div>
          </el-form>
        </template>

        <!-- ═══ 注册模式 ═══ -->
        <template v-else-if="formMode === 'register'">
          <div class="form-header">
            <h2>创建账号</h2>
            <p>开始你的个性化数据结构学习之旅</p>
          </div>

          <el-form ref="registerFormRef" :model="registerForm" :rules="registerRules" class="modern-form" @submit.prevent>
            <el-form-item prop="username">
              <label class="field-label">用户名</label>
              <el-input
                v-model.trim="registerForm.username"
                placeholder="3~20 位，字母、数字、下划线"
                size="large"
                :prefix-icon="User"
                maxlength="20"
                clearable
                @input="onUsernameInput"
                @blur="onUsernameBlur"
              >
                <!-- 用户名查重状态图标 -->
                <template #suffix>
                  <transition name="fade">
                    <el-icon v-if="usernameCheckStatus === 'checking'" class="check-icon checking"><Loading /></el-icon>
                    <el-icon v-else-if="usernameCheckStatus === 'available'" class="check-icon success"><CircleCheck /></el-icon>
                    <el-icon v-else-if="usernameCheckStatus === 'taken'" class="check-icon error"><CircleClose /></el-icon>
                  </transition>
                </template>
              </el-input>
              <!-- 用户名实时提示 -->
              <transition name="slide">
                <span v-if="usernameMsg" class="field-hint" :class="usernameCheckStatus">
                  {{ usernameMsg }}
                </span>
              </transition>
            </el-form-item>

            <el-form-item prop="email">
              <label class="field-label">邮箱 <span class="optional-tag">选填</span></label>
              <el-input
                v-model="registerForm.email"
                placeholder="用于找回密码"
                size="large"
                :prefix-icon="Message"
                clearable
              />
            </el-form-item>

            <el-form-item prop="password">
              <label class="field-label">密码</label>
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="设置一个安全的密码"
                size="large"
                :prefix-icon="Lock"
                show-password
                @input="onPasswordInput"
              />
              <!-- 密码强度条 -->
              <transition name="slide">
                <div v-if="registerForm.password" class="strength-bar-wrap">
                  <div class="strength-bar-track">
                    <div class="strength-bar-fill" :style="{ width: strengthPercent + '%' }" :class="strengthLevel"></div>
                  </div>
                  <span class="strength-text" :class="strengthLevel">{{ strengthLabel }}</span>
                </div>
              </transition>
            </el-form-item>

            <el-form-item prop="confirmPassword">
              <label class="field-label">确认密码</label>
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="再次输入密码"
                size="large"
                :prefix-icon="Lock"
                show-password
                @keyup.enter="handleRegister"
              />
              <transition name="slide">
                <span v-if="registerForm.confirmPassword && registerForm.password !== registerForm.confirmPassword" class="field-hint error">
                  两次输入的密码不一致
                </span>
              </transition>
            </el-form-item>

            <!-- ═══ 冷启动画像：第一阶段 基础信息 ═══ -->
            <div class="profile-section-title">
              <span class="section-icon">🎓</span> 学习背景（帮你定制个性化路径）
            </div>

            <div class="profile-row">
              <el-form-item prop="major" class="profile-half">
                <label class="field-label">专业</label>
                <el-input v-model="registerForm.major" placeholder="如：计算机科学" size="large" clearable />
              </el-form-item>
              <el-form-item prop="grade" class="profile-half">
                <label class="field-label">年级</label>
                <el-select v-model="registerForm.grade" placeholder="选择年级" size="large" class="full-width" clearable>
                  <el-option label="大一" value="大一" />
                  <el-option label="大二" value="大二" />
                  <el-option label="大三" value="大三" />
                  <el-option label="大四" value="大四" />
                  <el-option label="研一" value="研一" />
                  <el-option label="研二" value="研二" />
                  <el-option label="其他" value="其他" />
                </el-select>
              </el-form-item>
            </div>

            <el-form-item prop="course">
              <label class="field-label">课程</label>
              <el-input v-model="registerForm.course" placeholder="如：数据结构" size="large" clearable />
            </el-form-item>

            <el-form-item prop="learning_goal">
              <label class="field-label">学习目标</label>
              <el-select v-model="registerForm.learning_goal" placeholder="选择你的学习目标" size="large" class="full-width" clearable>
                <el-option label="期末考试" value="期末考试" />
                <el-option label="考研" value="考研" />
                <el-option label="课程预习" value="课程预习" />
                <el-option label="日常学习" value="日常学习" />
                <el-option label="项目实践" value="项目实践" />
                <el-option label="算法竞赛" value="算法竞赛" />
              </el-select>
            </el-form-item>

            <div class="profile-row">
              <el-form-item prop="target_score" class="profile-half">
                <label class="field-label">目标成绩 <span class="optional-tag">选填</span></label>
                <el-input v-model="registerForm.target_score" placeholder="如：90分" size="large" clearable />
              </el-form-item>
              <el-form-item prop="daily_study_time" class="profile-half">
                <label class="field-label">每天学习时间</label>
                <el-select v-model="registerForm.daily_study_time" placeholder="选择" size="large" class="full-width" clearable>
                  <el-option label="15分钟" value="15分钟" />
                  <el-option label="30分钟" value="30分钟" />
                  <el-option label="1小时" value="1小时" />
                  <el-option label="2小时以上" value="2小时以上" />
                </el-select>
              </el-form-item>
            </div>

            <el-form-item prop="exam_date">
              <label class="field-label">考试时间 <span class="optional-tag">选填</span></label>
              <el-input v-model="registerForm.exam_date" placeholder="如：2026年1月" size="large" clearable />
            </el-form-item>

            <el-button
              type="primary"
              size="large"
              class="submit-btn"
              :loading="loading"
              :disabled="usernameCheckStatus === 'taken'"
              @click="handleRegister"
            >
              {{ loading ? '注册中...' : '注 册' }}
            </el-button>

            <div class="switch-mode">
              已有账号？<a href="#" @click.prevent="formMode = 'login'">返回登录</a>
            </div>
          </el-form>
        </template>

        <!-- ═══ 忘记密码模式 ═══ -->
        <template v-else-if="formMode === 'forgot'">
          <div class="form-header">
            <h2>重置密码</h2>
            <p>输入你的注册邮箱，我们将发送重置链接</p>
          </div>

          <el-form ref="forgotFormRef" :model="forgotForm" :rules="forgotRules" class="modern-form" @submit.prevent>
            <el-form-item prop="email">
              <label class="field-label">注册邮箱</label>
              <el-input
                v-model="forgotForm.email"
                placeholder="请输入注册时使用的邮箱"
                size="large"
                :prefix-icon="Message"
                @keyup.enter="handleForgotPassword"
              />
            </el-form-item>

            <el-button
              type="primary"
              size="large"
              class="submit-btn"
              :loading="loading"
              @click="handleForgotPassword"
            >
              {{ loading ? '发送中...' : '发送重置邮件' }}
            </el-button>

            <div class="switch-mode back-link">
              <a href="#" @click.prevent="formMode = 'login'">&larr; 返回登录</a>
            </div>
          </el-form>
        </template>

        <!-- ═══ 重置成功提示 ═══ -->
        <template v-else-if="formMode === 'resetSent'">
          <div class="result-panel">
            <div class="result-icon success-icon">
              <el-icon :size="48"><CircleCheckFilled /></el-icon>
            </div>
            <h3>邮件已发送</h3>
            <p>重置密码的邮件已发送到你的邮箱，请注意查收。如果长时间未收到，请检查垃圾邮件文件夹。</p>
            <el-button type="primary" size="large" class="submit-btn" @click="formMode = 'login'">
              返回登录
            </el-button>
          </div>
        </template>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  User, Lock, DataLine, Connection, ChatDotRound,
  Message, Loading, CircleCheck, CircleClose, CircleCheckFilled
} from '@element-plus/icons-vue'
import { useSessionStore } from '../../store/session'
import { ElMessage } from 'element-plus'
import authApi from '../../api/auth'
import { getStorage, STORAGE_KEYS } from '../../utils/storage'

/** 从 localStorage 判断用户是否已完成引导（兜底逻辑） */
function hasLocalOnboardingDone() {
  if (getStorage(STORAGE_KEYS.ONBOARDING_DONE, false)) return true
  const profile = getStorage(STORAGE_KEYS.PROFILE)
  return !!(profile && (profile.persona_type || profile.ability_level))
}

const router = useRouter()
const sessionStore = useSessionStore()

// ===== 表单模式 =====
const formMode = ref('login') // 'login' | 'register' | 'forgot' | 'resetSent'

// ===== 表单状态 =====
const loading = ref(false)
const rememberMe = ref(false)

// ----- 登录表单 -----
const loginFormRef = ref(null)
const loginForm = reactive({
  username: '',
  password: '',
})
const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 4, message: '密码至少需要 4 个字符', trigger: 'blur' },
  ],
}

// ----- 注册表单 -----
const registerFormRef = ref(null)
const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  // 冷启动画像：第一阶段基础信息
  major: '',
  grade: '',
  course: '数据结构',
  learning_goal: '',
  target_score: '',
  daily_study_time: '',
  exam_date: '',
})

// 自定义校验器：两次密码一致
const validateConfirmPassword = (_rule, value, callback) => {
  if (!value) return callback(new Error('请再次输入密码'))
  if (value !== registerForm.password) return callback(new Error('两次输入的密码不一致'))
  return callback()
}

// 自定义校验器：邮箱格式（选填，但填了就要对）
const validateEmailOptional = (_rule, value, callback) => {
  if (!value || value.trim() === '') return callback()
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(value)) return callback(new Error('请输入正确的邮箱格式'))
  return callback()
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为 3~20 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '只能包含字母、数字和下划线', trigger: 'blur' },
  ],
  email: [
    { validator: validateEmailOptional, trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请设置密码', trigger: 'blur' },
    { min: 6, message: '密码至少需要 6 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

// ----- 忘记密码表单 -----
const forgotFormRef = ref(null)
const forgotForm = reactive({ email: '' })
const forgotRules = {
  email: [
    { required: true, message: '请输入注册邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' },
  ],
}

// ===== 用户名实时查重 =====
const usernameCheckStatus = ref('') // '' | 'checking' | 'available' | 'taken'
const usernameMsg = ref('')
let usernameDebounceTimer = null

function onUsernameInput() {
  usernameCheckStatus.value = ''
  usernameMsg.value = ''

  clearTimeout(usernameDebounceTimer)
  const val = registerForm.username

  if (val.length < 3) return

  usernameDebounceTimer = setTimeout(async () => {
    if (val.length < 3 || !/^[a-zA-Z0-9_]{3,20}$/.test(val)) return
    usernameCheckStatus.value = 'checking'
    try {
      const res = await authApi.checkUsername(val)
      if (res.available) {
        usernameCheckStatus.value = 'available'
        usernameMsg.value = '用户名可用'
      } else {
        usernameCheckStatus.value = 'taken'
        usernameMsg.value = res.hint || '该用户名已被占用'
      }
    } catch {
      usernameCheckStatus.value = ''
      usernameMsg.value = ''
    }
  }, 500)
}

function onUsernameBlur() {
  // blur 时如果正在检查，不清除，等结果出来
}

// ===== 密码强度计算 =====
function calcStrength(pwd) {
  let score = 0
  if (pwd.length >= 6) score++
  if (pwd.length >= 10) score++
  if (/[a-z]/.test(pwd)) score++
  if (/[A-Z]/.test(pwd)) score++
  if (/\d/.test(pwd)) score++
  if (/[^a-zA-Z0-9]/.test(pwd)) score++

  if (score <= 2) return { level: 'weak', percent: 33, label: '弱' }
  if (score <= 4) return { level: 'medium', percent: 66, label: '中等' }
  return { level: 'strong', percent: 100, label: '强' }
}

const strengthInfo = computed(() => calcStrength(registerForm.password))
const strengthPercent = computed(() => strengthInfo.value.percent)
const strengthLevel = computed(() => strengthInfo.value.level)
const strengthLabel = computed(() => strengthInfo.value.label)

function onPasswordInput() {
  // 触发 computed 更新即可
}

// ===== 角色状态（保持原有动画逻辑） =====
const stageRef = ref(null)
const accountInputRef = ref(null)
const passwordInputRef = ref(null)

const charState = ref('idle')
const showPassword = ref(false)
const brandVisible = ref(false)

const isPeeking = computed(() => showPassword.value && charState.value !== 'idle')
const peekingChar = computed(() => (showPassword.value && charState.value !== 'idle' ? 'orange' : ''))

// 眼球跟踪
const mousePos = reactive({ x: window.innerWidth / 2, y: window.innerHeight / 2 })
const MAX_PUPIL_MOVE = 11

function calcPupilOffset(charIdx) {
  const charCenters = [
    { cx: 0.14, cy: 0.52 },
    { cx: 0.20, cy: 0.50 },
    { cx: 0.26, cy: 0.48 },
    { cx: 0.32, cy: 0.51 }
  ]
  const center = charCenters[charIdx] || charCenters[0]
  const eyeCenterX = window.innerWidth * center.cx
  const eyeCenterY = window.innerHeight * center.cy
  const dx = mousePos.x - eyeCenterX
  const dy = mousePos.y - eyeCenterY
  const dist = Math.sqrt(dx * dx + dy * dy)
  if (dist < 1) return 'translate(-50%, -50%)'
  const moveRatio = Math.min(dist / 280, 1)
  const offsetAmount = MAX_PUPIL_MOVE * (0.3 + 0.7 * moveRatio)
  const offsetX = (dx / dist) * offsetAmount
  const offsetY = (dy / dist) * offsetAmount
  return `translate(calc(-50% + ${offsetX.toFixed(2)}px), calc(-50% + ${offsetY.toFixed(2)}px))`
}

const orangePupilStyle = computed(() => calcPupilOffset(0))
const orangePupil2Style = computed(() => calcPupilOffset(0))
const purplePupilStyle = computed(() => calcPupilOffset(1))
const purplePupil2Style = computed(() => calcPupilOffset(1))
const blackPupilStyle = computed(() => calcPupilOffset(2))
const blackPupil2Style = computed(() => calcPupilOffset(2))
const yellowPupilStyle = computed(() => calcPupilOffset(3))
const yellowPupil2Style = computed(() => calcPupilOffset(3))

const eyeBigStyle = 'transform: scale(1.3); height: 26px; width: 24px;'

function mouthClass(charName) {
  const s = charState.value
  if (s === 'email' || s === 'password') return 'curious'
  if (s === 'fail') return 'sad'
  if (s === 'success') return 'happy'
  return ''
}

// ===== 事件处理 =====
function onMouseMove(e) {
  mousePos.x = e.clientX
  mousePos.y = e.clientY
}
function resetChars() { charState.value = 'idle' }

function onEmailFocus() { charState.value = 'email' }
function onEmailBlur() {
  setTimeout(() => {
    if (document.activeElement !== passwordInputRef.value?.$el?.querySelector('input')) {
      if (!showPassword.value) resetChars()
    }
  }, 100)
}

function onPasswordFocus() { charState.value = 'password' }
function onPasswordBlur() {
  setTimeout(() => {
    if (document.activeElement !== accountInputRef.value?.$el?.querySelector('input')) {
      if (!showPassword.value) resetChars()
    }
  }, 100)
}

function switchToRegister() {
  formMode.value = 'register'
  resetChars()
}

// ===== 登录逻辑 =====
async function handleLogin() {
  console.log('═══════════ [Login] 开始登录 ═══════════')

  if (loginFormRef.value) {
    try {
      await loginFormRef.value.validate()
    } catch (err) {
      triggerFailAnimation()
      return
    }
  }

  loading.value = true

  try {
    const res = await authApi.login(
      { username: loginForm.username, password: loginForm.password },
      { timeout: 10000 }
    )

    if (!res || !res.token || !res.user) {
      throw { detail: '登录返回数据异常，请重试' }
    }

    sessionStore.login(res.user, res.token)

    if (rememberMe.value) {
      localStorage.setItem('learn-remember', 'true')
    } else {
      localStorage.removeItem('learn-remember')
    }

    const onboardingDone = res.user.has_completed_onboarding || hasLocalOnboardingDone()
    // ★ 管理员直接跳转管理后台
    const target = res.user.is_admin ? '/app/admin'
      : !onboardingDone ? '/onboarding' : '/app'

    triggerSuccessAnimation()
    await router.replace(target)
    ElMessage.success(`欢迎回来，${res.user.username}！`)
  } catch (error) {
    let msg = '登录失败，请检查用户名和密码'
    if (error?.detail) msg = error.detail
    else if (error?.error) msg = error.error
    else if (error?.message) msg = error.message

    if (msg.includes('超时') || msg.includes('timeout')) {
      msg = '登录请求超时——后端服务未启动，请先启动后端 (端口 8008)'
    } else if (msg.includes('网络') || msg.includes('Network Error')) {
      msg = '无法连接后端服务，请确认后端已启动 (端口 8008)'
    }

    ElMessage.error(msg)
    triggerFailAnimation()
  } finally {
    loading.value = false
  }
}

// ===== 注册逻辑 =====
async function handleRegister() {
  try {
    await registerFormRef.value.validate()
  } catch {
    triggerFailAnimation()
    return
  }

  if (registerForm.password !== registerForm.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    triggerFailAnimation()
    return
  }

  if (usernameCheckStatus.value === 'taken') {
    ElMessage.warning('该用户名已被占用，请更换')
    return
  }

  loading.value = true
  try {
    const res = await authApi.register({
      username: registerForm.username,
      password: registerForm.password,
      email: registerForm.email || undefined,
      // 冷启动画像：第一阶段基础信息
      major: registerForm.major || undefined,
      grade: registerForm.grade || undefined,
      course: registerForm.course || undefined,
      learning_goal: registerForm.learning_goal || undefined,
      target_score: registerForm.target_score || undefined,
      daily_study_time: registerForm.daily_study_time || undefined,
      exam_date: registerForm.exam_date || undefined,
    })

    sessionStore.login(res.user, res.token)
    await router.replace('/onboarding')
    ElMessage.success('注册成功！即将进入新手引导...')
  } catch (error) {
    const msg = error?.detail || error?.message || '注册失败，请重试'
    ElMessage.error(msg)
    triggerFailAnimation()
    if (typeof msg === 'string' && msg.includes('已存在')) {
      usernameCheckStatus.value = 'taken'
      usernameMsg.value = msg
    }
  } finally {
    setTimeout(() => { loading.value = false }, 800)
  }
}

// ===== 忘记密码 =====
async function handleForgotPassword() {
  try {
    await forgotFormRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    await authApi.forgotPassword({ email: forgotForm.email })
    formMode.value = 'resetSent'
  } catch (error) {
    const msg = error?.detail || error?.message || '发送失败，请稍后重试'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

// ===== 游客登录 =====
async function handleGuestLogin() {
  loading.value = true
  try {
    const res = await authApi.guest()
    sessionStore.login(res.user, res.token)
    triggerSuccessAnimation()
    setTimeout(() => { router.push('/onboarding') }, 1100)
  } catch {
    ElMessage.error('游客登录失败')
  } finally {
    loading.value = false
  }
}

// ===== 动画触发 =====
function triggerFailAnimation() {
  charState.value = 'fail'
  setTimeout(() => resetChars(), 2200)
}
function triggerSuccessAnimation() {
  charState.value = 'success'
  setTimeout(() => resetChars(), 2800)
}

// ===== 进场动画 =====
const hasEntered = ref(false)
onMounted(() => {
  mousePos.x = window.innerWidth / 2
  mousePos.y = window.innerHeight / 2
  hasEntered.value = true
  setTimeout(() => { brandVisible.value = true }, 1400)
})
</script>

<style lang="scss" scoped>
/* ═══════════════════════════════════════════════════════
   LOGIN CONTAINER
   ═══════════════════════════════════════════════════════ */
.login-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: rgba(255,255,255,0.5); backdrop-filter: blur(20px);
}

/* ═══════════════════════════════════════════════════════
   LEFT BRAND SECTION（角色区域 — 保持原样）
   ═══════════════════════════════════════════════════════ */
.brand-section {
  flex: 1.2;
  background: linear-gradient(155deg, #EEF4FF 0%, #F6F0FF 35%, #E8F9F6 60%, #F5F0FF 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 36px;
  color: #1E293B;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image: radial-gradient(circle, rgba(79,124,255,0.03) 1px, transparent 1px);
    background-size: 30px 30px;
  }
}

.bg-decor {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;

  .decor-circle {
    position: absolute;
    border-radius: 50%;
    filter: blur(60px);

    &--1 { width: 320px; height: 320px; background: rgba(var(--color-primary-rgb), 0.10); top: -80px; right: -60px; }
    &--2 { width: 240px; height: 240px; background: rgba(var(--color-accent-teal-rgb), 0.08); bottom: -60px; left: -40px; }
  }

  .decor-dots {
    position: absolute;
    inset: 0;
    background-image: radial-gradient(circle, rgba(255,255,255,0.03) 1.5px, transparent 1.5px);
    background-size: 44px 44px;
  }
}

/* 角色舞台 */
.characters-stage {
  position: relative;
  z-index: 2;
  width: 400px;
  height: 300px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  margin-bottom: 20px;
}

.character {
  position: absolute;
  bottom: 16px;
  transition: transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  opacity: 0;
  will-change: transform, opacity;

  &.char-orange { left: 12px; z-index: 4; &.has-entered { animation: enterBounceOrange 0.85s cubic-bezier(0.22, 1, 0.36, 1) 0.05s forwards; } &.peeking { animation: peekSneaky 0.6s ease forwards; } }
  &.char-purple { left: 95px; bottom: 20px; z-index: 1; &.has-entered { animation: enterSlideLeft 0.75s cubic-bezier(0.22, 1, 0.36, 1) 0.25s forwards; } }
  &.char-black { left: 168px; bottom: 14px; z-index: 3; &.has-entered { animation: enterDropBounce 0.9s cubic-bezier(0.22, 1, 0.36, 1) 0.15s forwards; } }
  &.char-yellow { left: 235px; bottom: 10px; z-index: 2; &.has-entered { animation: enterSlideRight 0.78s cubic-bezier(0.22, 1, 0.36, 1) 0.38s forwards; } }
}

@keyframes enterBounceOrange {
  0%   { opacity: 0; transform: translateX(-180px) translateY(80px) scale(0.5) rotate(-18deg); }
  50%  { opacity: 1; transform: translateX(-10px) translateY(-30px) scale(1.08) rotate(5deg); }
  72%  { transform: translateX(6px) translateY(-8px) scale(1.02) rotate(-2deg); }
  88%  { transform: translateX(-3px) translateY(3px) scale(0.99); }
  100% { opacity: 1; transform: translateX(0) translateY(0) scale(1) rotate(0); }
}
@keyframes enterSlideLeft {
  0%   { opacity: 0; transform: translateX(-200px) scaleX(0.7) rotate(8deg); }
  60%  { opacity: 1; transform: translateX(14px) scaleX(1.04) rotate(-3deg); }
  82%  { transform: translateX(-5px) scaleX(0.98) rotate(1deg); }
  100% { opacity: 1; transform: translateX(0) scaleX(1) rotate(0); }
}
@keyframes enterDropBounce {
  0%   { opacity: 0; transform: translateY(-220px) scaleY(1.2); }
  48%  { opacity: 1; transform: translateY(12px) scaleY(0.92); }
  68%  { transform: translateY(-18px) scaleY(1.03); }
  84%  { transform: translateY(5px) scaleY(0.97); }
  96%  { transform: translateY(-2px); }
  100% { opacity: 1; transform: translateY(0) scaleY(1); }
}
@keyframes enterSlideRight {
  0%   { opacity: 0; transform: translateX(200px) scaleX(0.7) rotate(-8deg); }
  58%  { opacity: 1; transform: translateX(-14px) scaleX(1.04) rotate(3deg); }
  80%  { transform: translateX(5px) scaleX(0.98) rotate(-1deg); }
  100% { opacity: 1; transform: translateX(0) scaleX(1) rotate(0); }
}

/* 角色身体容器 */
.character-body {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* 地面阴影 */
.ground-shadows {
  position: absolute; bottom: -4px; left: 50%; transform: translateX(-50%);
  display: flex; gap: 0; pointer-events: none; z-index: 0;

  .shadow { display: block; border-radius: 50%; background: rgba(0,0,0,0.18); opacity: 0; }
  .shadow--1 { width: 65px; height: 14px; margin-left: 20px; }
  .shadow--2 { width: 52px; height: 11px; margin-left: 32px; }
  .shadow--3 { width: 42px; height: 10px; margin-left: 38px; }
  .shadow--4 { width: 58px; height: 12px; margin-left: 28px; }

  &.has-entered .shadow {
    animation: shadowFadeIn 0.4s ease forwards;
    &--1 { animation-delay: 0.55s; }
    &--2 { animation-delay: 0.75s; }
    &--3 { animation-delay: 0.68s; }
    &--4 { animation-delay: 0.88s; }
  }
}
@keyframes shadowFadeIn { to { opacity: 1; } }

/* ── 眼睛系统 ── */
.eyes {
  position: absolute; top: 33%; left: 50%; transform: translateX(-50%);
  display: flex; gap: 17px; z-index: 5; transition: transform 0.3s ease;
}
.eye-wrapper { display: block; }
.eye {
  width: 20px; height: 22px; background: #fff; border-radius: 50%;
  position: relative; overflow: hidden; border: 2.5px solid #333;
  transition: all 0.28s ease-out; flex-shrink: 0;
}
.eye--narrow { border-radius: 42% 42% 50% 50%; height: 19px; }
.eye--round { width: 23px; height: 23px; border-radius: 52%; border-width: 2.5px; border-color: #111; }
.eye--gentle { width: 18px; height: 20px; border-radius: 46%; border-color: #444; border-width: 2px; }

.eye-closed {
  height: 4px; background: #333; border-radius: 10px; border: none; width: 20px;
  &--peek { background: #FF6B1A; }
  &--angry { background: #7D3C98; width: 18px; height: 5px; }
  &--flat { background: #111; width: 21px; height: 4px; }
  &--gentle { background: #666; width: 17px; height: 4px; border-radius: 8px; }
}

.pupil { width: 9px; height: 9px; background: #222; border-radius: 50%; position: absolute; top: 50%; left: 50%; transition: transform 0.12s ease-out; }
.pupil--slit { width: 6px; height: 10px; border-radius: 40%; background: #4A235A; }
.pupil--large { width: 11px; height: 11px; background: #111; }
.pupil-highlight { position: absolute; width: 3px; height: 3px; background: #fff; border-radius: 50%; top: 1px; right: 1px; }

.blush {
  position: absolute; top: 47%; left: 50%; transform: translateX(-50%);
  display: flex; gap: 28px; z-index: 3; opacity: 0; transition: opacity 0.35s ease;
  span { width: 12px; height: 7px; border-radius: 50%; }
  &.show { opacity: 1; }
  &--orange span { background: rgba(255, 150, 100, 0.5); }
  &--purple span { background: rgba(230, 130, 220, 0.5); width: 10px; height: 6px; gap: 26px; }
  &--yellow span { background: rgba(240, 200, 80, 0.5); }
}

.mouth { position: absolute; top: 57%; left: 50%; transform: translateX(-50%); z-index: 4; transition: all 0.4s ease; }

/* 角色样式 */
.char-orange-body {
  width: 82px; height: 72px; background: #FF8C42; border-radius: 82px 82px 4px 4px; border: 3px solid #333;
  .mouth { width: 24px; height: 12px; border: 3px solid #333; border-top: none; border-radius: 0 0 24px 24px; background: transparent;
    &.curious { width: 13px; height: 13px; border-radius: 50%; background: #FF6B1A; border-width: 3px; border-style: solid; }
    &.sad { width: 18px; height: 8px; border-radius: 0 0 18px 18px; border: 3px solid #333; border-top: none; background: transparent; transform: translateX(-50%) translateY(3px); }
    &.happy { width: 28px; height: 14px; border-radius: 0 0 28px 28px; background: #FF6B1A; border: none; }
  }
}
@keyframes peekSneaky { 0%, 100% { transform: rotate(0deg) translateX(0); } 30% { transform: rotate(-8deg) translateX(8px) translateY(-4px); } 60% { transform: rotate(5deg) translateX(12px) translateY(-2px); } }

.char-purple-body {
  width: 66px; height: 90px; background: #9B59B6; border-radius: 14px; border: 3px solid #333;
  .mouth--purple { width: 18px; height: 7px; border: 3px solid #333; border-radius: 7px; background: #7D3C98;
    &.curious { width: 9px; height: 15px; border-radius: 9px; background: #A569BD; }
    &.sad { width: 16px; height: 9px; border-radius: 0 0 16px 16px; border-top: none; background: transparent; }
    &.happy { width: 22px; height: 11px; border-radius: 0 0 22px 22px; background: #E8DAEF; border-top: none; }
  }
}

.char-black-body {
  width: 50px; height: 100px; background: #2C3E50; border-radius: 12px; border: 3px solid #111;
  .eyes--wide { gap: 19px; top: 31%; }
  .mouth--black { width: 13px; height: 5px; border: 3px solid #111; border-radius: 5px; background: #555;
    &.curious { width: 7px; height: 13px; border-radius: 7px; background: #777; }
    &.sad { width: 11px; height: 7px; border-radius: 0 0 11px 11px; border-top: none; border-color: #111; background: transparent; }
    &.happy { width: 17px; height: 9px; background: #888; border-radius: 0 0 17px 17px; border-top: none; border-color: #111; }
  }
}

.char-yellow-body {
  width: 72px; height: 82px; background: #F1C40F; border-radius: 18px 18px 4px 4px; border: 3px solid #333;
  .mouth--yellow { width: 19px; height: 6px; border: 3px solid #333; border-radius: 6px; background: #D4AC0D;
    &.curious { width: 9px; height: 13px; border-radius: 9px; background: #E8C547; }
    &.sad { width: 16px; height: 8px; border-radius: 0 0 16px 16px; border-top: none; background: transparent; }
    &.happy { width: 23px; height: 10px; background: #F39C12; border-radius: 0 0 23px 23px; border-top: none; }
  }
}

/* 角色状态修饰 */
.character.focus-email { animation: headTurnCurious 0.55s cubic-bezier(0.34, 1.56, 0.64, 1) forwards; }
@keyframes headTurnCurious { 0% { transform: rotate(0deg) translateY(0); } 35% { transform: rotate(12deg) translateY(-8px) scale(1.04); } 65% { transform: rotate(8deg) translateY(-4px) scale(1.02); } 100% { transform: rotate(10deg) translateY(-5px) scale(1.02); } }

.character.focus-password { animation: bodyLeanIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards; }
@keyframes bodyLeanIn { 0% { transform: translateY(0) scale(1); } 50% { transform: translateY(-10px) scale(1.06); } 100% { transform: translateY(-6px) scale(1.03); } }

.character.login-fail { animation: shakeSad 0.7s ease; }
@keyframes shakeSad { 0%,100%{transform:translateX(0)rotate(0)} 12%{transform:translateX(-7px)rotate(-3deg)} 28%{transform:translateX(6px)rotate(2.5deg)} 44%{transform:translateX(-5px)rotate(-1.5deg)} 60%{transform:translateX(4px)rotate(1deg)} 76%{transform:translateX(-2px)rotate(0)} 88%{transform:translateX(1px)rotate(0)} }

.character.login-success { animation: bounceHappy 0.85s cubic-bezier(0.34, 1.56, 0.64, 1); }
@keyframes bounceHappy { 0%{transform:translateY(0)scale(1)} 25%{transform:translateY(-28px)scale(1.08)} 45%{transform:translateY(-10px)scale(1.03)} 65%{transform:translateY(-20px)scale(1.05)} 82%{transform:translateY(-5px)scale(1.01)} 100%{transform:translateY(0)scale(1)} }

/* 品牌文字 */
.brand-content {
  position: relative; z-index: 2; max-width: 480px; text-align: center;
  opacity: 0; transform: translateY(20px); transition: opacity 0.6s ease, transform 0.6s cubic-bezier(0.22, 1, 0.36, 1);

  &.content-visible { opacity: 1; transform: translateY(0); }

  .logo {
    font-family: 'Space Grotesk', sans-serif; font-size: 32px; font-weight: 800; margin-bottom: 20px;
    letter-spacing: -1.5px; display: inline-flex; align-items: center;
    &::before {
      content: 'SQ'; margin-right: 12px; font-size: 28px; width: 44px; height: 44px;
      border-radius: 10px; background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
      color: #1E293B; display: flex; align-items: center; justify-content: center; letter-spacing: -0.5px;
    }
  }
  h1 { font-family: 'Space Grotesk', sans-serif; font-size: 26px; line-height: 1.25; margin-bottom: 14px; color: #1E293B; font-weight: 700; letter-spacing: -0.5px; }
  .subtitle { font-family: 'DM Sans', sans-serif; font-size: 14.5px; line-height: 1.65; opacity: 0.8; margin-bottom: 28px; color: rgba(30,41,59,0.80); }
}

.features {
  display: flex; flex-direction: column; gap: 10px;
  .feature-item {
    display: flex; align-items: center; gap: 13px; font-size: 13.5px;
    background: rgba(255,255,255,0.09); padding: 11px 15px; border-radius: 10px;
    backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.08);
    transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1);
    &:hover { transform: translateX(8px); background: rgba(255,255,255,0.14); }
    .el-icon { font-size: 19px; flex-shrink: 0; }
  }
}

/* ═══════════════════════════════════════════════════════
   RIGHT FORM SECTION — 全新现代化表单
   ═══════════════════════════════════════════════════════ */
.form-section {
  flex: 1; display: flex; align-items: center; justify-content: center;
  padding: 40px; background: rgba(255,255,255,0.5); backdrop-filter: blur(20px);
  overflow-y: auto;
}

.form-wrapper { width: 100%; max-width: 420px; }

.form-header {
  margin-bottom: 30px;
  h2 {
    font-family: 'Space Grotesk', sans-serif; font-size: 28px; font-weight: 800;
    margin-bottom: 8px; letter-spacing: -0.5px; color: var(--text-primary);
  }
  p { color: var(--text-secondary); font-size: 14.5px; }
}

/* ═══ 现代表单样式 ═══ */
.modern-form {
  .el-form-item { margin-bottom: 22px; }

  /* 输入框增强 */
  :deep(.el-input__wrapper) {
    border-radius: 10px;
    box-shadow: 0 0 0 1px var(--border-color) inset;
    transition: all 0.25s ease;
    padding: 4px 14px;

    &:hover { box-shadow: 0 0 0 1px var(--color-primary-light) inset; }
    &.is-focus { box-shadow: 0 0 0 1.5px var(--color-primary), 0 4px 16px rgba(var(--color-primary-rgb), 0.08) inset !important; }
  }

  :deep(.el-input__inner) { font-size: 14.5px; }
}

/* 字段标签 */
.field-label {
  display: block; font-size: 13px; font-weight: 600; color: var(--text-secondary);
  margin-bottom: 7px; letter-spacing: 0.3px;
  .optional-tag { font-weight: 400; color: var(--text-muted); font-size: 12px; margin-left: 4px; }
}

/* 表单操作行：记住我 + 忘记密码 */
.form-options-row {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 22px; padding: 0 2px;

  .remember-check {
    :deep(.el-checkbox__label) { font-size: 13px; color: var(--text-secondary); }
  }
  .forgot-link {
    font-size: 13px; color: var(--color-primary); text-decoration: none;
    font-weight: 500; transition: color 0.2s;
    &:hover { text-decoration: underline; color: var(--color-primary-dark); }
  }
}

/* 提交按钮 */
.submit-btn {
  width: 100%; height: 46px; font-size: 15px; border-radius: 10px;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  border: none; margin-bottom: 14px; letter-spacing: 3px; font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;

  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(var(--color-primary-rgb), 0.3);
  }
  &:active:not(:disabled) { transform: translateY(0); }
  &:disabled { opacity: 0.55; cursor: not-allowed; }
}

/* 分割线 */
.divider-row {
  text-align: center; margin-bottom: 14px; position: relative;
  &::before { content: ''; position: absolute; left: 0; right: 0; top: 50%; height: 1px; background: var(--border-color); }
  span { position: relative; padding: 0 16px; background: var(--bg-color); color: var(--text-muted); font-size: 13px; }
}

.guest-btn {
  width: 100%; height: 46px; font-size: 15px; border-radius: 10px;
  background: transparent; border: 1.5px solid var(--border-color);
  color: var(--text-secondary); margin-bottom: 20px; cursor: pointer;
  transition: all 0.25s ease;
  &:hover { border-color: var(--color-primary); color: var(--color-primary); }
}

/* 切换模式链接 */
.switch-mode {
  text-align: center; margin-top: 20px; color: var(--text-secondary); font-size: 13.5px;

  a { color: var(--color-primary); text-decoration: none; font-weight: 600; transition: color 0.2s; }
  a:hover { text-decoration: underline; }
}
.back-link { margin-top: 24px; a { font-size: 14px; } }

/* ═══ 密码强度条 ═══ */
.strength-bar-wrap {
  display: flex; align-items: center; gap: 10px; margin-top: 8px; padding: 0 2px;
}
.strength-bar-track {
  flex: 1; height: 5px; border-radius: 3px; background: var(--border-color); overflow: hidden;
}
.strength-bar-fill {
  height: 100%; border-radius: 3px; transition: width 0.35s ease, background 0.35s ease;
  &.weak { background: linear-gradient(90deg, #ef4444, #f87171); }
  &.medium { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
  &.strong { background: linear-gradient(90deg, #22c55e, #4ade80); }
}
.strength-text { font-size: 12px; font-weight: 600; white-space: nowrap; min-width: 26px;
  &.weak { color: #ef4444; }
  &.medium { color: #f59e0b; }
  &.strong { color: #22c55e; }
}

/* ═══ 用户名查重状态图标 ═══ */
.check-icon { font-size: 15px; margin-right: 4px;
  &.checking { color: var(--color-primary); animation: spin 1s linear infinite; }
  &.success { color: #22c55e; }
  &.error { color: #ef4444; }
}
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* ═══ 字段提示文字 ═══ */
.field-hint { display: inline-block; font-size: 12px; margin-top: 5px; padding-left: 2px;
  &.available { color: #22c55e; }
  &.taken { color: #ef4444; }
  &.error { color: #ef4444; }
}

/* 过渡动画 */
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.slide-enter-active, .slide-leave-active { transition: all 0.25s ease; }
.slide-enter-from, .slide-leave-to { opacity: 0; transform: translateY(-4px); }

/* ═══ 注册表单增强：基础信息采集 ═══ */
.profile-section-title {
  font-size: 13px; font-weight: 700; color: var(--color-primary);
  margin: 4px 0 16px; padding: 10px 14px;
  background: rgba(var(--color-primary-rgb), 0.06);
  border-radius: 8px; border-left: 3px solid var(--color-primary);
  .section-icon { margin-right: 4px; }
}
.profile-row { display: flex; gap: 16px; }
.profile-half { flex: 1; min-width: 0; }
.full-width { width: 100%; }

/* ═══ 结果面板（重置成功） ═══ */
.result-panel {
  text-align: center; padding: 20px 0;
  .result-icon { margin-bottom: 20px;
    .success-icon { color: #22c55e; }
  }
  h3 { font-family: 'Space Grotesk', sans-serif; font-size: 22px; font-weight: 700; margin-bottom: 12px; }
  p { color: var(--text-secondary); font-size: 14px; line-height: 1.65; margin-bottom: 28px; }
}

/* ═══ 响应式 ═══ */
@media (max-width: 1024px) {
  .brand-section { display: none; }
  .form-section { padding: 24px; }
  .form-wrapper { max-width: 420px; }
}
</style>
