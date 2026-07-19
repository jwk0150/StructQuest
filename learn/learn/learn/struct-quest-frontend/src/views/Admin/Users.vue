<template>
  <div class="users-page">
    <div class="page-header">
      <h2>用户管理</h2>
      <el-button type="primary" @click="loadUsers" :loading="loading">刷新</el-button>
    </div>

    <el-table :data="users" size="small" highlight-current-row style="width:100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" width="140" />
      <el-table-column label="角色" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_admin ? 'danger' : 'info'" size="small">{{ row.is_admin ? '管理员' : '学生' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="学习模式" width="100" align="center">
        <template #default="{ row }">{{ modeCn(row.learning_mode) }}</template>
      </el-table-column>
      <el-table-column prop="plan_count" label="计划" width="70" align="center" />
      <el-table-column prop="event_count" label="事件" width="70" align="center" />
      <el-table-column prop="latest_profile_summary" label="最新画像摘要" min-width="300" show-overflow-tooltip />
      <el-table-column label="上次画像" width="160">
        <template #default="{ row }">{{ formatDate(row.latest_profile_time) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180" align="center" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openDetail(row.id)">数据中心</el-button>
          <el-popconfirm
            :title="`确定彻底删除用户「${row.username}」及其所有数据？此操作不可逆！`"
            confirm-button-text="确认删除"
            cancel-button-text="取消"
            @confirm="handleCascadeDelete(row)"
          >
            <template #reference>
              <el-button link type="danger" size="small" :disabled="row.is_admin">级联删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 用户详情页面（新窗口打开或路由跳转） -->
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import adminApi from '../../api/admin'

const router = useRouter()
const users = ref([])
const loading = ref(false)

async function loadUsers() {
  loading.value = true
  try {
    const res = await adminApi.getStudents({ limit: 100 })
    users.value = res.items || []
  } catch (e) {
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

function openDetail(userId) {
  router.push(`/admin/users/${userId}`)
}

async function handleCascadeDelete(row) {
  try {
    const res = await adminApi.cascadeDeleteUser(row.id)
    ElMessage.success(res.message || `已删除用户「${row.username}」及其全部数据`)
    loadUsers()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

function formatDate(d) {
  if (!d) return '-'
  const dt = new Date(d)
  return `${dt.getMonth() + 1}/${dt.getDate()} ${String(dt.getHours()).padStart(2, '0')}:${String(dt.getMinutes()).padStart(2, '0')}`
}

const MODE_CN = { basic: '基础模式', beginner: '入门模式', exam: '考试模式' }
function modeCn(mode) { return MODE_CN[mode] || mode || '-' }

onMounted(loadUsers)
</script>

<style scoped>
.users-page { max-width: 1400px; }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; }
.page-header h2 { margin:0; font-size:22px; color:#1e293b; }
</style>
