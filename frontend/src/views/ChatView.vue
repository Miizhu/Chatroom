<script setup>
import { ref } from 'vue'
const peerAccount = ref('')
const messageContent = ref('')
const messages = ref([])
const errorMessage = ref('')

async function loadMessages() {
    errorMessage.value = ""

    const response = await fetch(
        `http://localhost:8000/messages?peer_account=${peerAccount.value}&after_id=0`,
        {
        credentials: 'include',
        }
    )
    console.log(response.status, response.ok)
    const data = await response.json()
    console.log(data)
    if(!response.ok){
        errorMessage.value = data.detail
        return
    }
    messages.value = data
}
</script>
<template>
    <main>
        <h1>聊天室</h1>
        <label for = "peer-account">对方账号</label>
        <input id = "peer-account" name="peer-account" type="text" v-model="peerAccount">
        <button type="button" @click="loadMessages">加载聊天记录</button>
        <p v-if="messages.length === 0">暂无消息</p>
        <div v-for="message in messages" :key = "message.id">
            <span>{{ message.content }}</span>
        </div>
        <p v-if="errorMessage">{{ errorMessage }}</p>
    </main>
</template>