import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'home', component: () => import('../views/HomeView.vue') },
  { path: '/locations', name: 'locations', component: () => import('../views/LocationsView.vue') },
  { path: '/locations/:id', name: 'location-detail', component: () => import('../views/LocationDetailView.vue') },
  { path: '/map', name: 'map', component: () => import('../views/MapView.vue') },
  { path: '/courses', name: 'courses', component: () => import('../views/CoursesView.vue') },
  { path: '/courses/:id', name: 'course-detail', component: () => import('../views/CourseDetailView.vue') },
  { path: '/community', name: 'community', component: () => import('../views/CommunityView.vue') },
  { path: '/community/write', name: 'post-write', component: () => import('../views/PostWriteView.vue') },
  { path: '/community/:id', name: 'post-detail', component: () => import('../views/PostDetailView.vue') },
  { path: '/community/:id/edit', name: 'post-edit', component: () => import('../views/PostWriteView.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

export default createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    return savedPosition || { top: 0 }
  },
})
