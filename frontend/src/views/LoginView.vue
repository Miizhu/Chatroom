<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
const account = ref('')
const password = ref('')
const errorMessage = ref('')
const router = useRouter()



async function handleLogin() {
    errorMessage.value = ""
    const loginData  = {
        account: account.value,
        password: password.value
    }
    const response = await fetch(
        "http://localhost:8000/login",
        {method: 'POST', 
        headers: {'Content-Type': 'application/json'},
        credentials: 'include',
        body: JSON.stringify(loginData)
        }
    )
    console.log(response.status, response.ok)
    const data = await response.json()
    console.log(data)
    if(!response.ok){
        errorMessage.value = data.detail
        return
    }
    router.push('/chat')
}
</script>
<template>
    <main class = "login-page">
        <h1>登录到聊天室</h1>
        <form @submit.prevent="handleLogin">
            <div class = "input-field">
                <label>
                    账号
                </label>
                <input type="text" v-model="account">
            </div>
            <div class = "input-field">
                <label>
                    密码
                </label>
                <input type="password" v-model="password">
            </div>
            <p class = "error-message">{{ errorMessage }}</p>
            <div>
                <button type="submit">登录</button>
            </div>
        </form>
        
    </main>
</template>