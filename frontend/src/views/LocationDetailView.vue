<script setup>
import { onMounted, ref } from 'vue'
import { ArrowLeft, ArrowUpRight, ExternalLink, Eye, Gauge, MapPin, MessageSquareText } from 'lucide-vue-next'
import { useRoute } from 'vue-router'
import { getCrowd, getLocation } from '../api/locations'
import { getPosts } from '../api/posts'
import { locationType } from '../constants/locations'
import StatePanel from '../components/common/StatePanel.vue'

const route = useRoute()
const place = ref(null)
const crowd = ref(null)
const loading = ref(true)
const error = ref('')
const crowdError = ref('')
const imageFailed = ref(false)
const relatedPosts = ref([])

async function load() {
  loading.value = true; error.value = ''
  try {
    place.value = await getLocation(route.params.id)
    relatedPosts.value = (await getPosts({ location_id: route.params.id, page: 1, size: 4 })).items
    try { crowd.value = await getCrowd(route.params.id) } catch (err) { crowdError.value = err.message }
  } catch (err) { error.value = err.message }
  finally { loading.value = false }
}
onMounted(load)
</script>

<template>
  <div class="page container">
    <RouterLink class="back-link" to="/locations"><ArrowLeft :size="17" />목록으로</RouterLink>
    <StatePanel v-if="loading" type="loading" title="장소 정보를 불러오고 있어요" />
    <StatePanel v-else-if="error" type="error" title="장소를 찾지 못했어요" :message="error" @retry="load" />
    <article v-else-if="place" class="detail-layout">
      <div class="detail-media panel">
        <img v-if="place.image_url && !imageFailed" :src="place.image_url" :alt="`${place.title} 전경`" referrerpolicy="no-referrer" @error="imageFailed = true" />
        <div v-else class="fallback"><MapPin :size="42" /><span>이미지가 제공되지 않은 장소입니다.</span></div>
      </div>
      <div class="detail-info">
        <span class="badge">{{ locationType(place.content_type_id).name }}</span>
        <h1>{{ place.title }}</h1>
        <p class="address"><MapPin :size="18" />{{ [place.address, place.address_detail].filter(Boolean).join(' ') || '주소 정보 없음' }}</p>
        <section class="crowd-panel panel">
          <Gauge :size="23" />
          <div>
            <span>실시간 혼잡도</span>
            <strong v-if="crowd?.available">{{ crowd.congestion_level || '정보 없음' }}<small v-if="crowd.population_estimate">약 {{ crowd.population_estimate.toLocaleString('ko-KR') }}명</small></strong>
            <strong v-else class="unavailable">{{ crowdError || crowd?.notice || '이 장소의 실시간 혼잡도 정보가 없어요.' }}</strong>
          </div>
        </section>
        <dl class="place-meta panel">
          <div><dt>대분류</dt><dd>{{ place.category1 || '-' }}</dd></div>
          <div><dt>중분류</dt><dd>{{ place.category2 || '-' }}</dd></div>
          <div><dt>데이터 ID</dt><dd>{{ place.content_id }}</dd></div>
        </dl>
        <section class="description-panel panel"><h2>장소 소개</h2><p v-if="place.description">{{ place.description }}</p><p v-else class="empty-description">이 장소는 원천 데이터에서 상세 설명을 제공하지 않습니다.</p></section>
        <a v-if="place.latitude != null && place.longitude != null" class="button primary map-link" :href="`https://www.openstreetmap.org/?mlat=${place.latitude}&mlon=${place.longitude}#map=17/${place.latitude}/${place.longitude}`" target="_blank" rel="noreferrer">지도에서 위치 확인 <ExternalLink :size="17" /></a>
      </div>
    </article>
    <section v-if="place" class="related-section">
      <div class="related-head"><div><p class="eyebrow">LOCAL STORIES</p><h2>이 장소의 커뮤니티 이야기</h2></div><RouterLink :to="`/community?location_id=${place.id}&location=${encodeURIComponent(place.title)}`">전체 보기 <ArrowUpRight :size="16" /></RouterLink></div>
      <div v-if="relatedPosts.length" class="related-posts"><RouterLink v-for="item in relatedPosts" :key="item.id" class="panel" :to="`/community/${item.id}`"><span class="badge">{{ item.category }}</span><h3>{{ item.title }}</h3><p>{{ item.content }}</p><small><span>{{ item.nickname || '익명' }}</span><span><Eye :size="13" />{{ item.views }}</span></small></RouterLink></div>
      <div v-else class="no-posts panel"><MessageSquareText :size="25" /><div><strong>아직 연결된 이야기가 없어요.</strong><p>이 장소에 관한 첫 경험이나 질문을 남겨보세요.</p></div><RouterLink class="button secondary" :to="`/community/write?location_id=${place.id}&location=${encodeURIComponent(place.title)}`">글쓰기</RouterLink></div>
    </section>
  </div>
