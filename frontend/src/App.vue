<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const characterFile = ref(null)
const characterPreview = ref('')
const referenceFile = ref(null)
const referencePreview = ref('')

const expressionIntensity = ref(3)
const bodyControl = ref(true)
const ratio = ref('720:1280')
const seed = ref('')

const taskId = ref('')
const taskStatus = ref('IDLE')
const taskDetail = ref('')
const resultUrl = ref('')
const submitting = ref(false)
let pollTimer = null

const terminalStatuses = new Set(['SUCCEEDED', 'FAILED', 'CANCELED', 'CANCELLED'])

const statusLabel = computed(() => {
  const map = {
    IDLE: '等待素材',
    UPLOADING: '上传素材',
    SUBMITTED: '已提交',
    PENDING: '排队中',
    THROTTLED: '排队中',
    RUNNING: '生成中',
    SUCCEEDED: '生成完成',
    FAILED: '生成失败',
    CANCELED: '已取消',
    CANCELLED: '已取消',
  }
  return map[taskStatus.value] || taskStatus.value
})

const canGenerate = computed(
  () => characterFile.value && referenceFile.value && !submitting.value
)

function setPreview(kind, file) {
  if (!file) return

  if (kind === 'character') {
    if (characterPreview.value) URL.revokeObjectURL(characterPreview.value)
    characterFile.value = file
    characterPreview.value = URL.createObjectURL(file)
  } else {
    if (referencePreview.value) URL.revokeObjectURL(referencePreview.value)
    referenceFile.value = file
    referencePreview.value = URL.createObjectURL(file)
  }
}

function onCharacterChange(event) {
  setPreview('character', event.target.files?.[0])
}

function onReferenceChange(event) {
  setPreview('reference', event.target.files?.[0])
}

function resetResult() {
  taskId.value = ''
  taskStatus.value = 'IDLE'
  taskDetail.value = ''
  resultUrl.value = ''
  if (pollTimer) {
    clearTimeout(pollTimer)
    pollTimer = null
  }
}

async function generate() {
  if (!canGenerate.value) return

  resetResult()
  submitting.value = true
  taskStatus.value = 'UPLOADING'
  taskDetail.value = '正在上传角色图与动作视频…'

  const form = new FormData()
  form.append('character_image', characterFile.value)
  form.append('reference_video', referenceFile.value)
  form.append('expression_intensity', String(expressionIntensity.value))
  form.append('body_control', String(bodyControl.value))
  form.append('ratio', ratio.value)
  if (seed.value.trim()) form.append('seed', seed.value.trim())

  try {
    const response = await fetch(`${API_BASE}/api/tasks`, {
      method: 'POST',
      body: form,
    })

    const payload = await response.json()
    if (!response.ok) {
      throw new Error(payload.detail || '提交失败')
    }

    taskId.value = payload.id
    taskStatus.value = 'SUBMITTED'
    taskDetail.value = 'Runway 已接收任务'
    schedulePoll(1200)
  } catch (error) {
    taskStatus.value = 'FAILED'
    taskDetail.value = error.message || '提交失败'
  } finally {
    submitting.value = false
  }
}

function schedulePoll(delay = 5200) {
  if (pollTimer) clearTimeout(pollTimer)
  pollTimer = setTimeout(pollTask, delay)
}

async function pollTask() {
  if (!taskId.value) return

  try {
    const response = await fetch(`${API_BASE}/api/tasks/${taskId.value}`)
    const payload = await response.json()

    if (!response.ok) {
      throw new Error(payload.detail || '状态查询失败')
    }

    taskStatus.value = payload.status || 'UNKNOWN'
    taskDetail.value =
      payload.failure ||
      payload.failureCode ||
      (taskStatus.value === 'SUCCEEDED' ? '结果已就绪' : 'Runway 正在处理')

    if (taskStatus.value === 'SUCCEEDED') {
      const output = Array.isArray(payload.output) ? payload.output : []
      resultUrl.value = output[0] || ''
    }

    if (!terminalStatuses.has(taskStatus.value)) {
      schedulePoll(5200 + Math.floor(Math.random() * 900))
    }
  } catch (error) {
    taskDetail.value = error.message || '状态查询暂时失败'
    schedulePoll(8000)
  }
}

function randomSeed() {
  seed.value = String(Math.floor(Math.random() * 4294967295))
}

