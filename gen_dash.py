import os, re

# Fix Bug 1: LoginSection.vue guest login
fp = r'D:\lastone\learn\learn\learn\struct-quest-frontend\src\views\Landing\LoginSection.vue'
content = open(fp, 'r', encoding='utf-8').read()
content = content.replace(
    "router.push('/app')",
    "router.push('/onboarding')",
    1
)
open(fp, 'w', encoding='utf-8').write(content)
print('Bug 1 fixed: LoginSection.vue guest login -> /onboarding')

# Fix Bug 2: session.js login() clear stale onboarding data
sp = r'D:\lastone\learn\learn\learn\struct-quest-frontend\src\store\session.js'
session = open(sp, 'r', encoding='utf-8').read()

marker = 'this.hasCompletedOnboarding = userData.has_completed_onboarding ?? false\n'
inject = '      // 新用户（未完成引导）清除可能残留的旧 localStorage 数据，防止路由守卫跳过\n'
inject += '      if (!this.hasCompletedOnboarding) {\n'
inject += '        removeStorage(STORAGE_KEYS.ONBOARDING_DONE)\n'
inject += '        removeStorage(STORAGE_KEYS.PROFILE)\n'
inject += '      }\n'

session = session.replace(marker, marker + inject, 1)
open(sp, 'w', encoding='utf-8').write(session)
print('Bug 2 fixed: session.js login() clears stale onboarding data')
