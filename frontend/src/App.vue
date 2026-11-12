<template>
  <div class="app-shell">
    <aside class="app-side">
      <h1 class="app-title">数据湖仓一体管理平台</h1>
      <nav class="nav-list">
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item">
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>
    <main class="app-main">
      <header class="app-head">
        <span class="head-desc">面向数据湖仓一体架构下的多源异构接入、原始文件编目、湖内分区治理、流批一体转换、版本回溯与数据编目检索的管理平台。</span>
        <span class="head-user">当前值班：{{ store.operator }} · {{ store.shiftLabel }}</span>
      </header>
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useSessionStore } from '@/stores/session'

const store = useSessionStore()

const navItems = [{ label: "运营概览", path: "/" }, { label: "数据编目", path: "/catalog" }, { label: "多源接入", path: "/ingest" }, { label: "原始层管理", path: "/bronze" }, { label: "清洗层管理", path: "/silver" }, { label: "聚合层管理", path: "/gold" }, { label: "湖区分区", path: "/lakezone" }, { label: "流式处理", path: "/stream" }, { label: "批量转换", path: "/batch" }, { label: "版本快照", path: "/snapshot" }, { label: "湖仓治理", path: "/govern" }, { label: "元数据中心", path: "/meta" }, { label: "血缘图谱", path: "/lineage" }, { label: "质量监控", path: "/quality" }, { label: "编排调度", path: "/schedule" }, { label: "历史回填", path: "/backfill" }, { label: "数据检索", path: "/search" }, { label: "资源计量", path: "/resource" }, { label: "操作审计", path: "/audit" }]
</script>
