<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { deleteUser, getAdminUsers, getConversations, getMessages, logout, sendMessage, updateUser } from '../api'

const router = useRouter()
const contacts = ref([])
const selectedContact = ref(null)
const messages = ref([])
const searchText = ref('')
const newAccount = ref('')
const draft = ref('')
const errorMessage = ref('')
const loadingContacts = ref(true)
const loadingMessages = ref(false)
const sending = ref(false)
const afterId = ref(0)
const messageList = ref(null)
const accountMenuOpen = ref(false)
const deleteDialogOpen = ref(false)
const deleteConfirmation = ref('')
const deletingAccount = ref(false)
const loggingOut = ref(false)
const editDialogOpen = ref(false)
const editUsername = ref('')
const editPassword = ref('')
const confirmEditPassword = ref('')
const editError = ref('')
const updatingProfile = ref(false)

let messageTimer
let contactTimer

const currentUser = ref(readCurrentUser())
const isAdmin = ref(currentUser.value.id === 1)
const filteredContacts = computed(() => {
  const keyword = searchText.value.trim().toLowerCase()
  if (!keyword) return contacts.value
  return contacts.value.filter((contact) =>
    contact.username.toLowerCase().includes(keyword) || contact.account.includes(keyword),
  )
})

function readCurrentUser() {
  try {
    return JSON.parse(sessionStorage.getItem('chat_user')) || {}
  } catch {
    return {}
  }
}

