<script setup>
import AppHeader from './components/common/AppHeader.vue'
import ChatWidget from './components/chatbot/ChatWidget.vue'
</script>

<template>
  <div class="app-shell">
    <AppHeader />
    <main class="app-main">
      <RouterView />
    </main>
    <ChatWidget />
  </div>
</template>
