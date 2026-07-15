<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Eye, MapPin, PenLine, Search, UserRound, X } from 'lucide-vue-next'
import { useRoute, useRouter } from 'vue-router'
import { getPosts } from '../api/posts'
import { getLocations } from '../api/locations'
import { POST_CATEGORIES } from '../constants/posts'
import PaginationBar from '../components/common/PaginationBar.vue'
import StatePanel from '../components/common/StatePanel.vue'

const route = useRoute()
const router = useRouter()
const SEARCH_FIELDS = [
  { value: 'title', label: '제목' },
  { value: 'content', label: '내용' },
  { value: 'nickname', label: '닉네임' },
]
const initialSearchField = SEARCH_FIELDS.some((item) => item.value === route.query.search_field) ? route.query.search_field : 'title'
const state = reactive({
  search: String(route.query.search || ''),
  search_field: initialSearchField,
  sort: route.query.sort === 'views' ? 'views' : 'latest',
  category: String(route.query.category || ''),
  location_id: route.query.location_id ? Number(route.query.location_id) : '',
  page: Math.max(1, Number(route.query.page) || 1),
  size: 10,
})
const draftSearch = ref(state.search)
const locationQuery = ref(String(route.query.location || ''))
const locationResults = ref([])
const locationSearching = ref(false)
const data = ref({ items: [], total: 0, page: 1, size: 10 })
const loading = ref(false)
const error = ref('')
const totalPages = computed(() => Math.max(1, Math.ceil(data.value.total / state.size)))
const searchPlaceholder = computed(() => `${SEARCH_FIELDS.find((item) => item.value === state.search_field)?.label || '제목'}으로 검색하세요`)

function formatDate(value) {
  return new Intl.DateTimeFormat('ko-KR', { dateStyle: 'medium' }).format(new Date(value))
}

async function load() {
  loading.value = true
  error.value = ''
  try { data.value = await getPosts(state) }
  catch (err) { error.value = err.message }
  finally { loading.value = false }
}

function syncRoute() {
  router.replace({ query: {
    ...(state.search && { search: state.search }),
    ...(state.search && state.search_field !== 'title' && { search_field: state.search_field }),
    ...(state.sort !== 'latest' && { sort: state.sort }),
    ...(state.category && { category: state.category }),
    ...(state.location_id && { location_id: state.location_id, location: locationQuery.value }),
    ...(state.page > 1 && { page: state.page }),
  } })
}

function submitSearch() { state.search = draftSearch.value.trim(); state.page = 1; syncRoute() }
function clearSearch() { draftSearch.value = ''; state.search = ''; state.page = 1; syncRoute() }
function setSort(sort) { state.sort = sort; state.page = 1; syncRoute() }
function setCategory(category) { state.category = category; state.page = 1; syncRoute() }
function setPage(page) { state.page = page; syncRoute(); window.scrollTo({ top: 0, behavior: 'smooth' }) }
async function searchLocations() {
  const keyword = locationQuery.value.trim()
  if (!keyword) { clearLocation(); return }
  locationSearching.value = true
  try { locationResults.value = (await getLocations({ search: keyword, page: 1, size: 6 })).items }
  catch { locationResults.value = [] }
  finally { locationSearching.value = false }
}
function selectLocation(place) { state.location_id = place.id; locationQuery.value = place.title; locationResults.value = []; state.page = 1; syncRoute() }
function clearLocation() { state.location_id = ''; locationQuery.value = ''; locationResults.value = []; state.page = 1; syncRoute() }

watch(() => route.fullPath, load)
onMounted(load)
</script>

