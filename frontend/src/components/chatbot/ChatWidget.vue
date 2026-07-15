<script setup>
import { computed, nextTick, ref } from 'vue'
import { Bot, ExternalLink, MessageCircle, Send, X } from 'lucide-vue-next'
import { sendChat } from '../../api/chatbot'

const open = ref(false)
const input = ref('')
const sending = ref(false)
const error = ref('')
const scrollArea = ref(null)
const messages = ref([{
  role: 'assistant',
  content: '안녕하세요! 서울의 장소, 여행 코스, 지역 이야기가 궁금하면 편하게 물어보세요.',
  references: [],
}])
const suggestions = ['오늘 서울에서 갈 만한 곳 추천해줘', '가족과 가기 좋은 장소가 있어?', '서울 여행 코스를 알려줘']
const canSend = computed(() => input.value.trim() && !sending.value)

function referenceLink(reference) {
  if (reference.type === 'location') return `/locations/${reference.id}`
  if (reference.type === 'post') return `/community/${reference.id}`
  if (reference.type === 'course') return `/courses/${reference.id}`
  return null
}

async function scrollToBottom() {
  await nextTick()
  if (scrollArea.value) scrollArea.value.scrollTop = scrollArea.value.scrollHeight
}

async function submit(text = input.value) {
  const content = text.trim()
  if (!content || sending.value) return
  const history = messages.value.map(({ role, content: itemContent }) => ({ role, content: itemContent }))
  messages.value.push({ role: 'user', content, references: [] })
  input.value = ''
  error.value = ''
  sending.value = true
  await scrollToBottom()
  try {
    const result = await sendChat(content, history)
    messages.value.push({ role: 'assistant', content: result.answer, references: result.references || [] })
  } catch (err) { error.value = err.message }
  finally { sending.value = false; scrollToBottom() }
}

function handleKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); submit() }
}
</script>

<template>
  <button class="chat-launcher" type="button" :aria-label="open ? '여행 도우미 닫기' : '여행 도우미 열기'" :aria-expanded="open" @click="open = !open">
    <X v-if="open" :size="23" /><MessageCircle v-else :size="25" />
  </button>
  <section v-if="open" class="chat-panel" aria-label="LocalHub 여행 도우미">
    <header><div class="bot-mark"><Bot :size="21" /></div><div><strong>LocalHub 도우미</strong><span><i></i>서울 데이터 기반 답변</span></div><button type="button" aria-label="닫기" @click="open = false"><X :size="20" /></button></header>
    <div ref="scrollArea" class="messages" role="log" aria-live="polite">
      <div v-for="(message, index) in messages" :key="index" :class="['message-row', message.role]">
        <div class="bubble">{{ message.content }}</div>
        <div v-if="message.references?.length" class="references">
          <template v-for="reference in message.references" :key="`${reference.type}-${reference.id}`">
            <RouterLink v-if="referenceLink(reference)" :to="referenceLink(reference)" @click="open = false">{{ reference.title }}<ExternalLink :size="12" /></RouterLink>
            <span v-else>{{ reference.title }}</span>
          </template>
        </div>
      </div>
      <div v-if="sending" class="message-row assistant"><div class="typing"><i></i><i></i><i></i></div></div>
    </div>
    <div v-if="messages.length === 1" class="suggestions"><button v-for="item in suggestions" :key="item" type="button" @click="submit(item)">{{ item }}</button></div>
    <p v-if="error" class="chat-error" role="alert">{{ error }} <button type="button" @click="submit(messages.at(-1)?.content || input)">다시 시도</button></p>
    <form class="chat-form" @submit.prevent="submit()">
      <textarea v-model="input" rows="1" maxlength="2000" placeholder="서울에 대해 물어보세요" aria-label="메시지" @keydown="handleKeydown"></textarea>
      <button type="submit" :disabled="!canSend" aria-label="전송"><Send :size="18" /></button>
    </form>
    <small class="notice">AI 답변은 부정확할 수 있으니 중요한 정보는 다시 확인해 주세요.</small>
  </section>
</template>

