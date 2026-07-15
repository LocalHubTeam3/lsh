<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { CalendarDays, ChevronDown, ChevronLeft, CloudSun, GripVertical, Layers3, MapPin, Plus, Save, Search, ShoppingBasket, Sparkles, Trash2, X } from 'lucide-vue-next'
import L from 'leaflet'
import { getCrowd, getMapLocations, searchMapLocations } from '../api/locations'
import { createCourse } from '../api/courses'
import { getSeoulWeather } from '../api/weather'
import { getTravelBasketFeedback } from '../api/aiFeedback'
import WeatherMetric from '../components/weather/WeatherMetric.vue'
import { LOCATION_TYPES, locationType } from '../constants/locations'
import { useRoute } from 'vue-router'

const SEOUL_BOUNDS = L.latLngBounds([37.413, 126.734], [37.715, 127.269])
const route = useRoute()
const mapElement = ref(null)
const workspaceElement = ref(null)
const detailElement = ref(null)
const cartElement = ref(null)
const tripPlannerElement = ref(null)
const detailStyle = ref({})
const selectedTypes = ref(['12'])
const counts = ref({})
const query = ref('')
const searchResults = ref([])
const searchTotal = ref(0)
const selected = ref(null)
const crowd = ref(null)
const crowdMessage = ref('')
const message = ref('')
const mobileFilters = ref(false)
const cart = ref([])
const cartOpen = ref(false)
const cartActive = ref(false)
const cartNotice = ref('')
const saveOpen = ref(false)
const saving = ref(false)
const saveError = ref('')
const savedCourse = ref(null)
const aiFeedback = ref(null)
const aiFeedbackError = ref('')
const aiFeedbackLoading = ref(false)
const aiFeedbackCartKey = ref('')
const aiFeedbackStyle = ref({})
let aiFeedbackRequestId = 0
let cartResizeObserver
const courseForm = reactive({ title: '', description: '', password: '' })

