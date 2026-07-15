<script setup>
import { onMounted, ref } from 'vue'
import { ArrowRight, Database, Map, MessageCircle, Search } from 'lucide-vue-next'
import { getLocations } from '../api/locations'
import LocationCard from '../components/location/LocationCard.vue'
import StatePanel from '../components/common/StatePanel.vue'

const places = ref([])
const total = ref(0)
const loading = ref(true)
const error = ref('')

async function loadFeatured() {
  loading.value = true
  error.value = ''
  try {
    const data = await getLocations({ page: 1, size: 4, content_type: '12' })
    places.value = data.items
    total.value = data.total
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}
onMounted(loadFeatured)
</script>

<template>
  <div>
    <section class="home-intro">
      <div class="container intro-grid">
        <div class="intro-copy">
          <p class="eyebrow">SEOUL LOCAL DISCOVERY</p>
          <h1>오늘의 서울을<br /><span>가까이 발견하세요.</span></h1>
          <p>관광지부터 문화시설, 축제와 쇼핑까지. 서울의 장소를 찾고 실시간 정보와 지역 이야기를 한곳에서 확인하세요.</p>
          <div class="intro-actions">
            <RouterLink class="button primary" to="/locations"><Search :size="18" />장소 탐색</RouterLink>
            <RouterLink class="button secondary" to="/map"><Map :size="18" />지도에서 보기</RouterLink>
          </div>
        </div>
        <div class="quick-panel panel">
          <div class="quick-head">
            <span class="live-dot"></span>
            <span>서울 여행 데이터</span>
            <strong>{{ total ? `${total.toLocaleString('ko-KR')}곳` : '연결 중' }}</strong>
          </div>
          <RouterLink to="/locations?type=15"><span><strong>지금 열리는 행사</strong><small>축제와 공연 찾아보기</small></span><ArrowRight :size="19" /></RouterLink>
          <RouterLink to="/map"><span><strong>내 주변 한눈에</strong><small>지도에서 장소 비교하기</small></span><ArrowRight :size="19" /></RouterLink>
          <RouterLink to="/community"><span><strong>서울 사람들의 이야기</strong><small>질문하고 경험 나누기</small></span><ArrowRight :size="19" /></RouterLink>
        </div>
      </div>
    </section>

    <section class="container featured-section">
      <div class="section-head">
        <div><p class="eyebrow">CURATED PLACES</p><h2>서울에서 시작하는 발견</h2></div>
        <RouterLink to="/locations">전체 장소 <ArrowRight :size="17" /></RouterLink>
      </div>
      <StatePanel v-if="loading" type="loading" title="장소를 불러오고 있어요" />
      <StatePanel v-else-if="error" type="error" title="장소를 불러오지 못했어요" :message="error" @retry="loadFeatured" />
      <div v-else class="location-grid"><LocationCard v-for="place in places" :key="place.id" :place="place" /></div>
    </section>

    <section class="service-band">
      <div class="container service-grid">
        <div><Database :size="24" /><strong>공공데이터 기반</strong><span>한국관광공사 TourAPI 데이터</span></div>
        <div><Map :size="24" /><strong>지도와 혼잡도</strong><span>위치와 실시간 현황 확인</span></div>
        <div><MessageCircle :size="24" /><strong>지역 커뮤니티</strong><span>익명으로 나누는 서울 이야기</span></div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-intro { padding: 68px 0 54px; border-bottom: 1px solid var(--color-line); background: #fff; }
.intro-grid { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(340px, .7fr); align-items: center; gap: 70px; }
.intro-copy h1 { max-width: 700px; margin-bottom: 22px; font-size: clamp(46px, 6vw, 74px); line-height: 1.05; letter-spacing: 0; }
.intro-copy h1 span { color: var(--color-primary); }
.intro-copy > p:not(.eyebrow) { max-width: 600px; color: var(--color-muted); font-size: 17px; line-height: 1.75; }
.intro-actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 28px; }
.quick-panel { padding: 10px 22px; box-shadow: var(--shadow-sm); }
.quick-head { display: flex; align-items: center; gap: 8px; min-height: 54px; border-bottom: 1px solid var(--color-line); color: var(--color-muted); font-size: 12px; }
.quick-head strong { margin-left: auto; color: var(--color-primary); }
.live-dot { width: 7px; height: 7px; border-radius: 50%; background: #24a77e; box-shadow: 0 0 0 4px #dff3ed; }
.quick-panel > a { display: flex; min-height: 82px; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--color-line); }
.quick-panel > a:last-child { border-bottom: 0; }
.quick-panel > a:hover svg { color: var(--color-primary); transform: translateX(3px); }
.quick-panel a span { display: grid; gap: 5px; }
.quick-panel a small { color: var(--color-muted); }
.featured-section { padding-block: 64px 76px; }
.section-head { display: flex; align-items: end; justify-content: space-between; margin-bottom: 24px; }
.section-head h2 { margin-bottom: 0; font-size: 30px; }
.section-head > a { display: flex; align-items: center; gap: 5px; color: var(--color-primary); font-size: 14px; font-weight: 800; }
.location-grid { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 16px; }
.service-band { padding: 32px 0; color: #fff; background: #18332c; }
.service-grid { display: grid; grid-template-columns: repeat(3, 1fr); }
.service-grid > div { display: grid; grid-template-columns: 40px 1fr; align-items: center; padding: 4px 28px; border-right: 1px solid rgba(255,255,255,.16); }
.service-grid > div:last-child { border: 0; }
.service-grid svg { grid-row: 1 / 3; color: #75d3b9; }
.service-grid span { color: #b7cac4; font-size: 12px; }
@media (max-width: 1000px) { .location-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 800px) { .intro-grid { grid-template-columns: 1fr; gap: 38px; } .home-intro { padding-top: 46px; } }
@media (max-width: 650px) {
  .intro-copy h1 { font-size: 43px; }
  .location-grid { grid-template-columns: 1fr; }
  .service-grid { grid-template-columns: 1fr; gap: 24px; }
  .service-grid > div { border-right: 0; padding-inline: 0; }
}
</style>
