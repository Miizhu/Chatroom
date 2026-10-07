const API_BASE = 'http://localhost:8000'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...options,
  })
  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const error = new Error(data?.detail || '请求失败，请稍后重试')
    error.status = response.status
    throw error
  }

  return data
}

export function login(payload) {
  return request('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function register(payload) {
  return request('/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function logout() {
  return request('/logout', { method: 'POST' })
}

export function getConversations() {
  return request('/conversations')
}

export function getAdminUsers() {
  return request('/admin/users')
}

export function deleteUser(userId) {
  return request(`/users/${userId}`, { method: 'DELETE' })
}

export function updateUser(userId, payload) {
  return request(`/users/${userId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function getMessages(peerAccount, afterId = 0) {
  const query = new URLSearchParams({
    peer_account: peerAccount,
    after_id: String(afterId),
  })
  return request(`/messages?${query}`)
}

export function sendMessage(receiverAccount, content) {
  return request('/messages', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ receiver_account: receiverAccount, content }),
  })
}
