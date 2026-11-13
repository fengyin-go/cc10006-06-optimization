<template>
  <section class="page" data-module="bronze">
    <header class="page-head">
      <div>
        <h2>原始层管理</h2>
        <p class="page-desc">登记与修改原始表的分区规则、保留策略、压缩类型与数据校验；同一表编号再次录入时历史版本退出当前同步，现网只跟随最新分区版本。</p>
      </div>
      <div class="page-actions">
        <button class="btn primary" type="button" @click="openCreate">登记原始表</button>
        <button class="btn" type="button" @click="exportRows">导出原始层管理清单</button>
      </div>
    </header>

    <div class="stat-row">
      <article v-for="item in stats" :key="item.label" class="stat-card">
        <span class="stat-label">{{ item.label }}</span>
        <strong class="stat-value">{{ item.value }}</strong>
      </article>
    </div>

    <div class="message-bar">
      <span v-if="noticeMessage" class="notice-text">{{ noticeMessage }}</span>
      <span v-if="warnMessage" class="warn-text">{{ warnMessage }}</span>
      <span v-if="errorMessage" class="error-text">{{ errorMessage }}</span>
    </div>

    <form class="filter-bar" @submit.prevent="reload">
      <label v-for="field in filterFields" :key="field" class="filter-item">
        <span>{{ field }}</span>
        <input v-model="filters[field]" :placeholder="`按${field}检索`" />
      </label>
      <button class="btn" type="submit">查询</button>
      <button class="btn ghost" type="button" @click="resetFilters">重置条件</button>
    </form>

    <table class="data-table">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column">{{ column }}</th>
          <th>版本</th>
          <th>状态</th>
          <th>同步状态</th>
          <th>可执行动作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="String(row.id)">
          <td v-for="column in columns" :key="column">{{ row[column] ?? '—' }}</td>
          <td>v{{ row.版本 ?? 1 }}</td>
          <td>{{ row.status }}</td>
          <td>
            <span class="tag" :class="isRetired(row) ? 'retired' : 'current'">{{ row.同步状态 ?? '当前同步' }}</span>
          </td>
          <td class="row-actions">
            <button class="link" type="button" @click="openDetail(row)">详情</button>
            <template v-if="!isRetired(row)">
              <button class="link" type="button" @click="openEdit(row)">编辑</button>
              <button
                v-for="action in actions"
                :key="action"
                class="link"
                type="button"
                @click="runAction(action, row)"
              >
                {{ action }}
              </button>
            </template>
          </td>
        </tr>
        <tr v-if="!rows.length">
          <td :colspan="columns.length + 4" class="empty-state">暂无原始层管理数据，可先登记原始表</td>
        </tr>
      </tbody>
    </table>

    <footer class="page-foot">
      <span>共 {{ total }} 条原始层管理记录</span>
    </footer>

    <BronzeForm
      v-if="showCreate"
      title="登记原始表"
      tip="分区规则、保留策略、压缩类型与数据校验会完整持久化，并同步到数据目录与血缘采集；同一表编号再次录入时历史版本退出当前同步。"
      :submitting="submitting"
      @submit="submitCreate"
      @cancel="showCreate = false"
    />
    <BronzeForm
      v-if="editingRow"
      :title="`编辑原始表 ${editingRow.表编号}（基于 v${editingRow.版本 ?? 1}）`"
      tip="保存时携带期望版本做并发校验；若他人已先保存，本次修改会被退回并说明现网采用的版本。"
      :initial="editInitial"
      :lock-code="true"
      :submitting="submitting"
      @submit="submitEdit"
      @cancel="editingRow = null"
    />
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { request } from '@/api/client'
import BronzeForm from '@/views/bronze/BronzeForm.vue'

type Row = Record<string, string | number | null>

const ENDPOINT = '/api/bronze'
const columns = ["表编号", "来源通道", "目标路径", "保留策略", "分区规则", "文件格式", "压缩类型", "数据校验"]
const actions = ["提交校验", "启用同步", "停用同步"]

