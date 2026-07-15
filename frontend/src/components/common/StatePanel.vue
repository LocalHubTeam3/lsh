<script setup>
import { AlertCircle, Inbox, LoaderCircle } from 'lucide-vue-next'
defineProps({ type: { type: String, default: 'empty' }, title: String, message: String })
defineEmits(['retry'])
</script>

<template>
  <div class="state-panel" role="status">
    <LoaderCircle v-if="type === 'loading'" class="spin" :size="28" />
    <AlertCircle v-else-if="type === 'error'" :size="28" />
    <Inbox v-else :size="28" />
    <strong>{{ title }}</strong>
    <p v-if="message">{{ message }}</p>
    <button v-if="type === 'error'" class="button secondary" type="button" @click="$emit('retry')">다시 시도</button>
  </div>
</template>

<style scoped>
.state-panel { display: grid; min-height: 240px; place-items: center; align-content: center; gap: 9px; padding: 30px; border: 1px dashed #cbd5d0; border-radius: 8px; color: var(--color-muted); text-align: center; background: rgba(255,255,255,.6); }
.state-panel strong { color: var(--color-text); }
.state-panel p { max-width: 480px; margin: 0; font-size: 14px; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
