import { request } from './client'

export const sendChat = (message, history) => request('/api/chat', {
  method: 'POST',
  body: JSON.stringify({ message, history: history.slice(-20) }),
})
