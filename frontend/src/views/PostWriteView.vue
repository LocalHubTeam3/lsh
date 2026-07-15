<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { onClickOutside } from '@vueuse/core'
import { ArrowLeft, MapPin, Save, Search, X } from 'lucide-vue-next'
import { useRoute, useRouter } from 'vue-router'
import { createPost, getPost, updatePost } from '../api/posts'
import { getLocation, getLocations } from '../api/locations'
import { POST_CATEGORIES } from '../constants/posts'
import StatePanel from '../components/common/StatePanel.vue'

const route = useRoute()
const router = useRouter()
const editing = computed(() => Boolean(route.params.id))
const form = reactive({ category: '여행질문', nickname: '', title: '', content: '', password: '', location_id: null })
const selectedLocation = ref(null)
const locationQuery = ref('')
const locationResults = ref([])
const locationSearching = ref(false)
const locationPicker = ref(null)
const locationOpen = ref(false)
const loading = ref(editing.value)
const submitting = ref(false)
const error = ref('')

onClickOutside(locationPicker, () => { locationOpen.value = false })

onMounted(async () => {
  if (!editing.value) {
    if (route.query.location_id) {
      try { chooseLocation(await getLocation(route.query.location_id)) }
      catch (err) { error.value = err.message }
    }
    return
  }
  try {
    const post = await getPost(route.params.id)
    form.category = post.category
    form.nickname = post.nickname
    form.title = post.title
    form.content = post.content
    form.location_id = post.location_id
    selectedLocation.value = post.location
    locationQuery.value = post.location?.title || ''
  } catch (err) { error.value = err.message }
  finally { loading.value = false }
})

async function submit() {
  error.value = ''
  submitting.value = true
  try {
    const payload = { ...form, category: form.category.trim(), nickname: form.nickname.trim(), title: form.title.trim(), content: form.content.trim() }
    const post = editing.value ? await updatePost(route.params.id, payload) : await createPost(payload)
    router.push(`/community/${post.id}`)
  } catch (err) { error.value = err.status === 403 ? '비밀번호가 일치하지 않습니다.' : err.message }
  finally { submitting.value = false }
}

async function searchLocations() {
  const keyword = locationQuery.value.trim()
  if (!keyword) { locationResults.value = []; locationOpen.value = false; return }
  locationSearching.value = true
  try { locationResults.value = (await getLocations({ search: keyword, page: 1, size: 8 })).items; locationOpen.value = true }
  catch (err) { locationOpen.value = false; error.value = err.message }
  finally { locationSearching.value = false }
}

function chooseLocation(place) { selectedLocation.value = place; form.location_id = place.id; locationQuery.value = place.title; locationResults.value = []; locationOpen.value = false }
function clearLocation() { selectedLocation.value = null; form.location_id = null; locationQuery.value = ''; locationResults.value = []; locationOpen.value = false }
function handleLocationInput() {
  if (selectedLocation.value && locationQuery.value !== selectedLocation.value.title) {
    selectedLocation.value = null
    form.location_id = null
  }
  locationOpen.value = false
}
</script>

