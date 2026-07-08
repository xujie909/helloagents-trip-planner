<template>
  <div class="history-container">
    <div class="history-header hero-header">
      <div>
        <h1 class="history-title">📋 旅行历史记录</h1>
        <p class="history-subtitle">把每次出发的行程、预算、清单、笔记和景点足迹收成一份完整旅程档案。</p>
      </div>
      <div class="history-header-badges">
        <span class="history-badge">{{ trips.length }} 条旅行记录</span>
        <span class="history-badge soft">{{ attractionStates.length }} 条景点足迹</span>
      </div>
    </div>

  <div v-if="!loading && currentTripSummary" class="current-trip-banner">
      <div>
        <div class="current-trip-banner-kicker">当前旅程</div>
        <div class="current-trip-banner-title">{{ currentTripSummary.title }}</div>
        <p class="current-trip-banner-desc">
          {{ currentTripSummary.city || '旅行中' }}
          <template v-if="currentTripSummary.startDate"> · {{ currentTripSummary.startDate }}</template>
          <template v-if="currentTripSummary.updatedAtLabel"> · 最近续接于 {{ currentTripSummary.updatedAtLabel }}</template>
        </p>
      </div>
      <div class="current-trip-banner-actions">
        <button class="current-trip-banner-btn primary" @click="continueCurrentTrip">继续执行</button>
        <button class="current-trip-banner-btn" @click="clearCurrentTripSelection">清除当前旅程</button>
      </div>
    </div>

    <div v-if="!loading && (hasTripRecords || hasStateRecords)" class="history-overview-strip">
      <div class="history-overview-card">
        <span>🏙️ 已记录城市</span>
        <strong>{{ groups.length }} 座</strong>
        <p>旅行记录已覆盖 {{ groups.length }} 个目的地城市</p>
      </div>
      <div class="history-overview-card">
        <span>📆 累计行程天数</span>
        <strong>{{ totalTripDays }} 天</strong>
        <p>所有旅行记录累计沉淀的出发时长</p>
      </div>
      <div class="history-overview-card">
        <span>📝 有笔记记录</span>
        <strong>{{ notesTripCount }} 条</strong>
        <p>已经留下文字或附件记录的旅程</p>
      </div>
      <div class="history-overview-card">
        <span>✅ 已完成旅程</span>
        <strong>{{ completedTripCount }} 条</strong>
        <p>行程手札完成度达到 100% 的记录</p>
      </div>
    </div>

    <div v-if="loading" class="loading-wrapper">
      <div class="think-seal">行</div>
      <div class="think-dots"><span></span><span></span><span></span></div>
      <p class="think-text">行知正在整理行囊...</p>
    </div>

      <div v-else-if="!hasTripRecords && !hasStateRecords" class="empty-state">
        <div class="empty-seal">囊</div>
        <p class="empty-title">行囊尚空</p>
        <p class="empty-desc">尚未留下旅途印记，何不即刻启程？</p>
        <button class="empty-btn" @click="emit('goPlan')">📜 去规划一趟旅程</button>
      </div>

      <div v-else-if="!hasTripRecords && hasStateRecords" class="empty-state soft-empty-state">
        <div class="empty-seal">迹</div>
        <p class="empty-title">已有景点足迹，还没沉淀成旅程</p>
        <p class="empty-desc">你已经收藏或打卡过景点了，现在可以去生成一条完整旅行记录，把预算、清单、笔记一起收进来。</p>
        <button class="empty-btn" @click="emit('goPlan')">📜 去补一条旅行记录</button>
      </div>

      <div v-else>
      <section v-if="recordSections.length" class="favorites-panel">
        <div class="favorites-header">
          <div>
            <h2 class="favorites-title">💖 我的收藏与足迹</h2>
            <p class="favorites-subtitle">收藏、想去、已去和打卡都收进旅行记录里，方便统一查看。</p>
          </div>
          <span class="favorites-total">{{ attractionStates.length }} 条景点记录</span>
        </div>

        <div class="favorites-grid">
          <div v-for="section in recordSections" :key="section.key" class="favorites-card">
            <div class="favorites-card-head">
              <span class="favorites-emoji">{{ section.emoji }}</span>
              <div>
                <h3>{{ section.title }}</h3>
                <p>{{ section.description }}</p>
              </div>
              <span class="favorites-badge">{{ section.items.length }}</span>
            </div>
            <div class="favorites-list">
              <div v-for="item in section.items" :key="`${section.key}-${item.name}-${item.city}`" class="favorites-item favorites-item-clickable" @click="openStateAttraction(item)">
                <div class="favorites-item-main">
                  <span class="favorites-item-name">{{ item.name }}</span>
                  <span v-if="item.city" class="favorites-item-city">{{ item.city }}</span>
                </div>
                <span class="favorites-item-time">{{ item.updated_at || '刚刚记录' }}</span>
                <span class="favorites-item-action">点击查看景点详情 →</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 按城市分组 -->
      <div v-for="group in groups" :key="group.city" class="city-group">
        <div class="city-group-header">
          <div class="city-group-title">
            <span class="city-folder">📁</span>
            <span class="city-name">{{ group.city }}</span>
            <span class="city-count">{{ group.trips.length }} 条记录</span>
          </div>
          <div class="city-group-stats">
            <span class="city-stat-chip">📝 {{ getGroupNotesCount(group.trips) }} 条有笔记</span>
            <span class="city-stat-chip done">✅ {{ getGroupCompletedCount(group.trips) }} 条已完成</span>
          </div>
        </div>

        <a-card v-for="trip in group.trips" :key="trip.id" class="trip-card" hoverable>
          <div class="trip-card-body">
            <div class="trip-info" @click="viewDetail(trip.id)">
              <div class="trip-title-row">
                <h3 class="trip-title">{{ trip.title || trip.start_date + ' ' + trip.city }}</h3>
                <span class="trip-status-pill" :class="trip.progress>=100 ? 'done' : 'going'">{{ trip.progress>=100 ? '已完成' : '进行中' }}</span>
              </div>
              <div class="trip-meta">
                <span class="meta-item">📆 {{ trip.days }}天</span>
                <span class="meta-item">🕐 {{ trip.created_at }}</span>
                <span v-if="trip.task_total>0" class="meta-tag">{{ trip.progress>=100?'✅':'📍' }} {{ trip.task_done }}/{{ trip.task_total }}</span>
                <span v-if="trip.has_notes" class="meta-tag">📝 有笔记</span>
                <span v-if="trip.has_images" class="meta-tag">🖼️ {{ trip.image_count }}</span>
                <span v-if="trip.checklist_summary?.total" class="meta-tag prep">🧳 行前 {{ trip.checklist_summary.done }}/{{ trip.checklist_summary.total }}</span>
              </div>
              <div class="trip-summary-row" v-if="trip.budget_summary?.total_planned || trip.budget_summary?.total_actual || trip.checklist_summary?.total">
                <span v-if="trip.budget_summary?.total_planned || trip.budget_summary?.total_actual" class="summary-chip budget">
                  💰 预算 {{ formatMoney(trip.budget_summary?.total_planned || 0) }} / 花费 {{ formatMoney(trip.budget_summary?.total_actual || 0) }}
                </span>
                <span v-if="trip.checklist_summary?.total" class="summary-chip checklist">
                  ✅ 清单 {{ trip.checklist_summary.progress }}%
                </span>
              </div>
              <p class="trip-budget-note">{{ getBudgetStatusText(trip) }}</p>
              <div class="trip-progress" v-if="trip.task_total>0">
                <div class="trip-progress-head">
                  <span>当前完成度</span>
                  <strong>{{ trip.progress }}%</strong>
                </div>
                <div class="trip-progress-bar"><div class="trip-progress-fill" :style="{width:trip.progress+'%'}" :class="{done:trip.progress>=100}"></div></div>
              </div>
              <p class="trip-preview" v-if="trip.preview">{{ trip.preview }}</p>
            </div>
            <div class="trip-actions">
              <a-button type="text" @click="setAsCurrentTrip(trip)">{{ isCurrentTrip(trip.id) ? '当前旅程' : '设为当前旅程' }}</a-button>
              <a-button type="text" @click="continueTrip(trip)">继续执行</a-button>
              <a-button type="text" @click="viewDetail(trip.id)">查看</a-button>
              <a-button type="text" @click="openNotes(trip.id)">{{ trip.has_notes ? '📝 笔记' : '🖊️ 写笔记' }}</a-button>
              <a-popconfirm title="确定删除？" ok-text="删除" cancel-text="取消" @confirm="handleDelete(trip.id)">
                <a-button type="text" danger>删除</a-button>
              </a-popconfirm>
            </div>
          </div>
        </a-card>
      </div>
    </div>

    <!-- 景点详情弹窗（收藏/足迹入口） -->
    <a-modal v-model:open="detailVisible" :title="attrName || detailTitle || '景点详情'" width="900px" :footer="null" @cancel="closeAttractionDetail" :bodyStyle="{padding:0}">
      <div v-if="detailTrip" class="detail-content">
        <div v-if="tripActionFeedback" :class="['trip-action-feedback', tripActionFeedback.type]">
          <div class="trip-action-feedback-main">
            <strong>{{ tripActionFeedback.title }}</strong>
            <p>{{ tripActionFeedback.description }}</p>
          </div>
          <button v-if="tripActionFeedback.tripId" class="trip-action-feedback-btn" @click="viewDetail(tripActionFeedback.tripId)">
            打开这条旅行记录
          </button>
        </div>

        <div v-if="attrName" class="attraction-panel-shell">
          <div v-if="attrLoading" class="attr-loading">
            <div class="think-seal">行</div>
            <div class="think-dots"><span></span><span></span><span></span></div>
            <p class="think-text">行知正在思考中...</p>
          </div>
          <div v-else class="attr-detail-wrap">
            <div class="attr-hero-card">
              <div v-if="attrImage" class="attr-hero-media">
                <img :src="attrImage" :alt="attrName" class="attr-hero-img" @click="previewImage=attrImage;previewVisible=true" />
              </div>
              <div v-else class="attr-hero-empty">暂未获取到景点图片</div>
              <div class="attr-hero-main">
                <div class="attr-hero-head">
                  <div>
                    <h3>{{ attrName }}</h3>
                    <p>{{ attrCity || detailTrip?.city || '旅行记录' }}</p>
                  </div>
                  <span v-if="attrSource" class="attr-source">{{ attrSource }}</span>
                </div>
                <div v-if="attrMeta.address || attrMeta.type || attrMeta.weather || attrMeta.tel || attrMeta.openTime || attrMeta.locationText" class="attr-meta-grid">
                  <div v-if="attrMeta.address" class="attr-meta-item">
                    <span class="attr-meta-label">地址</span>
                    <span class="attr-meta-value">{{ attrMeta.address }}</span>
                  </div>
                  <div v-if="attrMeta.type" class="attr-meta-item">
                    <span class="attr-meta-label">类型</span>
                    <span class="attr-meta-value">{{ attrMeta.type }}</span>
                  </div>
                  <div v-if="attrMeta.weather" class="attr-meta-item">
                    <span class="attr-meta-label">天气</span>
                    <span class="attr-meta-value">{{ attrMeta.weather }}</span>
                  </div>
                  <div v-if="attrMeta.tel" class="attr-meta-item">
                    <span class="attr-meta-label">电话</span>
                    <span class="attr-meta-value">{{ attrMeta.tel }}</span>
                  </div>
                  <div v-if="attrMeta.openTime" class="attr-meta-item">
                    <span class="attr-meta-label">开放时间</span>
                    <span class="attr-meta-value">{{ attrMeta.openTime }}</span>
                  </div>
                  <div v-if="attrMeta.locationText" class="attr-meta-item">
                    <span class="attr-meta-label">坐标</span>
                    <span class="attr-meta-value">{{ attrMeta.locationText }}</span>
                  </div>
                </div>
                <div v-if="attrMeta.lat !== null && attrMeta.lng !== null" class="attr-map-row">
                  <button class="attr-map-btn" @click="openAttractionMap">📍 在地图中打开这个景点</button>
                </div>
                <div class="attr-quick-actions">
                  <div class="attr-action-card">
                    <span class="attr-action-label">用这个景点新建旅行记录</span>
                    <input v-model="quickCreateDate" type="date" class="attr-action-input" />
                    <button class="attr-action-btn primary" :disabled="tripActionLoading" @click="createTripFromCurrentAttraction">
                      {{ tripActionLoading ? '创建中...' : '＋ 新建旅行记录' }}
                    </button>
                  </div>
                  <div class="attr-action-card">
                    <span class="attr-action-label">加入已有行程</span>
                    <select v-model="selectedTripId" class="attr-action-select">
                      <option value="">请选择一个旅行记录</option>
                      <option v-for="trip in tripOptions" :key="trip.id" :value="trip.id">
                        {{ trip.title || `${trip.start_date} ${trip.city}` }}
                        <template v-if="isSameTrip(trip.id)">（当前正在查看）</template>
                      </option>
                    </select>
                    <select v-model="selectedTripDayIndex" class="attr-action-select" :disabled="!selectedTripId || !selectedTripDayOptions.length">
                      <option v-if="!selectedTripDayOptions.length" :value="0">默认加入第1天</option>
                      <option v-for="day in selectedTripDayOptions" :key="day.value" :value="day.value">
                        {{ day.label }}
                      </option>
                    </select>
                    <button class="attr-action-btn" :disabled="tripActionLoading || !selectedTripId" @click="addCurrentAttractionToTrip">
                      {{ tripActionLoading ? '加入中...' : '加入这个行程' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="attrIntro" class="attr-intro" v-html="renderMd(attrIntro)"></div>
            <div v-else class="attr-empty-intro">暂时还没有拿到这处景点的详细介绍。</div>
          </div>
        </div>
      </div>
    </a-modal>

    <!-- 旅行笔记弹窗 - 备忘录风格 -->
    <a-modal v-model:open="notesVisible" width="720px" :footer="null" @cancel="notesVisible=false" :bodyStyle="{padding:0}" wrapClassName="memo-modal">
      <div v-if="notesTrip" class="memo-wrap">
        <div class="memo-head">
          <div class="memo-head-icon">📝</div>
          <div class="memo-head-text">
            <h3>{{ notesTrip.title || notesTrip.start_date + ' ' + notesTrip.city }}</h3>
            <span>旅行笔记 · 记录此刻心情</span>
          </div>
        </div>
        <textarea v-model="notesText" class="memo-area" placeholder="写下你的旅行感悟...&#10;&#10;这里的风景让我想起...&#10;今天遇到了一件有趣的事...&#10;不知下次再来会是何时..."></textarea>

        <!-- 附件区 -->
        <div class="memo-attach">
          <span class="attach-label">📎 附件</span>
          <div class="attach-list">
            <div v-for="(f,i) in notesFiles" :key="i" :class="['attach-item', f.type]">
              <span class="attach-type">{{ f.type==='image'?'🖼️':f.type==='video'?'🎬':'🎙️' }}</span>
              <span class="attach-name">{{ f.name }}</span>
              <span class="attach-size">{{ formatSizeFromData(f) }}</span>
              <span class="attach-del" @click="notesFiles.splice(i,1)">✕</span>
            </div>
          </div>
          <div class="attach-btns">
            <label class="attach-btn"><input type="file" accept="image/*" @change="e=>addFile(e,'image')" hidden />🖼️ 图片</label>
            <label class="attach-btn"><input type="file" accept="video/*" @change="e=>addFile(e,'video')" hidden />🎬 视频</label>
            <button class="attach-btn" @click="toggleRecord" :class="{recording:isRecording}">{{ isRecording ? '🔴 录音中' : '🎙️ 语音' }}</button>
          </div>
        </div>

        <div class="memo-foot">
          <span class="memo-hint">✍️ 所思所感，皆可落笔</span>
          <button class="memo-save" @click="saveNotes" :disabled="notesSaving">{{ notesSaving ? '保存中...' : '💾 保存笔记' }}</button>
        </div>
      </div>
      <!-- 浮动AI助手 -->
      <div class="detail-ai" v-if="notesTrip" @click="fetchTripSuggestion">
        <div class="detail-ai-bubble" v-if="tripSuggestion">{{ tripSuggestion }}</div>
        <div class="detail-ai-btn"><span>🤖</span></div>
      </div>
    </a-modal>

    <!-- 图片预览 -->
    <a-modal v-model:open="previewVisible" :footer="null" width="80vw" @cancel="previewVisible = false">
      <img :src="previewImage" style="width:100%; max-height:80vh; object-fit:contain;" />
    </a-modal>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  getHistory,
  getHistoryDetail,
  updateHistory,
  deleteHistory,
  getAttractionDetail,
  getTripSuggestion,
  listAttractionStates,
  addAttractionToTrip,
  createTripWithAttraction,
  buildCurrentTripContext,
  getCurrentTripContext,
  setCurrentTripContext,
  clearCurrentTripContext,
} from '@/services/api'
import { message } from 'ant-design-vue'

const emit = defineEmits<{ goPlan: [] }>()
const router = useRouter()

interface TripSummary {
  id: string; city: string; start_date: string; title: string;
  created_at: string; updated_at: string;
  has_notes: boolean; has_images: boolean; image_count: number;
  days: number; task_done: number; task_total: number; progress: number; preview: string;
  budget_summary?: BudgetSummary
  checklist_summary?: ChecklistSummary
}

interface BudgetTypeSummary {
  label: string
  planned: number
  actual: number
  count: number
}

interface BudgetSummary {
  total_planned: number
  total_actual: number
  difference: number
  is_over_budget: boolean
  by_type?: Record<string, BudgetTypeSummary>
}

interface ChecklistSummary {
  total: number
  done: number
  progress: number
}

interface AttractionStateRecord {
  name: string
  city: string
  favorite: boolean
  want_to_go: boolean
  visited: boolean
  checked_in: boolean
  updated_at: string
}

interface AttractionQuickPayload {
  name: string
  city?: string
  intro?: string
  image?: string
  location?: { lat?: number | null; lng?: number | null } | null
}

interface AttractionMetaInfo {
  address: string
  type: string
  tel: string
  weather: string
  openTime: string
  locationText: string
  lat: number | null
  lng: number | null
}

interface TripDayOption {
  value: number
  label: string
}

interface TripActionFeedback {
  type: 'create' | 'add' | 'duplicate'
  title: string
  description: string
  tripId: string
}

const trips = ref<TripSummary[]>([])
const attractionStates = ref<AttractionStateRecord[]>([])
const loading = ref(true)
const currentTripContext = ref(getCurrentTripContext())

function syncCurrentTripState() {
  currentTripContext.value = getCurrentTripContext()
}

function formatCurrentTripTime(value = '') {
  const date = value ? new Date(value) : null
  if (!date || Number.isNaN(date.getTime())) return ''
  return `${date.getMonth() + 1}月${date.getDate()}日 ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function buildTripTitle(trip?: Partial<TripSummary> | null) {
  if (!trip) return '当前旅程'
  return trip.title || `${trip.start_date || '这次'} ${trip.city || '旅行'}`
}

const currentTripSummary = computed(() => {
  const current = currentTripContext.value
  if (!current?.tripId) return null
  const matchedTrip = trips.value.find(item => item.id === current.tripId)
  return {
    tripId: current.tripId,
    title: matchedTrip?.title || current.title || buildTripTitle({
      title: current.title || '',
      start_date: current.startDate || '',
      city: current.city || '',
    }),
    city: matchedTrip?.city || current.city || '',
    startDate: matchedTrip?.start_date || current.startDate || '',
    updatedAtLabel: formatCurrentTripTime(current.updatedAt || matchedTrip?.updated_at || ''),
  }
})

const hasTripRecords = computed(() => trips.value.length > 0)
const hasStateRecords = computed(() => attractionStates.value.length > 0)

const totalTripDays = computed(() => trips.value.reduce((sum, trip) => sum + Number(trip.days || 0), 0))
const notesTripCount = computed(() => trips.value.filter(trip => trip.has_notes || trip.has_images).length)
const completedTripCount = computed(() => trips.value.filter(trip => trip.task_total > 0 && trip.progress >= 100).length)

const recordSections = computed(() => {
  const source = attractionStates.value
  const sections = [
    {
      key: 'favorite',
      title: '我的收藏',
      emoji: '💖',
      description: '留下最想反复回看的景点。',
      items: source.filter(item => item.favorite),
    },
    {
      key: 'want_to_go',
      title: '想去清单',
      emoji: '🧭',
      description: '下一次出发前先来这里挑目的地。',
      items: source.filter(item => item.want_to_go),
    },
    {
      key: 'visited',
      title: '已去足迹',
      emoji: '👣',
      description: '走过的地方都会沉淀成旅行印记。',
      items: source.filter(item => item.visited),
    },
    {
      key: 'checked_in',
      title: '打卡完成',
      emoji: '📍',
      description: '已经完成现场打卡的景点。',
      items: source.filter(item => item.checked_in),
    },
  ]
  return sections.filter(section => section.items.length > 0)
})

// 按城市分组
const groups = computed(() => {
  const map: Record<string, TripSummary[]> = {}
  for (const t of trips.value) {
    if (!map[t.city]) map[t.city] = []
    map[t.city].push(t)
  }
  return Object.entries(map).map(([city, trips]) => ({ city, trips }))
})

function getGroupNotesCount(groupTrips: TripSummary[]) {
  return groupTrips.filter(trip => trip.has_notes || trip.has_images).length
}

function getGroupCompletedCount(groupTrips: TripSummary[]) {
  return groupTrips.filter(trip => trip.task_total > 0 && trip.progress >= 100).length
}

function getBudgetStatusText(trip: TripSummary) {
  const summary = trip.budget_summary
  if (!summary) return '暂无预算记录'

  const planned = Number(summary.total_planned || 0)
  const actual = Number(summary.total_actual || 0)
  const diff = Number(summary.difference || 0)

  if (!planned && !actual) return '暂无预算记录'
  if (!planned && actual) return `已记录花费 ${formatMoney(actual)}，暂未填写预算`
  if (summary.is_over_budget) return `当前已超支 ${formatMoney(Math.abs(diff))}`
  if (actual === planned && planned > 0) return '预算刚好持平'
  return `当前还剩 ${formatMoney(Math.max(diff, 0))} 预算空间`
}

function isCurrentTrip(tripId: string) {
  return !!tripId && tripId === currentTripContext.value?.tripId
}

function setAsCurrentTrip(trip: TripSummary) {
  if (!trip?.id) return
  const wasCurrent = isCurrentTrip(trip.id)
  setCurrentTripContext(buildCurrentTripContext({
    tripId: trip.id,
    title: buildTripTitle(trip),
    city: trip.city,
    startDate: trip.start_date,
    source: 'history-select',
    lastView: 'history',
  }))
  syncCurrentTripState()
  message.success(wasCurrent ? '已刷新当前旅程' : '已设为当前旅程')
}

function continueTrip(trip: TripSummary) {
  if (!trip?.id) return
  setCurrentTripContext(buildCurrentTripContext({
    tripId: trip.id,
    title: buildTripTitle(trip),
    city: trip.city,
    startDate: trip.start_date,
    source: 'history-select',
    lastView: 'history',
  }))
  syncCurrentTripState()
  viewDetail(trip.id)
}

function continueCurrentTrip() {
  const current = currentTripContext.value
  if (!current?.tripId) {
    message.info('还没有设定当前旅程')
    return
  }
  router.push({ path: `/history/${current.tripId}` })
}

function clearCurrentTripSelection() {
  clearCurrentTripContext()
  syncCurrentTripState()
  message.success('已清除当前旅程')
}

// 详情
const detailVisible = ref(false)
const detailTrip = ref<any>(null)
const detailTitle = computed(() => detailTrip.value ? (detailTrip.value.title || `${detailTrip.value.start_date} ${detailTrip.value.city}`) : '')
const previewVisible = ref(false)
const previewImage = ref('')
const quickCreateDate = ref('')
const selectedTripId = ref('')
const selectedTripDayIndex = ref(0)
const tripActionLoading = ref(false)
const tripOptions = ref<TripSummary[]>([])
const selectedTripDayOptions = ref<TripDayOption[]>([])
const attrImage = ref('')
const attrCity = ref('')
const attrSource = ref('')
const attrMeta = ref<AttractionMetaInfo>({
  address: '',
  type: '',
  tel: '',
  weather: '',
  openTime: '',
  locationText: '',
  lat: null,
  lng: null,
})
const tripActionFeedback = ref<TripActionFeedback | null>(null)
const currentAttractionPayload = ref<AttractionQuickPayload | null>(null)
const tripSuggestion = ref('')
const tripSugLoading = ref(false)

// 笔记
const notesVisible = ref(false)
const notesTrip = ref<any>(null)
const notesText = ref('')
const notesSaving = ref(false)
const notesFiles = ref<any[]>([])
const isRecording = ref(false)
let mediaRecorder: any = null; let audioChunks: any[] = []

function addFile(e: Event, type: string) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  const file = input.files[0]
  const maxSize = type === 'video' ? 15 * 1024 * 1024 : 5 * 1024 * 1024
  if (file.size > maxSize) { message.warning(`${type==='video'?'视频':'图片'}不能超过${type==='video'?15:5}MB`); return }
  const reader = new FileReader()
  reader.onload = () => notesFiles.value.push({ type, name: file.name, size: formatSize(file.size), data: reader.result as string })
  reader.readAsDataURL(file)
}
function formatSize(b: number) { return b<1024*1024 ? Math.round(b/1024)+'KB' : (b/(1024*1024)).toFixed(1)+'MB' }
function formatSizeFromData(file: any) {
  if (!file) return '附件'
  if (typeof file.size === 'string' && file.size.trim()) return file.size
  if (typeof file.size === 'number' && Number.isFinite(file.size)) return formatSize(file.size)
  const data = typeof file.data === 'string' ? file.data : ''
  const base64 = data.includes(',') ? data.split(',')[1] || '' : data
  if (!base64) return '附件'
  const padding = base64.endsWith('==') ? 2 : base64.endsWith('=') ? 1 : 0
  const bytes = Math.max(0, Math.floor(base64.length * 3 / 4) - padding)
  return bytes ? formatSize(bytes) : '附件'
}

async function toggleRecord() {
  if (isRecording.value) { mediaRecorder?.stop(); return }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new MediaRecorder(stream)
    audioChunks = []
    mediaRecorder.ondataavailable = (e: any) => audioChunks.push(e.data)
    mediaRecorder.onstop = () => {
      stream.getTracks().forEach((t: any) => t.stop())
      const blob = new Blob(audioChunks, { type: 'audio/webm' })
      const reader = new FileReader()
      reader.onload = () => notesFiles.value.push({ type: 'audio', name: `录音_${new Date().toLocaleTimeString()}.webm`, size: formatSize(blob.size), data: reader.result as string })
      reader.readAsDataURL(blob)
      isRecording.value = false
    }
    mediaRecorder.start(); isRecording.value = true
  } catch { message.warning('无法访问麦克风') }
}

async function loadHistory() {
  loading.value = true
  try {
    const [historyRes, stateRes] = await Promise.all([
      getHistory(),
      listAttractionStates(),
    ])
    trips.value = historyRes.data || []
    tripOptions.value = historyRes.data || []
    attractionStates.value = stateRes.data || []
    syncCurrentTripState()
    if (selectedTripId.value && !tripOptions.value.find(item => item.id === selectedTripId.value)) {
      selectedTripId.value = ''
    }
  } catch {
    message.error('加载失败')
  }
  finally { loading.value = false }
}

async function viewDetail(id: string) {
  if (!id) return
  router.push({ path: `/history/${id}` })
}

async function openNotes(id: string) {
  try {
    const res = await getHistoryDetail(id)
    notesTrip.value = res.data
    notesText.value = res.data.notes || ''
    notesFiles.value = [...(res.data.files || [])]
    notesVisible.value = true
  } catch { message.error('获取失败') }
}

async function saveNotes() {
  if (!notesTrip.value) return
  notesSaving.value = true
  try {
    await updateHistory(notesTrip.value.id, {
      notes: notesText.value,
      files: notesFiles.value,
    })
    message.success('笔记已保存')
    notesVisible.value = false
    await loadHistory()
  } catch { message.error('保存失败') }
  finally { notesSaving.value = false }
}

const attrName = ref(''); const attrIntro = ref(''); const attrLoading = ref(false)

function formatMoney(value: number) {
  const amount = Number(value || 0)
  return `¥${amount.toLocaleString('zh-CN')}`
}

function resetTripActionFeedback() {
  tripActionFeedback.value = null
}

function resetAttractionMeta() {
  attrMeta.value = {
    address: '',
    type: '',
    tel: '',
    weather: '',
    openTime: '',
    locationText: '',
    lat: null,
    lng: null,
  }
}

function closeAttractionDetail() {
  detailVisible.value = false
  tripActionFeedback.value = null
  currentAttractionPayload.value = null
  tripSuggestion.value = ''
  attrName.value = ''
  attrIntro.value = ''
  attrImage.value = ''
  attrCity.value = ''
  attrSource.value = ''
  resetAttractionMeta()
}

function buildAttractionMeta(detail: any, fallbackAttraction?: any): AttractionMetaInfo {
  const geo = detail?.geo || {}
  const rawLocation = String(geo.location || '').trim()
  let lat: number | null = null
  let lng: number | null = null
  if (rawLocation.includes(',')) {
    const [rawLng, rawLat] = rawLocation.split(',')
    const parsedLat = Number(rawLat)
    const parsedLng = Number(rawLng)
    if (Number.isFinite(parsedLat) && Number.isFinite(parsedLng)) {
      lat = parsedLat
      lng = parsedLng
    }
  }
  if (lat === null || lng === null) {
    const fallbackLocation = fallbackAttraction?.location || {}
    const fallbackLat = fallbackLocation.latitude ?? fallbackLocation.lat ?? null
    const fallbackLng = fallbackLocation.longitude ?? fallbackLocation.lng ?? null
    lat = fallbackLat != null ? Number(fallbackLat) : null
    lng = fallbackLng != null ? Number(fallbackLng) : null
  }
  return {
    address: String(geo.address || fallbackAttraction?.location?.address || '').trim(),
    type: String(geo.type || '').trim(),
    tel: String(geo.tel || '').trim(),
    weather: String(detail?.weather || '').trim(),
    openTime: String(geo.opentime || geo.open_time || '').trim(),
    locationText: rawLocation,
    lat: Number.isFinite(lat) ? Number(lat) : null,
    lng: Number.isFinite(lng) ? Number(lng) : null,
  }
}

function openAttractionMap() {
  const { lat, lng } = attrMeta.value
  if (lat == null || lng == null) {
    message.info('暂时没有这处景点的坐标信息')
    return
  }
  window.open(`https://uri.amap.com/marker?position=${lng},${lat}&name=${encodeURIComponent(attrName.value)}`, '_blank')
}

function isSameTrip(tripId: string) {
  return !!tripId && tripId === detailTrip.value?.id
}

function normalizeAttractionPayload(name: string, city = '', fallbackAttraction?: any): AttractionQuickPayload {
  const fallbackLocation = fallbackAttraction?.location || {}
  const lat = fallbackLocation.latitude ?? fallbackLocation.lat ?? null
  const lng = fallbackLocation.longitude ?? fallbackLocation.lng ?? null
  return {
    name,
    city,
    intro: attrIntro.value || fallbackAttraction?.description || '',
    image: attrImage.value || fallbackAttraction?.image || '',
    location: lat != null && lng != null ? { lat: Number(lat), lng: Number(lng) } : null,
  }
}

async function createTripFromCurrentAttraction() {
  if (!currentAttractionPayload.value?.name) {
    message.warning('请先打开一个景点详情')
    return
  }
  if (!quickCreateDate.value) {
    message.warning('请先选择出发日期')
    return
  }
  tripActionLoading.value = true
  resetTripActionFeedback()
  try {
    const res = await createTripWithAttraction({
      city: currentAttractionPayload.value.city || detailTrip.value?.city || '未知城市',
      startDate: quickCreateDate.value,
      attraction: currentAttractionPayload.value,
    })
    if (res?.success) {
      const createdTrip = res?.data || null
      const newTripId = createdTrip?.id || ''
      const summary = createdTrip?.title || `${quickCreateDate.value} ${currentAttractionPayload.value.city || detailTrip.value?.city || '旅行记录'}`
      tripActionFeedback.value = {
        type: 'create',
        title: `已为「${currentAttractionPayload.value.name}」新建旅行记录`,
        description: `出发日期：${quickCreateDate.value}，已自动收进 ${summary}`,
        tripId: newTripId,
      }
      if (newTripId) {
        setCurrentTripContext(buildCurrentTripContext({
          tripId: newTripId,
          title: summary,
          city: currentAttractionPayload.value.city || detailTrip.value?.city || '',
          startDate: quickCreateDate.value,
          source: 'attraction-create',
          lastView: 'history',
        }))
        syncCurrentTripState()
      }
      message.success(res.message || '已新建旅行记录')
      await loadHistory()
      selectedTripId.value = newTripId || selectedTripId.value
      if (newTripId) {
        await viewDetail(newTripId)
      }
    } else {
      message.error(res?.message || '新建旅行记录失败')
    }
  } catch {
    message.error('新建旅行记录失败，请稍后再试')
  } finally {
    tripActionLoading.value = false
  }
}

async function addCurrentAttractionToTrip() {
  if (!currentAttractionPayload.value?.name) {
    message.warning('请先打开一个景点详情')
    return
  }
  if (!selectedTripId.value) {
    message.warning('请先选择一个旅行记录')
    return
  }
  tripActionLoading.value = true
  resetTripActionFeedback()
  try {
    const targetTripId = selectedTripId.value
    const targetTripLabel = tripOptions.value.find(item => item.id === targetTripId)?.title
      || tripOptions.value.find(item => item.id === targetTripId)?.start_date
      || '所选旅行记录'
    const dayLabel = selectedTripDayOptions.value.find(day => day.value === selectedTripDayIndex.value)?.label || '第1天'
    const beforeDetail = await getHistoryDetail(targetTripId)
    const beforeNames = new Set(
      (beforeDetail?.data?.data?.days || []).flatMap((day: any) => day?.attractions || []).map((item: any) => String(item?.name || '').trim()).filter(Boolean)
    )
    const res = await addAttractionToTrip({
      tripId: targetTripId,
      dayIndex: selectedTripDayIndex.value,
      attraction: currentAttractionPayload.value,
    })
    if (res?.success) {
      const alreadyExists = beforeNames.has(currentAttractionPayload.value.name)
      tripActionFeedback.value = alreadyExists
        ? {
            type: 'duplicate',
            title: `「${currentAttractionPayload.value.name}」已经在这个行程里了`,
            description: `我帮你直接打开了 ${targetTripLabel}，你可以继续调整第几天或补充其他景点。`,
            tripId: targetTripId,
          }
        : {
            type: 'add',
            title: `已加入 ${targetTripLabel}`,
            description: `已放入 ${dayLabel}，现在就带你回到这条旅行记录继续查看。`,
            tripId: targetTripId,
          }
      setCurrentTripContext(buildCurrentTripContext({
        tripId: targetTripId,
        title: tripOptions.value.find(item => item.id === targetTripId)?.title || targetTripLabel,
        city: tripOptions.value.find(item => item.id === targetTripId)?.city || currentAttractionPayload.value.city || '',
        startDate: tripOptions.value.find(item => item.id === targetTripId)?.start_date || '',
        source: 'attraction-add',
        lastView: 'history',
      }))
      syncCurrentTripState()
      if (alreadyExists) {
        message.info(`这个景点已经在行程里了，已为你打开对应记录`)
      } else {
        message.success(res.message || '已加入行程')
      }
      await loadHistory()
      await viewDetail(targetTripId)
    } else {
      message.error(res?.message || '加入行程失败')
    }
  } catch {
    message.error('加入行程失败，请稍后再试')
  } finally {
    tripActionLoading.value = false
  }
}

async function openAttractionPage(name: string, city = '', fallbackAttraction?: any) {
  attrName.value = name; attrLoading.value = true; attrIntro.value = ''; attrImage.value = ''; attrCity.value = city || detailTrip.value?.city || ''; attrSource.value = ''; currentAttractionPayload.value = normalizeAttractionPayload(name, attrCity.value, fallbackAttraction)
  resetAttractionMeta()
  resetTripActionFeedback()
  if (!quickCreateDate.value) quickCreateDate.value = new Date().toISOString().slice(0, 10)
  if (!detailVisible.value) detailVisible.value = true
  try {
    const targetCity = city || detailTrip.value?.city || ''
    const d = await getAttractionDetail(name, targetCity)
    if (d.success) {
      const detail = d.data || {}
      attrIntro.value = detail.intro || '暂时还没有拿到这处景点的详细介绍。'
      attrImage.value = detail.image || fallbackAttraction?.image || ''
      attrCity.value = detail.city || targetCity
      attrSource.value = d.source ? `来源：${d.source}` : ''
      const nextMeta = buildAttractionMeta(detail, fallbackAttraction)
      attrMeta.value = nextMeta
      currentAttractionPayload.value = {
        name: detail.name || name,
        city: detail.city || targetCity,
        intro: detail.intro || fallbackAttraction?.description || '',
        image: detail.image || fallbackAttraction?.image || '',
        location: nextMeta.lat != null && nextMeta.lng != null ? { lat: nextMeta.lat, lng: nextMeta.lng } : normalizeAttractionPayload(name, targetCity, fallbackAttraction).location,
      }
    }
    else {
      attrIntro.value = '抱歉，获取景点介绍失败'
      attrImage.value = fallbackAttraction?.image || ''
      currentAttractionPayload.value = normalizeAttractionPayload(name, targetCity, fallbackAttraction)
    }
  } catch {
    attrIntro.value = '网络异常'
    attrImage.value = fallbackAttraction?.image || ''
    currentAttractionPayload.value = normalizeAttractionPayload(name, city || detailTrip.value?.city || '', fallbackAttraction)
  }
  finally { attrLoading.value = false }
}

function buildTripDayOptions(days: any[] = []) {
  if (!Array.isArray(days) || !days.length) {
    selectedTripDayOptions.value = [{ value: 0, label: '第1天' }]
    selectedTripDayIndex.value = 0
    return
  }
  selectedTripDayOptions.value = days.map((day: any, index: number) => ({
    value: Number(day?.day_index ?? index),
    label: day?.date ? `第${index + 1}天 · ${day.date}` : `第${index + 1}天`,
  }))
  const exists = selectedTripDayOptions.value.some(day => day.value === selectedTripDayIndex.value)
  if (!exists) selectedTripDayIndex.value = selectedTripDayOptions.value[0]?.value ?? 0
}

watch(selectedTripId, async (id) => {
  if (!id) {
    selectedTripDayOptions.value = []
    selectedTripDayIndex.value = 0
    return
  }
  try {
    const res = await getHistoryDetail(id)
    buildTripDayOptions(res?.data?.data?.days || [])
  } catch {
    selectedTripDayOptions.value = [{ value: 0, label: '第1天' }]
    selectedTripDayIndex.value = 0
  }
})

function openStateAttraction(item: AttractionStateRecord) {
  detailTrip.value = {
    title: '景点详情',
    city: item.city || '旅行记录',
    data: { days: [], budget: null },
    notes: '',
    images: [],
  }
  openAttractionPage(item.name, item.city)
}

function renderMd(t: string): string {
  if (!t) return ''
  let h = t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
  h = h.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
  h = h.replace(/\*(.+?)\*/g,'<em>$1</em>')
  h = h.replace(/`(.+?)`/g,'<code>$1</code>')
  h = h.replace(/^### (.+)$/gm,'<h4>$1</h4>')
  h = h.replace(/^## (.+)$/gm,'<h3>$1</h3>')
  h = h.replace(/^# (.+)$/gm,'<h2>$1</h2>')
  h = h.replace(/^- (.+)$/gm,'<li>$1</li>')
  h = h.replace(/^\d+\. (.+)$/gm,'<li>$1</li>')
  h = h.replace(/\n\n/g,'<br><br>')
  h = h.replace(/\n/g,'<br>')
  return h
}

async function fetchTripSuggestion() {
  if (tripSugLoading.value || !detailTrip.value) return
  tripSugLoading.value = true
  try {
    const city = detailTrip.value.city
    const d = await getTripSuggestion(city)
    if (d.success) tripSuggestion.value = d.suggestion
  } catch { tripSuggestion.value = '出行记得注意天气变化哦～' }
  finally { tripSugLoading.value = false }
}

async function handleDelete(id: string) {
  try { await deleteHistory(id); message.success('已删除'); loadHistory() }
  catch { message.error('删除失败') }
}

onMounted(() => {
  syncCurrentTripState()
  loadHistory()
  window.addEventListener('storage', syncCurrentTripState)
})

onBeforeUnmount(() => {
  window.removeEventListener('storage', syncCurrentTripState)
})
</script>

<style scoped>
.history-container { max-width: 960px; margin: 0 auto; padding: 24px; animation: viewIn .35s ease-out both }
@keyframes viewIn { from{opacity:0;transform:scale(.98) translateY(6px)} to{opacity:1;transform:scale(1) translateY(0)} }
.history-header { display: flex; align-items: center; gap: 20px; margin-bottom: 24px; }
.hero-header { align-items: flex-start; justify-content: space-between; padding: 20px 22px; border: 1px solid #eadccf; border-radius: 20px; background: linear-gradient(135deg, #fffaf6 0%, #fff 58%, #fdf4ee 100%); box-shadow: 0 12px 32px rgba(139, 69, 19, 0.06); }
.history-title { margin: 0; font-size: 28px; font-weight: 700; color: #5c3a21; font-family: 'STKaiti','楷体','KaiTi',serif; }
.history-subtitle { margin: 8px 0 0; color: #b08a72; font-size: 14px; line-height: 1.8; max-width: 620px; }
.history-header-badges { display:flex; flex-wrap:wrap; gap:8px; justify-content:flex-end; }
.history-badge { display:inline-flex; align-items:center; padding:6px 12px; border-radius:999px; background:#fdf0e8; color:#c43b3b; font-size:12px; font-weight:600; }
.history-badge.soft { background:#fff; color:#8b6b52; border:1px solid #f0dfd1; }
.current-trip-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 0 0 20px;
  padding: 18px 20px;
  border: 1px solid #eadccf;
  border-radius: 18px;
  background: linear-gradient(135deg, #fff7f0 0%, #fffdf9 100%);
  box-shadow: 0 10px 28px rgba(196, 59, 59, 0.08);
}
.current-trip-banner-kicker {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #c43b3b;
}
.current-trip-banner-title {
  margin-top: 6px;
  font-size: 22px;
  font-weight: 700;
  color: #5c3a21;
  font-family: 'STKaiti','楷体','KaiTi',serif;
}
.current-trip-banner-desc {
  margin: 8px 0 0;
  color: #8b6b52;
  font-size: 13px;
  line-height: 1.7;
}
.current-trip-banner-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.current-trip-banner-btn {
  border: 1px solid #e7c7b3;
  border-radius: 999px;
  background: #fff;
  color: #8b5a3c;
  padding: 10px 16px;
  font-size: 13px;
  cursor: pointer;
  transition: all .18s;
}
.current-trip-banner-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(139,69,19,.08);
}
.current-trip-banner-btn.primary {
  background: linear-gradient(135deg,#c43b3b,#a0522d);
  color: #fff;
  border-color: transparent;
}
.history-overview-strip { display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:14px; margin:0 0 24px; }
.history-overview-card { padding:16px; border-radius:16px; border:1px solid #eadccf; background:#fff; box-shadow:0 8px 24px rgba(139,69,19,.04); display:flex; flex-direction:column; gap:8px; }
.history-overview-card span { font-size:12px; color:#b08a72; }
.history-overview-card strong { font-size:24px; color:#5c3a21; }
.history-overview-card p { margin:0; font-size:12px; line-height:1.7; color:#8b6b52; }
.loading-wrapper { text-align:center;padding:80px 0;display:flex;flex-direction:column;align-items:center;gap:20px }
.empty-state { text-align: center; padding: 80px 0; color: #999; }
.favorites-panel { margin-bottom: 28px; padding: 20px 22px; background: linear-gradient(180deg, #fffaf6 0%, #fff 100%); border: 1px solid #eadccf; border-radius: 18px; box-shadow: 0 10px 30px rgba(139, 69, 19, 0.06); }
.favorites-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 18px; }
.favorites-title { margin: 0; font-size: 22px; color: #5c3a21; font-family: 'STKaiti','楷体','KaiTi',serif; }
.favorites-subtitle { margin: 6px 0 0; color: #b08a72; font-size: 13px; line-height: 1.7; }
.favorites-total { flex-shrink: 0; padding: 6px 12px; border-radius: 999px; background: #fdf0e8; color: #c43b3b; font-size: 12px; font-weight: 600; }
.favorites-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; }
.favorites-card { border: 1px solid #f0dfd1; border-radius: 16px; background: #fff; padding: 16px; min-height: 180px; }
.favorites-card-head { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 14px; }
.favorites-emoji { font-size: 20px; line-height: 1; margin-top: 2px; }
.favorites-card-head h3 { margin: 0; font-size: 16px; color: #5c3a21; }
.favorites-card-head p { margin: 4px 0 0; color: #b8a088; font-size: 12px; line-height: 1.6; }
.favorites-badge { margin-left: auto; padding: 2px 10px; border-radius: 999px; background: #f5ede0; color: #8b5a3c; font-size: 12px; }
.favorites-list { display: flex; flex-direction: column; gap: 10px; }
.favorites-item { padding: 10px 12px; border-radius: 12px; background: #faf7f2; border: 1px solid #f3e7db; }
.favorites-item-clickable { cursor: pointer; transition: all .18s; }
.favorites-item-clickable:hover { background: #fff7f0; border-color: #e7c7b3; transform: translateY(-1px); box-shadow: 0 6px 16px rgba(196,59,59,.08); }
.favorites-item-main { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.favorites-item-name { font-size: 14px; font-weight: 600; color: #5c3a21; }
.favorites-item-city { font-size: 12px; color: #c43b3b; background: #fff1ea; padding: 2px 8px; border-radius: 999px; }
.favorites-item-time { display: block; margin-top: 6px; font-size: 12px; color: #b8a088; }
.favorites-item-action { display: inline-block; margin-top: 6px; font-size: 12px; color: #c43b3b; font-weight: 600; }
.empty-seal { width:64px;height:64px;border-radius:12px;background:#c43b3b;color:#faf0d7;display:flex;align-items:center;justify-content:center;font-size:32px;font-weight:900;font-family:'STKaiti','楷体','KaiTi',serif;margin:0 auto 16px }
.empty-title { font-size:20px;font-weight:700;color:#5c3a21;margin:0 0 4px;font-family:'STKaiti','楷体','KaiTi',serif }
.empty-desc { font-size:14px;color:#b8a088;margin:0 0 24px }
.empty-btn { padding:10px 28px;border:1px solid #c43b3b;border-radius:20px;background:#fdf5ee;color:#c43b3b;font-size:15px;cursor:pointer;font-family:'STKaiti','楷体','KaiTi',serif;transition:all .2s }
.empty-btn:hover { background:#c43b3b;color:#fff }

/* 城市分组 */
.city-group { margin-bottom: 24px; }
.city-group-header {
  display:flex; align-items:center; justify-content:space-between; gap:14px;
  padding: 14px 16px; background: linear-gradient(180deg,#f8f3ed 0%,#fff 100%);
  border:1px solid #eadccf; border-radius: 14px; margin-bottom: 10px;
}
.city-group-title { display:flex; align-items:center; gap:10px; min-width:0; flex-wrap:wrap; }
.city-folder { font-size: 20px; }
.city-name { font-size: 17px; font-weight: 700; color: #5c3a21; }
.city-count { font-size: 13px; color: #8b6b52; }
.city-group-stats { display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-end; }
.city-stat-chip { display:inline-flex; align-items:center; padding:4px 10px; border-radius:999px; background:#f5ede0; color:#8b5a3c; font-size:12px; }
.city-stat-chip.done { background:#f6ffed; color:#389e0d; }

.trip-card { border-radius: 16px; margin-bottom: 12px; border: 1px solid #f0dfd1; box-shadow: 0 8px 24px rgba(139,69,19,.04); }
.trip-card-body { display: flex; align-items: center; gap: 16px; }
.trip-info { flex: 1; cursor: pointer; min-width: 0; }
.trip-title-row { display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:6px; }
.trip-title { margin: 0; font-size: 17px; font-weight: 700; color:#5c3a21; }
.trip-status-pill { flex-shrink:0; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:600; }
.trip-status-pill.going { background:#fff7e8; color:#ad6800; }
.trip-status-pill.done { background:#f6ffed; color:#389e0d; }
.trip-meta { display: flex; gap: 14px; font-size: 13px; color: #888; flex-wrap: wrap; align-items: center; }
.meta-item { white-space: nowrap; }
.meta-tag { background: #f0f5ff; color: #667eea; padding: 1px 8px; border-radius: 10px; font-size: 12px; }
.meta-tag.prep { background:#fff7e8; color:#ad6800; }
.trip-summary-row { display:flex; gap:8px; flex-wrap:wrap; margin-top:8px; }
.summary-chip { display:inline-flex; align-items:center; gap:4px; padding:4px 10px; border-radius:999px; font-size:12px; line-height:1.4; }
.summary-chip.budget { background:#fff7e8; color:#ad6800; }
.summary-chip.checklist { background:#f6ffed; color:#389e0d; }
.trip-budget-note { margin:8px 0 0; font-size:12px; color:#8b6b52; line-height:1.6; }
.trip-preview { margin: 8px 0 0 0; font-size: 13px; color: #aaa; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 500px; }
.trip-actions { flex-shrink: 0; white-space: nowrap; display:flex; flex-direction:column; align-items:flex-end; gap:4px; }

/* 详情 */
.detail-content { max-height: 60vh; overflow-y: auto; }
.detail-time { color: #999; font-size: 13px; margin-bottom: 16px; }

/* 详情内浮动AI */
.detail-ai { position:absolute;bottom:20px;right:20px;display:flex;flex-direction:column;align-items:flex-end;gap:8px;z-index:10 }
.detail-ai-bubble { background:#fff;border-radius:12px;padding:10px 16px;max-width:200px;box-shadow:0 4px 16px rgba(139,69,19,.1);font-size:13px;color:#6b5344;line-height:1.5;cursor:pointer;animation:floatIn .4s ease-out;border:1px solid #eadccf }
@keyframes floatIn { from{opacity:0;transform:translateY(8px) scale(.95)} to{opacity:1;transform:translateY(0) scale(1)} }
.detail-ai-btn { width:42px;height:42px;border-radius:50%;background:linear-gradient(135deg,#c43b3b,#a0522d);display:flex;align-items:center;justify-content:center;font-size:20px;cursor:pointer;box-shadow:0 3px 12px rgba(196,59,59,.3);transition:all .2s }
.detail-ai-btn:hover { transform:scale(1.1) }

/* 详情分页标签 */
.detail-tabs { display:flex;gap:0;border-bottom:2px solid #eadccf;padding:0 24px;background:#faf7f2;border-radius:16px 16px 0 0 }
.dt-tab { padding:12px 20px;font-size:14px;color:#b8a088;cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-2px;transition:all .2s;font-family:'STKaiti','楷体','KaiTi',serif;white-space:nowrap }
.dt-tab:hover { color:#5c3a21 }
.dt-tab.active { color:#c43b3b;border-bottom-color:#c43b3b;font-weight:600 }
/* 进度条 */
.trip-progress { margin-top: 10px; }
.trip-progress-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; font-size:12px; color:#8b6b52; }
.trip-progress-head strong { color:#5c3a21; font-size:13px; }
.trip-progress-bar { height: 5px; background: #eadccf; border-radius: 3px; overflow: hidden; }
.trip-progress-fill { height: 100%; background: #c43b3b; border-radius: 3px; transition: width .3s; }
.trip-progress-fill.done { background: #52c41a; }

/* 景点介绍 */
.trip-action-feedback { display:flex; align-items:center; justify-content:space-between; gap:14px; margin:0 0 16px; padding:14px 16px; border-radius:14px; border:1px solid #eadccf; background:linear-gradient(180deg,#fffaf6 0%,#fff 100%); }
.trip-action-feedback.create { border-color:#d7c2f5; background:linear-gradient(180deg,#faf6ff 0%,#fff 100%); }
.trip-action-feedback.add { border-color:#cfe7d2; background:linear-gradient(180deg,#f7fff8 0%,#fff 100%); }
.trip-action-feedback.duplicate { border-color:#f3dfb3; background:linear-gradient(180deg,#fffaf0 0%,#fff 100%); }
.trip-action-feedback-main { display:flex; flex-direction:column; gap:4px; }
.trip-action-feedback-main strong { color:#5c3a21; font-size:15px; }
.trip-action-feedback-main p { margin:0; color:#8b6b52; font-size:13px; line-height:1.7; }
.trip-action-feedback-btn { flex-shrink:0; border:none; border-radius:12px; background:#c43b3b; color:#fff; padding:10px 14px; font-size:13px; cursor:pointer; transition:all .18s; }
.trip-action-feedback-btn:hover { transform:translateY(-1px); box-shadow:0 6px 16px rgba(196,59,59,.18); }
.attr-detail-wrap { display:flex; flex-direction:column; gap:18px; }
.attr-hero-card { display:grid; grid-template-columns: minmax(240px, 320px) 1fr; gap:18px; padding:18px; background:linear-gradient(180deg,#fffaf6 0%,#fff 100%); border:1px solid #eadccf; border-radius:16px; }
.attr-hero-media { min-height:220px; border-radius:14px; overflow:hidden; background:#f6efe7; }
.attr-hero-img { width:100%; height:100%; min-height:220px; object-fit:cover; cursor:pointer; display:block; }
.attr-hero-empty { min-height:220px; display:flex; align-items:center; justify-content:center; text-align:center; padding:20px; border:1px dashed #e2c9b7; border-radius:14px; background:#fcf7f1; color:#b8a088; font-size:14px; }
.attr-hero-main { display:flex; flex-direction:column; gap:16px; }
.attr-hero-head { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; }
.attr-hero-head h3 { margin:0; font-size:24px; color:#5c3a21; font-family:'STKaiti','楷体','KaiTi',serif; }
.attr-hero-head p { margin:6px 0 0; color:#b08a72; font-size:13px; }
.attr-source { flex-shrink:0; padding:5px 10px; border-radius:999px; background:#fdf0e8; color:#c43b3b; font-size:12px; font-weight:600; }
.attr-meta-grid { display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:10px; }
.attr-meta-item { padding:10px 12px; border:1px solid #f2e4d8; border-radius:12px; background:#fffaf6; display:flex; flex-direction:column; gap:4px; }
.attr-meta-label { font-size:12px; color:#b08a72; }
.attr-meta-value { font-size:13px; color:#5c3a21; line-height:1.6; word-break:break-word; }
.attr-map-row { display:flex; }
.attr-map-btn { border:none; border-radius:12px; background:#fdf0e8; color:#c43b3b; padding:10px 14px; font-size:13px; cursor:pointer; transition:all .18s; }
.attr-map-btn:hover { transform:translateY(-1px); box-shadow:0 6px 16px rgba(196,59,59,.1); }
.attr-quick-actions { display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:12px; }
.attr-action-card { display:flex; flex-direction:column; gap:10px; padding:14px; border:1px solid #f0dfd1; border-radius:14px; background:#fff; }
.attr-action-label { font-size:13px; color:#8b5a3c; font-weight:600; }
.attr-action-input, .attr-action-select { width:100%; padding:10px 12px; border:1px solid #e3d3c6; border-radius:10px; background:#fff; color:#5c3a21; font-size:14px; outline:none; }
.attr-action-input:focus, .attr-action-select:focus { border-color:#c43b3b; box-shadow:0 0 0 2px rgba(196,59,59,.08); }
.attr-action-btn { border:none; border-radius:12px; background:#f6efe7; color:#8b5a3c; padding:10px 14px; font-size:14px; cursor:pointer; transition:all .18s; }
.attr-action-btn:hover:not(:disabled) { transform:translateY(-1px); box-shadow:0 6px 16px rgba(139,69,19,.08); }
.attr-action-btn.primary { background:linear-gradient(135deg,#c43b3b,#a0522d); color:#fff; }
.attr-action-btn:disabled { opacity:.55; cursor:not-allowed; box-shadow:none; }
.attr-empty-intro { padding:20px; border-radius:14px; background:#fcf7f1; color:#b8a088; font-size:14px; text-align:center; }
/* 中国风加载 */
.attr-loading { text-align:center;padding:60px 40px;display:flex;flex-direction:column;align-items:center;gap:20px }
.think-seal { width:56px;height:56px;border-radius:10px;background:#c43b3b;color:#faf0d7;display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:900;font-family:'STKaiti','楷体','KaiTi',serif;animation:pulse 2s infinite ease-in-out }
@keyframes pulse { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.08);opacity:.7} }
.think-dots { display:flex;gap:6px }
.think-dots span { width:8px;height:8px;border-radius:50%;background:#d4a89a;animation:dotBounce 1.4s infinite ease-in-out both }
.think-dots span:nth-child(2){animation-delay:.16s}.think-dots span:nth-child(3){animation-delay:.32s}
@keyframes dotBounce { 0%,80%,100%{opacity:.3;transform:scale(.8)} 40%{opacity:1;transform:scale(1.2)} }
.think-text { font-size:16px;color:#b8a088;font-family:'STKaiti','楷体','KaiTi',serif;margin:0 }

.attr-intro { font-size: 15px; color: #5c3a21; line-height: 2; }
.attr-intro :deep(h2) { font-size: 22px; font-weight: 700; margin: 20px 0 12px; color: #5c3a21; border-bottom: 2px solid #eadccf; padding-bottom: 8px; }
.attr-intro :deep(h3) { font-size: 18px; font-weight: 700; margin: 16px 0 8px; color: #6b5344; }
.attr-intro :deep(h4) { font-size: 15px; font-weight: 700; margin: 12px 0 6px; }
.attr-intro :deep(strong) { color: #c43b3b; }
.attr-intro :deep(li) { margin: 4px 0; }
.attr-intro :deep(ul) { padding-left: 20px; margin: 8px 0; }
.attr-intro :deep(code) { background: #fdf0e8; padding: 2px 6px; border-radius: 4px; font-size: 13px; }

/* 旅行笔记 - 备忘录 */
.memo-modal :deep(.ant-modal-content) { border-radius:16px; overflow:hidden }
.memo-wrap { display:flex;flex-direction:column }
.memo-head { display:flex;align-items:center;gap:14px;padding:24px 28px;background:linear-gradient(135deg,#fdf8f2,#fefaf6);border-bottom:1px solid #eadccf }
.memo-head-icon { font-size:32px }
.memo-head-text h3 { margin:0;font-size:18px;color:#5c3a21;font-family:'STKaiti','楷体','KaiTi',serif }
.memo-head-text span { font-size:12px;color:#b8a088 }
.memo-area {
  width:100%;min-height:300px;border:none;outline:none;resize:vertical;
  padding:24px 28px;font-size:16px;line-height:2;color:#5c3a21;
  background:#fefcf8;
  background-image:repeating-linear-gradient(#fefcf8 0,#fefcf8 31px,#e8e0d5 31px,#e8e0d5 32px);
  font-family:'STKaiti','楷体','KaiTi','Georgia',serif
}
.memo-area::placeholder { color:#c4b5a5;font-style:italic }
.memo-foot { display:flex;align-items:center;justify-content:space-between;padding:16px 28px;background:#faf7f2;border-top:1px solid #eadccf }
.memo-hint { font-size:13px;color:#b8a088;font-family:'STKaiti','楷体','KaiTi',serif }
.memo-save { padding:8px 22px;border:none;border-radius:18px;background:linear-gradient(135deg,#c43b3b,#a0522d);color:#fff;font-size:14px;cursor:pointer;font-family:'STKaiti','楷体','KaiTi',serif;transition:all .2s }
.memo-save:hover:not(:disabled) { transform:translateY(-1px);box-shadow:0 3px 12px rgba(196,59,59,.3) }
.memo-save:disabled { opacity:.5;cursor:not-allowed }
/* 附件 */
.memo-attach { padding:0 28px 16px;background:#fefcf8 }
.attach-label { font-size:13px;color:#b8a088;display:block;margin-bottom:8px }
.attach-list { display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px }
.attach-item { display:flex;align-items:center;gap:6px;padding:4px 10px;background:#faf7f2;border:1px solid #eadccf;border-radius:8px;font-size:12px }
.attach-type { font-size:14px }
.attach-name { color:#5c3a21;max-width:120px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis }
.attach-size { color:#b8a088 }
.attach-del { cursor:pointer;color:#ccc;font-size:14px }
.attach-del:hover { color:#c43b3b }
.attach-btns { display:flex;gap:8px }
.attach-btn { padding:6px 14px;border:1px dashed #d4a89a;border-radius:14px;background:transparent;color:#b8a088;font-size:13px;cursor:pointer;transition:all .2s }
.attach-btn:hover { border-color:#c43b3b;color:#c43b3b;background:#fdf8f3 }
.attach-btn.recording { border-color:#ff4d4f;color:#ff4d4f;background:#fff0f0;animation:pulse 1s infinite }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.6} }
@media (max-width: 767px) {
  .hero-header { padding: 16px; flex-direction: column; }
  .history-header-badges { justify-content: flex-start; }
  .current-trip-banner { flex-direction: column; align-items: flex-start; padding: 16px; }
  .current-trip-banner-actions { width: 100%; justify-content: flex-start; }
  .history-overview-strip { grid-template-columns: 1fr; }
  .favorites-panel { padding: 18px 16px; }
  .favorites-header { flex-direction: column; align-items: stretch; }
  .favorites-total { align-self: flex-start; }
  .city-group-header { flex-direction: column; align-items: flex-start; }
  .city-group-stats { justify-content: flex-start; }
  .trip-card-body { flex-direction: column; align-items: stretch; }
  .trip-title-row { flex-direction: column; align-items: flex-start; }
  .trip-actions { display: flex; flex-direction: row; justify-content: flex-end; align-items: center; flex-wrap: wrap; }
  .trip-action-feedback { flex-direction: column; align-items: stretch; }
  .attr-hero-card { grid-template-columns: 1fr; }
  .attr-meta-grid { grid-template-columns: 1fr; }
  .attr-quick-actions { grid-template-columns: 1fr; }
  .budget-overview, .budget-type-grid, .prep-actions { grid-template-columns: 1fr; }
  .task-cost-head { display:none; }
  .task-item { flex-wrap:wrap; align-items:flex-start; }
  .task-day-inp { width:56px; }
  .task-name-inp { min-width: calc(100% - 140px); }
  .task-cost-wrap { margin-left: 28px; }
  .prep-header { flex-direction:column; align-items:stretch; }
  .prep-item { flex-wrap:wrap; }
  .prep-category-select, .prep-name-inp { width:100%; }
}

</style>
