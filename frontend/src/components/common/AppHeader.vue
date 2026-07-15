<script setup>
import { ref, watch } from 'vue'
import { Menu, X, Map, MessageSquareText, Route, Search } from 'lucide-vue-next'
import { useRoute } from 'vue-router'

const open = ref(false)
const route = useRoute()
watch(() => route.fullPath, () => { open.value = false })
</script>

<template>
  <header class="site-header">
    <div class="header-inner">
      <RouterLink class="brand" to="/" aria-label="LocalHub 홈">LOCAL<span>HUB</span></RouterLink>
      <nav :class="['main-nav', { open }]" aria-label="주요 메뉴">
        <RouterLink to="/locations"><Search :size="17" />장소 탐색</RouterLink>
        <RouterLink to="/map"><Map :size="17" />지도</RouterLink>
        <RouterLink to="/courses"><Route :size="17" />여행 코스</RouterLink>
        <RouterLink to="/community"><MessageSquareText :size="17" />커뮤니티</RouterLink>
      </nav>
      <button class="menu-button" type="button" :aria-label="open ? '메뉴 닫기' : '메뉴 열기'" @click="open = !open">
        <X v-if="open" :size="22" /><Menu v-else :size="22" />
      </button>
    </div>
  </header>
</template>

<style scoped>
.site-header { position: sticky; z-index: 1000; top: 0; height: var(--header-height); border-bottom: 0; background: rgba(23,59,79,.97); box-shadow: 0 5px 18px rgba(23,59,79,.12); backdrop-filter: blur(14px); }
.header-inner { display: flex; width: min(calc(100% - 40px), var(--container)); height: 100%; align-items: center; justify-content: space-between; margin: auto; }
.brand { color: var(--color-surface); font-size: 19px; font-weight: 900; }
.brand span { color: #8fc8c2; }
.main-nav { display: flex; align-items: center; gap: 6px; }
.main-nav a { display: flex; align-items: center; gap: 7px; padding: 10px 13px; border-radius: 6px; color: #d8e2e4; font-size: 14px; font-weight: 700; }
.main-nav a:hover, .main-nav a.router-link-active { color: #fff; background: var(--color-primary); }
.menu-button { display: none; border: 0; color: #fff; background: transparent; }
@media (max-width: 700px) {
  .header-inner { width: calc(100% - 28px); }
  .menu-button { display: grid; place-items: center; }
  .main-nav { position: absolute; top: var(--header-height); right: 0; left: 0; display: none; padding: 12px 14px 16px; border-bottom: 1px solid rgba(216,210,199,.4); background: var(--color-primary-dark); box-shadow: var(--shadow-sm); }
  .main-nav.open { display: grid; }
  .main-nav a { min-height: 44px; }
}
</style>
