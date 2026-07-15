<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: String, required: true },
})
</script>

<template>
  <div class="weather-metric">
    <small>{{ label }}</small>
    <strong>{{ value }}</strong>
  </div>
</template>

<style scoped>
.weather-metric {
  display: grid;
  min-width: 64px;
  min-height: 40px;
  place-items: center;
  align-content: center;
  gap: 3px;
  padding: 5px 9px;
  border: 1px solid rgba(8, 127, 104, .13);
  border-radius: 6px;
  background: rgba(255, 255, 255, .72);
}

small {
  color: var(--color-muted);
  font-size: 10px;
  line-height: 1;
}

strong {
  color: var(--color-text);
  font-size: 12px;
  line-height: 1.1;
  white-space: nowrap;
}
</style>
