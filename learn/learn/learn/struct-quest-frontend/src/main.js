import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import { useSessionStore } from './store/session'
import { initRequestRouter } from './utils/request'

console.log('═══════════ [App] 开始启动 ═══════════')
console.log('[App] 1/6 注册 router 到 request.js...')
// ★ 将 router 绑定到 request.js，以便 401 拦截器可用 router.push 而非全页刷新
initRequestRouter(router)
console.log('[App] ✅ router 绑定完成')

// 引入全局样式覆盖
console.log('[App] 2/6 加载全局样式...')
import './assets/styles/index.scss'

console.log('[App] 3/6 创建 Vue 应用...')
const app = createApp(App)

const pinia = createPinia()

console.log('[App] 4/6 安装插件 (pinia, router, element-plus)...')
app.use(pinia)
app.use(router)
app.use(ElementPlus)

console.log('[App] 5/6 注册 Element Plus 图标...')
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 全局错误捕获，防止白屏
app.config.errorHandler = (err, vm, info) => {
  console.error('[Vue Error]', err, info)
  // 即使出现错误，也不应该炸掉整个页面
  console.warn('[Vue Error] 已捕获异常，页面将继续渲染（如有降级展示）')
}

// 全局警告处理，防止 Vue 警告被吞
app.config.warnHandler = (msg, vm, trace) => {
  console.warn('[Vue Warn]', msg, trace)
}

// 先挂载应用，后台同步登录状态（避免同步请求阻塞渲染导致白屏）
console.log('[App] 6/6 挂载 Vue 应用...')
app.mount('#app')
console.log('[App] ✅ Vue 应用挂载完成')

console.log('[App] 后台同步登录状态...')
const sessionStore = useSessionStore()
sessionStore.syncFromServer().then(synced => {
  console.log('[App] ✅ 登录状态同步完成:', synced ? '已登录' : '未登录')
}).catch((e) => {
  console.warn('[App] syncFromServer 失败:', e)
})
console.log('[App] ═══════════ 启动流程完成 ═══════════')
