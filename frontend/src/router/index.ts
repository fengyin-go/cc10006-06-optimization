import { createRouter, createWebHistory } from 'vue-router'

import Overview from '@/views/Overview.vue'
const Catalog = () => import('@/views/catalog/index.vue')
const Ingest = () => import('@/views/ingest/index.vue')
const Bronze = () => import('@/views/bronze/index.vue')
const Silver = () => import('@/views/silver/index.vue')
const Gold = () => import('@/views/gold/index.vue')
const Lakezone = () => import('@/views/lakezone/index.vue')
const Stream = () => import('@/views/stream/index.vue')
const Batch = () => import('@/views/batch/index.vue')
const Snapshot = () => import('@/views/snapshot/index.vue')
const Govern = () => import('@/views/govern/index.vue')
const Meta = () => import('@/views/meta/index.vue')
const Lineage = () => import('@/views/lineage/index.vue')
const Quality = () => import('@/views/quality/index.vue')
const Schedule = () => import('@/views/schedule/index.vue')
const Backfill = () => import('@/views/backfill/index.vue')
const Search = () => import('@/views/search/index.vue')
const Resource = () => import('@/views/resource/index.vue')
const Audit = () => import('@/views/audit/index.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'overview', component: Overview },
    { path: '/catalog', name: 'catalog', component: Catalog },
    { path: '/ingest', name: 'ingest', component: Ingest },
    { path: '/bronze', name: 'bronze', component: Bronze },
    { path: '/silver', name: 'silver', component: Silver },
    { path: '/gold', name: 'gold', component: Gold },
    { path: '/lakezone', name: 'lakezone', component: Lakezone },
    { path: '/stream', name: 'stream', component: Stream },
    { path: '/batch', name: 'batch', component: Batch },
    { path: '/snapshot', name: 'snapshot', component: Snapshot },
    { path: '/govern', name: 'govern', component: Govern },
    { path: '/meta', name: 'meta', component: Meta },
    { path: '/lineage', name: 'lineage', component: Lineage },
    { path: '/quality', name: 'quality', component: Quality },
    { path: '/schedule', name: 'schedule', component: Schedule },
    { path: '/backfill', name: 'backfill', component: Backfill },
    { path: '/search', name: 'search', component: Search },
    { path: '/resource', name: 'resource', component: Resource },
    { path: '/audit', name: 'audit', component: Audit },
  ],
})

export default router
