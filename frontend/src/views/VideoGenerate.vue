<template>
  <div class="video-generate">
    <div class="page-header">
      <h1 class="page-title">🎬 生成旅行视频</h1>
      <p class="page-desc">既能单独生成景区介绍，也能把当前旅程沉淀成可回看的回顾视频。</p>
    </div>

    <div v-if="tripRecapContext.tripId" class="trip-context-banner">
      <div class="trip-context-main">
        <span class="trip-context-kicker">当前旅程回顾</span>
        <strong>{{ tripContextTitle }}</strong>
        <p>{{ tripContextDescription }}</p>
      </div>
      <div class="trip-context-actions">
        <a-button size="small" @click="fillFromTripContext">带入旅程景点</a-button>
        <a-button size="small" @click="clearTripContext">清除关联</a-button>
      </div>
    </div>

    <div class="input-section">
      <a-input-search
        v-model:value="scenicName"
        placeholder="输入景区名称，如：故宫、西湖、兵马俑..."
        :enter-button="tripRecapContext.tripId ? '🎥 生成旅程回顾' : '🎥 生成视频'"
        size="large"
        :loading="isGenerating"
        @search="handleGenerate"
        :disabled="isGenerating"
      />
      <p v-if="tripRecapContext.tripId" class="input-hint">本次会把视频记录关联到当前旅程，后续可从行程详情继续回看。</p>
    </div>

    <!-- 进度展示 -->
    <div v-if="isGenerating || taskStatus" class="progress-section">
      <a-card :bordered="false" class="progress-card">
        <div class="progress-header">
          <span class="progress-title">
            <a-spin v-if="isGenerating" size="small" />
            {{ isGenerating ? '正在生成中...' : taskStatus?.status === 'done' ? '✅ 生成完成！' : taskStatus?.status === 'error' ? '❌ 生成失败' : '' }}
          </span>
          <span class="progress-percent">{{ taskStatus?.progress || 0 }}%</span>
        </div>

        <a-progress
          :percent="taskStatus?.progress || 0"
          :status="taskStatus?.status === 'error' ? 'exception' : taskStatus?.status === 'done' ? 'success' : 'active'"
          :stroke-color="{ from: '#c9a0dc', to: '#c43b3b' }"
        />

        <p class="progress-message">{{ taskStatus?.message || '准备中...' }}</p>
        <p v-if="activeTripBadge" class="progress-trip-badge">{{ activeTripBadge }}</p>

        <div class="steps-hint">
          <div :class="['step', { active: (taskStatus?.progress || 0) >= 5, done: (taskStatus?.progress || 0) >= 20 }]">
            <span class="step-icon">✍️</span> 生成脚本
          </div>
          <div :class="['step', { active: (taskStatus?.progress || 0) >= 25, done: (taskStatus?.progress || 0) >= 50 }]">
            <span class="step-icon">🔊</span> 合成语音
          </div>
          <div :class="['step', { active: (taskStatus?.progress || 0) >= 60, done: (taskStatus?.progress || 0) >= 70 }]">
            <span class="step-icon">🖼️</span> 获取图片
          </div>
          <div :class="['step', { active: (taskStatus?.progress || 0) >= 80, done: (taskStatus?.progress || 0) >= 95 }]">
            <span class="step-icon">🎬</span> 渲染视频
          </div>
        </div>
      </a-card>
    </div>

    <!-- 视频播放 -->
    <div v-if="taskStatus?.status === 'done' && videoUrl" class="video-section">
      <a-card :bordered="false" class="video-card">
        <h3>🎥 {{ currentVideoTitle || scenicName }} · {{ tripRecapContext.tripId ? '旅程回顾' : '景区介绍' }}</h3>
        <p class="guide-label">🎀 导游：红美铃</p>
        <p v-if="activeTripBadge" class="video-trip-badge">{{ activeTripBadge }}</p>
        <video
          :src="videoUrl"
          controls
          autoplay
          class="video-player"
        >
          您的浏览器不支持视频播放
        </video>
        <div class="video-actions">
          <a-button type="primary" size="large" @click="downloadVideo(videoUrl, currentVideoTitle || scenicName)">
            📥 下载视频
          </a-button>
          <a-button size="large" @click="resetForm">
            🔄 重新生成
          </a-button>
        </div>
      </a-card>
    </div>

    <div class="history-section">
      <a-card :bordered="false" class="history-card">
        <div class="history-header">
          <div>
            <h3>🕘 最近生成</h3>
            <p>刷新页面后也能回来继续预览、下载或再次生成。</p>
          </div>
          <a-button size="small" :loading="historyLoading" @click="loadHistory">
            刷新记录
          </a-button>
        </div>

        <a-empty v-if="!historyLoading && !historyItems.length" description="还没有生成记录，先试试上面的景区吧～" />

        <div v-else class="history-list">
          <div v-for="item in historyItems" :key="item.task_id" class="history-item">
            <div class="history-main">
              <div class="history-topline">
                <span class="history-name">{{ item.scenic_name || '未命名景区' }}</span>
                <span :class="['history-status', item.status]">{{ statusLabel(item.status) }}</span>
              </div>
              <div class="history-meta">
                <span>任务ID：{{ item.task_id }}</span>
                <span v-if="item.updated_at">最近更新：{{ formatTime(item.updated_at) }}</span>
              </div>
              <div v-if="historyTripBadge(item)" class="history-trip-badge">{{ historyTripBadge(item) }}</div>
              <div class="history-message">{{ historyMessage(item) }}</div>
            </div>
            <div class="history-actions">
              <a-button v-if="item.status === 'processing'" type="primary" size="small" @click="resumeHistoryItem(item)">
                继续等待
              </a-button>
              <a-button v-if="item.status === 'done' && item.video_url" type="primary" size="small" :disabled="!item.file_exists" @click="playHistoryItem(item)">
                继续预览
              </a-button>
              <a-button v-if="item.status === 'done' && item.video_url" size="small" :disabled="!item.file_exists" @click="downloadVideo(resolveVideoUrl(item.video_url), item.scenic_name)">
                下载
              </a-button>
              <a-button size="small" @click="regenerate(item.scenic_name, item)">
                再次生成
              </a-button>
              <a-popconfirm
                title="确定删除这条记录吗？"
                ok-text="删除"
                cancel-text="取消"
                @confirm="removeHistory(item.task_id)"
              >
                <a-button danger size="small">删除记录</a-button>
              </a-popconfirm>
            </div>
          </div>
        </div>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  deleteVideoHistory,
  generateVideo,
  getVideoHistory,
  getVideoStatus,
  getCurrentTripContext,
  setCurrentTripContext,
  buildCurrentTripContext,
  type VideoTaskStatus,
  type VideoHistoryItem,
} from '@/services/api'