function inputDate(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function localDate(value) {
  const [year, month, day] = value.split('-').map(Number)
  return new Date(year, month - 1, day)
}

function addDays(value, amount) {
  const result = localDate(value)
  result.setDate(result.getDate() + amount)
  return inputDate(result)
}

const initialDate = inputDate(new Date())
const tripStart = ref(initialDate)
const tripEnd = ref(addDays(initialDate, 2))
const selectedTravelDate = ref(initialDate)
const dateMessage = ref('')
const weatherItems = ref({})
const weatherLoading = ref(false)
const weatherError = ref('')
let weatherRequestId = 0
const maxTripEnd = computed(() => tripStart.value ? addDays(tripStart.value, 9) : '')
const travelDates = computed(() => {
  if (!tripStart.value || !tripEnd.value) return []
  const start = localDate(tripStart.value)
  const end = localDate(tripEnd.value)
  const result = []
  for (let date = new Date(start); date <= end && result.length < 10; date.setDate(date.getDate() + 1)) {
    result.push({
      value: inputDate(date),
      label: `${date.getMonth() + 1}월 ${date.getDate()}일`,
      weekday: new Intl.DateTimeFormat('ko-KR', { weekday: 'short' }).format(date),
    })
  }
  return result
})
const selectedDateLabel = computed(() => travelDates.value.find((item) => item.value === selectedTravelDate.value)?.label || '')
const selectedWeather = computed(() => weatherItems.value[selectedTravelDate.value] || null)
const feedbackWeather = computed(() => travelDates.value
  .map((date) => weatherItems.value[date.value])
  .filter(Boolean)
  .map((item) => ({
    date: item.date,
    forecast_type: item.forecast_type,
    condition: item.condition,
    temperature_min: item.temperature_min,
    temperature_max: item.temperature_max,
    precipitation_probability: item.precipitation_probability,
    humidity: item.humidity,
    wind_speed: item.wind_speed,
  })))
const aiFeedbackPanelOpen = computed(() => aiFeedbackLoading.value || Boolean(aiFeedback.value) || Boolean(aiFeedbackError.value))
const showAIFeedbackPanel = computed(() => cartOpen.value && aiFeedbackPanelOpen.value)

function updateAIFeedbackPosition() {
  if (!workspaceElement.value || !cartElement.value || window.innerWidth <= 800) {
    aiFeedbackStyle.value = {}
    return
  }
  const workspaceRect = workspaceElement.value.getBoundingClientRect()
  const cartRect = cartElement.value.getBoundingClientRect()
  const gap = 10
  const edge = 18
  const availableWidth = workspaceRect.right - cartRect.right - gap - edge
  aiFeedbackStyle.value = {
    left: `${Math.round(cartRect.right - workspaceRect.left + gap)}px`,
    top: `${Math.round(cartRect.top - workspaceRect.top)}px`,
    width: `${Math.max(120, Math.min(320, availableWidth))}px`,
    height: `${Math.round(cartRect.height)}px`,
  }
}

function displayNumber(value, suffix = '') {
  return value === null || value === undefined ? '-' : `${Math.round(Number(value))}${suffix}`
}

function weatherDateLabel(value) {
  const date = localDate(value)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

async function loadWeather() {
  if (!tripStart.value || !tripEnd.value) return
  const requestId = ++weatherRequestId
  weatherLoading.value = true
  weatherError.value = ''
  try {
    const response = await getSeoulWeather(tripStart.value, tripEnd.value)
    if (requestId !== weatherRequestId) return
    weatherItems.value = Object.fromEntries(response.items.map((item) => [item.date, item]))
  } catch (error) {
    if (requestId !== weatherRequestId) return
    weatherItems.value = {}
    weatherError.value = error.message
  } finally {
    if (requestId === weatherRequestId) weatherLoading.value = false
  }
}

function handleStartDate() {
  dateMessage.value = ''
  if (!tripStart.value) return
  if (!tripEnd.value || tripEnd.value < tripStart.value) tripEnd.value = tripStart.value
  if (tripEnd.value > maxTripEnd.value) { tripEnd.value = maxTripEnd.value; dateMessage.value = '여행 기간은 최대 10일까지 선택할 수 있어요.' }
  selectedTravelDate.value = tripStart.value
  loadWeather()
}

function handleEndDate() {
  dateMessage.value = ''
  if (!tripEnd.value || tripEnd.value < tripStart.value) tripEnd.value = tripStart.value
  if (tripEnd.value > maxTripEnd.value) { tripEnd.value = maxTripEnd.value; dateMessage.value = '여행 기간은 최대 10일까지 선택할 수 있어요.' }
  if (!travelDates.value.some((item) => item.value === selectedTravelDate.value)) selectedTravelDate.value = tripStart.value
  loadWeather()
}
let draggedCartIndex = null
let placeDropped = false
let map
let renderer
let searchLayer
let cartRouteLayer
const layers = new Map()
const cache = new Map()

function updateDetailPosition() {
  if (!map || !selected.value || !detailElement.value) return
  const size = map.getSize()
  if (size.x <= 800) { detailStyle.value = {}; return }
  const point = map.latLngToContainerPoint([selected.value.latitude, selected.value.longitude])
  const width = detailElement.value.offsetWidth || 480
  const height = detailElement.value.offsetHeight || 280
  const gap = 18
  const edge = 20
  const topEdge = (tripPlannerElement.value?.offsetHeight || 0) + 38
  let left = point.x + gap
  let top = point.y - height - gap
  if (left + width > size.x - edge) left = point.x - width - gap
  left = Math.max(edge, Math.min(left, size.x - width - edge))
  top = Math.max(topEdge, Math.min(top, size.y - height - edge))
  detailStyle.value = { left: `${Math.round(left)}px`, top: `${Math.round(top)}px` }
}

function updateCartRoute() {
  if (!map || !cartRouteLayer) return
  cartRouteLayer.clearLayers()
  const places = cart.value.filter((place) => Number.isFinite(Number(place.latitude)) && Number.isFinite(Number(place.longitude)))
  const points = places.map((place) => [Number(place.latitude), Number(place.longitude)])
  if (points.length >= 2) {
    L.polyline(points, { color: '#ffffff', weight: 8, opacity: .92, lineCap: 'round', lineJoin: 'round', interactive: false }).addTo(cartRouteLayer)
    L.polyline(points, { color: '#087f68', weight: 4, opacity: .95, dashArray: '9 7', lineCap: 'round', lineJoin: 'round', interactive: false }).addTo(cartRouteLayer)
  }
  places.forEach((place) => {
    const order = cart.value.findIndex((item) => item.id === place.id) + 1
    const type = locationType(place.content_type_id)
    L.marker([Number(place.latitude), Number(place.longitude)], {
      icon: L.divIcon({ className: 'course-order-marker', html: `<span style="--marker-color:${type.color}">${order}</span>`, iconSize: [32, 32], iconAnchor: [16, 16] }),
      keyboard: true,
      title: `${order}. ${place.title} · ${type.name}`,
      zIndexOffset: 1200,
    }).on('click', () => selectPlace(place)).addTo(cartRouteLayer)
  })
}

async function focusCartRoute() {
  if (!map || !cart.value.length) return
  await nextTick()
  const points = cart.value
    .filter((place) => Number.isFinite(Number(place.latitude)) && Number.isFinite(Number(place.longitude)))
    .map((place) => [Number(place.latitude), Number(place.longitude)])
  if (!points.length) return
  const size = map.getSize()
  const cartHeight = cartElement.value?.offsetHeight || 220
  const leftPadding = size.x > 800 ? 350 : 24
  const bottomPadding = Math.min(cartHeight + 34, Math.round(size.y * .55))
  const plannerHeight = tripPlannerElement.value?.offsetHeight || 150
  const options = {
    paddingTopLeft: [leftPadding, plannerHeight + 38],
    paddingBottomRight: [24, bottomPadding],
    maxZoom: 15,
    animate: true,
    duration: .55,
  }
  map.fitBounds(L.latLngBounds(points), options)
}

function openCart() {
  if (!cart.value.length) return
  cartOpen.value = true
  focusCartRoute()
}

function toggleCart() {
  if (cartOpen.value) cartOpen.value = false
  else openCart()
}

try {
  const storedCart = JSON.parse(localStorage.getItem('localhub-course-cart') || '[]')
  if (Array.isArray(storedCart)) cart.value = storedCart.filter((place) => place?.id && place?.title)
} catch { localStorage.removeItem('localhub-course-cart') }

watch(cart, (items) => {
  localStorage.setItem('localhub-course-cart', JSON.stringify(items))
  if (!items.length && !cartActive.value) cartOpen.value = false
  const currentKey = items.map((item) => item.id).join(',')
  if (aiFeedbackCartKey.value && aiFeedbackCartKey.value !== currentKey) {
    aiFeedback.value = null
    aiFeedbackError.value = ''
    aiFeedbackCartKey.value = ''
    aiFeedbackRequestId += 1
    aiFeedbackLoading.value = false
  }
  updateCartRoute()
}, { deep: true })
watch(selected, (value, previous) => {
  if (previous && !value && cart.value.length) openCart()
})
watch(showAIFeedbackPanel, async (visible) => {
  if (!visible) return
  await nextTick()
  updateAIFeedbackPosition()
  window.setTimeout(updateAIFeedbackPosition, 320)
})
watch(cartOpen, (open) => {
  if (open && aiFeedbackPanelOpen.value) window.setTimeout(updateAIFeedbackPosition, 320)
})

function beginPlaceDrag(event, place) {
  event.stopPropagation()
  event.dataTransfer.effectAllowed = 'copy'
  event.dataTransfer.setData('application/x-localhub-place', JSON.stringify(place))
  event.dataTransfer.setData('text/plain', place.title)
  placeDropped = false
  cartActive.value = true
}

function endPlaceDrag() {
  cartActive.value = false
  if (!placeDropped) cartOpen.value = false
}

function handleWorkspaceDragOver(event) {
  const types = Array.from(event.dataTransfer?.types || [])
  if (!types.includes('application/x-localhub-place')) return
  const bounds = event.currentTarget.getBoundingClientRect()
  if (bounds.bottom - event.clientY <= 180) cartOpen.value = true
}

function addSpot(place) {
  if (cart.value.some((item) => item.id === place.id)) {
    cartNotice.value = `${place.title}은(는) 이미 담겨 있어요.`
    return
  }
  cart.value.push(place)
  cartNotice.value = `${place.title}을(를) 여행 장바구니에 담았어요.`
}

function dropOnCart(event) {
  placeDropped = true
  cartActive.value = false
  const raw = event.dataTransfer.getData('application/x-localhub-place')
  if (!raw) return
  try {
    addSpot(JSON.parse(raw))
    selected.value = null
    cartOpen.value = true
    focusCartRoute()
  } catch { cartNotice.value = '장소를 담지 못했어요.' }
}

function removeSpot(index) { cart.value.splice(index, 1); savedCourse.value = null; if (!cart.value.length) cartOpen.value = false }
function clearCart() { cart.value = []; cartOpen.value = false; saveOpen.value = false; cartNotice.value = ''; savedCourse.value = null }

function handleMapBackgroundClick(event) {
  if (event.sourceTarget === map) cartOpen.value = false
}

function beginCartDrag(event, index) {
  draggedCartIndex = index
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('application/x-localhub-cart', String(index))
}

function reorderCart(targetIndex) {
  if (draggedCartIndex == null || draggedCartIndex === targetIndex) return
  const [item] = cart.value.splice(draggedCartIndex, 1)
  cart.value.splice(targetIndex, 0, item)
  draggedCartIndex = targetIndex
}

function endCartDrag() { draggedCartIndex = null }

async function requestAIFeedback() {
  if (cart.value.length < 2) return
  const cartKey = cart.value.map((item) => item.id).join(',')
  const requestId = ++aiFeedbackRequestId
  aiFeedbackLoading.value = true
  aiFeedbackError.value = ''
  try {
    const result = await getTravelBasketFeedback(cart.value.map((item) => item.id), feedbackWeather.value)
    if (requestId !== aiFeedbackRequestId || cartKey !== cart.value.map((item) => item.id).join(',')) return
    aiFeedback.value = result
    aiFeedbackCartKey.value = cartKey
  } catch (error) {
    if (requestId === aiFeedbackRequestId) aiFeedbackError.value = error.message
  } finally {
    if (requestId === aiFeedbackRequestId) aiFeedbackLoading.value = false
  }
}

function applyRecommendedRoute() {
  if (!aiFeedback.value) return
  const byId = new Map(cart.value.map((item) => [item.id, item]))
  const reordered = aiFeedback.value.recommended_route.location_ids.map((id) => byId.get(id))
  if (reordered.some((item) => !item)) return
  cart.value = reordered
  aiFeedback.value = null
  aiFeedbackCartKey.value = ''
  cartNotice.value = 'AI가 제안한 방문 순서를 장바구니에 적용했어요.'
  focusCartRoute()
}

async function saveCourse() {
  saveError.value = ''
  savedCourse.value = null
  if (cart.value.length < 2) { saveError.value = '코스에는 장소가 2곳 이상 필요합니다.'; return }
  saving.value = true
  try {
    savedCourse.value = await createCourse({
      title: courseForm.title.trim(),
      description: courseForm.description.trim(),
      password: courseForm.password,
      location_ids: cart.value.map((place) => place.id),
    })
    cartNotice.value = `“${savedCourse.value.title}” 코스를 저장했어요.`
    courseForm.title = ''; courseForm.description = ''; courseForm.password = ''
    saveOpen.value = false
  } catch (err) { saveError.value = err.message }
  finally { saving.value = false }
}

function markerFor(place, type, radius = 5) {
  const highlighted = radius > 5
  const size = highlighted ? 42 : 34
  const height = highlighted ? 50 : 42
  const icon = L.divIcon({
    className: `spot-map-marker${highlighted ? ' highlighted' : ''}`,
    html: `<span class="spot-pin" style="--marker-color:${type.color}" aria-hidden="true"><i></i></span>`,
    iconSize: [size, height],
    iconAnchor: [size / 2, height - 2],
  })

  return L.marker([place.latitude, place.longitude], {
    icon,
    keyboard: true,
    title: `${place.title} · ${type.name}`,
    riseOnHover: true,
  }).on('click', () => selectPlace(place))
}

async function toggleType(type) {
  const enabled = selectedTypes.value.includes(type.id)
  if (!enabled) {
    if (layers.has(type.id)) map.removeLayer(layers.get(type.id))
    return
  }
  message.value = `${type.name} 장소를 불러오고 있어요.`
  try {
    if (!cache.has(type.id)) cache.set(type.id, await getMapLocations(type.id))
    if (!layers.has(type.id)) {
      const group = L.layerGroup(cache.get(type.id).items.map((place) => markerFor(place, type)))
      layers.set(type.id, group)
    }
    layers.get(type.id).addTo(map)
    counts.value[type.id] = cache.get(type.id).total
    message.value = ''
  } catch (err) { message.value = err.message }
}

async function handleType(type) {
  const index = selectedTypes.value.indexOf(type.id)
  if (index >= 0) selectedTypes.value.splice(index, 1)
  else selectedTypes.value.push(type.id)
  await toggleType(type)
}

async function selectPlace(place) {
  cartOpen.value = false
  selected.value = place
  await nextTick()
  updateDetailPosition()
  crowd.value = null
  crowdMessage.value = '혼잡도를 확인하고 있어요.'
  map.flyTo([place.latitude, place.longitude], Math.max(map.getZoom(), 15), { duration: .6 })
  try {
    const result = await getCrowd(place.id)
    if (selected.value?.id !== place.id) return
    crowd.value = result
    crowdMessage.value = result.available ? '' : (result.notice || '실시간 혼잡도 정보가 없어요.')
  } catch (err) { if (selected.value?.id === place.id) crowdMessage.value = err.message }
  await nextTick()
  updateDetailPosition()
}

async function search() {
  const keyword = query.value.trim()
  searchLayer.clearLayers()
  if (!keyword) { searchResults.value = []; searchTotal.value = 0; return }
  message.value = '장소를 검색하고 있어요.'
  try {
    const data = await searchMapLocations(keyword)
    searchResults.value = data.items
    searchTotal.value = data.total
    data.items.forEach((place) => markerFor(place, locationType(place.content_type_id), 8).addTo(searchLayer))
    if (data.items.length === 1) selectPlace(data.items[0])
    else if (data.items.length > 1) map.fitBounds(data.items.map((place) => [place.latitude, place.longitude]), { padding: [60, 60], maxZoom: 15 })
    message.value = ''
  } catch (err) { message.value = err.message }
}

function clearSearch() { query.value = ''; searchResults.value = []; searchTotal.value = 0; searchLayer.clearLayers() }

onMounted(async () => {
  loadWeather()
  await nextTick()
  cartResizeObserver = new ResizeObserver(updateAIFeedbackPosition)
  if (cartElement.value) cartResizeObserver.observe(cartElement.value)
  window.addEventListener('resize', updateAIFeedbackPosition)
  map = L.map(mapElement.value, {
    preferCanvas: true,
    zoomControl: false,
    minZoom: 10,
    zoomSnap: .5,
    maxBounds: SEOUL_BOUNDS.pad(.15),
    maxBoundsViscosity: .8,
  })
  L.control.zoom({ position: 'bottomright' }).addTo(map)
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; OpenStreetMap contributors' }).addTo(map)
  const plannerPadding = (tripPlannerElement.value?.offsetHeight || 150) + 38
  const desktopPadding = mapElement.value.clientWidth > 800 ? [350, plannerPadding] : [24, plannerPadding]
  map.fitBounds(SEOUL_BOUNDS, { paddingTopLeft: desktopPadding, paddingBottomRight: [24, 24], maxZoom: 12 })
  renderer = L.canvas({ padding: .5 })
  searchLayer = L.layerGroup().addTo(map)
  cartRouteLayer = L.layerGroup().addTo(map)
  updateCartRoute()
  map.on('move zoom resize', updateDetailPosition)
  map.on('click', handleMapBackgroundClick)
  await toggleType(LOCATION_TYPES[0])
  if (route.query.search) { query.value = String(route.query.search); await search() }
})
onBeforeUnmount(() => {
  cartResizeObserver?.disconnect()
  window.removeEventListener('resize', updateAIFeedbackPosition)
  map?.remove()
})
</script>

<template>
  <div ref="workspaceElement" class="map-workspace" @dragover.prevent="handleWorkspaceDragOver">
    <div ref="mapElement" class="map-canvas" aria-label="서울 장소 지도"></div>
    <button class="mobile-filter-button icon-button" type="button" title="분류 필터" @click="mobileFilters = !mobileFilters"><Layers3 :size="19" /></button>
    <section ref="tripPlannerElement" class="trip-planner panel" aria-label="여행 날짜와 날씨">
      <div class="trip-controls">
        <div class="trip-title"><span><CalendarDays :size="20" /></span><div><strong>여행 날짜</strong><small>최대 10일까지 선택할 수 있어요</small></div></div>
        <div class="date-range"><label>시작일<input v-model="tripStart" type="date" @change="handleStartDate" /></label><i>~</i><label>종료일<input v-model="tripEnd" type="date" :min="tripStart" :max="maxTripEnd" @change="handleEndDate" /></label></div>
        <div class="date-tabs" role="tablist" aria-label="날짜별 날씨"><button v-for="date in travelDates" :key="date.value" type="button" role="tab" :aria-selected="selectedTravelDate === date.value" :class="{ active: selectedTravelDate === date.value }" @click="selectedTravelDate = date.value"><strong>{{ date.label }}</strong><small>{{ date.weekday }}요일</small></button></div>
      </div>
      <p v-if="dateMessage" class="date-message">{{ dateMessage }}</p>
      <div class="trip-weather">
        <div class="weather-card" :class="{ error: weatherError }" aria-live="polite">
          <CloudSun :size="25" />
          <div class="weather-summary">
            <small>{{ selectedDateLabel }} · 서울<span v-if="selectedWeather"> · {{ selectedWeather.forecast_type === 'mid' ? '중기예보' : '단기예보' }}</span></small>
            <strong v-if="weatherLoading">날씨를 불러오는 중...</strong>
            <strong v-else-if="weatherError">날씨를 불러오지 못했어요</strong>
            <strong v-else-if="!selectedWeather">선택한 날짜의 예보가 아직 없어요</strong>
            <strong v-else>{{ selectedWeather.condition }}</strong>
          </div>
          <div v-if="selectedWeather && !weatherLoading" class="weather-metrics">
            <WeatherMetric label="기온" :value="`${displayNumber(selectedWeather.temperature_min, '°')} / ${displayNumber(selectedWeather.temperature_max, '°')}`" />
            <WeatherMetric label="강수" :value="displayNumber(selectedWeather.precipitation_probability, '%')" />
            <WeatherMetric label="습도" :value="displayNumber(selectedWeather.humidity, '%')" />
            <WeatherMetric label="바람" :value="selectedWeather.wind_speed == null ? '-' : `${Number(selectedWeather.wind_speed).toFixed(1)}m/s`" />
          </div>
          <button v-if="weatherError" type="button" @click="loadWeather">다시 시도</button>
        </div>
        <p v-if="weatherError" class="weather-error" role="alert">{{ weatherError }}</p>
      </div>
    </section>
    <aside :class="['map-sidebar', { mobileOpen: mobileFilters }]">
      <div class="sidebar-content">
      <div class="sidebar-title"><div><span class="eyebrow">SEOUL MAP</span><strong>장소 지도</strong></div><button class="mobile-close" type="button" aria-label="필터 닫기" @click="mobileFilters = false"><X :size="20" /></button></div>
      <form class="map-search" @submit.prevent="search">
        <Search :size="18" /><input v-model="query" maxlength="100" placeholder="장소명 검색" aria-label="지도 장소 검색" />
        <button v-if="query" type="button" aria-label="검색 지우기" @click="clearSearch"><X :size="16" /></button>
      </form>
      <div v-if="searchResults.length || (query && searchTotal === 0 && !message)" class="search-results">
        <p>{{ searchTotal ? `총 ${searchTotal.toLocaleString('ko-KR')}개 장소` : '검색 결과가 없어요' }}</p>
        <button v-for="place in searchResults" :key="place.id" type="button" draggable="true" title="클릭하면 상세 보기, 드래그하면 장바구니에 담기" @click="selectPlace(place)" @dragstart="beginPlaceDrag($event, place)" @dragend="endPlaceDrag">
          <span class="result-grip"><GripVertical :size="16" /></span><span class="result-copy"><strong>{{ place.title }}</strong><small>{{ locationType(place.content_type_id).name }} · {{ place.address || '주소 없음' }}</small></span>
        </button>
      </div>
      <div class="category-head"><strong>장소 분류</strong><span>{{ selectedTypes.length }}개 선택</span></div>
      <div class="category-list">
        <label v-for="type in LOCATION_TYPES" :key="type.id">
          <input type="checkbox" :checked="selectedTypes.includes(type.id)" @change="handleType(type)" />
          <i :style="{ background: type.color }"></i><span>{{ type.name }}</span><small>{{ counts[type.id] != null ? `${counts[type.id].toLocaleString('ko-KR')}곳` : '' }}</small>
        </label>
      </div>
      <p v-if="message" class="map-message">{{ message }}</p>
      <div class="interaction-guide"><span><i class="click-mark"></i><strong>마커 클릭</strong> 상세보기</span><span><GripVertical :size="14" /><strong>spot 드래그</strong> 장바구니 담기</span></div>
      <RouterLink class="back-list" to="/locations"><ChevronLeft :size="16" />목록으로 보기</RouterLink>
      </div>
    </aside>

    <div v-if="cartActive && !cartOpen" class="bottom-drop-trigger"><ShoppingBasket :size="20" /><strong>화면 아래로 가져오세요</strong><span>여행 장바구니가 열립니다</span></div>
    <button v-if="!cartOpen && cart.length && !selected" class="cart-peek" type="button" @click="openCart"><ShoppingBasket :size="18" /><span>여행 장바구니</span><b>{{ cart.length }}</b></button>

    <section ref="cartElement" :class="['course-cart', { active: cartActive, visible: cartOpen }]" @dragover.prevent="cartActive = true" @dragleave.self="cartActive = false" @drop.prevent="dropOnCart">
      <button class="cart-header" type="button" :aria-expanded="cartOpen" @click="toggleCart">
        <span class="cart-icon"><ShoppingBasket :size="19" /><b v-if="cart.length">{{ cart.length }}</b></span>
        <span><strong>여행 장바구니</strong><small>spot을 끌어 나만의 코스를 만드세요</small></span>
        <ChevronDown :class="{ rotated: cartOpen }" :size="19" />
      </button>
      <div v-if="cartOpen" class="cart-body">
        <div v-if="!cart.length" class="empty-cart"><ShoppingBasket :size="28" /><strong>아직 담은 spot이 없어요</strong><span>검색 결과나 상세 카드의 <GripVertical :size="13" /> 핸들을<br />이곳으로 드래그해 주세요.</span></div>
        <template v-else>
          <p class="route-label">방문 순서 <span>드래그해 순서를 바꿀 수 있어요</span></p>
          <ol class="cart-list">
            <li v-for="(place, index) in cart" :key="place.id" draggable="true" @dragstart="beginCartDrag($event, index)" @dragover.prevent="reorderCart(index)" @dragend="endCartDrag">
              <GripVertical class="cart-grip" :size="17" /><b>{{ index + 1 }}</b><button class="cart-place" type="button" @click="selectPlace(place)"><strong>{{ place.title }}</strong><small>{{ place.address || locationType(place.content_type_id).name }}</small></button><button class="remove-spot" type="button" :aria-label="`${place.title} 빼기`" @click="removeSpot(index)"><X :size="15" /></button>
            </li>
          </ol>
          <p v-if="cartNotice" class="cart-notice" role="status">{{ cartNotice }} <RouterLink v-if="savedCourse" :to="`/courses/${savedCourse.id}`">저장한 코스 보기</RouterLink></p>
          <div class="cart-actions">
            <button class="button ghost" type="button" @click="clearCart"><Trash2 :size="15" />비우기</button>
            <div class="cart-action-group">
              <button class="button ai-button" type="button" :disabled="cart.length < 2 || aiFeedbackLoading" @click="requestAIFeedback"><Sparkles :size="15" />{{ aiFeedbackLoading ? '분석 중...' : 'AI 피드백' }}</button>
              <button class="button primary" type="button" :disabled="cart.length < 2" @click="saveOpen = !saveOpen"><Save :size="15" />코스로 저장</button>
            </div>
          </div>
          <form v-if="saveOpen" class="course-form" @submit.prevent="saveCourse">
            <div class="field"><label for="course-title">코스 이름</label><input id="course-title" v-model="courseForm.title" class="input" maxlength="200" required placeholder="예: 성수동 하루 코스" /></div>
            <div class="field"><label for="course-description">코스 설명</label><textarea id="course-description" v-model="courseForm.description" class="textarea" maxlength="10000" required placeholder="코스를 간단히 소개해 주세요."></textarea></div>
            <div class="field"><label for="course-password">관리 비밀번호</label><input id="course-password" v-model="courseForm.password" class="input" type="password" maxlength="100" required autocomplete="new-password" /></div>
            <p v-if="saveError" class="save-error" role="alert">{{ saveError }}</p>
            <button class="button primary" type="submit" :disabled="saving">{{ saving ? '저장 중...' : '이 순서로 저장' }}</button>
          </form>
        </template>
      </div>
    </section>

    <aside v-if="showAIFeedbackPanel" class="ai-feedback-panel" :style="aiFeedbackStyle" aria-live="polite">
      <div class="ai-feedback-title"><span><Sparkles :size="16" /></span><strong>AI 여행 피드백</strong><button type="button" aria-label="AI 피드백 닫기" @click="aiFeedback = null; aiFeedbackError = ''; aiFeedbackRequestId += 1; aiFeedbackLoading = false"><X :size="15" /></button></div>
      <div v-if="feedbackWeather.length" class="ai-weather-context">
        <span v-for="weather in feedbackWeather" :key="weather.date"><b>{{ weatherDateLabel(weather.date) }}</b><small>{{ weather.condition }}</small><strong>{{ displayNumber(weather.temperature_min, '°') }}~{{ displayNumber(weather.temperature_max, '°') }}</strong><em>강수 {{ displayNumber(weather.precipitation_probability, '%') }}</em></span>
      </div>
      <p v-if="aiFeedbackLoading" class="ai-feedback-loading"><Sparkles :size="17" />동선과 날씨를 함께 분석하고 있어요...</p>
      <p v-else-if="aiFeedbackError" class="ai-feedback-error" role="alert">{{ aiFeedbackError }}</p>
      <template v-else-if="aiFeedback">
        <div class="route-comparison">
          <span><small>현재 직선거리</small><strong>{{ aiFeedback.current_route.total_distance_km.toFixed(2) }}km</strong></span>
          <i>→</i>
          <span><small>추천 직선거리</small><strong>{{ aiFeedback.recommended_route.total_distance_km.toFixed(2) }}km</strong></span>
          <b v-if="aiFeedback.distance_saved_km > 0">{{ aiFeedback.distance_saved_km.toFixed(2) }}km 절약</b>
        </div>
        <p class="ai-feedback-copy">{{ aiFeedback.feedback }}</p>
        <div class="route-legs"><span v-for="(leg, index) in aiFeedback.current_route.legs" :key="`${leg.from_id}-${leg.to_id}`"><b>{{ index + 1 }}→{{ index + 2 }}</b>{{ leg.distance_km.toFixed(2) }}km</span></div>
        <div class="recommended-order"><small>추천 순서</small><ol><li v-for="referenceId in aiFeedback.recommended_route.location_ids" :key="referenceId">{{ aiFeedback.references.find((item) => item.id === referenceId)?.title }}</li></ol></div>
        <button v-if="aiFeedback.recommended_route.location_ids.join(',') !== cart.map((item) => item.id).join(',')" class="button ai-apply" type="button" @click="applyRecommendedRoute">추천 순서 적용</button>
        <small class="distance-notice">장소 좌표 사이의 직선거리 기준이며 실제 도로 거리와 이동시간은 다를 수 있어요.</small>
      </template>
    </aside>

    <aside v-if="selected" ref="detailElement" class="detail-sheet" :style="detailStyle" draggable="true" title="팝업 전체를 여행 장바구니로 드래그할 수 있습니다" @dragstart="beginPlaceDrag($event, selected)" @dragend="endPlaceDrag">
      <button class="sheet-close icon-button" type="button" title="상세 닫기" @click="selected = null"><X :size="18" /></button>
      <div class="popup-drag-guide"><GripVertical :size="15" />팝업을 장바구니로 드래그</div>
      <div class="sheet-image">
        <img v-if="selected.image_url" :src="selected.image_url" :alt="selected.title" referrerpolicy="no-referrer" />
        <MapPin v-else :size="30" />
      </div>
      <div class="sheet-copy">
        <span class="badge">{{ locationType(selected.content_type_id).name }}</span>
        <h2>{{ selected.title }}</h2>
        <p><MapPin :size="15" />{{ selected.address || '주소 정보 없음' }}</p>
        <div :class="['crowd', { active: crowd?.available }]">
          <span>실시간 혼잡도</span>
          <strong v-if="crowd?.available">{{ crowd.congestion_level }} <small v-if="crowd.population_estimate">· 약 {{ crowd.population_estimate.toLocaleString('ko-KR') }}명</small></strong>
          <strong v-else>{{ crowdMessage }}</strong>
        </div>
        <div class="sheet-actions"><RouterLink class="button primary" :to="`/locations/${selected.id}`">상세 정보 보기</RouterLink><button class="button secondary add-mobile" type="button" @click="addSpot(selected); selected = null"><Plus :size="16" />장바구니 담기</button></div>
        <div class="drag-spot"><GripVertical :size="17" /><span><strong>팝업 전체를 아래로 드래그하세요</strong><small>화면 하단에서 여행 장바구니가 올라옵니다</small></span></div>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.map-workspace { position: relative; height: calc(100vh - var(--header-height)); min-height: 600px; overflow: hidden; }
.map-canvas { width: 100%; height: 100%; background: #dfe7e3; }
:deep(.course-order-marker) { border: 0; background: transparent; }
:deep(.course-order-marker span) { display: grid; width: 32px; height: 32px; place-items: center; border: 3px solid #fff; border-radius: 50%; color: #fff; background: var(--marker-color, var(--color-primary)); box-shadow: 0 4px 12px rgba(6,99,81,.38); font-size: 12px; font-weight: 900; }
:deep(.spot-map-marker) { border: 0; background: transparent; filter: drop-shadow(0 4px 5px rgba(20,43,35,.28)); }
:deep(.spot-map-marker .spot-pin) { position: absolute; top: 2px; left: 50%; display: grid; width: 26px; height: 26px; place-items: center; border: 3px solid #fff; border-radius: 50% 50% 50% 8px; background: var(--marker-color); transform: translateX(-50%) rotate(-45deg); transition: transform .16s ease, filter .16s ease; }
:deep(.spot-map-marker .spot-pin i) { display: block; width: 8px; height: 8px; border: 2px solid rgba(255,255,255,.92); border-radius: 50%; background: rgba(255,255,255,.28); }
:deep(.spot-map-marker.highlighted .spot-pin) { width: 32px; height: 32px; border-width: 4px; }
:deep(.spot-map-marker.highlighted .spot-pin i) { width: 10px; height: 10px; background: #fff; }
:deep(.spot-map-marker:hover .spot-pin), :deep(.spot-map-marker:focus .spot-pin), :deep(.spot-map-marker:focus-within .spot-pin) { filter: brightness(1.08) saturate(1.08); transform: translateX(-50%) translateY(-4px) rotate(-45deg) scale(1.08); }
.trip-planner { position: absolute; z-index: 480; top: 20px; left: 360px; width: min(50vw, 760px, calc(100% - 380px)); overflow: hidden; padding: 8px 10px; background: rgba(255,255,255,.97); box-shadow: var(--shadow-lg); backdrop-filter: blur(12px); }.trip-controls { display: flex; align-items: center; gap: 8px; }.trip-title { display: flex; flex: 0 0 auto; align-items: center; gap: 6px; }.trip-title > span { display: grid; width: 30px; height: 30px; place-items: center; border-radius: 7px; color: var(--color-primary-dark); background: var(--color-primary-soft); }.trip-title > div { display: grid; gap: 1px; }.trip-title strong { font-size: 14px; }.trip-title small { display: none; }.date-range { display: flex; flex: 0 0 auto; align-items: end; gap: 4px; }.date-range label { display: grid; gap: 1px; color: var(--color-muted); font-size: 10px; font-weight: 700; }.date-range input { width: 112px; height: 31px; padding: 0 5px; border: 1px solid var(--color-line); border-radius: 5px; color: var(--color-text); background: #fff; font-size: 11px; }.date-range i { padding-bottom: 8px; color: var(--color-muted); font-size: 12px; font-style: normal; }.date-message { margin: 4px 0 0; color: var(--color-warning); font-size: 10px; text-align: right; }.date-tabs { display: flex; min-width: 190px; max-width: 310px; flex: 1; gap: 3px; overflow-x: auto; scrollbar-width: thin; }.date-tabs button { display: grid; min-height: 34px; flex: 0 0 76px; place-items: center; align-content: center; gap: 1px; padding: 2px; border: 1px solid var(--color-line); border-radius: 5px; color: var(--color-muted); background: #fff; }.date-tabs button strong { font-size: 11px; }.date-tabs button small { font-size: 9px; }.date-tabs button.active { border-color: var(--color-primary); color: #fff; background: var(--color-primary); box-shadow: 0 3px 8px rgba(8,127,104,.16); }.trip-weather { margin-top: 6px; padding-top: 6px; border-top: 1px solid var(--color-line); }.weather-card { display: flex; width: 100%; min-width: 0; min-height: 52px; align-items: center; gap: 12px; padding: 7px 10px; border-radius: 5px; color: var(--color-primary-dark); background: var(--color-primary-soft); }.weather-card > svg { width: 22px; height: 22px; flex: 0 0 auto; }.weather-summary { display: grid; min-width: 120px; gap: 2px; }.weather-summary small { color: var(--color-muted); font-size: 10px; }.weather-summary strong { font-size: 13px; }.weather-metrics { display: flex; min-width: 0; flex: 1; justify-content: flex-end; gap: 8px; }.weather-card button { margin-left: auto; padding: 5px 8px; border: 1px solid currentColor; border-radius: 5px; color: var(--color-danger); background: #fff; font-size: 10px; font-weight: 800; }.weather-card.error { color: var(--color-danger); background: #fff1f1; }.weather-error { overflow: hidden; margin: 4px 2px 0; color: var(--color-danger); font-size: 9px; text-overflow: ellipsis; white-space: nowrap; }
.map-sidebar { position: absolute; z-index: 500; top: 20px; bottom: 20px; left: 20px; display: flex; width: 320px; flex-direction: column; overflow: hidden; padding: 20px; border: 1px solid var(--color-line); border-radius: 8px; background: rgba(255,255,255,.97); box-shadow: var(--shadow-lg); }
.sidebar-content { min-height: 0; flex: 1 1 auto; overflow-y: auto; padding-right: 3px; }
.sidebar-title { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; }
.sidebar-title div { display: grid; }.sidebar-title .eyebrow { margin: 0; }.sidebar-title strong { font-size: 22px; }
.mobile-close { display: none; border: 0; background: transparent; }
.map-search { display: flex; height: 44px; align-items: center; gap: 8px; padding: 0 11px; border: 1px solid var(--color-line); border-radius: 6px; }
.map-search input { min-width: 0; flex: 1; border: 0; outline: 0; }.map-search button { display: grid; place-items: center; padding: 0; border: 0; background: transparent; }
.search-results { max-height: 220px; overflow-y: auto; margin-top: 8px; border: 1px solid var(--color-line); border-radius: 6px; background: #fff; }
.search-results p { margin: 0; padding: 10px 12px; color: var(--color-muted); font-size: 11px; }
.search-results button { display: flex; width: 100%; align-items: center; gap: 6px; padding: 10px 9px 10px 5px; border: 0; border-top: 1px solid var(--color-line); text-align: left; background: #fff; cursor: grab; }
.search-results button:active { cursor: grabbing; }.search-results button:hover { background: var(--color-surface-soft); }.result-grip { display: grid; flex: 0 0 auto; place-items: center; color: #9aa7a1; }.result-copy { display: grid; min-width: 0; flex: 1; gap: 3px; }.result-copy strong, .result-copy small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.result-copy small { color: var(--color-muted); font-size: 11px; }
.category-head { display: flex; justify-content: space-between; margin: 22px 0 10px; font-size: 13px; }.category-head span { color: var(--color-muted); font-size: 11px; }
.category-list { display: grid; }
.category-list label { display: flex; min-height: 46px; align-items: center; gap: 10px; border-bottom: 1px solid var(--color-line); cursor: pointer; font-size: 13px; }
.category-list input { accent-color: var(--color-primary); }.category-list i { width: 8px; height: 8px; border-radius: 50%; }.category-list span { font-weight: 700; }.category-list small { margin-left: auto; color: var(--color-muted); }
.map-message { margin-top: 12px; padding: 10px; border-radius: 6px; color: var(--color-primary-dark); background: var(--color-primary-soft); font-size: 12px; line-height: 1.5; }
.interaction-guide { display: grid; gap: 7px; margin-top: 14px; padding: 11px; border-radius: 6px; color: var(--color-muted); background: #f3f6f4; font-size: 10px; }.interaction-guide span { display: flex; align-items: center; gap: 5px; }.interaction-guide strong { color: var(--color-text); }.click-mark { width: 10px; height: 10px; border: 2px solid #fff; border-radius: 50%; background: var(--color-primary); box-shadow: 0 0 0 1px var(--color-primary); }
.back-list { display: flex; align-items: center; gap: 4px; margin-top: 18px; color: var(--color-primary); font-size: 12px; font-weight: 800; }
.course-cart { position: absolute; z-index: 650; bottom: 18px; left: 50%; width: 60%; min-width: 560px; max-width: 920px; overflow: hidden; border: 1px solid var(--color-line); border-radius: 14px; opacity: 0; background: rgba(255,255,255,.98); box-shadow: 0 20px 60px rgba(13,31,24,.22); pointer-events: none; transform: translate(-50%, calc(100% + 40px)); transition: transform .28s cubic-bezier(.2,.8,.2,1), opacity .2s ease, box-shadow .18s ease; }.course-cart.visible { opacity: 1; pointer-events: auto; transform: translate(-50%,0); }.course-cart.active { border: 2px dashed var(--color-primary); box-shadow: 0 0 0 7px rgba(8,127,104,.14), 0 20px 60px rgba(13,31,24,.25); }
.cart-header { display: flex; width: 100%; min-height: 72px; align-items: center; gap: 12px; padding: 13px 18px; border: 0; border-bottom: 1px solid var(--color-line); text-align: left; background: #f8faf9; }.cart-header > span:nth-child(2) { display: grid; flex: 1; gap: 3px; }.cart-header strong { font-size: 15px; }.cart-header small { color: var(--color-muted); font-size: 10px; }.cart-header > svg { color: var(--color-muted); transition: transform .18s ease; }.cart-header > svg.rotated { transform: rotate(180deg); }.cart-icon { position: relative; display: grid; width: 42px; height: 42px; flex: 0 0 auto; place-items: center; border-radius: 10px; color: var(--color-primary-dark); background: var(--color-primary-soft); }.cart-icon b { position: absolute; top: -6px; right: -6px; display: grid; min-width: 18px; height: 18px; place-items: center; padding: 0 4px; border: 2px solid #fff; border-radius: 999px; color: #fff; background: var(--color-accent); font-size: 9px; }
.cart-body { max-height: min(390px, calc(100vh - 190px)); overflow-y: auto; padding: 0 18px 18px; background: #fff; }.empty-cart { display: grid; min-height: 190px; place-items: center; align-content: center; gap: 9px; color: var(--color-muted); text-align: center; }.empty-cart > svg { color: #93a29b; }.empty-cart strong { color: var(--color-text); font-size: 13px; }.empty-cart span { font-size: 11px; line-height: 1.6; }.empty-cart span svg { display: inline; vertical-align: middle; }
.bottom-drop-trigger { position: absolute; z-index: 640; bottom: 0; left: 50%; display: flex; width: 60%; max-width: 920px; min-height: 74px; align-items: center; justify-content: center; gap: 7px; border: 2px dashed var(--color-primary); border-bottom: 0; border-radius: 14px 14px 0 0; color: var(--color-primary-dark); background: rgba(223,243,237,.92); box-shadow: 0 -8px 30px rgba(8,127,104,.12); transform: translateX(-50%); pointer-events: none; animation: trigger-up .2s ease; }.bottom-drop-trigger span { color: var(--color-muted); font-size: 10px; }.cart-peek { position: absolute; z-index: 620; bottom: 12px; left: 50%; display: flex; min-height: 42px; align-items: center; gap: 7px; padding: 0 14px; border: 1px solid var(--color-line); border-radius: 999px; color: var(--color-primary-dark); background: #fff; box-shadow: var(--shadow-lg); transform: translateX(-50%); }.cart-peek span { font-size: 12px; font-weight: 800; }.cart-peek b { display: grid; min-width: 20px; height: 20px; place-items: center; padding: 0 5px; border-radius: 999px; color: #fff; background: var(--color-accent); font-size: 10px; }
.route-label { display: flex; justify-content: space-between; margin: 13px 2px 7px; font-size: 11px; font-weight: 800; }.route-label span { color: var(--color-muted); font-size: 9px; font-weight: 500; }.cart-list { display: grid; gap: 6px; margin: 0; padding: 0; list-style: none; }.cart-list li { display: flex; min-width: 0; align-items: center; gap: 7px; padding: 7px 6px; border: 1px solid var(--color-line); border-radius: 6px; background: #fff; cursor: grab; }.cart-list li:active { cursor: grabbing; }.cart-grip { flex: 0 0 auto; color: #9aa7a1; }.cart-list li > b { display: grid; width: 22px; height: 22px; flex: 0 0 auto; place-items: center; border-radius: 50%; color: var(--color-primary-dark); background: var(--color-primary-soft); font-size: 10px; }.cart-place { display: grid; min-width: 0; flex: 1; gap: 2px; padding: 2px; border: 0; text-align: left; background: transparent; }.cart-place strong, .cart-place small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.cart-place strong { font-size: 11px; }.cart-place small { color: var(--color-muted); font-size: 9px; }.remove-spot { display: grid; flex: 0 0 auto; place-items: center; padding: 5px; border: 0; color: var(--color-muted); background: transparent; }.remove-spot:hover { color: var(--color-danger); }
.cart-notice { margin: 9px 0 0; padding: 8px; border-radius: 5px; color: var(--color-primary-dark); background: var(--color-primary-soft); font-size: 10px; line-height: 1.4; }.cart-notice a { margin-left: 4px; font-weight: 900; text-decoration: underline; }.cart-actions { display: flex; justify-content: space-between; gap: 6px; margin-top: 11px; }.cart-action-group { display: flex; gap: 6px; }.cart-actions .button { min-height: 36px; padding-inline: 10px; font-size: 11px; }.ai-button { border: 1px solid #8b72d8; color: #6046ad; background: #f5f1ff; }.ai-button:hover:not(:disabled) { color: #fff; background: #7155c4; }.ai-feedback { display: grid; gap: 9px; margin-top: 11px; padding: 12px; border: 1px solid #dcd2f5; border-radius: 8px; background: #faf8ff; }.ai-feedback-title { display: flex; align-items: center; gap: 7px; }.ai-feedback-title span { display: grid; width: 28px; height: 28px; place-items: center; border-radius: 7px; color: #6046ad; background: #ebe4ff; }.ai-feedback-title strong { font-size: 12px; }.route-comparison { display: flex; align-items: center; gap: 10px; padding: 8px 10px; border-radius: 6px; background: #fff; }.route-comparison span { display: grid; gap: 2px; }.route-comparison small { color: var(--color-muted); font-size: 9px; }.route-comparison strong { font-size: 12px; }.route-comparison i { color: #8b72d8; font-style: normal; }.route-comparison > b { margin-left: auto; padding: 4px 7px; border-radius: 999px; color: #6046ad; background: #ebe4ff; font-size: 9px; }.ai-feedback-copy { margin: 0; color: var(--color-text); font-size: 11px; line-height: 1.65; white-space: pre-line; }.route-legs { display: flex; flex-wrap: wrap; gap: 5px; }.route-legs span { display: flex; align-items: center; gap: 4px; padding: 4px 7px; border-radius: 999px; color: var(--color-muted); background: #fff; font-size: 9px; }.route-legs b { color: #6046ad; }.recommended-order { display: grid; gap: 5px; }.recommended-order > small { color: var(--color-muted); font-size: 9px; font-weight: 800; }.recommended-order ol { display: flex; flex-wrap: wrap; gap: 5px; margin: 0; padding: 0; list-style: none; counter-reset: recommended; }.recommended-order li { counter-increment: recommended; padding: 5px 7px; border: 1px solid #e2daf5; border-radius: 5px; background: #fff; font-size: 9px; }.recommended-order li::before { content: counter(recommended) '. '; color: #6046ad; font-weight: 900; }.ai-apply { justify-self: start; border: 0; color: #fff; background: #7155c4; }.distance-notice { color: var(--color-muted); font-size: 8px; }.ai-feedback-error { margin: 0; color: var(--color-danger); font-size: 10px; }.course-form { display: grid; gap: 11px; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--color-line); }.course-form .field { gap: 5px; }.course-form label { font-size: 11px; }.course-form .input { height: 38px; font-size: 11px; }.course-form .textarea { min-height: 72px; padding: 9px; font-size: 11px; }.course-form > .button { min-height: 38px; font-size: 11px; }.save-error { margin: 0; color: var(--color-danger); font-size: 10px; }
.detail-sheet { position: absolute; z-index: 500; top: 20px; left: 360px; display: grid; width: min(480px, calc(100% - 400px)); grid-template-columns: 170px 1fr; overflow: hidden; border: 1px solid var(--color-line); border-radius: 8px; background: #fff; box-shadow: var(--shadow-lg); cursor: grab; transition: left .12s ease, top .12s ease; }.detail-sheet:active { cursor: grabbing; }.detail-sheet a, .detail-sheet button { cursor: pointer; }
.sheet-close { position: absolute; z-index: 2; top: 10px; right: 10px; width: 34px; height: 34px; }
.popup-drag-guide { position: absolute; z-index: 2; top: 10px; left: 10px; display: flex; align-items: center; gap: 4px; padding: 6px 9px; border-radius: 999px; color: #fff; background: rgba(23,33,29,.78); font-size: 9px; font-weight: 800; backdrop-filter: blur(5px); pointer-events: none; }
.sheet-image { display: grid; min-height: 245px; place-items: center; color: var(--color-muted); background: #e7eeea; }.sheet-image img { width: 100%; height: 100%; object-fit: cover; }
.sheet-copy { padding: 24px 22px; }.sheet-copy h2 { margin: 10px 34px 7px 0; font-size: 23px; }.sheet-copy > p { display: flex; gap: 5px; color: var(--color-muted); font-size: 12px; line-height: 1.5; }
.crowd { display: grid; gap: 4px; margin: 17px 0; padding: 10px 12px; border-radius: 6px; color: var(--color-muted); background: #f2f4f3; font-size: 11px; }.crowd strong { font-size: 12px; }.crowd.active { color: var(--color-primary-dark); background: var(--color-primary-soft); }
.sheet-actions { display: flex; gap: 6px; }.sheet-actions .button { flex: 1; padding-inline: 8px; font-size: 11px; }.add-mobile { display: none; }.drag-spot { display: flex; width: 100%; align-items: center; gap: 7px; margin-top: 9px; padding: 8px; border: 1px dashed #a9c8bd; border-radius: 6px; color: var(--color-primary-dark); text-align: left; background: #f3faf7; }.drag-spot > svg { flex: 0 0 auto; }.drag-spot span { display: grid; gap: 2px; }.drag-spot strong { font-size: 10px; }.drag-spot small { color: var(--color-muted); font-size: 8px; }
.mobile-filter-button { display: none; position: absolute; z-index: 450; top: 12px; left: 12px; }
.ai-feedback-panel { position: absolute; z-index: 660; display: grid; min-width: 0; min-height: 0; align-content: start; gap: 10px; overflow-y: auto; padding: 14px; border: 1px solid #dcd2f5; border-radius: 12px; background: rgba(250,248,255,.98); box-shadow: 0 18px 50px rgba(50,35,92,.22); backdrop-filter: blur(12px); }
.ai-feedback-title button { display: grid; margin-left: auto; padding: 5px; border: 0; place-items: center; color: var(--color-muted); background: transparent; }
.ai-weather-context { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 5px; }
.ai-weather-context > span { display: grid; min-width: 0; grid-template-columns: auto 1fr; gap: 2px 6px; padding: 7px 8px; border: 1px solid #e5def6; border-radius: 6px; background: #fff; }
.ai-weather-context b { color: #6046ad; font-size: 9px; }.ai-weather-context small { overflow: hidden; color: var(--color-muted); font-size: 9px; text-overflow: ellipsis; white-space: nowrap; }.ai-weather-context strong { font-size: 10px; }.ai-weather-context em { color: var(--color-muted); font-size: 8px; font-style: normal; text-align: right; }
.ai-feedback-loading { display: flex; min-height: 90px; align-items: center; justify-content: center; gap: 7px; margin: 0; color: #6046ad; font-size: 11px; }
@media (max-width: 800px) {
  .map-sidebar { top: 0; bottom: 0; left: 0; width: min(360px, 88vw); border-radius: 0; transform: translateX(-105%); transition: transform .22s ease; }.map-sidebar.mobileOpen { transform: translateX(0); }
  .mobile-filter-button, .mobile-close { display: grid; place-items: center; }
  .trip-planner { top: 12px; right: 12px; left: 62px; width: auto; padding: 8px; }.trip-controls { align-items: stretch; flex-direction: column; gap: 5px; }.date-range { justify-content: stretch; }.date-range label { flex: 1; }.date-range input { width: 100%; }.date-tabs { width: 100%; max-width: none; }.trip-weather { margin-top: 5px; padding-top: 5px; }.weather-card { flex-wrap: wrap; }.weather-metrics { order: 3; width: 100%; justify-content: space-between; }
  .course-cart { right: 10px; bottom: 10px; left: 10px; width: auto; min-width: 0; max-width: none; transform: translateY(calc(100% + 30px)); }.course-cart.visible { transform: translateY(0); }.cart-body { max-height: 48vh; }.bottom-drop-trigger { width: calc(100% - 20px); }.cart-peek { bottom: 10px; }
  .ai-feedback-panel { right: 10px; bottom: 86px; left: 10px; width: auto; max-height: min(45vh, 430px); }
  .detail-sheet { top: auto; right: 10px; bottom: 10px; left: 10px; width: auto; grid-template-columns: 110px 1fr; }.sheet-image { min-height: 220px; }.sheet-copy { padding: 18px 16px; }.sheet-copy h2 { font-size: 19px; }
  .drag-spot { display: none; }.add-mobile { display: inline-flex; }
}
@media (min-width: 801px) and (max-width: 1100px) { .trip-controls { flex-wrap: wrap; }.date-tabs { max-width: none; }.weather-metrics { gap: 9px; } }
@media (max-width: 480px) { .trip-planner { left: 56px; }.trip-title > span { width: 32px; height: 32px; }.date-range { gap: 4px; }.date-range input { padding-inline: 4px; font-size: 9px; }.weather-card { padding: 7px 9px; }.cart-header small { display: none; }.cart-actions { align-items: stretch; flex-direction: column; }.cart-action-group { display: grid; grid-template-columns: 1fr 1fr; }.route-comparison { flex-wrap: wrap; }.route-comparison > b { margin-left: 0; }.detail-sheet { grid-template-columns: 1fr; }.sheet-image { display: none; }.sheet-copy { padding: 18px; } }
@keyframes trigger-up { from { transform: translate(-50%, 30px); opacity: 0; } }
</style>