<template>
  <div class="page container">
    <header class="page-heading">
      <div><p class="eyebrow">LOCAL STORIES</p><h1>커뮤니티</h1><p>나만의 닉네임으로 서울의 장소와 경험을 편하게 나눠보세요.</p></div>
      <RouterLink class="button primary" to="/community/write"><PenLine :size="18" />글쓰기</RouterLink>
    </header>

    <section class="board-tools panel">
      <form class="search-form" @submit.prevent="submitSearch">
        <Search :size="18" />
        <label class="sr-only" for="post-search-field">검색 기준</label><select id="post-search-field" v-model="state.search_field" aria-label="게시글 검색 기준"><option v-for="field in SEARCH_FIELDS" :key="field.value" :value="field.value">{{ field.label }}</option></select>
        <input v-model="draftSearch" type="search" maxlength="100" :placeholder="searchPlaceholder" aria-label="게시글 검색어" />
        <button v-if="draftSearch" class="clear" type="button" aria-label="검색어 지우기" @click="clearSearch"><X :size="17" /></button>
        <button class="button secondary" type="submit">검색</button>
      </form>
      <div class="sort-tabs" aria-label="정렬 방식">
        <button type="button" :class="{ active: state.sort === 'latest' }" @click="setSort('latest')">최신순</button>
        <button type="button" :class="{ active: state.sort === 'views' }" @click="setSort('views')">조회순</button>
      </div>
    </section>
    <section class="filter-panel panel" aria-label="게시글 필터">
      <div class="category-filters"><button type="button" :class="{ active: !state.category }" @click="setCategory('')">전체</button><button v-for="category in POST_CATEGORIES" :key="category" type="button" :class="{ active: state.category === category }" @click="setCategory(category)">{{ category }}</button></div>
      <div class="location-filter">
        <form @submit.prevent="searchLocations"><MapPin :size="16" /><input v-model="locationQuery" placeholder="관련 장소로 필터" aria-label="관련 장소 검색" @input="state.location_id = ''" /><button v-if="locationQuery" type="button" aria-label="장소 필터 지우기" @click="clearLocation"><X :size="15" /></button><button type="submit">{{ locationSearching ? '검색 중' : '장소 검색' }}</button></form>
        <div v-if="locationResults.length" class="location-results"><button v-for="place in locationResults" :key="place.id" type="button" @click="selectLocation(place)"><strong>{{ place.title }}</strong><span>{{ place.address || '주소 없음' }}</span></button></div>
      </div>
    </section>

    <div class="result-meta"><strong>{{ data.total.toLocaleString('ko-KR') }}</strong>개의 이야기</div>
    <StatePanel v-if="loading" type="loading" title="이야기를 불러오고 있어요" />
    <StatePanel v-else-if="error" type="error" title="게시글을 불러오지 못했어요" :message="error" @retry="load" />
    <StatePanel v-else-if="!data.items.length" title="아직 등록된 이야기가 없어요" message="첫 번째 서울 이야기를 남겨보세요." />
    <section v-else class="post-list panel">
      <RouterLink v-for="post in data.items" :key="post.id" class="post-row" :to="`/community/${post.id}`">
        <span class="badge">{{ post.category }}</span>
        <div class="post-copy"><h2>{{ post.title }}</h2><small v-if="post.location"><MapPin :size="12" />{{ post.location.title }}</small></div>
        <div class="post-meta"><span><UserRound :size="14" />{{ post.nickname || '익명' }}</span><span>{{ formatDate(post.created_at) }}</span><span><Eye :size="14" />{{ post.views.toLocaleString('ko-KR') }}</span></div>
      </RouterLink>
    </section>
    <PaginationBar v-if="data.total" :page="state.page" :total-pages="totalPages" :disabled="loading" @change="setPage" />
  </div>
</template>