type VideoHistoryResponse = {
  success?: boolean
  message?: string
  data?: VideoHistoryItem[]
}

type TripRecapContext = {
  tripId: string
  tripTitle?: string
  tripCity?: string
  sourceAttraction?: string
}

const route = useRoute()
const router = useRouter()
const scenicName = ref('')
const isGenerating = ref(false)
const taskStatus = ref<VideoTaskStatus | null>(null)
const videoUrl = ref<string | null>(null)
const currentVideoTitle = ref('')
const historyLoading = ref(false)
const historyItems = ref<VideoHistoryItem[]>([])
const tripRecapContext = ref<TripRecapContext>({ tripId: '' })
let pollTimer: ReturnType<typeof setInterval> | null = null

const tripContextTitle = computed(() => tripRecapContext.value.tripTitle || `${tripRecapContext.value.tripCity || '当前'}旅程`)
const tripContextDescription = computed(() => {
  if (!tripRecapContext.value.tripId) return ''
  return tripRecapContext.value.sourceAttraction
    ? `将以「${tripRecapContext.value.sourceAttraction}」为主角生成回顾视频，并把结果沉淀到这条旅程下。`
    : '本次生成会自动关联到当前旅程，后续可从旅程详情继续回看和分享。'
})
const activeTripBadge = computed(() => {
  const source = taskStatus.value || null
  if (!source?.trip_id) return ''
  const title = source.trip_title || source.trip_city || '关联旅程'
  const attraction = source.source_attraction ? ` · 景点：${source.source_attraction}` : ''
  return `🧳 已关联：${title}${attraction}`
})