<style scoped>
.chat-launcher { position: fixed; z-index: 1501; right: 24px; bottom: 24px; display: grid; width: 56px; height: 56px; place-items: center; border: 0; border-radius: 50%; color: #fff; background: var(--color-primary); box-shadow: 0 10px 30px rgba(8,127,104,.3); transition: transform .18s ease; }.chat-launcher:hover { transform: translateY(-2px); }
.chat-panel { position: fixed; z-index: 1500; right: 24px; bottom: 92px; display: grid; width: min(390px, calc(100vw - 32px)); height: min(620px, calc(100vh - 130px)); grid-template-rows: auto minmax(0,1fr) auto auto auto; overflow: hidden; border: 1px solid var(--color-line); border-radius: 14px; background: #fff; box-shadow: var(--shadow-lg); }
.chat-panel > header { display: flex; align-items: center; gap: 11px; padding: 15px 16px; color: #fff; background: #18332c; }.bot-mark { display: grid; width: 38px; height: 38px; place-items: center; border-radius: 10px; color: #18332c; background: #7bdbc0; }.chat-panel header > div:nth-child(2) { display: grid; gap: 3px; }.chat-panel header strong { font-size: 14px; }.chat-panel header span { display: flex; align-items: center; gap: 5px; color: #bdd0ca; font-size: 10px; }.chat-panel header i { width: 6px; height: 6px; border-radius: 50%; background: #64dfb9; }.chat-panel header button { display: grid; margin-left: auto; place-items: center; padding: 7px; border: 0; color: #fff; background: transparent; }
.messages { overflow-y: auto; padding: 18px 15px 10px; background: #f7f9f8; }.message-row { display: grid; justify-items: start; margin-bottom: 13px; }.message-row.user { justify-items: end; }.bubble { max-width: 85%; padding: 11px 13px; border: 1px solid var(--color-line); border-radius: 5px 14px 14px; background: #fff; font-size: 13px; line-height: 1.6; white-space: pre-wrap; }.user .bubble { border-color: var(--color-primary); border-radius: 14px 5px 14px 14px; color: #fff; background: var(--color-primary); }
.references { display: flex; max-width: 88%; flex-wrap: wrap; gap: 5px; margin-top: 7px; }.references a, .references span { display: inline-flex; align-items: center; gap: 3px; padding: 5px 8px; border: 1px solid #cce5dc; border-radius: 999px; color: var(--color-primary-dark); background: #fff; font-size: 10px; font-weight: 700; }
.typing { display: flex; gap: 4px; padding: 13px; border: 1px solid var(--color-line); border-radius: 5px 14px 14px; background: #fff; }.typing i { width: 5px; height: 5px; border-radius: 50%; background: #91a099; animation: bounce 1s infinite; }.typing i:nth-child(2) { animation-delay: .12s; }.typing i:nth-child(3) { animation-delay: .24s; }
.suggestions { display: flex; gap: 6px; overflow-x: auto; padding: 8px 12px; border-top: 1px solid var(--color-line); }.suggestions button { flex: 0 0 auto; padding: 7px 10px; border: 1px solid var(--color-line); border-radius: 999px; color: var(--color-primary-dark); background: #fff; font-size: 10px; }
.chat-error { margin: 0; padding: 7px 13px; color: var(--color-danger); background: #fff2f2; font-size: 11px; }.chat-error button { border: 0; color: inherit; background: transparent; font-weight: 800; text-decoration: underline; }
.chat-form { display: flex; align-items: end; gap: 8px; padding: 11px 12px 7px; border-top: 1px solid var(--color-line); }.chat-form textarea { min-height: 40px; max-height: 96px; flex: 1; padding: 10px 2px; resize: none; border: 0; outline: 0; font-size: 13px; }.chat-form button { display: grid; width: 38px; height: 38px; place-items: center; border: 0; border-radius: 8px; color: #fff; background: var(--color-primary); }.notice { padding: 0 12px 9px; color: #89938e; font-size: 9px; text-align: center; }
@keyframes bounce { 50% { transform: translateY(-3px); opacity: .5; } }
@media (max-width: 520px) { .chat-launcher { right: 16px; bottom: 16px; }.chat-panel { right: 8px; bottom: 80px; width: calc(100vw - 16px); height: calc(100vh - 96px); } }
</style>
