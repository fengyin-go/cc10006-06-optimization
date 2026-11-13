<template>
  <section class="page" data-module="bronze-detail">
    <header class="page-head">
      <div>
        <h2>原始表详情 {{ entry ? `${entry.表编号} · v${entry.版本 ?? 1}` : '' }}</h2>
        <p class="page-desc">详情、目录与血缘采集读取同一份持久结果；刷新、返回或重新进入后看到的分区、保留期、压缩参数和校验结果完全一致。</p>
      </div>
      <div class="page-actions">
        <button class="btn" type="button" @click="goBack">返回列表</button>
        <button v-if="entry && !isRetired" class="btn primary" type="button" @click="openEdit">编辑当前版本</button>
      </div>
    </header>

    <div class="message-bar">
      <span v-if="noticeMessage" class="notice-text">{{ noticeMessage }}</span>
      <span v-if="warnMessage" class="warn-text">{{ warnMessage }}</span>
      <span v-if="errorMessage" class="error-text">{{ errorMessage }}</span>
    </div>

    <template v-if="entry">
      <div class="panel-card">
        <h3>基本信息 <span class="tag" :class="isRetired ? 'retired' : 'current'">{{ entry.同步状态 ?? '当前同步' }}</span></h3>
        <div class="desc-grid">
          <div v-for="field in businessFields" :key="field" class="desc-item">
            <span class="desc-label">{{ field }}</span>
            <span class="desc-value">{{ entry[field] ?? '—' }}</span>
          </div>
          <div class="desc-item"><span class="desc-label">版本</span><span class="desc-value">v{{ entry.版本 ?? 1 }}</span></div>
          <div class="desc-item"><span class="desc-label">状态</span><span class="desc-value">{{ entry.status }}</span></div>
          <div class="desc-item"><span class="desc-label">登记时间</span><span class="desc-value">{{ entry.登记时间 ?? '—' }}</span></div>
          <div class="desc-item"><span class="desc-label">更新时间</span><span class="desc-value">{{ entry.更新时间 ?? '—' }}</span></div>
        </div>
      </div>

      <div class="panel-card">
        <h3>数据目录同步</h3>
        <div v-if="catalog" class="desc-grid">
          <div class="desc-item"><span class="desc-label">编目编号</span><span class="desc-value">{{ catalog.编目编号 }}</span></div>
          <div class="desc-item"><span class="desc-label">编目版本</span><span class="desc-value">{{ catalog.编目版本 }}</span></div>
          <div class="desc-item"><span class="desc-label">文件格式</span><span class="desc-value">{{ catalog.文件格式 }}</span></div>
          <div class="desc-item"><span class="desc-label">保留策略</span><span class="desc-value">{{ catalog.保留策略 }}</span></div>
          <div class="desc-item"><span class="desc-label">分区规则</span><span class="desc-value">{{ catalog.分区规则 }}</span></div>
          <div class="desc-item"><span class="desc-label">压缩类型</span><span class="desc-value">{{ catalog.压缩类型 }}</span></div>
          <div class="desc-item"><span class="desc-label">数据校验</span><span class="desc-value">{{ catalog.数据校验 }}</span></div>
          <div class="desc-item"><span class="desc-label">同步时间</span><span class="desc-value">{{ catalog.同步时间 }}</span></div>
        </div>
        <p v-else class="page-desc">目录中尚无该表的同步记录</p>
      </div>

      <div class="panel-card">
        <h3>血缘采集状态</h3>
        <div v-if="lineage" class="desc-grid">
          <div class="desc-item"><span class="desc-label">节点编号</span><span class="desc-value">{{ lineage.节点编号 }}</span></div>
          <div class="desc-item"><span class="desc-label">图谱版本</span><span class="desc-value">{{ lineage.图谱版本 }}</span></div>
          <div class="desc-item"><span class="desc-label">采集状态</span><span class="desc-value">{{ lineage.status }}</span></div>
          <div class="desc-item"><span class="desc-label">采集时间</span><span class="desc-value">{{ lineage.采集时间 }}</span></div>
          <div class="desc-item"><span class="desc-label">保留策略</span><span class="desc-value">{{ lineage.保留策略 }}</span></div>
          <div class="desc-item"><span class="desc-label">分区规则</span><span class="desc-value">{{ lineage.分区规则 }}</span></div>
          <div class="desc-item"><span class="desc-label">压缩类型</span><span class="desc-value">{{ lineage.压缩类型 }}</span></div>
          <div class="desc-item"><span class="desc-label">转换说明</span><span class="desc-value">{{ lineage.转换说明 }}</span></div>
        </div>
        <p v-else class="page-desc">血缘中尚无该表的采集记录</p>
      </div>

      <div class="panel-card">
        <h3>版本列表（现网只跟随最新版本，历史版本退出同步但保留可查）</h3>
        <table class="data-table">
          <thead>
            <tr>
              <th>版本</th><th>分区规则</th><th>保留策略</th><th>压缩类型</th><th>数据校验</th><th>状态</th><th>同步状态</th><th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="version in versions" :key="String(version.id)">
              <td>v{{ version.版本 ?? 1 }}</td>
              <td>{{ version.分区规则 }}</td>
              <td>{{ version.保留策略 }}</td>
              <td>{{ version.压缩类型 }}</td>
              <td>{{ version.数据校验 }}</td>
              <td>{{ version.status }}</td>
              <td><span class="tag" :class="version.同步状态 === '已退出同步' ? 'retired' : 'current'">{{ version.同步状态 ?? '当前同步' }}</span></td>
              <td><button v-if="version.id !== entry.id" class="link" type="button" @click="openVersion(version)">查看</button><span v-else>当前</span></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="panel-card">
        <h3>变更历史</h3>
        <table v-if="changeHistory.length" class="data-table">
          <thead>
            <tr><th>版本</th><th>时间</th><th>操作</th><th>变更前快照</th></tr>
          </thead>
          <tbody>
            <tr v-for="(change, index) in changeHistory" :key="index">
              <td>v{{ change.版本 }}</td>
              <td>{{ change.时间 }}</td>
              <td>{{ change.操作 }}</td>
              <td>{{ snapshotText(change.快照) }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else class="page-desc">当前版本尚无修改记录</p>
      </div>
    </template>

    <BronzeForm
      v-if="editing"
      :title="`编辑原始表 ${entry?.表编号}（基于 v${entry?.版本 ?? 1}）`"
      tip="保存时携带期望版本做并发校验；若他人已先保存，本次修改会被退回并说明现网采用的版本。"
      :initial="editInitial"
      :lock-code="true"
      :submitting="submitting"
      @submit="submitEdit"
      @cancel="editing = false"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { request } from '@/api/client'
import BronzeForm from '@/views/bronze/BronzeForm.vue'

type Row = Record<string, any>

const ENDPOINT = '/api/bronze'
const businessFields = ["表编号", "来源通道", "目标路径", "保留策略", "分区规则", "文件格式", "压缩类型", "数据校验"]

const route = useRoute()
const router = useRouter()
const entry = ref<Row | null>(null)
const versions = ref<Row[]>([])
const catalog = ref<Row | null>(null)
const lineage = ref<Row | null>(null)
const editing = ref(false)
const editInitial = ref<Record<string, string>>({})
const submitting = ref(false)
const errorMessage = ref('')
const noticeMessage = ref('')
const warnMessage = ref('')

const isRetired = computed(() => entry.value?.同步状态 === '已退出同步')
const changeHistory = computed<Row[]>(() => (Array.isArray(entry.value?.变更历史) ? [...entry.value.变更历史].reverse() : []))

function snapshotText(snapshot: Row | undefined) {
  if (!snapshot) return '—'
  return `分区规则 ${snapshot.分区规则}、保留策略 ${snapshot.保留策略}、压缩类型 ${snapshot.压缩类型}、数据校验 ${snapshot.数据校验}`
}

function clearMessages() {
  errorMessage.value = ''
  noticeMessage.value = ''
  warnMessage.value = ''
}

function goBack() {
  void router.push('/bronze')
}

function openVersion(version: Row) {
  void router.push(`/bronze/${version.id}`)
}

function openEdit() {
  if (!entry.value) return
  clearMessages()
  editInitial.value = Object.fromEntries(businessFields.map((field) => [field, String(entry.value?.[field] ?? '')]))
  editing.value = true
}

async function submitEdit(values: Record<string, string>) {
  if (!entry.value) return
  clearMessages()
  submitting.value = true
  try {
    const response = await request(`${ENDPOINT}/${entry.value.id}`, {
      method: 'PUT',
      body: JSON.stringify({ values, 期望版本: Number(entry.value.版本 ?? 1) }),
    })
    if (response.status === 409) {
      const body = (await response.json()) as { detail?: { message?: string } }
      warnMessage.value = body.detail?.message ?? '保存冲突：现网已采用更新的版本，本次修改已退回'
      editing.value = false
      await load()
      return
    }
    const payload = (await response.json()) as { ok: boolean; message: string }
    if (!payload.ok) {
      throw new Error(payload.message)
    }
    editing.value = false
    noticeMessage.value = payload.message
    await load()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '原始表修改失败'
  } finally {
    submitting.value = false
  }
}

async function load() {
  const id = route.params.id
  try {
    const [entryResp, versionsResp, syncResp] = await Promise.all([
      request(`${ENDPOINT}/${id}`),
      request(`${ENDPOINT}/${id}/versions`),
      request(`${ENDPOINT}/${id}/sync`),
    ])
    if (!entryResp.ok) {
      throw new Error(`原始表 ${id} 不存在或已归档`)
    }
    entry.value = await entryResp.json()
    versions.value = versionsResp.ok ? ((await versionsResp.json()).items ?? []) : []
    if (syncResp.ok) {
      const sync = await syncResp.json()
      catalog.value = sync.catalog ?? null
      lineage.value = sync.lineage ?? null
    }
  } catch (error) {
    entry.value = null
    errorMessage.value = error instanceof Error ? error.message : '原始表详情读取失败'
  }
}

watch(() => route.params.id, () => { clearMessages(); void load() }, { immediate: true })
</script>