function formatTime(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function avatarText(contact) {
  return (contact.username || contact.account || '?').slice(0, 1).toUpperCase()
}

function handleError(error, silent = false) {
  if (error.status === 401) {
    sessionStorage.removeItem('chat_user')
    router.replace('/')
    return
  }
  if (!silent) errorMessage.value = error.message
}

async function detectAdmin() {
  if (isAdmin.value) return

  try {
    const users = await getAdminUsers()
    const admin = users.find((user) => user.id === 1)
    if (!admin) return

    currentUser.value = admin
    isAdmin.value = true
    sessionStorage.setItem('chat_user', JSON.stringify(admin))
  } catch {
    isAdmin.value = false
  }
}

async function loadContacts() {
  try {
    const data = await getConversations()
    contacts.value = data

    if (selectedContact.value) {
      const updated = data.find((item) => item.account === selectedContact.value.account)
      if (updated) selectedContact.value = updated
    } else if (data.length) {
      await selectContact(data[0])
    }
  } catch (error) {
    handleError(error)
  } finally {
    loadingContacts.value = false
  }
}

async function selectContact(contact) {
  selectedContact.value = contact
  messages.value = []
  afterId.value = 0
  errorMessage.value = ''
  await loadConversation()
}

async function openConversation() {
  const account = newAccount.value.trim()
  if (!account) return

  const existing = contacts.value.find((contact) => contact.account === account)
  newAccount.value = ''
  await selectContact(existing || { account, username: account })
}

async function loadConversation(incremental = false, silent = false) {
  if (!selectedContact.value || loadingMessages.value) return
  loadingMessages.value = true

  try {
    const startId = incremental ? afterId.value : 0
    const data = await getMessages(selectedContact.value.account, startId)
    const knownIds = new Set(messages.value.map((message) => message.id))
    const newMessages = data.filter((message) => !knownIds.has(message.id))
    messages.value = incremental ? [...messages.value, ...newMessages] : data
    if (data.length) afterId.value = data[data.length - 1].id
    if (data.length || !incremental) await scrollToBottom()
  } catch (error) {
    handleError(error, silent)
  } finally {
    loadingMessages.value = false
  }
}

async function submitMessage() {
  const content = draft.value
  if (!selectedContact.value || content.length === 0 || sending.value) return

  errorMessage.value = ''
  sending.value = true
  try {
    const message = await sendMessage(selectedContact.value.account, content)
    messages.value.push({ ...message, is_mine: true })
    afterId.value = Math.max(afterId.value, message.id)
    draft.value = ''
    await scrollToBottom()
    await loadContacts()
  } catch (error) {
    handleError(error)
  } finally {
    sending.value = false
  }
}

async function scrollToBottom() {
  await nextTick()
  if (messageList.value) messageList.value.scrollTop = messageList.value.scrollHeight
}

function openDeleteDialog() {
  accountMenuOpen.value = false
  deleteConfirmation.value = ''
  deleteDialogOpen.value = true
}

function openEditDialog() {
  accountMenuOpen.value = false
  editUsername.value = currentUser.value.username || ''
  editPassword.value = ''
  confirmEditPassword.value = ''
  editError.value = ''
  editDialogOpen.value = true
}

function closeEditDialog() {
  if (updatingProfile.value) return
  editDialogOpen.value = false
}

async function saveProfile() {
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
  if (username !== currentUser.value.username) payload.username = username
  if (password) payload.password = password
  if (!Object.keys(payload).length) {
    editError.value = '没有需要修改的内容'
    return
  }

  updatingProfile.value = true
  try {
    const user = await updateUser(currentUser.value.id, payload)
    currentUser.value = { ...currentUser.value, ...user }
    sessionStorage.setItem('chat_user', JSON.stringify(currentUser.value))
    editDialogOpen.value = false
  } catch (error) {
    if (error.status === 401) {
      handleError(error)
    } else {
      editError.value = error.message
    }
  } finally {
    updatingProfile.value = false
  }
}

function closeDeleteDialog() {
  if (deletingAccount.value) return
  deleteDialogOpen.value = false
  deleteConfirmation.value = ''
}

async function deleteOwnAccount() {
  if (deleteConfirmation.value !== 'Potato' || !currentUser.value.id) return

  deletingAccount.value = true
  try {
    await deleteUser(currentUser.value.id)
    sessionStorage.removeItem('chat_user')
    router.replace('/')
  } catch (error) {
    handleError(error)
  } finally {
    deletingAccount.value = false
  }
}

async function handleLogout() {
  if (loggingOut.value) return

  accountMenuOpen.value = false
  loggingOut.value = true
  try {
    await logout()
    sessionStorage.removeItem('chat_user')
    router.replace('/')
  } catch (error) {
    handleError(error)
  } finally {
    loggingOut.value = false
  }
}

onMounted(async () => {
  await detectAdmin()
  await loadContacts()
  messageTimer = setInterval(() => loadConversation(true, true), 1500)
  contactTimer = setInterval(loadContacts, 5000)
})

onUnmounted(() => {
  clearInterval(messageTimer)
  clearInterval(contactTimer)
})
</script>

<template>
  <main class="chat-page">
    <div class="chat-layout">
      <aside class="sidebar">
        <header class="profile-bar">
          <button
            class="avatar avatar-button"
            type="button"
            aria-label="打开账户菜单"
            @click="accountMenuOpen = !accountMenuOpen"
          >{{ (currentUser.username || '我').slice(0, 1) }}</button>
          <div class="profile-copy">
            <strong>{{ currentUser.username || '我的消息' }}</strong>
            <small>{{ currentUser.account || '已登录' }}</small>
          </div>
          <button
            v-if="isAdmin"
            class="admin-shortcut"
            type="button"
            aria-label="进入管理后台"
            title="进入管理后台"
            @click="router.push('/admin')"
          >★</button>
          <div v-if="accountMenuOpen" class="account-menu">
            <button type="button" :disabled="!currentUser.id" @click="openEditDialog">修改资料</button>
            <button type="button" :disabled="loggingOut" @click="handleLogout">
              {{ loggingOut ? '正在退出…' : '退出登录' }}
            </button>
            <button class="danger-menu-button" type="button" :disabled="!currentUser.id" @click="openDeleteDialog">注销账号</button>
          </div>
        </header>

        <form class="new-chat" @submit.prevent="openConversation">
          <input v-model="newAccount" aria-label="对方账号" placeholder="输入账号发起聊天">
          <button type="submit" aria-label="发起聊天">＋</button>
        </form>

        <input v-model="searchText" class="contact-search" aria-label="搜索联系人" placeholder="搜索联系人">

        <div class="contact-list">
          <p v-if="loadingContacts" class="list-tip">正在加载联系人…</p>
          <p v-else-if="!filteredContacts.length" class="list-tip">暂无联系人</p>
          <button
            v-for="contact in filteredContacts"
            :key="contact.account"
            class="contact-item"
            :class="{ active: selectedContact?.account === contact.account }"
            type="button"
            @click="selectContact(contact)"
          >
            <span class="avatar small">{{ avatarText(contact) }}</span>
            <span class="contact-copy">
              <span class="contact-line">
                <strong>{{ contact.username }}</strong>
                <time>{{ formatTime(contact.last_message_at) }}</time>
              </span>
              <span class="last-message">{{ contact.last_message }}</span>
            </span>
          </button>
        </div>
      </aside>

      <section class="conversation-panel">
        <div v-if="!selectedContact" class="empty-chat">
          <div class="empty-icon">聊</div>
          <h2>选择一个联系人开始聊天</h2>
          <p>也可以在左侧输入账号发起新会话</p>
        </div>

        <template v-else>
          <header class="conversation-header">
            <div>
              <h2>{{ selectedContact.username }}</h2>
              <p>账号 {{ selectedContact.account }}</p>
            </div>
            <span v-if="selectedContact.last_seen_at">最近登录 {{ formatTime(selectedContact.last_seen_at) }}</span>
          </header>

          <div ref="messageList" class="message-list">
            <p v-if="loadingMessages && !messages.length" class="list-tip">正在加载消息…</p>
            <div v-else-if="!messages.length" class="message-empty">还没有消息，打个招呼吧</div>
            <div
              v-for="message in messages"
              :key="message.id"
              class="message-row"
              :class="{ mine: message.is_mine }"
            >
              <div class="message-bubble">
                <p>{{ message.content }}</p>
                <time>{{ formatTime(message.created_at) }}</time>
              </div>
            </div>
          </div>

          <p v-if="errorMessage" class="chat-error">{{ errorMessage }}</p>

          <form class="composer" @submit.prevent="submitMessage">
            <textarea
              v-model="draft"
              aria-label="消息内容"
              placeholder="输入消息，Enter 发送，Shift + Enter 换行"
              rows="3"
              @keydown.enter.exact.prevent="submitMessage"
            ></textarea>
            <button type="submit" :disabled="sending || draft.length === 0">
              {{ sending ? '发送中…' : '发送' }}
            </button>
          </form>
        </template>
      </section>
    </div>

    <div v-if="editDialogOpen" class="dialog-backdrop" @click.self="closeEditDialog">
      <section class="confirm-dialog profile-dialog" role="dialog" aria-modal="true" aria-labelledby="edit-profile-title">
        <h2 id="edit-profile-title">修改资料</h2>
        <label for="edit-username">用户名</label>
        <input id="edit-username" v-model="editUsername" autocomplete="username">
        <label for="edit-password">新密码</label>
        <input id="edit-password" v-model="editPassword" type="password" autocomplete="new-password" placeholder="留空则不修改">
        <label for="confirm-edit-password">确认新密码</label>
        <input id="confirm-edit-password" v-model="confirmEditPassword" type="password" autocomplete="new-password" placeholder="再次输入新密码">
        <p v-if="editError" class="form-error">{{ editError }}</p>
        <div class="dialog-actions">
          <button type="button" @click="closeEditDialog">取消</button>
          <button class="primary-dialog-button" type="button" :disabled="updatingProfile" @click="saveProfile">
            {{ updatingProfile ? '保存中…' : '保存修改' }}
          </button>
        </div>
      </section>
    </div>

    <div v-if="deleteDialogOpen" class="dialog-backdrop" @click.self="closeDeleteDialog">
      <section class="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="delete-account-title">
        <h2 id="delete-account-title">确认注销账号</h2>
        <p>注销后无法恢复，但历史消息会保留并显示为“已注销用户”。请输入 <strong>Potato</strong> 继续。</p>
        <input v-model="deleteConfirmation" aria-label="注销确认文字" autocomplete="off" placeholder="输入 Potato">
        <div class="dialog-actions">
          <button type="button" @click="closeDeleteDialog">取消</button>
          <button
            class="danger-button"
            type="button"
            :disabled="deleteConfirmation !== 'Potato' || deletingAccount"
            @click="deleteOwnAccount"
          >{{ deletingAccount ? '正在注销…' : '确认注销' }}</button>
        </div>
      </section>
    </div>
  </main>
</template>