</template>

<style scoped>
.back-link { display: inline-flex; align-items: center; gap: 6px; margin-bottom: 22px; color: var(--color-muted); font-size: 14px; font-weight: 700; }
.detail-layout { display: grid; grid-template-columns: minmax(0,1.25fr) minmax(340px,.75fr); gap: 42px; align-items: start; }
.detail-media { overflow: hidden; aspect-ratio: 4 / 3; background: #e7eeea; }
.detail-media img { width: 100%; height: 100%; object-fit: cover; }
.fallback { display: grid; height: 100%; place-items: center; align-content: center; gap: 12px; color: var(--color-muted); }
.detail-info { padding-top: 8px; }
.detail-info h1 { margin: 15px 0 13px; font-size: clamp(34px,5vw,52px); line-height: 1.15; }
.address { display: flex; gap: 7px; color: var(--color-muted); line-height: 1.6; }
.address svg { flex: 0 0 auto; margin-top: 3px; color: var(--color-primary); }
.crowd-panel { display: flex; gap: 14px; margin-top: 28px; padding: 18px; }
.crowd-panel > svg { color: var(--color-primary); }
.crowd-panel div { display: grid; gap: 5px; }
.crowd-panel span { color: var(--color-muted); font-size: 12px; }
.crowd-panel strong { display: flex; align-items: center; gap: 12px; }
.crowd-panel small { color: var(--color-primary); }
.crowd-panel .unavailable { color: var(--color-muted); font-size: 13px; font-weight: 600; line-height: 1.5; }
.place-meta { margin: 12px 0 20px; padding: 8px 18px; }
.place-meta div { display: grid; grid-template-columns: 90px 1fr; padding: 12px 0; border-bottom: 1px solid var(--color-line); font-size: 13px; }
.place-meta div:last-child { border-bottom: 0; }
.place-meta dt { color: var(--color-muted); }.place-meta dd { margin: 0; font-weight: 700; }
.description-panel { margin-bottom: 12px; padding: 17px 18px; }.description-panel h2 { margin-bottom: 9px; font-size: 14px; }.description-panel p { margin: 0; color: var(--color-muted); font-size: 13px; line-height: 1.7; }.description-panel .empty-description { font-size: 11px; }
.map-link { width: 100%; }
.related-section { margin-top: 64px; }.related-head { display: flex; align-items: end; justify-content: space-between; margin-bottom: 18px; }.related-head h2 { margin: 0; }.related-head > a { display: flex; align-items: center; gap: 4px; color: var(--color-primary); font-size: 12px; font-weight: 800; }.related-posts { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 13px; }.related-posts > a { min-width: 0; padding: 19px; }.related-posts h3 { overflow: hidden; margin: 12px 0 7px; text-overflow: ellipsis; white-space: nowrap; }.related-posts p { overflow: hidden; color: var(--color-muted); font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }.related-posts small { display: flex; justify-content: space-between; color: var(--color-muted); }.related-posts small span:last-child { display: flex; align-items: center; gap: 3px; }.no-posts { display: flex; align-items: center; gap: 14px; padding: 22px; color: var(--color-muted); }.no-posts div { flex: 1; }.no-posts strong { color: var(--color-text); }.no-posts p { margin: 4px 0 0; font-size: 12px; }
@media (max-width: 850px) { .detail-layout { grid-template-columns: 1fr; gap: 26px; } }
@media (max-width: 600px) { .related-posts { grid-template-columns: 1fr; }.no-posts { align-items: flex-start; flex-wrap: wrap; }.no-posts .button { width: 100%; } }
</style>
