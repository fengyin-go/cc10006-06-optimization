<template>
  <div class="modal-mask" @click.self="emit('cancel')">
    <div class="modal-panel">
      <h3>{{ title }}</h3>
      <p class="modal-tip">{{ tip }}</p>
      <form @submit.prevent="onSubmit">
        <div class="form-grid">
          <label class="form-item">
            <span>表编号 *</span>
            <input v-model.trim="form.表编号" :disabled="lockCode" placeholder="如 BRON-9001" required />
          </label>
          <label class="form-item">
            <span>来源通道 *</span>
            <input v-model.trim="form.来源通道" placeholder="如 INGE-0003" required />
          </label>
          <label class="form-item">
            <span>目标路径 *</span>
            <input v-model.trim="form.目标路径" placeholder="如 /lake/bronze/bron_9001" required />
          </label>
          <label class="form-item">
            <span>保留策略 *（保留天数 1-3650）</span>
            <input v-model.trim="form.保留策略" placeholder="如 30 或 30天" required />
          </label>
          <label class="form-item">
            <span>分区规则 *</span>
            <select v-model="form.分区规则" required>
              <option v-for="option in partitionOptions" :key="option" :value="option">{{ option }}</option>
            </select>
          </label>
          <label class="form-item">
            <span>文件格式 *</span>
            <select v-model="form.文件格式" required>
              <option v-for="option in formatOptions" :key="option" :value="option">{{ option }}</option>
            </select>
          </label>
          <label class="form-item">
            <span>压缩类型 *</span>
            <select v-model="form.压缩类型" required>
              <option v-for="option in compressionOptions" :key="option" :value="option">{{ option }}</option>
            </select>
          </label>
          <label class="form-item">
            <span>数据校验 *</span>
            <input v-model.trim="form.数据校验" placeholder="如 行数与schema校验" required />
          </label>
        </div>
        <div class="modal-actions">
          <button class="btn" type="button" @click="emit('cancel')">取消</button>
          <button class="btn primary" type="submit" :disabled="submitting">保存</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'

const props = withDefaults(
  defineProps<{
    title: string
    tip?: string
    initial?: Record<string, string>
    lockCode?: boolean
    submitting?: boolean
  }>(),
  { tip: '', initial: () => ({}), lockCode: false, submitting: false },
)

const emit = defineEmits<{
  submit: [values: Record<string, string>]
  cancel: []
}>()

const partitionOptions = ['dt', 'hour', 'dt,hour', 'none']
const formatOptions = ['parquet', 'orc', 'avro', 'json', 'csv']
const compressionOptions = ['zstd', 'snappy', 'gzip', 'lz4', 'none']

const form = reactive({
  表编号: props.initial.表编号 ?? '',
  来源通道: props.initial.来源通道 ?? '',
  目标路径: props.initial.目标路径 ?? '',
  保留策略: props.initial.保留策略 ?? '',
  分区规则: props.initial.分区规则 ?? 'dt',
  文件格式: props.initial.文件格式 ?? 'parquet',
  压缩类型: props.initial.压缩类型 ?? 'zstd',
  数据校验: props.initial.数据校验 ?? '',
})

function onSubmit() {
  emit('submit', { ...form })
}
</script>
