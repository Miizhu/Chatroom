<script setup>
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { register } from '../api'

const router = useRouter()
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const registeredAccount = ref('')
const errorMessage = ref('')
const pending = ref(false)

async function handleRegister() {
  errorMessage.value = ''

  if (password.value !== password.value.trim()) {
    errorMessage.value = '密码开头和结尾不能使用空格'
    return
  }

  if (password.value !== confirmPassword.value) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }

  pending.value = true
  try {
    const data = await register({ username: username.value.trim(), password: password.value })
    registeredAccount.value = data.account
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    pending.value = false
  }
}

function goToLogin() {
  router.push({ name: 'login', query: { account: registeredAccount.value } })
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-card">
      <div class="brand-mark">聊</div>

      <template v-if="registeredAccount">
        <h1>注册成功</h1>
        <p class="auth-subtitle">请保存你的登录账号</p>
        <div class="account-result">{{ registeredAccount }}</div>
        <button class="primary-button" type="button" @click="goToLogin">去登录</button>
      </template>

      <template v-else>
        <h1>创建账号</h1>
        <p class="auth-subtitle">注册后系统会生成登录账号</p>

        <form class="auth-form" @submit.prevent="handleRegister">
          <label for="username">昵称</label>
          <input id="username" v-model="username" name="username" autocomplete="nickname" required>

          <label for="new-password">密码</label>
          <input id="new-password" v-model="password" name="password" type="password" autocomplete="new-password" required>
          <p class="field-hint">密码开头和结尾不能使用空格</p>

          <label for="confirm-password">确认密码</label>
          <input id="confirm-password" v-model="confirmPassword" name="confirm-password" type="password" autocomplete="new-password" required>

          <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
          <button class="primary-button" type="submit" :disabled="pending">
            {{ pending ? '注册中…' : '注册' }}
          </button>
        </form>

        <p class="auth-switch">已有账号？<RouterLink to="/">返回登录</RouterLink></p>
      </template>
    </section>
  </main>
</template>