onBeforeUnmount(() => {
  if (pollTimer) clearTimeout(pollTimer)
  if (characterPreview.value) URL.revokeObjectURL(characterPreview.value)
  if (referencePreview.value) URL.revokeObjectURL(referencePreview.value)
})
</script>

<template>
  <main class="app-shell">
    <section class="hero">
      <div class="eyebrow">RUNWAY · ACT-TWO</div>
      <h1>动作迁移</h1>
      <p>角色参考 + 动作视频，手机直接提交生成。</p>
    </section>

    <section class="upload-grid">
      <label class="upload-card">
        <input type="file" accept="image/*" @change="onCharacterChange" />
        <div v-if="!characterPreview" class="empty-state">
          <span class="plus">＋</span>
          <strong>角色参考图</strong>
          <small>从相册选择图片</small>
        </div>
        <img v-else :src="characterPreview" alt="角色参考预览" />
        <div v-if="characterPreview" class="file-badge">角色图</div>
      </label>

      <label class="upload-card">
        <input type="file" accept="video/*" @change="onReferenceChange" />
        <div v-if="!referencePreview" class="empty-state">
          <span class="plus">＋</span>
          <strong>动作参考视频</strong>
          <small>建议 3–30 秒</small>
        </div>
        <video v-else :src="referencePreview" muted playsinline />
        <div v-if="referencePreview" class="file-badge">动作视频</div>
      </label>
    </section>

    <section class="panel controls">
      <div class="control-row">
        <div>
          <span class="label">表情强度</span>
          <small>Expression Intensity</small>
        </div>
        <div class="stepper">
          <button type="button" @click="expressionIntensity = Math.max(1, expressionIntensity - 1)">−</button>
          <strong>{{ expressionIntensity }}</strong>
          <button type="button" @click="expressionIntensity = Math.min(5, expressionIntensity + 1)">＋</button>
        </div>
      </div>

      <div class="control-row">
        <div>
          <span class="label">身体动作</span>
          <small>Body Control</small>
        </div>
        <button
          type="button"
          class="switch"
          :class="{ active: bodyControl }"
          @click="bodyControl = !bodyControl"
          :aria-pressed="bodyControl"
        >
          <span></span>
        </button>
      </div>

      <div class="field-group">
        <label for="ratio">输出比例</label>
        <select id="ratio" v-model="ratio">
          <option value="720:1280">9:16 · 720×1280</option>
          <option value="832:1104">3:4 · 832×1104</option>
          <option value="960:960">1:1 · 960×960</option>
          <option value="1104:832">4:3 · 1104×832</option>
          <option value="1280:720">16:9 · 1280×720</option>
          <option value="1584:672">超宽 · 1584×672</option>
        </select>
      </div>

      <div class="field-group">
        <div class="field-heading">
          <label for="seed">Seed</label>
          <button type="button" class="text-button" @click="randomSeed">随机</button>
        </div>
        <input id="seed" v-model="seed" inputmode="numeric" placeholder="留空 = 自动随机" />
      </div>
    </section>

    <button class="generate-button" :disabled="!canGenerate" @click="generate">
      <span v-if="submitting" class="spinner"></span>
      {{ submitting ? '正在提交…' : '开始生成' }}
    </button>

    <section v-if="taskStatus !== 'IDLE'" class="panel status-panel">
      <div class="status-top">
        <div>
          <small>任务状态</small>
          <strong>{{ statusLabel }}</strong>
        </div>
        <span class="status-dot" :class="taskStatus.toLowerCase()"></span>
      </div>

      <p>{{ taskDetail }}</p>
      <code v-if="taskId">{{ taskId }}</code>

      <div v-if="!terminalStatuses.has(taskStatus)" class="progress-track">
        <span></span>
      </div>
    </section>

    <section v-if="resultUrl" class="result-card">
      <div class="result-heading">
        <div>
          <small>OUTPUT</small>
          <h2>生成结果</h2>
        </div>
        <span>完成</span>
      </div>

      <video :src="resultUrl" controls playsinline preload="metadata"></video>

      <div class="result-actions">
        <a :href="resultUrl" target="_blank" rel="noopener">全屏打开</a>
        <a :href="resultUrl" download>下载视频</a>
      </div>
    </section>

    <p class="footnote">API Key 仅保存在后端，不会发送到手机前端。</p>
  </main>
</template>
