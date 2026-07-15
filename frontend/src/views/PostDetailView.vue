<script setup>
import { onMounted, ref } from 'vue'
import { ArrowLeft, CalendarDays, Eye, MapPin, Pencil, Trash2, UserRound } from 'lucide-vue-next'
import { useRoute, useRouter } from 'vue-router'
import { deletePost, getPost } from '../api/posts'
import StatePanel from '../components/common/StatePanel.vue'

const route = useRoute()
const router = useRouter()
const post = ref(null)
const loading = ref(true)
const deleting = ref(false)
const error = ref('')
const password = ref('')
const deleteOpen = ref(false)
const deleteError = ref('')

function formatDate(value) {
  return new Intl.DateTimeFormat('ko-KR', { dateStyle: 'long', timeStyle: 'short' }).format(new Date(value))
}

async function load() {
  loading.value = true; error.value = ''
  try { post.value = await getPost(route.params.id) }
  catch (err) { error.value = err.message }
  finally { loading.value = false }
}

async function remove() {
  deleteError.value = ''; deleting.value = true
  try { await deletePost(route.params.id, password.value); router.push('/community') }
  catch (err) { deleteError.value = err.status === 403 ? '비밀번호가 일치하지 않습니다.' : err.message }
  finally { deleting.value = false }
}

onMounted(load)
</script>

<template>
  <div class="page article-page container">
    <RouterLink class="back-link" to="/community"><ArrowLeft :size="17" />목록으로</RouterLink>
    <StatePanel v-if="loading" type="loading" title="게시글을 불러오고 있어요" />
    <StatePanel v-else-if="error" type="error" title="게시글을 찾지 못했어요" :message="error" @retry="load" />
    <article v-else-if="post" class="post-article panel">
      <header>
        <span class="badge">{{ post.category }}</span>
        <h1>{{ post.title }}</h1>
        <div class="meta"><span><UserRound :size="15" />익명</span><span><CalendarDays :size="15" />{{ formatDate(post.created_at) }}</span><span><Eye :size="15" />조회 {{ post.views.toLocaleString('ko-KR') }}</span></div>
      </header>
      <RouterLink v-if="post.location" class="related-place" :to="`/locations/${post.location.id}`"><MapPin :size="19" /><span><small>관련 장소</small><strong>{{ post.location.title }}</strong><em>{{ post.location.address || '주소 정보 없음' }}</em></span></RouterLink>
      <div class="content">{{ post.content }}</div>
      <footer><RouterLink class="button secondary" :to="`/community/${post.id}/edit`"><Pencil :size="16" />수정</RouterLink><button class="button danger" type="button" @click="deleteOpen = true"><Trash2 :size="16" />삭제</button></footer>
    </article>

    <div v-if="deleteOpen" class="modal-backdrop" @click.self="deleteOpen = false">
      <form class="delete-modal panel" @submit.prevent="remove">
        <h2>게시글을 삭제할까요?</h2><p>작성할 때 입력한 비밀번호를 확인한 뒤 삭제합니다. 삭제한 글은 복구할 수 없습니다.</p>
        <div class="field"><label for="delete-password">비밀번호</label><input id="delete-password" v-model="password" class="input" type="password" required autofocus autocomplete="current-password" /></div>
        <p v-if="deleteError" class="delete-error" role="alert">{{ deleteError }}</p>
        <div class="modal-actions"><button class="button ghost" type="button" @click="deleteOpen = false">취소</button><button class="button danger" type="submit" :disabled="deleting">{{ deleting ? '삭제 중...' : '삭제하기' }}</button></div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.article-page { max-width: 940px; }.back-link { display: inline-flex; align-items: center; gap: 6px; margin-bottom: 22px; color: var(--color-muted); font-size: 14px; font-weight: 700; }
.post-article { overflow: hidden; }.post-article header { padding: 38px 42px 30px; border-bottom: 1px solid var(--color-line); }.post-article h1 { margin: 15px 0 18px; font-size: clamp(30px,5vw,44px); line-height: 1.25; }
.meta { display: flex; flex-wrap: wrap; gap: 18px; color: var(--color-muted); font-size: 13px; }.meta span { display: flex; align-items: center; gap: 5px; }.content { min-height: 300px; padding: 42px; white-space: pre-wrap; line-height: 1.9; }
.related-place { display: flex; align-items: center; gap: 12px; margin: 24px 42px 0; padding: 15px 17px; border: 1px solid #c6ded5; border-radius: 8px; color: var(--color-primary-dark); background: var(--color-primary-soft); }.related-place > svg { flex: 0 0 auto; }.related-place span { display: grid; gap: 2px; }.related-place small { font-size: 10px; font-weight: 800; }.related-place em { color: var(--color-muted); font-size: 11px; font-style: normal; }
.post-article footer { display: flex; justify-content: flex-end; gap: 8px; padding: 20px 42px; border-top: 1px solid var(--color-line); background: #fafbfa; }
.modal-backdrop { position: fixed; z-index: 2000; inset: 0; display: grid; place-items: center; padding: 20px; background: rgba(12,25,20,.48); }.delete-modal { width: min(100%, 440px); padding: 28px; box-shadow: var(--shadow-lg); }.delete-modal h2 { margin-bottom: 10px; }.delete-modal > p { color: var(--color-muted); font-size: 14px; line-height: 1.6; }.delete-error { color: var(--color-danger) !important; }.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 24px; }
@media (max-width: 600px) { .post-article header, .content { padding: 26px 20px; }.related-place { margin: 18px 20px 0; }.post-article footer { padding: 16px 20px; } }
</style>