function parseTripContextFromRoute() {
  const query = route.query || {}
  const currentTrip = getCurrentTripContext()
  const tripId = String(query.tripId || currentTrip?.tripId || '').trim()
  const tripTitle = String(query.tripTitle || currentTrip?.title || '').trim()
  const tripCity = String(query.tripCity || currentTrip?.city || '').trim()
  const sourceAttraction = String(query.attraction || query.sourceAttraction || '').trim()
  tripRecapContext.value = {
    tripId,
    tripTitle,
    tripCity,
    sourceAttraction,
  }
  if (tripId) {
    setCurrentTripContext(buildCurrentTripContext({
      tripId,
      title: tripTitle,
      city: tripCity,
      source: 'video-recap',
      lastView: 'video',
    }))
  }
  if (!scenicName.value.trim() && sourceAttraction) {
    scenicName.value = sourceAttraction
  }
}

function fillFromTripContext() {
  scenicName.value = tripRecapContext.value.sourceAttraction || tripRecapContext.value.tripCity || scenicName.value
}

function clearTripContext() {
  tripRecapContext.value = { tripId: '' }
  router.replace({ path: '/dashboard', query: { view: 'video' } })
}

function resolveVideoUrl(url?: string | null) {
  if (!url) return null
  if (url.startsWith('http')) return url
  return import.meta.env.VITE_API_BASE_URL
    ? `${import.meta.env.VITE_API_BASE_URL}${url}`
    : url
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function applyTaskToPanel(task: VideoTaskStatus, scenicNameValue = '') {
  scenicName.value = scenicNameValue || scenicName.value
  currentVideoTitle.value = scenicNameValue || currentVideoTitle.value || scenicName.value
  taskStatus.value = task
  videoUrl.value = resolveVideoUrl(task.video_url)
  if (task.trip_id) {
    tripRecapContext.value = {
      tripId: String(task.trip_id || '').trim(),
      tripTitle: String(task.trip_title || '').trim(),
      tripCity: String(task.trip_city || '').trim(),
      sourceAttraction: String(task.source_attraction || '').trim(),
    }
  }
}

async function loadHistory() {
  historyLoading.value = true
  try {
    const res = await getVideoHistory() as VideoHistoryResponse
    historyItems.value = Array.isArray(res?.data) ? res.data : []

    const activeItem = historyItems.value.find((item) => item.status === 'processing')
    if (!pollTimer && activeItem) {
      resumeHistoryItem(activeItem)
    }
  } catch {
    historyItems.value = []
  } finally {
    historyLoading.value = false
  }
}

async function pollVideoStatus(taskId: string, scenicTitle = scenicName.value) {
  stopPolling()
  isGenerating.value = true
  pollTimer = setInterval(async () => {
    try {
      const status = await getVideoStatus(taskId) as VideoTaskStatus
      applyTaskToPanel(status, scenicTitle)

      if (status.status === 'done') {
        stopPolling()
        isGenerating.value = false
        videoUrl.value = resolveVideoUrl(status.video_url)
        await loadHistory()
      } else if (status.status === 'error') {
        stopPolling()
        isGenerating.value = false
        await loadHistory()
      }
    } catch (err) {
      console.error('Poll error:', err)
    }
  }, 3000)
}

async function handleGenerate() {
  const name = scenicName.value.trim()
  if (!name) return

  isGenerating.value = true
  taskStatus.value = null
  videoUrl.value = null
  currentVideoTitle.value = name

  try {
    const res = await generateVideo(name, {
      tripId: tripRecapContext.value.tripId,
      tripTitle: tripRecapContext.value.tripTitle,
      tripCity: tripRecapContext.value.tripCity,
      sourceAttraction: tripRecapContext.value.sourceAttraction || name,
    }) as VideoTaskStatus
    const taskId = res.task_id || ''
    applyTaskToPanel(res, name)
    await loadHistory()
    if (taskId) {
      await pollVideoStatus(taskId, name)
    }
  } catch (err: any) {
    isGenerating.value = false
    taskStatus.value = {
      status: 'error',
      message: err?.response?.data?.detail || err?.message || '请求失败',
      progress: 0,
    }
  }
}

function downloadVideo(url?: string | null, title = '') {
  const finalUrl = resolveVideoUrl(url || videoUrl.value)
  if (!finalUrl) return
  const a = document.createElement('a')
  a.href = finalUrl
  a.download = `${title || scenicName.value || '景区'}_介绍.mp4`
  a.click()
}

function resetForm() {
  scenicName.value = tripRecapContext.value.sourceAttraction || ''
  taskStatus.value = null
  videoUrl.value = null
  currentVideoTitle.value = ''
  isGenerating.value = false
  stopPolling()
}

function playHistoryItem(item: VideoHistoryItem) {
  applyTaskToPanel({
    task_id: item.task_id,
    status: item.status,
    progress: item.progress,
    message: item.message,
    video_url: item.video_url,
    trip_id: item.trip_id,
    trip_title: item.trip_title,
    trip_city: item.trip_city,
    source_attraction: item.source_attraction,
  }, item.scenic_name || '')
  isGenerating.value = false
  stopPolling()
}

function resumeHistoryItem(item: VideoHistoryItem) {
  applyTaskToPanel({
    task_id: item.task_id,
    status: item.status,
    progress: item.progress,
    message: item.message,
    video_url: item.video_url,
    trip_id: item.trip_id,
    trip_title: item.trip_title,
    trip_city: item.trip_city,
    source_attraction: item.source_attraction,
  }, item.scenic_name || '')
  pollVideoStatus(item.task_id, item.scenic_name || scenicName.value)
}

function regenerate(name: string, item?: VideoHistoryItem) {
  scenicName.value = name || ''
  if (item?.trip_id) {
    tripRecapContext.value = {
      tripId: String(item.trip_id || '').trim(),
      tripTitle: String(item.trip_title || '').trim(),
      tripCity: String(item.trip_city || '').trim(),
      sourceAttraction: String(item.source_attraction || name || '').trim(),
    }
  }
  handleGenerate()
}

async function removeHistory(taskId: string) {
  try {
    const res = await deleteVideoHistory(taskId)
    if (taskStatus.value?.task_id === taskId) {
      resetForm()
    }
    message.success(res?.message || '已删除该视频记录')
    await loadHistory()
  } catch (err: any) {
    message.error(err?.response?.data?.detail || err?.message || '删除失败')
  }
}

function statusLabel(status: string) {
  if (status === 'done') return '已完成'
  if (status === 'error') return '失败'
  return '生成中'
}

function historyMessage(item: VideoHistoryItem) {
  if (item.status === 'done' && item.file_exists === false) {
    return '视频文件已失效，可再次生成新的版本。'
  }
  return item.message || '暂无说明'
}

function historyTripBadge(item: VideoHistoryItem) {
  if (!item.trip_id) return ''
  const title = item.trip_title || item.trip_city || '关联旅程'
  const attraction = item.source_attraction ? ` · ${item.source_attraction}` : ''
  return `🧳 ${title}${attraction}`
}

function formatTime(value?: string) {
  if (!value) return ''
  return value.replace('T', ' ')
}

onMounted(() => {
  parseTripContextFromRoute()
  loadHistory()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.video-generate {
  max-width: 900px;
  margin: 0 auto;
  padding: 32px 24px;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}
.page-title {
  font-size: 28px;
  font-weight: 700;
  color: #5c3a21;
  margin: 0 0 8px;
  font-family: 'STKaiti', '楷体', 'KaiTi', serif;
}
.page-desc {
  font-size: 15px;
  color: #9a8a7a;
  margin: 0;
}

.input-section {
  margin-bottom: 24px;
}
.trip-context-banner {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  padding: 16px 18px;
  margin-bottom: 18px;
  border-radius: 14px;
  background: linear-gradient(135deg, #fff7ef, #fff0f4);
  border: 1px solid #f1d8c8;
}
.trip-context-main {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.trip-context-kicker {
  font-size: 12px;
  color: #a56a43;
  letter-spacing: 0.08em;
}
.trip-context-main strong {
  color: #5c3a21;
  font-size: 18px;
}
.trip-context-main p,
.input-hint,
.progress-trip-badge,
.video-trip-badge,
.history-trip-badge {
  margin: 0;
  color: #7a5a45;
  font-size: 13px;
}
.trip-context-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.input-hint {
  margin-top: 10px;
}
.input-section :deep(.ant-input-search-button) {
  background: linear-gradient(135deg, #c43b3b, #a04040);
  border: none;
  font-weight: 600;
}

.progress-section {
  margin-bottom: 24px;
}
.progress-card,
.video-card,
.history-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.progress-header,
.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  gap: 12px;
}
.progress-title {
  font-size: 16px;
  font-weight: 600;
  color: #5c3a21;
}
.progress-percent {
  font-size: 14px;
  color: #8b4513;
  font-weight: 500;
}
.progress-message {
  margin-top: 12px;
  color: #6b5344;
  font-size: 14px;
}

.steps-hint {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
  gap: 8px;
  flex-wrap: wrap;
}
.step {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #c0b0a0;
  padding: 6px 12px;
  border-radius: 20px;
  background: #f8f4ef;
  transition: all 0.3s;
}
.step.active {
  color: #8b4513;
  background: #fef0e8;
  font-weight: 500;
}
.step.done {
  color: #5c8a5c;
  background: #f0f8f0;
}
.step-icon {
  font-size: 16px;
}

.video-section,
.history-section {
  margin-bottom: 24px;
}
.video-card {
  text-align: center;
}
.video-card h3,
.history-header h3 {
  color: #5c3a21;
  font-family: 'STKaiti', '楷体', 'KaiTi', serif;
  margin: 0;
}
.history-header p {
  margin: 6px 0 0;
  color: #9a8a7a;
  font-size: 13px;
}
.guide-label {
  font-size: 14px;
  color: #8b4513;
  margin-bottom: 16px;
}
.video-player {
  width: 100%;
  max-height: 480px;
  border-radius: 8px;
  background: #000;
}
.video-actions,
.history-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.history-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 16px;
  border: 1px solid #f0e3d6;
  border-radius: 12px;
  background: #fffaf6;
}
.history-main {
  flex: 1;
  min-width: 0;
}
.history-topline {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.history-name {
  font-size: 16px;
  font-weight: 700;
  color: #5c3a21;
}
.history-status {
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}
.history-status.done {
  color: #2e7d32;
  background: #edf7ed;
}
.history-status.error {
  color: #c43b3b;
  background: #fff1f0;
}
.history-status.processing {
  color: #8b4513;
  background: #fff7e6;
}
.history-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  color: #9a8a7a;
  font-size: 12px;
  margin-bottom: 6px;
}
.history-message {
  color: #6b5344;
  font-size: 14px;
}

@media (max-width: 767px) {
  .trip-context-banner,
  .history-item,
  .progress-header,
  .history-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .video-generate {
    padding: 16px 12px;
  }
  .video-actions,
  .history-actions {
    justify-content: flex-start;
  }
}
</style>
