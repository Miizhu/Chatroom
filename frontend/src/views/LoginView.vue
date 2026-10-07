<script setup>
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { login } from '../api'

const route = useRoute()
const router = useRouter()
const account = ref(typeof route.query.account === 'string' ? route.query.account : '')
const password = ref('')
const errorMessage = ref('')
const pending = ref(false)

async function handleLogin() {
  errorMessage.value = ''
  pending.value = true

  try {
    const user = await login({ account: account.value.trim(), password: password.value })
    sessionStorage.setItem('chat_user', JSON.stringify(user))
    router.replace('/chat')
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    pending.value = false
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-card">
      <div class="brand-mark">聊</div>
      <h1>欢迎回来</h1>
      <p class="auth-subtitle">登录后继续你的聊天</p>

      <form class="auth-form" @submit.prevent="handleLogin">
        <label for="account">账号</label>
        <input id="account" v-model="account" name="account" autocomplete="username" required>

        <label for="password">密码</label>
        <input id="password" v-model="password" name="password" type="password" autocomplete="current-password" required>

        <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
        <button class="primary-button" type="submit" :disabled="pending">
          {{ pending ? '登录中…' : '登录' }}
        </button>
      </form>

      <p class="auth-switch">还没有账号？<RouterLink to="/register">立即注册</RouterLink></p>
    </section>
  </main>
</template>
