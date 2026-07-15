<script setup>
import { ref } from 'vue'
import { ArrowUpRight, Map, MapPin } from 'lucide-vue-next'
import { locationType } from '../../constants/locations'

defineProps({ place: { type: Object, required: true } })
const imageFailed = ref(false)
</script>

<template>
  <article class="location-card panel">
    <RouterLink class="card-media" :to="`/locations/${place.id}`" :aria-label="`${place.title} 상세 보기`">
      <img v-if="place.image_url && !imageFailed" :src="place.image_url" :alt="`${place.title} 전경`" loading="lazy" referrerpolicy="no-referrer" @error="imageFailed = true" />
      <span v-else class="image-fallback"><MapPin :size="30" /><small>LOCALHUB</small></span>
      <span class="badge">{{ locationType(place.content_type_id).name }}</span>
    </RouterLink>
    <div class="card-content">
      <div>
        <h3><RouterLink :to="`/locations/${place.id}`">{{ place.title }}</RouterLink></h3>
        <p><MapPin :size="14" />{{ [place.address, place.address_detail].filter(Boolean).join(' ') || '주소 정보 없음' }}</p>
        <p class="description">{{ place.description || '원천 데이터에서 상세 설명을 제공하지 않습니다.' }}</p>
      </div>
      <div class="card-actions"><RouterLink class="detail-link" :to="`/locations/${place.id}`">자세히 <ArrowUpRight :size="16" /></RouterLink><RouterLink class="map-link" :to="{ path: '/map', query: { search: place.title } }"><Map :size="14" />지도</RouterLink></div>
    </div>
  </article>
</template>

<style scoped>
.location-card { min-width: 0; overflow: hidden; transition: transform .2s ease, box-shadow .2s ease; }
.location-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-sm); }
.card-media { position: relative; display: block; aspect-ratio: 16 / 10; overflow: hidden; background: #e6eeea; }
.card-media img { width: 100%; height: 100%; object-fit: cover; transition: transform .35s ease; }
.location-card:hover img { transform: scale(1.03); }
.card-media .badge { position: absolute; top: 12px; left: 12px; color: #fff; background: rgba(23,33,29,.78); backdrop-filter: blur(6px); }
.image-fallback { display: grid; width: 100%; height: 100%; place-items: center; align-content: center; gap: 9px; color: #6e8178; background: linear-gradient(135deg, #e4ede8, #f1f4f2); }
.image-fallback small { font-size: 10px; font-weight: 900; }
.card-content { display: flex; min-height: 142px; flex-direction: column; justify-content: space-between; padding: 18px; }
h3 { margin-bottom: 8px; overflow: hidden; font-size: 18px; text-overflow: ellipsis; white-space: nowrap; }
p { display: flex; align-items: flex-start; gap: 5px; margin-bottom: 0; color: var(--color-muted); font-size: 13px; line-height: 1.5; }
p svg { flex: 0 0 auto; margin-top: 2px; }
.description { display: -webkit-box; overflow: hidden; margin-top: 8px; font-size: 11px; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
.card-actions { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.detail-link { display: inline-flex; width: fit-content; align-items: center; gap: 4px; margin-top: 18px; color: var(--color-primary); font-size: 13px; font-weight: 800; }
.map-link { display: inline-flex; align-items: center; gap: 4px; margin-top: 18px; color: var(--color-muted); font-size: 12px; font-weight: 700; }
</style>