<template>
  <div class="page narrow container">
    <RouterLink class="back-link" :to="editing ? `/community/${route.params.id}` : '/community'"><ArrowLeft :size="17" />돌아가기</RouterLink>
    <header class="write-heading"><p class="eyebrow">SHARE A STORY</p><h1>{{ editing ? '게시글 수정' : '새 이야기 작성' }}</h1><p>지역에 도움이 되는 질문과 경험을 나눠주세요.</p></header>
    <StatePanel v-if="loading" type="loading" title="게시글을 불러오고 있어요" />
    <StatePanel v-else-if="error && editing && !form.title" type="error" title="게시글을 불러오지 못했어요" :message="error" />
    <form v-else class="write-form panel" @submit.prevent="submit">
      <div class="field"><label for="category">분류</label><select id="category" v-model="form.category" class="select" required><option v-for="category in POST_CATEGORIES" :key="category">{{ category }}</option></select></div>
      <div class="field nickname-field"><label for="nickname">닉네임</label><input id="nickname" v-model="form.nickname" class="input" maxlength="30" required autocomplete="nickname" placeholder="게시글에 표시할 닉네임을 입력하세요" /><small>{{ form.nickname.length }} / 30</small></div>
      <div ref="locationPicker" class="field location-picker"><label for="location-search">관련 장소 <small>선택 사항</small></label>
        <div class="location-search"><div class="location-input"><Search :size="17" /><input id="location-search" v-model="locationQuery" maxlength="100" placeholder="게시글과 관련된 서울 장소를 검색하세요" role="combobox" :aria-expanded="locationOpen && Boolean(locationResults.length)" aria-controls="location-options" @input="handleLocationInput" @focus="locationOpen = Boolean(locationResults.length)" @keydown.enter.prevent="searchLocations" @keydown.esc="locationOpen = false" /><button v-show="selectedLocation" type="button" aria-label="관련 장소 선택 해제" @click="clearLocation"><X :size="16" /></button></div><button class="button secondary" type="button" :disabled="locationSearching" @click="searchLocations">{{ locationSearching ? '검색 중' : '검색' }}</button></div>
        <div v-if="locationOpen && locationResults.length" id="location-options" class="location-options" role="listbox"><button v-for="place in locationResults" :key="place.id" type="button" role="option" @click="chooseLocation(place)"><MapPin :size="15" /><span><strong>{{ place.title }}</strong><small>{{ place.address || '주소 정보 없음' }}</small></span></button></div>
      </div>
      <div class="field"><label for="title">제목</label><input id="title" v-model="form.title" class="input" maxlength="200" required placeholder="이야기의 제목을 입력하세요" /></div>
      <div class="field"><label for="content">내용</label><textarea id="content" v-model="form.content" class="textarea" maxlength="10000" required placeholder="서울에서 궁금한 점이나 나누고 싶은 경험을 적어주세요."></textarea><small>{{ form.content.length.toLocaleString('ko-KR') }} / 10,000</small></div>
      <div class="password-row">
        <div class="field"><label for="password">{{ editing ? '수정 비밀번호' : '비밀번호' }}</label><input id="password" v-model="form.password" class="input" type="password" maxlength="100" required autocomplete="new-password" placeholder="수정·삭제할 때 필요합니다" /><small>로그인 없이 게시글을 수정하거나 삭제할 때 사용됩니다.</small></div>
      </div>
      <p v-if="error" class="form-error" role="alert">{{ error }}</p>
      <div class="form-actions"><RouterLink class="button ghost" :to="editing ? `/community/${route.params.id}` : '/community'">취소</RouterLink><button class="button primary" type="submit" :disabled="submitting"><Save :size="17" />{{ submitting ? '저장 중...' : (editing ? '수정하기' : '등록하기') }}</button></div>
    </form>
  </div>
</template>

<style scoped>
.narrow { max-width: 860px; }.back-link { display: inline-flex; align-items: center; gap: 6px; margin-bottom: 24px; color: var(--color-muted); font-size: 14px; font-weight: 700; }
.write-heading { margin-bottom: 26px; }.write-heading h1 { margin: 4px 0 8px; font-size: 38px; }.write-heading > p:last-child { color: var(--color-muted); }
.write-form { display: grid; gap: 24px; padding: 30px; }.field small { justify-self: end; color: var(--color-muted); font-size: 11px; }.nickname-field, .password-row { max-width: 420px; }
.location-picker { position: relative; }.location-search { display: flex; align-items: center; gap: 8px; }.location-input { position: relative; display: flex; min-width: 0; height: 44px; flex: 1; align-items: center; }.location-input > svg { position: absolute; left: 11px; color: var(--color-muted); pointer-events: none; }.location-input input { width: 100%; min-width: 0; height: 44px; padding: 0 38px 0 36px; border: 1px solid var(--color-line); border-radius: 6px; outline: 0; }.location-input input:focus { border-color: var(--color-primary); }.location-input > button { position: absolute; right: 7px; display: grid; width: 28px; height: 28px; place-items: center; padding: 0; border: 0; color: var(--color-muted); background: transparent; }.location-options { position: absolute; z-index: 50; top: calc(100% + 6px); right: 0; left: 0; display: grid; max-height: 240px; overflow-y: auto; border: 1px solid var(--color-line); border-radius: 6px; background: #fff; box-shadow: 0 14px 34px rgba(18,43,34,.16); }.location-options button { display: flex; align-items: center; gap: 9px; padding: 11px; border: 0; border-bottom: 1px solid var(--color-line); text-align: left; background: #fff; }.location-options button:last-child { border-bottom: 0; }.location-options button:hover { background: var(--color-surface-soft); }.location-options span { display: grid; flex: 1; gap: 3px; }.location-options small { color: var(--color-muted); font-size: 10px; }
.form-error { margin: 0; padding: 12px 14px; border-radius: 6px; color: var(--color-danger); background: #fff0f0; font-size: 13px; }.form-actions { display: flex; justify-content: flex-end; gap: 8px; padding-top: 4px; }
@media (max-width: 600px) { .write-form { padding: 20px 16px; }.write-heading h1 { font-size: 32px; } }
</style>
