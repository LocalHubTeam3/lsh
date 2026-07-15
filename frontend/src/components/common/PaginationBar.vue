<script setup>
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
defineProps({ page: Number, totalPages: Number, disabled: Boolean })
defineEmits(['change'])
</script>

<template>
  <nav class="pagination" aria-label="페이지 이동">
    <button class="icon-button" type="button" title="이전 페이지" :disabled="disabled || page <= 1" @click="$emit('change', page - 1)"><ChevronLeft :size="19" /></button>
    <span><strong>{{ page }}</strong> / {{ totalPages }}</span>
    <button class="icon-button" type="button" title="다음 페이지" :disabled="disabled || page >= totalPages" @click="$emit('change', page + 1)"><ChevronRight :size="19" /></button>
  </nav>
</template>

<style scoped>
.pagination { display: flex; align-items: center; justify-content: center; gap: 16px; margin-top: 30px; color: var(--color-muted); font-size: 14px; }
.pagination strong { color: var(--color-primary); }
</style>
