<template>
  <div class="plaza">
    <div class="plaza-top">
      <div class="plaza-head">
        <h1>📊 旅行数据广场</h1>
        <p>万千行者的足迹，汇聚于此</p>
      </div>
      <div class="plaza-search">
        <input v-model="searchText" class="search-inp" placeholder="搜索省份、城市或景点..." @input="doSearch" />
        <span class="search-icon">🔍</span>
      </div>
    </div>

    <Transition name="slide">
      <div v-if="searchText && searchResults.length" class="search-results">
        <div v-for="r in searchResults" :key="`${r.name}-${r.city || ''}`" class="search-item" @click="jumpTo(r)">
          <span class="sr-type">{{ r.type === 'attraction' ? '🎯' : r.type === 'city' ? '🏙️' : '📍' }}</span>
          <div class="sr-info">
            <span class="sr-name">{{ r.name }}</span>
            <span class="sr-path">{{ r.province }}{{ r.city ? ' · ' + r.city : '' }}</span>
          </div>
          <span class="sr-count">{{ r.count }} 人次</span>
        </div>
      </div>
    </Transition>

    <div class="plaza-reco" v-if="recommendation && !searchText">
      <span class="reco-icon">🤖</span>
      <span class="reco-text">{{ recommendation }}</span>
    </div>

    <div class="bread" v-if="!searchText">
      <span :class="{ on: !selProvince }" @click="goToNationwide">🌏 全国</span>
      <template v-if="selProvince">
        <span class="sep">›</span><span :class="{ on: !selCity && !activeAttraction.name }" @click="goToProvince">{{ selProvince }}</span>
      </template>
      <template v-if="selCity">
        <span class="sep">›</span><span :class="{ on: !activeAttraction.name }" @click="goToCity">{{ selCity }}</span>
      </template>
      <template v-if="activeAttraction.name">
        <span class="sep">›</span><span class="on">{{ activeAttraction.name }}</span>
      </template>
    </div>

    <div v-if="!selProvince && !searchText" class="view">
      <div class="pie-section">
        <div class="pie-visual">
          <svg viewBox="0 0 240 240" class="pie-svg">
            <circle
              v-for="(seg, i) in pieSegs"
              :key="i"
              cx="120"
              cy="120"
              r="70"
              fill="transparent"
              :stroke="seg.color"
              stroke-width="40"
              :stroke-dasharray="seg.dash"
              :stroke-dashoffset="seg.offset"
              @click="selProvince = seg.name"
              @mouseenter="hoverSeg = seg.name"
              @mouseleave="hoverSeg = ''"
              :opacity="hoverSeg && hoverSeg !== seg.name ? 0.35 : 1"
              style="cursor: pointer; transition: opacity 0.3s"
              transform="rotate(-90 120 120)"
            />
            <text x="120" y="115" text-anchor="middle" font-size="18" font-weight="800" fill="#5c3a21">{{ totalCount.toLocaleString() }}</text>
            <text x="120" y="135" text-anchor="middle" font-size="11" fill="#b8a088">条旅行记录</text>
          </svg>
          <div class="pie-center-hint" v-if="hoverSeg">{{ hoverSeg }}</div>
        </div>
        <div class="pie-legend">
          <div
            v-for="seg in pieSegs.slice(0, 8)"
            :key="seg.name"
            class="legend-row"
            @click="selProvince = seg.name"
            @mouseenter="hoverSeg = seg.name"
            @mouseleave="hoverSeg = ''"
          >
            <span class="lg-dot" :style="{ background: seg.color }"></span>
            <span class="lg-name">{{ seg.name }}</span>
            <span class="lg-bar"><i :style="{ width: (seg.count / totalCount) * 100 + '%', background: seg.color }"></i></span>
            <span class="lg-num">{{ seg.count.toLocaleString() }}</span>
          </div>
        </div>
      </div>

      <div class="prov-list">
        <h3>全部省份</h3>
        <div class="prov-scroll">
          <TransitionGroup name="list" tag="div">
            <div v-for="p in sortedProvinces" :key="p.name" class="prov-row" @click="selProvince = p.name">
              <span class="pr-rank" :class="{ top3: p.count > 5000 }">{{ sortedProvinces.indexOf(p) + 1 }}</span>
              <span class="pr-name">{{ p.name }}</span>
              <span class="pr-bar-wrap"><span class="pr-bar" :style="{ width: (p.count / maxCount) * 100 + '%' }"></span></span>
              <span class="pr-num">{{ p.count.toLocaleString() }}</span>
            </div>
          </TransitionGroup>
        </div>
      </div>
    </div>

    <Transition name="slide" mode="out-in">
      <div v-if="selProvince && !selCity && !searchText" :key="'p' + selProvince" class="view detail">
        <h3>{{ provinceData?.count.toLocaleString() }} 人次到过 {{ selProvince }}</h3>
        <div class="city-grid">
          <div v-for="c in provinceData?.cities || []" :key="c.name" class="city-tile" @click="selCity = c.name">
            <div class="ct-rank">{{ (provinceData?.cities || []).indexOf(c) + 1 }}</div>
            <div class="ct-info">
              <span class="ct-name">{{ c.name }}</span>
              <span class="ct-count">{{ c.count.toLocaleString() }} 人次</span>
            </div>
            <div class="ct-bar"><div :style="{ width: (c.count / (provinceData?.count || 1)) * 100 + '%' }"></div></div>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="slide" mode="out-in">
      <div v-if="selCity && !activeAttraction.name && !searchText" :key="'c' + selCity" class="view detail">
        <h3>{{ cityTotal.toLocaleString() }} 人次到过 {{ selCity }}</h3>
        <div class="attr-list">
          <div v-for="a in cityAttractions" :key="a.name" class="attr-row clickable" @click="openAttractionDetail(a.name, selCity)">
            <span class="ar-rank" :class="{ top: cityAttractions.indexOf(a) < 3 }">{{ cityAttractions.indexOf(a) + 1 }}</span>
            <span class="ar-name">{{ a.name }}</span>
            <span class="ar-bar"><i :style="{ width: (a.count / cityTotal) * 100 + '%' }"></i></span>
            <span class="ar-num">{{ a.count.toLocaleString() }}</span>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="slide" mode="out-in">
      <div v-if="activeAttraction.name && !searchText" :key="`a${activeAttraction.city}-${activeAttraction.name}`" class="view detail scenic-detail-page">
        <div class="scenic-page-head">
          <div>
            <div class="scenic-kicker">景区详情</div>
            <h2>{{ attractionDetail.name || activeAttraction.name || '景区介绍' }}</h2>
            <div class="scenic-meta">
              <span>{{ activeAttraction.city || selCity || '未知城市' }}</span>
              <span v-if="attractionDetail.source">{{ attractionDetail.source }}</span>
              <span v-if="detailResponseSource">返回：{{ detailResponseSource }}</span>
            </div>
          </div>
          <button class="guide-btn" @click="openDigitalHuman" :disabled="detailLoading || !attractionDetail.intro">
            打开数字人讲解
          </button>
        </div>

        <div v-if="detailLoading" class="scenic-loading">正在生成景区图文介绍…</div>
        <div v-else class="scenic-page-body">
          <div class="hero-card scenic-hero-card">
            <div class="hero-image-wrap">
              <img v-if="attractionDetail.image" :src="attractionDetail.image" class="hero-image" :alt="attractionDetail.name" />
              <div v-else class="hero-placeholder">
                <span>🏞️</span>
                <p>暂未获取到景区图片</p>
              </div>
            </div>
            <div class="hero-side">
              <div class="hero-info" v-if="attractionDetail.geo">
                <h4>基础信息</h4>
                <p v-if="attractionDetail.geo.address"><strong>地址：</strong>{{ attractionDetail.geo.address }}</p>
                <p v-if="attractionDetail.geo.type"><strong>类型：</strong>{{ attractionDetail.geo.type }}</p>
                <p v-if="attractionDetail.geo.tel"><strong>电话：</strong>{{ attractionDetail.geo.tel }}</p>
              </div>
              <div class="hero-info" v-if="attractionDetail.weather">
                <h4>出行天气</h4>
                <p>{{ attractionDetail.weather }}</p>
              </div>
              <div class="hero-info hero-tips">
                <h4>讲解模式</h4>
                <p>当前图片仅展示后端景区图片接口返回结果；你可以直接阅读图文，也可以打开数字人弹层自动播报并继续追问。</p>
              </div>
            </div>
          </div>

          <div v-if="tripActionFeedback" :class="['trip-action-feedback', tripActionFeedback.type]">
            <div class="trip-action-feedback-main">
              <strong>{{ tripActionFeedback.title }}</strong>
              <p>{{ tripActionFeedback.description }}</p>
            </div>
            <button v-if="tripActionFeedback.tripId" class="trip-action-feedback-btn" @click="openTripDetail(tripActionFeedback.tripId)">
              打开这条旅行记录
            </button>
          </div>

          <div class="action-grid">
            <div class="intro-card scenic-state-card">
              <div class="intro-card-head">
                <h3>景点状态</h3>
                <span class="state-sync-text">{{ stateLoading ? '同步中…' : '状态会自动保存' }}</span>
              </div>
              <div class="state-actions">
                <button class="state-btn" :class="{ active: attractionState.favorite }" :disabled="stateActionLoading" @click="toggleAttractionState('favorite')">
                  {{ attractionState.favorite ? '已收藏' : '收藏' }}
                </button>
                <button class="state-btn" :class="{ active: attractionState.want_to_go }" :disabled="stateActionLoading" @click="toggleAttractionState('want_to_go')">
                  {{ attractionState.want_to_go ? '已想去' : '想去' }}
                </button>
                <button class="state-btn" :class="{ active: attractionState.visited }" :disabled="stateActionLoading" @click="toggleAttractionState('visited')">
                  {{ attractionState.visited ? '已去过' : '标记已去' }}
                </button>
                <button class="state-btn" :class="{ active: attractionState.checked_in }" :disabled="stateActionLoading" @click="toggleAttractionState('checked_in')">
                  {{ attractionState.checked_in ? '已打卡' : '立即打卡' }}
                </button>
              </div>
              <div class="state-summary-tags">
                <span class="summary-tag" :class="{ on: attractionState.favorite }">收藏</span>
                <span class="summary-tag" :class="{ on: attractionState.want_to_go }">想去</span>
                <span class="summary-tag" :class="{ on: attractionState.visited }">已去</span>
                <span class="summary-tag" :class="{ on: attractionState.checked_in }">打卡</span>
              </div>
            </div>

            <div class="intro-card trip-action-card">
              <div class="intro-card-head trip-head">
                <h3>旅行记录</h3>
                <span class="trip-count">支持新建记录，也支持加入已有行程</span>
              </div>
              <div class="trip-actions-body">
                <label class="trip-field">
                  <span>新建旅行记录日期</span>
                  <input v-model="quickCreateDate" class="trip-date-input" type="date" />
                </label>
                <button class="trip-primary-btn" :disabled="tripActionLoading || !quickCreateDate" @click="createTripFromCurrentAttraction">
                  {{ tripActionLoading ? '处理中…' : '用这个景点新建旅行记录' }}
                </button>
                <div class="trip-split-line"></div>
                <label class="trip-field">
                  <span>加入已有行程</span>
                  <select v-model="selectedTripId" class="trip-select">
                    <option value="">请选择行程</option>
                    <option v-for="trip in tripOptions" :key="trip.id" :value="trip.id">{{ trip.title || `${trip.start_date} ${trip.city}` }}</option>
                  </select>
                </label>
                <button class="trip-secondary-btn" :disabled="tripActionLoading || !selectedTripId" @click="addCurrentAttractionToTrip">
                  {{ tripActionLoading ? '处理中…' : '加入所选行程' }}
                </button>
              </div>
            </div>
          </div>

          <div class="intro-card scenic-intro-card">
            <div class="intro-card-head">
              <h3>景区介绍</h3>
              <div class="intro-audio-actions">
                <button class="intro-audio-btn" @click="toggleNarration" :disabled="!narrationAvailable">
                  {{ narrationButtonText }}
                </button>
              </div>
            </div>
            <div v-if="currentNarrationSegment" class="intro-now-playing">
              <span>正在讲解</span>
              <p>{{ currentNarrationSegment }}</p>
            </div>
            <div class="intro-content">{{ cleanedIntro || '暂无景区介绍' }}</div>
          </div>
        </div>
      </div>
    </Transition>

    <div class="insights" v-if="insights && !searchText">
      <h3 class="insights-title">📊 数据洞察</h3>
      <div class="insight-grid">
        <div class="insight-card season-card">
          <div class="ic-icon-wrap">🌸</div>
          <div class="ic-content">
            <div class="ic-head">{{ insights.season }}适合去这些地方</div>
            <div class="ic-body">
              <span v-for="a in insights.current_season_top" :key="a.name" class="ic-tag">{{ a.name }}</span>
            </div>
          </div>
        </div>

        <div class="insight-card next-card">
          <div class="ic-icon-wrap">🔮</div>
          <div class="ic-content">
            <div class="ic-head">{{ insights.next_season }}值得期待</div>
            <div class="ic-body">
              <span v-for="a in insights.next_season_top" :key="a.name" class="ic-tag">{{ a.name }}</span>
            </div>
          </div>
        </div>

        <div class="insight-card gender-card">
          <div class="ic-icon-wrap">👩</div>
          <div class="ic-content">
            <div class="ic-head">女性游客偏爱这些类型</div>
            <div class="ic-body">
              <span v-for="t in insights.female_top_types" :key="t.type" class="ic-tag">{{ t.type }}</span>
            </div>
          </div>
        </div>

        <div class="insight-card gender-card">
          <div class="ic-icon-wrap">👨</div>
          <div class="ic-content">
            <div class="ic-head">男性游客偏爱这些类型</div>
            <div class="ic-body">
              <span v-for="t in insights.male_top_types" :key="t.type" class="ic-tag">{{ t.type }}</span>
            </div>
          </div>
        </div>

        <div class="insight-card age-card" v-for="(items, group) in insights.age_top" :key="group">
          <div class="ic-icon-wrap">👥</div>
          <div class="ic-content">
            <div class="ic-head">{{ group }}喜欢</div>
            <div class="ic-body">
              <span v-for="a in items" :key="a.name" class="ic-tag">{{ a.name }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <ScenicDigitalHuman
      :visible="showDigitalHuman"
      :attraction-name="attractionDetail.name || activeAttraction.name"
      :city="activeAttraction.city || selCity"
      :intro-text="cleanedIntro"
      @close="showDigitalHuman = false"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import ScenicDigitalHuman from '@/components/ScenicDigitalHuman.vue'
import {
  addAttractionToTrip,
  createTripWithAttraction,
  getAttractionDetail,
  getAttractionState,
  getHistory,
  getPlazaInsights,
  getPlazaProvinceDetail,
  getPlazaProvinces,
  getPlazaRecommendation,
  searchPlazaAttractions,
  updateAttractionState,
} from '@/services/api'

const router = useRouter()
const provinces = ref<any[]>([])
const selProvince = ref('')
const selCity = ref('')
const recommendation = ref('')
const hoverSeg = ref('')
const searchText = ref('')
const searchResults = ref<any[]>([])
const insights = ref<any>(null)

const detailLoading = ref(false)
const showDigitalHuman = ref(false)
const detailResponseSource = ref('')
const activeAttraction = ref<{ name: string; city: string; province?: string }>({ name: '', city: '' })
const attractionDetail = ref<any>({ image: '', intro: '', geo: null, weather: '', source: '' })
const narrationPlaying = ref(false)
const currentNarrationSegment = ref('')
const stateLoading = ref(false)
const stateActionLoading = ref(false)
const tripActionLoading = ref(false)
const selectedTripId = ref('')
const quickCreateDate = ref('')
const tripOptions = ref<any[]>([])
const tripActionFeedback = ref<null | {
  type: 'create' | 'append'
  title: string
  description: string
  tripId?: string
}>(null)
const attractionState = ref({
  name: '',
  city: '',
  favorite: false,
  want_to_go: false,
  visited: false,
  checked_in: false,
  updated_at: '',
})

let narrationSynth: SpeechSynthesis | null = null
let narrationSegments: string[] = []
let narrationKey = ''

const totalCount = computed(() => provinces.value.reduce((s: number, p: any) => s + p.count, 0))
const maxCount = computed(() => Math.max(...provinces.value.map((p: any) => p.count), 1))
const sortedProvinces = computed(() => [...provinces.value].sort((a, b) => b.count - a.count))

const colors = ['#c43b3b', '#d4734e', '#d4946e', '#d4a070', '#c4a080', '#b8a090', '#a0a8b8', '#88a0c0', '#7098c8', '#8098b8', '#9098a8', '#a09898']
const pieSegs = computed(() => {
  const all = [...provinces.value].sort((a, b) => b.count - a.count)
  const top12 = all.slice(0, 12)
  const shown = top12.filter((p) => p.count > 0)
  const circ = 2 * Math.PI * 70
  let off = 0
  return shown.map((p, i) => {
    const r = p.count / totalCount.value
    const d = circ * r
    const s = { name: p.name, count: p.count, dash: `${d} ${circ}`, offset: -off, color: colors[i % colors.length] }
    off += d
    return s
  })
})

const provinceData = computed(() => provinces.value.find((p: any) => p.name === selProvince.value)?._detail)
const cityAttractions = computed(() => {
  if (!selCity.value || !provinceData.value) return []
  return provinceData.value.cities.find((c: any) => c.name === selCity.value)?.attractions || []
})
const cityTotal = computed(() => cityAttractions.value.reduce((s: number, a: any) => s + a.count, 0))
const cleanedIntro = computed(() =>
  String(attractionDetail.value?.intro || '')
    .replace(/[*#[\]()`>_]/g, '')
    .replace(/###.*\n/g, '')
    .replace(/##.*\n/g, '')
    .trim()
)

const narrationButtonText = computed(() => (narrationPlaying.value ? '停止讲解' : '播放讲解'))
const narrationAvailable = computed(() => !detailLoading.value && !!cleanedIntro.value)

function ensureNarrationSpeech() {
  if (typeof window === 'undefined') return null
  if (!narrationSynth && 'speechSynthesis' in window) {
    narrationSynth = window.speechSynthesis
  }
  return narrationSynth
}

function splitNarrationSegments(content: string) {
  const raw = content.split(/(?<=[。！？\n])/g).filter((s) => s.trim())
  const segs: string[] = []
  for (const s of raw) {
    if (s.length <= 42) {
      segs.push(s.trim())
      continue
    }
    const sub = s.split(/[,，]/g).filter((x) => x.trim())
    let buf = ''
    for (const ss of sub) {
      if (buf.length + ss.length > 42 && buf) {
        segs.push(buf.trim())
        buf = ss
      } else {
        buf += ss
      }
    }
    if (buf.trim()) segs.push(buf.trim())
  }
  return segs.filter(Boolean)
}

function stopNarration() {
  const synth = ensureNarrationSpeech()
  if (synth) synth.cancel()
  narrationPlaying.value = false
  currentNarrationSegment.value = ''
  narrationSegments = []
}

function playNarrationAt(index: number) {
  if (index >= narrationSegments.length) {
    narrationPlaying.value = false
    currentNarrationSegment.value = ''
    narrationSegments = []
    return
  }

  const seg = narrationSegments[index]
  currentNarrationSegment.value = seg
  narrationPlaying.value = true

  const synth = ensureNarrationSpeech()
  if (!synth) {
    playNarrationAt(index + 1)
    return
  }

  synth.cancel()
  const utterance = new SpeechSynthesisUtterance(seg)
  utterance.lang = 'zh-CN'
  utterance.rate = 1
  utterance.pitch = 1.02
  utterance.onend = () => playNarrationAt(index + 1)
  utterance.onerror = () => stopNarration()
  synth.speak(utterance)
}

function playNarration() {
  const intro = cleanedIntro.value
  if (!intro) return

  stopNarration()
  narrationKey = `${attractionDetail.value?.name || activeAttraction.value.name}|${activeAttraction.value.city || selCity.value || ''}|${intro}`
  narrationSegments = splitNarrationSegments(intro)
  if (!narrationSegments.length) return
  playNarrationAt(0)
}

function toggleNarration() {
  if (narrationPlaying.value) {
    stopNarration()
    return
  }
  playNarration()
}

function openDigitalHuman() {
  stopNarration()
  showDigitalHuman.value = false
  requestAnimationFrame(() => {
    showDigitalHuman.value = true
  })
}

function buildCurrentAttractionPayload() {
  const geo = attractionDetail.value?.geo || {}
  let lat: number | null = null
  let lng: number | null = null
  const rawLocation = String(geo.location || '').trim()
  if (rawLocation.includes(',')) {
    const [rawLng, rawLat] = rawLocation.split(',')
    const parsedLat = Number(rawLat)
    const parsedLng = Number(rawLng)
    lat = Number.isFinite(parsedLat) ? parsedLat : null
    lng = Number.isFinite(parsedLng) ? parsedLng : null
  }
  return {
    name: attractionDetail.value?.name || activeAttraction.value.name,
    city: activeAttraction.value.city || selCity.value || '',
    intro: cleanedIntro.value,
    image: attractionDetail.value?.image || '',
    location: lat !== null && lng !== null ? { lat, lng } : null,
  }
}

function openTripDetail(id?: string) {
  if (!id) return
  router.push({ path: `/history/${id}` })
}

async function loadTripOptions() {
  try {
    const res = await getHistory()
    tripOptions.value = (res?.data || []).filter((item: any) => item?.id)
    if (selectedTripId.value && !tripOptions.value.find((item: any) => item.id === selectedTripId.value)) {
      selectedTripId.value = ''
    }
  } catch {
    tripOptions.value = []
  }
}

async function loadCurrentAttractionState(name: string, city = '') {
  if (!name) return
  stateLoading.value = true
  try {
    const res = await getAttractionState(name, city)
    if (res?.success && res.data) {
      attractionState.value = {
        name: res.data.name || name,
        city: res.data.city || city,
        favorite: !!res.data.favorite,
        want_to_go: !!res.data.want_to_go,
        visited: !!res.data.visited,
        checked_in: !!res.data.checked_in,
        updated_at: res.data.updated_at || '',
      }
    }
  } catch {
    attractionState.value = {
      name,
      city,
      favorite: false,
      want_to_go: false,
      visited: false,
      checked_in: false,
      updated_at: '',
    }
  } finally {
    stateLoading.value = false
  }
}

async function toggleAttractionState(field: 'favorite' | 'want_to_go' | 'visited' | 'checked_in') {
  const name = attractionDetail.value?.name || activeAttraction.value.name
  const city = activeAttraction.value.city || selCity.value || ''
  if (!name) return

  const nextValue = !attractionState.value[field]
  const payload: {
    name: string
    city: string
    favorite?: boolean
    want_to_go?: boolean
    visited?: boolean
    checked_in?: boolean
  } = { name, city, [field]: nextValue }
  if (field === 'checked_in' && nextValue) payload.visited = true
  if (field === 'visited' && !nextValue) payload.checked_in = false

  stateActionLoading.value = true
  try {
    const res = await updateAttractionState(payload)
    if (res?.success) {
      attractionState.value = {
        ...attractionState.value,
        ...res.data,
      }
      const labelMap = {
        favorite: nextValue ? '已收藏该景点' : '已取消收藏',
        want_to_go: nextValue ? '已标记为想去' : '已取消想去',
        visited: nextValue ? '已标记为去过' : '已取消已去标记',
        checked_in: nextValue ? '打卡成功' : '已取消打卡',
      }
      message.success(labelMap[field])
    } else {
      message.error(res?.message || '更新景点状态失败')
    }
  } catch {
    message.error('更新景点状态失败，请稍后再试')
  } finally {
    stateActionLoading.value = false
  }
}

async function addCurrentAttractionToTrip() {
  if (!selectedTripId.value) {
    message.warning('请先选择一个目标行程')
    return
  }
  tripActionLoading.value = true
  tripActionFeedback.value = null
  try {
    const res = await addAttractionToTrip({
      tripId: selectedTripId.value,
      attraction: buildCurrentAttractionPayload(),
    })
    if (res?.success) {
      const matchedTrip = tripOptions.value.find((item: any) => item.id === selectedTripId.value)
      const summary = matchedTrip?.title || `${matchedTrip?.start_date || ''} ${matchedTrip?.city || ''}`.trim() || '所选旅行记录'
      tripActionFeedback.value = {
        type: 'append',
        title: `已把「${buildCurrentAttractionPayload().name}」加入旅行记录`,
        description: `景点已收进 ${summary}，现在可以继续去完善预算、清单和笔记。`,
        tripId: selectedTripId.value,
      }
      message.success(res.message || '已加入行程')
      await loadTripOptions()
    } else {
      message.error(res?.message || '加入行程失败')
    }
  } catch {
    message.error('加入行程失败，请稍后再试')
  } finally {
    tripActionLoading.value = false
  }
}

async function createTripFromCurrentAttraction() {
  if (!quickCreateDate.value) {
    message.warning('请先选择出发日期')
    return
  }
  tripActionLoading.value = true
  tripActionFeedback.value = null
  try {
    const res = await createTripWithAttraction({
      city: activeAttraction.value.city || selCity.value || '未知城市',
      startDate: quickCreateDate.value,
      attraction: buildCurrentAttractionPayload(),
    })
    if (res?.success) {
      const createdTrip = res?.data || null
      const newTripId = createdTrip?.id || ''
      const summary = createdTrip?.title || `${quickCreateDate.value} ${activeAttraction.value.city || selCity.value || '旅行记录'}`
      tripActionFeedback.value = {
        type: 'create',
        title: `已为「${buildCurrentAttractionPayload().name}」新建旅行记录`,
        description: `出发日期：${quickCreateDate.value}，已自动收进 ${summary}`,
        tripId: newTripId,
      }
      message.success(res.message || '已创建行程')
      selectedTripId.value = newTripId
      await loadTripOptions()
    } else {
      message.error(res?.message || '创建行程失败')
    }
  } catch {
    message.error('创建行程失败，请稍后再试')
  } finally {
    tripActionLoading.value = false
  }
}

async function loadPlaza() {
  try {
    const p = await getPlazaProvinces()
    provinces.value = p.data || []
  } catch {}

  try {
    const d = await getPlazaRecommendation()
    recommendation.value = d.recommendation || ''
  } catch {}
}

async function loadDetail(prov: string) {
  try {
    const d = await getPlazaProvinceDetail(prov)
    if (d.success) {
      const i = provinces.value.findIndex((p: any) => p.name === prov)
      if (i >= 0) provinces.value[i]._detail = d.data
    }
  } catch {}
}

watch(selProvince, (v) => {
  if (v) loadDetail(v)
})

let searchTimer: any = null
function doSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    if (!searchText.value.trim()) {
      searchResults.value = []
      return
    }
    try {
      const d = await searchPlazaAttractions(searchText.value)
      searchResults.value = (d.data || []).map((a: any) => ({ ...a, type: 'attraction' }))
    } catch {}
  }, 300)
}

async function jumpTo(r: any) {
  selProvince.value = r.province
  selCity.value = r.city || ''
  activeAttraction.value = { name: '', city: '', province: r.province }
  searchText.value = ''
  searchResults.value = []
  if (r.type === 'attraction' || r.city) {
    await openAttractionDetail(r.name, r.city || '')
  }
}

function goToNationwide() {
  stopNarration()
  selProvince.value = ''
  selCity.value = ''
  activeAttraction.value = { name: '', city: '' }
}

function goToProvince() {
  stopNarration()
  selCity.value = ''
  activeAttraction.value = { name: '', city: '', province: selProvince.value }
}

function goToCity() {
  stopNarration()
  activeAttraction.value = { name: '', city: selCity.value, province: selProvince.value }
}

async function loadInsights() {
  try {
    const d = await getPlazaInsights()
    if (d.success) insights.value = d.data
  } catch {}
}

async function openAttractionDetail(name: string, city = '') {
  stopNarration()
  activeAttraction.value = { name, city, province: selProvince.value }
  attractionDetail.value = { name, image: '', intro: '', geo: null, weather: '', source: '' }
  detailResponseSource.value = ''
  detailLoading.value = true
  await Promise.allSettled([loadTripOptions(), loadCurrentAttractionState(name, city)])
  try {
    const res = await getAttractionDetail(name, city)
    if (res?.success) {
      attractionDetail.value = { ...res.data }
      detailResponseSource.value = res.source || ''
    } else {
      attractionDetail.value = {
        name,
        image: '',
        intro: res?.message || '暂时无法获取景区介绍，请稍后再试。',
        geo: null,
        weather: '',
        source: '',
      }
    }
  } catch {
    attractionDetail.value = {
      name,
      image: '',
      intro: '暂时无法获取景区介绍，请稍后再试。',
      geo: null,
      weather: '',
      source: '',
    }
  } finally {
    detailLoading.value = false
  }
}

watch(
  () => `${attractionDetail.value?.name || activeAttraction.value.name}|${activeAttraction.value.city || selCity.value || ''}|${cleanedIntro.value}`,
  (key) => {
    if (!key) return
    if (key !== narrationKey) stopNarration()
  }
)

onMounted(() => {
  quickCreateDate.value = new Date().toISOString().slice(0, 10)
  loadPlaza()
  loadInsights()
  loadTripOptions()
})

onBeforeUnmount(() => {
  stopNarration()
})
</script>

<style scoped>
.plaza { padding: 28px 36px; max-width: 960px; margin: 0 auto; animation: viewIn 0.35s ease-out both }
@keyframes viewIn { from { opacity: 0; transform: scale(.98) translateY(6px) } to { opacity: 1; transform: scale(1) translateY(0) } }

.plaza-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; margin-bottom: 16px; flex-wrap: wrap }
.plaza-head h1 { font-size: 26px; font-weight: 800; color: #5c3a21; margin: 0; font-family: 'STKaiti', '楷体', 'KaiTi', serif }
.plaza-head p { font-size: 14px; color: #b8a088; margin: 4px 0 0 }

.plaza-search { position: relative; min-width: 240px }
.search-inp { width: 100%; padding: 10px 38px 10px 16px; border: 2px solid #eadccf; border-radius: 22px; font-size: 14px; color: #5c3a21; outline: none; background: #fff; transition: border-color .2s }
.search-inp:focus { border-color: #c43b3b }
.search-icon { position: absolute; right: 14px; top: 50%; transform: translateY(-50%); font-size: 16px; pointer-events: none }
.search-results { background: #fff; border: 1px solid #eadccf; border-radius: 14px; margin-bottom: 16px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,.06) }
.search-item { display: flex; align-items: center; gap: 10px; padding: 12px 16px; cursor: pointer; transition: background .15s; border-bottom: 1px solid #f5f0eb }
.search-item:hover { background: #fdf8f3 }
.sr-type { font-size: 18px }
.sr-info { flex: 1; display: flex; flex-direction: column }
.sr-name { font-size: 14px; font-weight: 600; color: #5c3a21 }
.sr-path { font-size: 11px; color: #b8a088 }
.sr-count { font-size: 12px; color: #b8a088 }

.plaza-reco { display: flex; align-items: center; gap: 10px; padding: 12px 18px; background: linear-gradient(135deg,#fdf5ee,#fef9f4); border: 1px solid #e8d0bf; border-radius: 14px; margin-bottom: 16px }
.reco-icon { font-size: 20px }
.reco-text { font-size: 14px; color: #6b5344; line-height: 1.6 }

.bread { display: flex; align-items: center; gap: 4px; margin-bottom: 18px; font-size: 14px }
.bread span { cursor: pointer; color: #b8a088; padding: 4px 8px; border-radius: 6px; transition: all .15s }
.bread span:hover { color: #c43b3b; background: #fdf5ee }
.bread span.on { color: #5c3a21; font-weight: 600; cursor: default }
.sep { cursor: default !important; color: #ddd !important; padding: 0 !important }

.view { display: flex; gap: 24px }
.pie-section { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 10px }
.pie-visual { position: relative; width: 180px; height: 180px }
.pie-svg { width: 100%; height: 100% }
.pie-center-hint { position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); font-size: 13px; color: #c43b3b; font-weight: 600; background: #fdf5ee; padding: 2px 10px; border-radius: 8px }
.pie-legend { width: 100%; display: flex; flex-direction: column; gap: 3px }
.legend-row { display: flex; align-items: center; gap: 8px; cursor: pointer; padding: 5px 8px; border-radius: 6px; font-size: 13px; transition: background .15s }
.legend-row:hover { background: #faf7f2 }
.lg-dot { width: 9px; height: 9px; border-radius: 2px; flex-shrink: 0 }
.lg-name { width: 48px; flex-shrink: 0; color: #5c3a21 }
.lg-bar { flex: 1; height: 6px; background: #f0ebe5; border-radius: 3px; overflow: hidden }
.lg-bar i { display: block; height: 100%; border-radius: 3px; transition: width .5s }
.lg-num { font-size: 11px; color: #b8a088; width: 50px; text-align: right }

.prov-list { flex: 1; min-width: 0 }
.prov-list h3 { font-size: 15px; color: #5c3a21; margin: 0 0 8px; font-family: 'STKaiti', '楷体', 'KaiTi', serif }
.prov-scroll { max-height: 340px; overflow-y: auto; padding-right: 4px }
.prov-scroll::-webkit-scrollbar { width: 4px }
.prov-scroll::-webkit-scrollbar-thumb { background: #eadccf; border-radius: 2px }
.prov-row { display: flex; align-items: center; gap: 8px; padding: 5px 8px; border-radius: 6px; cursor: pointer; font-size: 13px; transition: all .15s }
.prov-row:hover { background: #faf7f2 }
.pr-rank { width: 22px; height: 22px; border-radius: 50%; background: #f0ebe5; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; color: #b8a088; flex-shrink: 0 }
.pr-rank.top3 { background: #fdf0e8; color: #c43b3b }
.pr-name { width: 56px; flex-shrink: 0; color: #5c3a21 }
.pr-bar-wrap { flex: 1; height: 7px; background: #f0ebe5; border-radius: 4px; overflow: hidden }
.pr-bar { display: block; height: 100%; background: linear-gradient(90deg,#d4a89a,#c43b3b); border-radius: 4px; transition: width .6s }
.pr-num { font-size: 12px; color: #b8a088; width: 55px; text-align: right }

.view.detail { flex-direction: column; gap: 16px }
.view.detail h3 { font-size: 17px; color: #5c3a21; margin: 0; font-family: 'STKaiti', '楷体', 'KaiTi', serif }

.city-grid { display: flex; flex-direction: column; gap: 8px }
.city-tile { display: flex; align-items: center; gap: 14px; padding: 16px 20px; background: #fff; border: 1px solid #eadccf; border-radius: 14px; cursor: pointer; transition: all .2s }
.city-tile:hover { border-color: #c43b3b; box-shadow: 0 3px 14px rgba(196,59,59,.08); transform: translateY(-2px) }
.ct-rank { width: 28px; height: 28px; border-radius: 50%; background: #fdf0e8; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; color: #c43b3b; flex-shrink: 0 }
.ct-info { flex: 1; display: flex; justify-content: space-between; align-items: center }
.ct-name { font-size: 15px; font-weight: 600; color: #5c3a21 }
.ct-count { font-size: 12px; color: #b8a088 }
.ct-bar { height: 5px; background: #eadccf; border-radius: 3px; overflow: hidden; width: 120px; flex-shrink: 0 }
.ct-bar div { height: 100%; background: linear-gradient(90deg,#d4a89a,#c43b3b); border-radius: 3px; transition: width .5s }

.attr-list { display: flex; flex-direction: column; gap: 6px }
.attr-row { display: flex; align-items: center; gap: 12px; padding: 10px 14px; background: #fff; border: 1px solid #eadccf; border-radius: 10px; transition: all .15s }
.attr-row:hover { background: #fdf8f3 }
.attr-row.clickable { cursor: pointer }
.attr-row.clickable:hover { border-color: #c43b3b; transform: translateY(-1px); box-shadow: 0 3px 12px rgba(196,59,59,.08) }
.ar-rank { width: 24px; height: 24px; border-radius: 50%; background: #f0ebe5; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; color: #b8a088; flex-shrink: 0 }
.ar-rank.top { background: #fdf0e8; color: #c43b3b }
.ar-name { flex: 1; font-size: 14px; color: #5c3a21 }
.ar-bar { width: 120px; height: 5px; background: #f0ebe5; border-radius: 3px; overflow: hidden; flex-shrink: 0 }
.ar-bar i { display: block; height: 100%; background: #d4a89a; border-radius: 3px; transition: width .5s }
.ar-num { font-size: 12px; color: #b8a088; width: 55px; text-align: right }

.slide-enter-active,.slide-leave-active { transition: all .3s ease }
.slide-enter-from,.slide-leave-to { opacity: 0; transform: translateY(8px) }
.list-enter-active,.list-leave-active { transition: all .3s ease }
.list-enter-from,.list-leave-to { opacity: 0; transform: translateX(-10px) }

.insights { margin-top: 28px }
.insights-title { font-size: 18px; font-weight: 700; color: #5c3a21; margin: 0 0 12px; font-family: 'STKaiti', '楷体', 'KaiTi', serif }
.insight-grid { display: flex; flex-direction: column; gap: 10px }
.insight-card { background: #fff; border: 1px solid #eadccf; border-radius: 14px; padding: 16px 20px; transition: all .3s; animation: cardUp .4s ease-out both; display: flex; align-items: center; gap: 16px }
.insight-card:hover { transform: translateX(4px); box-shadow: 0 4px 18px rgba(139,69,19,.08); border-color: #d4a89a }
.insight-card:nth-child(1){animation-delay:.1s}.insight-card:nth-child(2){animation-delay:.18s}.insight-card:nth-child(3){animation-delay:.26s}.insight-card:nth-child(4){animation-delay:.34s}.insight-card:nth-child(5){animation-delay:.42s}.insight-card:nth-child(6){animation-delay:.50s}.insight-card:nth-child(7){animation-delay:.58s}
.ic-icon-wrap { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0 }
.season-card .ic-icon-wrap { background: linear-gradient(135deg,#fef0e6,#fde8d8) }
.next-card .ic-icon-wrap { background: linear-gradient(135deg,#e6f0fe,#d8e8fd) }
.gender-card .ic-icon-wrap { background: linear-gradient(135deg,#fde6f0,#fcd8e8) }
.age-card .ic-icon-wrap { background: linear-gradient(135deg,#e6fde6,#d8fcd8) }
.ic-content { flex: 1; min-width: 0 }
.ic-head { font-size: 15px; font-weight: 700; color: #5c3a21; margin-bottom: 10px; font-family: 'STKaiti', '楷体', 'KaiTi', serif }
.ic-body { display: flex; flex-wrap: wrap; gap: 8px }
.ic-tag { color: #6b5344; background: #fdf0e8; padding: 3px 12px; border-radius: 12px; font-size: 12px; white-space: nowrap }

.guide-btn { padding: 11px 18px; border: none; border-radius: 999px; background: linear-gradient(135deg,#c43b3b,#a0522d); color: #fff; cursor: pointer; white-space: nowrap }
.guide-btn:disabled { opacity: .45; cursor: not-allowed }
.scenic-detail-page { gap: 18px }
.scenic-page-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; padding: 4px 0 }
.scenic-kicker { font-size: 12px; color: #c43b3b; letter-spacing: 1px; margin-bottom: 6px }
.scenic-page-head h2 { margin: 0; color: #5c3a21; font-size: 30px; font-family: 'STKaiti', '楷体', 'KaiTi', serif }
.scenic-meta { margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap }
.scenic-meta span { background: #f8eee4; color: #8f6e55; font-size: 12px; padding: 5px 10px; border-radius: 999px }
.scenic-loading { padding: 42px 20px; text-align: center; color: #8f6e55; background: #fff; border: 1px solid #eadccf; border-radius: 18px }
.scenic-page-body { display: flex; flex-direction: column; gap: 18px }
.hero-card { display: grid; grid-template-columns: minmax(280px, 1.2fr) minmax(220px, .8fr); gap: 16px; align-items: stretch }
.hero-image-wrap { border-radius: 20px; overflow: hidden; background: #f3e8dc; min-height: 280px }
.hero-image { width: 100%; height: 100%; min-height: 280px; object-fit: cover; display: block }
.hero-placeholder { height: 100%; min-height: 280px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #b08d74; gap: 8px }
.hero-placeholder span { font-size: 54px }
.hero-side { display: flex; flex-direction: column; gap: 12px }
.hero-info, .intro-card { background: #fff; border: 1px solid #eadccf; border-radius: 18px; padding: 18px }
.hero-info h4, .intro-card h3 { margin: 0 0 10px; color: #5c3a21; font-size: 18px; font-family: 'STKaiti', '楷体', 'KaiTi', serif }
.hero-info p { margin: 0 0 8px; color: #6b5344; line-height: 1.7; font-size: 14px }
.hero-info p:last-child { margin-bottom: 0 }
.hero-tips { background: linear-gradient(135deg,#fff7ee,#fff) }
.action-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px }
.intro-card-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 10px }
.state-sync-text,.trip-count { font-size: 12px; color: #b08d74 }
.state-actions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px }
.state-btn { border: 1px solid #eadccf; background: #faf7f2; color: #6b5344; border-radius: 14px; padding: 10px 12px; cursor: pointer; transition: all .2s }
.state-btn:hover { border-color: #c43b3b; color: #c43b3b }
.state-btn.active { background: linear-gradient(135deg,#fff0ea,#fff8f2); color: #c43b3b; border-color: #e4b5a1; font-weight: 600 }
.state-btn:disabled { opacity: .55; cursor: not-allowed }
.state-summary-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px }
.summary-tag { font-size: 12px; padding: 5px 10px; border-radius: 999px; background: #f5eee8; color: #9a7b61 }
.summary-tag.on { background: #fff1ec; color: #c43b3b }
.trip-head { align-items: flex-start }
.trip-actions-body { display: flex; flex-direction: column; gap: 12px }
.trip-field { display: flex; flex-direction: column; gap: 6px; color: #6b5344; font-size: 13px }
.trip-select,.trip-date-input { border: 1px solid #eadccf; border-radius: 12px; padding: 10px 12px; font-size: 14px; color: #5c3a21; background: #fff }
.trip-primary-btn,.trip-secondary-btn { border: none; border-radius: 999px; padding: 10px 16px; cursor: pointer; transition: all .2s }
.trip-primary-btn { background: linear-gradient(135deg,#c43b3b,#a0522d); color: #fff }
.trip-secondary-btn { background: #f8eee4; color: #8b5e3c }
.trip-primary-btn:disabled,.trip-secondary-btn:disabled { opacity: .55; cursor: not-allowed }
.trip-split-line { height: 1px; background: #f0e3d6; margin: 2px 0 }
.intro-audio-actions { display: flex; justify-content: flex-end }
.intro-audio-btn { border: none; border-radius: 999px; padding: 8px 14px; background: #f8eee4; color: #8b5e3c; cursor: pointer; white-space: nowrap }
.intro-audio-btn:disabled { opacity: .5; cursor: not-allowed }
.intro-now-playing { margin-bottom: 12px; padding: 12px 14px; border-radius: 14px; background: linear-gradient(135deg,#fdf5ee,#fff); border: 1px solid #f0dcc8 }
.intro-now-playing span { display: inline-block; font-size: 12px; color: #c43b3b; margin-bottom: 6px }
.intro-now-playing p { margin: 0; color: #6b5344; line-height: 1.8; font-size: 14px }
.intro-content { white-space: pre-wrap; color: #5f4839; line-height: 1.95; font-size: 15px }

@media (max-width: 767px) {
  .plaza { padding: 14px }
  .view { flex-direction: column }
  .plaza-top { flex-direction: column }
  .plaza-search { width: 100% }
  .ct-bar,.ar-bar { width: 60px }
  .insight-card { padding: 16px; gap: 14px }
  .ic-icon-wrap { width: 44px; height: 44px; font-size: 22px; border-radius: 10px }
  .scenic-page-head { flex-direction: column }
  .hero-card { grid-template-columns: 1fr }
  .action-grid { grid-template-columns: 1fr }
  .state-actions { grid-template-columns: 1fr 1fr }
}
</style>