<style scoped>
.board-tools { display: flex; align-items: center; gap: 18px; padding: 14px; }
.search-form { display: flex; min-width: 0; flex: 1; align-items: center; gap: 9px; }
.search-form > svg { margin-left: 4px; color: var(--color-muted); }
.search-form select { height: 34px; padding: 0 28px 0 8px; border: 0; border-radius: 6px; outline: 0; color: var(--color-primary-dark); background: var(--color-primary-soft); font-size: 12px; font-weight: 800; }
.search-form input { min-width: 0; flex: 1; height: 42px; border: 0; outline: 0; background: transparent; }
.clear { display: grid; place-items: center; padding: 6px; border: 0; color: var(--color-muted); background: transparent; }
.sort-tabs { display: flex; gap: 4px; padding-left: 16px; border-left: 1px solid var(--color-line); }
.sort-tabs button { height: 36px; padding: 0 12px; border: 0; border-radius: 6px; color: var(--color-muted); background: transparent; font-size: 13px; font-weight: 700; }
.sort-tabs button.active { color: var(--color-primary-dark); background: var(--color-primary-soft); }
.filter-panel { display: grid; grid-template-columns: minmax(0,1fr) 300px; gap: 14px; margin-top: 10px; padding: 13px; }.category-filters { display: flex; gap: 6px; overflow-x: auto; }.category-filters button { min-height: 36px; flex: 0 0 auto; padding: 0 11px; border: 1px solid var(--color-line); border-radius: 999px; color: var(--color-muted); background: #fff; font-size: 11px; font-weight: 700; }.category-filters button.active { border-color: var(--color-primary); color: #fff; background: var(--color-primary); }.location-filter { position: relative; }.location-filter form { display: flex; height: 38px; align-items: center; gap: 6px; padding-left: 9px; border: 1px solid var(--color-line); border-radius: 6px; }.location-filter input { min-width: 0; flex: 1; border: 0; outline: 0; font-size: 11px; }.location-filter form button { height: 100%; padding: 0 9px; border: 0; color: var(--color-primary-dark); background: var(--color-primary-soft); font-size: 10px; font-weight: 800; }.location-results { position: absolute; z-index: 10; top: 42px; right: 0; left: 0; overflow: hidden; border: 1px solid var(--color-line); border-radius: 6px; background: #fff; box-shadow: var(--shadow-lg); }.location-results button { display: grid; width: 100%; gap: 2px; padding: 9px 11px; border: 0; border-bottom: 1px solid var(--color-line); text-align: left; background: #fff; }.location-results button:hover { background: var(--color-surface-soft); }.location-results span { color: var(--color-muted); font-size: 9px; }
.result-meta { margin: 22px 2px 14px; color: var(--color-muted); font-size: 14px; }.result-meta strong { color: var(--color-primary); font-size: 18px; }
.post-list { overflow: hidden; }
.post-row { display: grid; grid-template-columns: 90px minmax(0,1fr) 130px; align-items: center; gap: 18px; min-height: 112px; padding: 20px 24px; border-bottom: 1px solid var(--color-line); transition: background .18s ease; }
.post-row:last-child { border-bottom: 0; }.post-row:hover { background: #fbfcfb; }
.post-row > .badge { min-width: 72px; justify-content: center; justify-self: center; text-align: center; }
.post-copy { min-width: 0; }.post-copy h2 { overflow: hidden; margin: 0; font-size: 17px; text-overflow: ellipsis; white-space: nowrap; }
.post-copy small { display: flex; align-items: center; gap: 3px; margin-top: 7px; color: var(--color-primary); font-size: 10px; font-weight: 700; }
.post-meta { display: grid; justify-items: end; gap: 9px; color: var(--color-muted); font-size: 12px; }.post-meta span:last-child { display: flex; align-items: center; gap: 4px; }
@media (max-width: 700px) { .board-tools { align-items: stretch; flex-direction: column; }.sort-tabs { padding: 10px 0 0; border-top: 1px solid var(--color-line); border-left: 0; }.filter-panel { grid-template-columns: 1fr; }.post-row { grid-template-columns: 1fr; gap: 9px; padding: 18px; }.post-row .badge { width: fit-content; }.post-meta { display: flex; justify-content: space-between; } }
</style>
