<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { deleteUser, getAdminUsers, login, updateUser } from '../api'

const account = ref('')
const password = ref('')
const users = ref([])
const errorMessage = ref('')
const authenticated = ref(false)
const pending = ref(false)
const deleteTarget = ref(null)
const deleteConfirmation = ref('')
const deletingUser = ref(false)
const editTarget = ref(null)
const editUsername = ref('')
const editPassword = ref('')
const confirmEditPassword = ref('')
const editError = ref('')
const updatingUser = ref(false)

async function handleLogin() {
  errorMessage.value = ''
  pending.value = true

  try {
    const admin = await login({ account: account.value.trim(), password: password.value })
    if (admin.id !== 1) {
      errorMessage.value = '该账号没有管理员权限'
      return
    }
    users.value = await getAdminUsers()
    authenticated.value = true
    password.value = ''
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    pending.value = false
  }
}

async function refreshUsers() {
  errorMessage.value = ''
  pending.value = true
  try {
    users.value = await getAdminUsers()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    pending.value = false
  }
}

onMounted(async () => {
  const currentUser = JSON.parse(sessionStorage.getItem('chat_user') || 'null')
  if (currentUser?.id !== 1) return

  authenticated.value = true
  await refreshUsers()
})

function formatTime(value) {
  if (!value) return '暂无记录'
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function openDeleteDialog(user) {
  deleteTarget.value = user
  deleteConfirmation.value = ''
}

function openEditDialog(user) {
  editTarget.value = user
  editUsername.value = user.username
  editPassword.value = ''
  confirmEditPassword.value = ''
  editError.value = ''
}

function closeEditDialog() {
  if (updatingUser.value) return
  editTarget.value = null
}

async function confirmUpdateUser() {
  if (!editTarget.value) return

  const username = editUsername.value.trim()
  const password = editPassword.value
  editError.value = ''

  if (!username) {
    editError.value = '用户名不能为空'
    return
  }
  if (password !== password.trim()) {
    editError.value = '密码开头和结尾不能使用空格'
    return
  }
  if (password !== confirmEditPassword.value) {
    editError.value = '两次输入的密码不一致'
    return
  }

  const payload = {}
  if (username !== editTarget.value.username) payload.username = username
  if (password) payload.password = password
  if (!Object.keys(payload).length) {
    editError.value = '没有需要修改的内容'
    return
  }

  updatingUser.value = true
  try {
    const user = await updateUser(editTarget.value.id, payload)
    const currentUser = JSON.parse(sessionStorage.getItem('chat_user') || 'null')
    if (currentUser?.id === user.id) {
      sessionStorage.setItem('chat_user', JSON.stringify({ ...currentUser, ...user }))
    }
    editTarget.value = null
    await refreshUsers()
  } catch (error) {
    editError.value = error.message
  } finally {
    updatingUser.value = false
  }
}

function closeDeleteDialog() {
  if (deletingUser.value) return
  deleteTarget.value = null
  deleteConfirmation.value = ''
}

async function confirmDeleteUser() {
  if (!deleteTarget.value || deleteConfirmation.value !== 'Potato') return

  errorMessage.value = ''
  deletingUser.value = true
  try {
    await deleteUser(deleteTarget.value.id)
    closeDeleteDialog()
    await refreshUsers()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    deletingUser.value = false
    deleteTarget.value = null
    deleteConfirmation.value = ''
  }
}
</script>

<template>
  <main v-if="!authenticated" class="auth-page">
    <section class="auth-card">
      <div class="brand-mark">管</div>
      <h1>管理员登录</h1>
      <p class="auth-subtitle">仅第一个注册账号可以进入</p>

      <form class="auth-form" @submit.prevent="handleLogin">
        <label for="admin-account">管理员账号</label>
        <input id="admin-account" v-model="account" name="account" autocomplete="username" required>

        <label for="admin-password">密码</label>
        <input id="admin-password" v-model="password" name="password" type="password" autocomplete="current-password" required>

        <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
        <button class="primary-button" type="submit" :disabled="pending">
          {{ pending ? '验证中…' : '进入后台' }}
        </button>
      </form>

      <p class="auth-switch"><RouterLink to="/">返回普通登录</RouterLink></p>
    </section>
  </main>

  <main v-else class="admin-page">
    <header class="admin-header">
      <div>
        <p>Chatroom Admin</p>
        <h1>用户管理</h1>
      </div>
      <button type="button" :disabled="pending" @click="refreshUsers">
        {{ pending ? '刷新中…' : '刷新列表' }}
      </button>
    </header>

    <section class="admin-panel">
      <div class="admin-summary">
        <strong>{{ users.length }}</strong>
        <span>当前注册用户</span>
      </div>

      <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>账号</th>
              <th>用户名</th>
              <th>注册时间</th>
              <th>最后登录</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>{{ user.id }}</td>
              <td class="account-cell">{{ user.account }}</td>
              <td>{{ user.username }}</td>
              <td>{{ formatTime(user.created_at) }}</td>
              <td>{{ formatTime(user.last_seen_at) }}</td>
              <td>
                <span v-if="user.account.startsWith('deleted_')" class="deleted-label">已注销</span>
                <div v-else class="table-actions">
                  <button class="table-edit-button" type="button" @click="openEditDialog(user)">修改</button>
                  <button
                    v-if="user.id !== 1"
                    class="table-danger-button"
                    type="button"
                    @click="openDeleteDialog(user)"
                  >注销</button>
                  <span v-else class="admin-label">管理员</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p class="admin-note">密码经过哈希后保存，后台无法查看原始密码。</p>
    </section>

    <div v-if="editTarget" class="dialog-backdrop" @click.self="closeEditDialog">
      <section class="confirm-dialog profile-dialog" role="dialog" aria-modal="true" aria-labelledby="admin-edit-title">
        <h2 id="admin-edit-title">修改用户</h2>
        <p>正在修改账号 {{ editTarget.account }}</p>
        <label for="admin-edit-username">用户名</label>
        <input id="admin-edit-username" v-model="editUsername" autocomplete="off">
        <label for="admin-edit-password">新密码</label>
        <input id="admin-edit-password" v-model="editPassword" type="password" autocomplete="new-password" placeholder="留空则不修改">
        <label for="admin-confirm-password">确认新密码</label>
        <input id="admin-confirm-password" v-model="confirmEditPassword" type="password" autocomplete="new-password" placeholder="再次输入新密码">
        <p v-if="editError" class="form-error">{{ editError }}</p>
        <div class="dialog-actions">
          <button type="button" @click="closeEditDialog">取消</button>
          <button class="primary-dialog-button" type="button" :disabled="updatingUser" @click="confirmUpdateUser">
            {{ updatingUser ? '保存中…' : '保存修改' }}
          </button>
        </div>
      </section>
    </div>

    <div v-if="deleteTarget" class="dialog-backdrop" @click.self="closeDeleteDialog">
      <section class="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="admin-delete-title">
        <h2 id="admin-delete-title">注销用户</h2>
        <p>即将注销 <strong>{{ deleteTarget.username }}</strong>（{{ deleteTarget.account }}）。请输入 <strong>Potato</strong> 继续。</p>
        <input v-model="deleteConfirmation" aria-label="注销确认文字" autocomplete="off" placeholder="输入 Potato">
        <div class="dialog-actions">
          <button type="button" @click="closeDeleteDialog">取消</button>
          <button
            class="danger-button"
            type="button"
            :disabled="deleteConfirmation !== 'Potato' || deletingUser"
            @click="confirmDeleteUser"
          >{{ deletingUser ? '正在注销…' : '确认注销' }}</button>
        </div>
      </section>
    </div>
  </main>
</template>
