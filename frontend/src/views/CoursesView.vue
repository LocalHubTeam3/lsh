<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ArrowUpRight, Eye, Map, Route } from 'lucide-vue-next'
import { getCourses } from '../api/courses'
import PaginationBar from '../components/common/PaginationBar.vue'
import StatePanel from '../components/common/StatePanel.vue'

const state = reactive({ sort: 'latest', page: 1, size: 12 })
const data = ref({ items: [], total: 0 })
const loading = ref(true)
const error = ref('')
const totalPages = computed(() => Math.max(1, Math.ceil(data.value.total / state.size)))
function formatDate(value) { return new Intl.DateTimeFormat('ko-KR', { dateStyle: 'medium' }).format(new Date(value)) }
async function load() { loading.value = true; error.value = ''; try { data.value = await getCourses(state) } catch (err) { error.value = err.message } finally { loading.value = false } }
function setSort(value) { state.sort = value; state.page = 1; load() }
function setPage(value) { state.page = value; load(); window.scrollTo({ top: 0, behavior: 'smooth' }) }
onMounted(load)
</script>

<template>
  <div class="page container">
    <header class="page-heading"><div><p class="eyebrow">LOCAL ROUTES</p><h1>여행 코스</h1><p>LocalHub 사용자들이 서울의 spot을 연결해 만든 여행 동선을 만나보세요.</p></div><RouterLink class="button primary" to="/map"><Map :size="18" />지도에서 코스 만들기</RouterLink></header>
    <div class="course-toolbar panel"><strong>{{ data.total.toLocaleString('ko-KR') }}개의 코스</strong><div><button type="button" :class="{ active: state.sort === 'latest' }" @click="setSort('latest')">최신순</button><button type="button" :class="{ active: state.sort === 'popular' }" @click="setSort('popular')">인기순</button></div></div>
    <StatePanel v-if="loading" type="loading" title="여행 코스를 불러오고 있어요" />
    <StatePanel v-else-if="error" type="error" title="코스를 불러오지 못했어요" :message="error" @retry="load" />
    <StatePanel v-else-if="!data.items.length" title="아직 저장된 코스가 없어요" message="지도에서 spot을 장바구니에 담아 첫 코스를 만들어보세요." />
    <section v-else class="course-grid"><RouterLink v-for="course in data.items" :key="course.id" class="course-card panel" :to="`/courses/${course.id}`"><div class="route-icon"><Route :size="24" /></div><span>{{ formatDate(course.created_at) }}</span><h2>{{ course.title }}</h2><p>{{ course.description }}</p><footer><small><Eye :size="14" />{{ course.views.toLocaleString('ko-KR') }}</small><strong>코스 보기 <ArrowUpRight :size="15" /></strong></footer></RouterLink></section>
    <PaginationBar v-if="data.total" :page="state.page" :total-pages="totalPages" :disabled="loading" @change="setPage" />
  </div>
</template>

<style scoped>
.course-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; padding: 13px 16px; }.course-toolbar strong { font-size: 13px; }.course-toolbar div { display: flex; gap: 4px; }.course-toolbar button { height: 34px; padding: 0 11px; border: 0; border-radius: 6px; color: var(--color-muted); background: transparent; font-size: 11px; font-weight: 700; }.course-toolbar button.active { color: var(--color-primary-dark); background: var(--color-primary-soft); }.course-grid { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 15px; }.course-card { display: grid; min-width: 0; padding: 21px; transition: transform .18s ease, box-shadow .18s ease; }.course-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-sm); }.route-icon { display: grid; width: 44px; height: 44px; place-items: center; margin-bottom: 15px; border-radius: 10px; color: var(--color-primary-dark); background: var(--color-primary-soft); }.course-card > span { color: var(--color-muted); font-size: 10px; }.course-card h2 { overflow: hidden; margin: 7px 0 8px; font-size: 19px; text-overflow: ellipsis; white-space: nowrap; }.course-card p { display: -webkit-box; min-height: 42px; overflow: hidden; color: var(--color-muted); font-size: 12px; line-height: 1.7; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }.course-card footer { display: flex; align-items: center; justify-content: space-between; margin-top: 18px; padding-top: 14px; border-top: 1px solid var(--color-line); }.course-card footer small, .course-card footer strong { display: flex; align-items: center; gap: 4px; }.course-card footer small { color: var(--color-muted); }.course-card footer strong { color: var(--color-primary); font-size: 11px; }
@media (max-width: 900px) { .course-grid { grid-template-columns: repeat(2,1fr); } } @media (max-width: 600px) { .course-grid { grid-template-columns: 1fr; } }
</style>