const router = useRouter()
const rows = ref<Row[]>([])
const total = ref(0)
const stats = ref([{ label: '原始表总数', value: 0 }, { label: '当前同步表', value: 0 }, { label: '已启用表', value: 0 }])
const errorMessage = ref('')
const noticeMessage = ref('')
const warnMessage = ref('')
const filters = ref<Record<string, string>>({})
const filterFields = columns.slice(0, 3)
const showCreate = ref(false)
const editingRow = ref<Row | null>(null)
const editInitial = ref<Record<string, string>>({})
const submitting = ref(false)

function isRetired(row: Row) {
  return row.同步状态 === '已退出同步'
}

function clearMessages() {
  errorMessage.value = ''
  noticeMessage.value = ''
  warnMessage.value = ''
}

function resetFilters() {
  filters.value = {}
  void reload()
}

function exportRows() {
  window.open(`${ENDPOINT}/export`, '_blank')
}

function openCreate() {
  clearMessages()
  showCreate.value = true
}

function openDetail(row: Row) {
  void router.push(`/bronze/${row.id}`)
}

function openEdit(row: Row) {
  clearMessages()
  editInitial.value = Object.fromEntries(columns.map((column) => [column, String(row[column] ?? '')]))
  editingRow.value = row
}

async function parseActionResult(response: Response) {
  const payload = (await response.json()) as { ok: boolean; message: string }
  if (!payload.ok) {
    throw new Error(payload.message)
  }
  return payload
}

async function submitCreate(values: Record<string, string>) {
  clearMessages()
  submitting.value = true
  try {
    const response = await request(ENDPOINT, { method: 'POST', body: JSON.stringify({ values }) })
    const payload = await parseActionResult(response)
    showCreate.value = false
    noticeMessage.value = payload.message
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '原始表登记失败'
  } finally {
    submitting.value = false
  }
}

async function submitEdit(values: Record<string, string>) {
  if (!editingRow.value) return
  clearMessages()
  submitting.value = true
  const target = editingRow.value
  try {
    const response = await request(`${ENDPOINT}/${target.id}`, {
      method: 'PUT',
      body: JSON.stringify({ values, 期望版本: Number(target.版本 ?? 1) }),
    })
    if (response.status === 409) {
      const body = (await response.json()) as { detail?: { message?: string } }
      warnMessage.value = body.detail?.message ?? '保存冲突：现网已采用更新的版本，本次修改已退回'
      editingRow.value = null
      await reload()
      return
    }
    const payload = await parseActionResult(response)
    editingRow.value = null
    noticeMessage.value = payload.message
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '原始表修改失败'
  } finally {
    submitting.value = false
  }
}

async function runAction(action: string, row: Row) {
  clearMessages()
  try {
    const response = await request(`${ENDPOINT}/${row.id}/actions`, {
      method: 'POST',
      body: JSON.stringify({ values: { action } }),
    })
    const payload = await parseActionResult(response)
    noticeMessage.value = payload.message
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '原始层管理操作失败'
  }
}

async function reload() {
  const query = new URLSearchParams(filters.value as Record<string, string>).toString()
  try {
    const response = await request(`${ENDPOINT}?${query}`)
    if (!response.ok) {
      throw new Error('原始表列表读取失败')
    }
    const payload = await response.json()
    rows.value = payload.items ?? []
    total.value = payload.total ?? rows.value.length
    await loadStats()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '原始层管理列表读取失败'
  }
}

async function loadStats() {
  try {
    const response = await request(`${ENDPOINT}/export`)
    if (!response.ok) return
    const payload = await response.json()
    const items = (payload.items ?? []) as Row[]
    stats.value = [
      { label: '原始表总数', value: items.length },
      { label: '当前同步表', value: items.filter((row) => row.同步状态 !== '已退出同步').length },
      { label: '已启用表', value: items.filter((row) => row.status === '已启用').length },
    ]
  } catch {
    // 统计卡片失败不阻断列表
  }
}

onMounted(reload)
</script>
