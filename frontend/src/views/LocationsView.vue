<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Map, Search, X } from 'lucide-vue-next'
import { useRoute, useRouter } from 'vue-router'
import { getLocations } from '../api/locations'
import { LOCATION_TYPES } from '../constants/locations'
import LocationCard from '../components/location/LocationCard.vue'
import PaginationBar from '../components/common/PaginationBar.vue'
import StatePanel from '../components/common/StatePanel.vue'

const route = useRoute()
const router = useRouter()
const state = reactive({ search: String(route.query.search || ''), content_type: String(route.query.type || ''), page: Number(route.query.page) || 1, size: 12 })
const draftSearch = ref(state.search)
const data = ref({ items: [], total: 0, page: 1, size: 12 })
const loading = ref(false)
const error = ref('')
const totalPages = computed(() => Math.max(1, Math.ceil(data.value.total / state.size)))

async function load() {
  loading.value = true
  error.value = ''
  try { data.value = await getLocations(state) }
  catch (err) { error.value = err.message }
  finally { loading.value = false }
}
function submitSearch() { state.search = draftSearch.value.trim(); state.page = 1; syncRoute() }
function setType(type) { state.content_type = type; state.page = 1; syncRoute() }
function setPage(page) { state.page = page; syncRoute(); window.scrollTo({ top: 0, behavior: 'smooth' }) }
function clearSearch() { draftSearch.value = ''; state.search = ''; state.page = 1; syncRoute() }
function syncRoute() {
  router.replace({ query: { ...(state.search && { search: state.search }), ...(state.content_type && { type: state.content_type }), ...(state.page > 1 && { page: state.page }) } })
}
watch(() => route.fullPath, load)
onMounted(load)
</script>

<template>
  <div class="page container">
    <header class="page-heading">
      <div><p class="eyebrow">EXPLORE SEOUL</p><h1>장소 탐색</h1><p>서울의 다양한 장소를 검색하고 새로운 목적지를 찾아보세요.</p></div>
      <RouterLink class="button secondary" to="/map"><Map :size="18" />지도에서 보기</RouterLink>
    </header>
    <section class="search-area panel" aria-label="장소 검색 및 분류">
      <form class="search-form" @submit.prevent="submitSearch">
        <Search :size="19" />
        <input v-model="draftSearch" type="search" maxlength="100" placeholder="장소명이나 주소를 검색하세요" aria-label="장소 검색어" />
        <button v-if="draftSearch" class="clear" type="button" aria-label="검색어 지우기" @click="clearSearch"><X :size="17" /></button>
        <button class="button primary" type="submit">검색</button>
      </form>
      <div class="type-tabs" role="group" aria-label="장소 분류">
        <button type="button" :class="{ active: !state.content_type }" @click="setType('')">전체</button>
        <button v-for="type in LOCATION_TYPES" :key="type.id" type="button" :class="{ active: state.content_type === type.id }" @click="setType(type.id)">{{ type.name }}</button>
      </div>
    </section>
    <div class="result-meta"><strong>{{ data.total.toLocaleString('ko-KR') }}</strong>개의 장소<span v-if="state.search">· “{{ state.search }}” 검색 결과</span></div>
    <StatePanel v-if="loading" type="loading" title="서울의 장소를 찾고 있어요" />
    <StatePanel v-else-if="error" type="error" title="장소를 불러오지 못했어요" :message="error" @retry="load" />
    <StatePanel v-else-if="!data.items.length" title="조건에 맞는 장소가 없어요" message="검색어나 분류를 바꿔 다시 찾아보세요." />
    <div v-else class="location-grid"><LocationCard v-for="place in data.items" :key="place.id" :place="place" /></div>
    <PaginationBar v-if="data.total" :page="state.page" :total-pages="totalPages" :disabled="loading" @change="setPage" />
  </div>
</template>

<style scoped>
.search-area { margin-bottom: 22px; padding: 18px; }
.search-form { display: flex; align-items: center; gap: 10px; }
.search-form > svg { margin-left: 4px; color: var(--color-muted); }
.search-form input { min-width: 0; flex: 1; height: 44px; border: 0; outline: 0; }
.clear { display: grid; place-items: center; border: 0; color: var(--color-muted); background: transparent; }
.type-tabs { display: flex; gap: 7px; overflow-x: auto; margin-top: 15px; padding-top: 15px; border-top: 1px solid var(--color-line); scrollbar-width: none; }
.type-tabs button { min-height: 34px; flex: 0 0 auto; padding: 0 13px; border: 1px solid var(--color-line); border-radius: 999px; color: var(--color-muted); background: #fff; font-size: 13px; font-weight: 700; }
.type-tabs button.active { border-color: var(--color-primary); color: #fff; background: var(--color-primary); }
.result-meta { margin: 22px 2px 16px; color: var(--color-muted); font-size: 14px; }
.result-meta strong { color: var(--color-primary); font-size: 18px; }
.location-grid { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 18px; }
@media (max-width: 900px) { .location-grid { grid-template-columns: repeat(2,1fr); } }
@media (max-width: 600px) { .location-grid { grid-template-columns: 1fr; } .search-area { padding: 12px; } .search-form .button { padding-inline: 13px; } }
</style>
