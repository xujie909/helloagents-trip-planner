<template>
  <div class="homepage">
    <!-- 左侧主内容 -->
    <div class="main-col">
      <!-- 顶部横幅 -->
      <div class="hero">
        <div class="hero-bg-deco">
          <span class="deco-dot d1"></span><span class="deco-dot d2"></span><span class="deco-dot d3"></span>
        </div>
        <div class="hero-mountains">
          <span class="mtn" v-for="i in 4" :key="i" :style="{ animationDelay: i * 0.3 + 's' }">⛰️</span>
        </div>
        <div class="hero-cloud c1">☁️</div><div class="hero-cloud c2">☁️</div>

        <div class="hero-content">
          <div class="hero-left">
            <div class="hero-seal">行</div>
            <div class="hero-text">
              <h1 class="hero-greeting">
                <span
                  v-for="(c, i) in greetingChars"
                  :key="i"
                  class="greeting-char"
                  :style="{ animationDelay: 0.1 * i + 's' }"
                >{{ c }}</span>
              </h1>
              <p class="hero-poem">{{ poem }}</p>
            </div>
          </div>
          <div class="hero-time">
            <span class="time-val">{{ timeStr }}</span>
            <span class="time-date">{{ dateStr }}</span>
          </div>
        </div>
      </div>

      <!-- 信息卡片 -->
      <div class="cards-row">
        <div class="card card-loc" @click="openCityPicker">
          <div class="card-head"><span class="card-seal">地</span><span class="card-label">所在</span></div>
          <span class="card-val" :class="{ pulse: !city }">{{ city || '点击设置' }}</span>
          <span class="card-hint" v-if="!city">点击选择 →</span>
        </div>
        <div class="card card-wth">
          <div class="card-head"><span class="card-seal">天</span><span class="card-label">气象</span></div>
          <span class="card-val-big">{{ weatherIcon }} {{ weather || '--' }}</span>
        </div>
        <div class="card card-tmp">
          <div class="card-head"><span class="card-seal">温</span><span class="card-label">冷暖</span></div>
          <span class="card-val-big">{{ temp || '--°C' }}</span>
        </div>
        <div class="card card-hmd">
          <div class="card-head"><span class="card-seal">润</span><span class="card-label">湿度</span></div>
          <span class="card-val-big">{{ humidity || '--%' }}</span>
        </div>
      </div>

      <!-- 下一步入口 -->
      <div class="shortcuts">
        <div class="shortcut chat-s" @click="emitNavigate('chat')">
          <div class="s-left"><span class="s-icon">💬</span><div><span class="s-title">旅行顾问</span><span class="s-desc">山川异域 · 风月同天</span></div></div><span class="s-arrow">→</span>
        </div>
        <div class="shortcut plan-s" @click="emitNavigate('plan')">
          <div class="s-left"><span class="s-icon">📜</span><div><span class="s-title">行程规划</span><span class="s-desc">千里之行 · 始于足下</span></div></div><span class="s-arrow">→</span>
        </div>
        <div class="shortcut plaza-s" @click="emitNavigate('plaza')">
          <div class="s-left"><span class="s-icon">📊</span><div><span class="s-title">灵感广场</span><span class="s-desc">热门目的地 · 偏好推荐</span></div></div><span class="s-arrow">→</span>
        </div>
        <div class="shortcut hist-s" @click="emitNavigate('history')">
          <div class="s-left"><span class="s-icon">📋</span><div><span class="s-title">行囊记录</span><span class="s-desc">往事如烟 · 历历在目</span></div></div><span class="s-arrow">→</span>
        </div>
      </div>

      <!-- 首页推荐与回流 -->
      <div v-if="homeCacheNotice" :class="['cache-note', { stale: homeCacheNotice.stale }]">
        <strong>{{ homeCacheNotice.stale ? '当前显示的是上次成功加载的首页内容' : '首页部分内容来自本地缓存' }}</strong>
        <p>{{ homeCacheNotice.message }}</p>
      </div>

      <div class="home-grid">
        <section class="feature-panel recommend-panel">
          <div class="panel-head">
            <div>
              <div class="panel-title-row"><span class="panel-seal">荐</span><h3>今日灵感</h3></div>
              <p>结合你的档案、天气和近期足迹，给你一个更适合此刻的出发方向。</p>
            </div>
            <button class="ghost-btn" @click="reloadRecommendation" :disabled="recommendationLoading">
              {{ recommendationLoading ? '刷新中...' : '换个推荐' }}
            </button>
          </div>
          <div class="recommend-body">
            <p class="recommend-text">{{ personalizedRecommendation }}</p>
            <div class="recommend-tags">
              <span class="rec-tag">{{ city ? `${city}天气灵感` : '随心出发' }}</span>
              <span class="rec-tag" v-if="profileFilled">{{ preferenceBadge }}</span>
              <span class="rec-tag" v-if="recentStates.length">最近沉淀 {{ recentStates.length }} 条足迹</span>
            </div>
            <div class="recommend-actions">
              <button class="primary-btn" @click="emitNavigate('plaza')">去找灵感</button>
              <button class="secondary-btn" @click="continuePrimaryAction">
                {{ currentTrip ? '继续当前旅程' : stats?.trip_count ? '继续我的旅程' : '开始规划行程' }}
              </button>
            </div>
          </div>
        </section>

        <section class="feature-panel summary-panel">
          <div class="panel-head">
            <div>
              <div class="panel-title-row"><span class="panel-seal">偏</span><h3>我的偏好摘要</h3></div>
              <p>{{ profileFilled ? '首页和档案页共用同一份旅行画像。' : '先写一点偏好，推荐会更像懂你的朋友。' }}</p>
            </div>
            <button class="ghost-btn" @click="showProfile = true">{{ profileFilled ? '修改档案' : '填写档案' }}</button>
          </div>
          <div v-if="profileFilled" class="summary-list">
            <div v-for="item in profileSummaryItems" :key="item.label" class="summary-item">
              <span class="summary-label">{{ item.label }}</span>
              <span class="summary-value">{{ item.value }}</span>
            </div>
          </div>
          <div v-else class="summary-empty">
            <p>告诉我你的旅行习惯、同行者和出发动机，首页推荐、广场推荐都会更贴近你。</p>
            <button class="primary-btn" @click="showProfile = true">立即建立旅行档案</button>
          </div>
        </section>
      </div>

      <section v-if="currentTrip" class="feature-panel current-trip-panel">
        <div class="panel-head current-trip-head">
          <div>
            <div class="panel-title-row"><span class="panel-seal">程</span><h3>当前旅程</h3></div>
            <p>从首页直接回到你上次正在推进的那条旅行记录。</p>
          </div>
          <span class="current-trip-badge">{{ currentTrip.sourceLabel }}</span>
        </div>
        <div class="current-trip-body">
          <div>
            <div class="current-trip-title">{{ currentTrip.title }}</div>
            <div class="current-trip-meta">
              <span v-if="currentTrip.city">🏙️ {{ currentTrip.city }}</span>
              <span v-if="currentTrip.startDate">📆 {{ currentTrip.startDate }}</span>
              <span v-if="currentTrip.updatedAtLabel">🕘 {{ currentTrip.updatedAtLabel }}</span>
            </div>
            <p class="current-trip-desc">
              {{ currentTrip.lastViewLabel }}
              <template v-if="currentTrip.lastDetailTabLabel"> · 上次停在 {{ currentTrip.lastDetailTabLabel }}</template>
            </p>
          </div>
          <div class="current-trip-actions">
            <button class="primary-btn" @click="emitNavigate('resume-current-trip')">继续执行</button>
            <button class="secondary-btn" @click="emitNavigate('history')">打开行囊记录</button>
          </div>
        </div>
      </section>

      <!-- 最近收藏与足迹 -->
      <section class="feature-panel states-panel">
        <div class="panel-head states-head">
          <div>
            <div class="panel-title-row"><span class="panel-seal">迹</span><h3>最近收藏与足迹</h3></div>
            <p>把你在广场和旅途中留下的“收藏、想去、去过、打卡”都拉回首页看一眼。</p>
          </div>
          <button class="ghost-btn" @click="emitNavigate('history')">去行囊记录</button>
        </div>

        <div v-if="recentStates.length" class="states-grid">
          <div v-for="item in recentStates" :key="`${item.name}-${item.city}`" class="state-card">
            <div class="state-main">
              <div>
                <div class="state-name">{{ item.name }}</div>
                <div class="state-city">{{ item.city || '旅行足迹' }}</div>
              </div>
              <span class="state-badge">{{ formatStateBadge(item) }}</span>
            </div>
            <div class="state-flags">
              <span v-if="item.favorite">❤️ 收藏</span>
              <span v-if="item.want_to_go">🧭 想去</span>
              <span v-if="item.visited">👣 去过</span>
              <span v-if="item.checked_in">📍 打卡</span>
            </div>
          </div>
        </div>
        <div v-else class="states-empty">
          <p>你还没有沉淀景点状态，去数据广场逛逛，把喜欢和想去的地方先收藏起来吧。</p>
          <button class="secondary-btn" @click="emitNavigate('plaza')">去数据广场</button>
        </div>
      </section>

      <!-- AI 旅行锦囊 -->
      <div class="ai-tip-card">
        <div class="ai-tip-inner" @click="refreshSuggestion">
          <div class="ai-tip-head">
            <img src="/meiling-avatar.png" class="ai-tip-avatar" @click.stop="refreshSuggestion" title="换一条锦囊" />
            <span class="ai-tip-title">红美玲</span>
          </div>
          <p class="ai-tip-text" v-if="suggestion">
            <span class="ai-quote-l">「</span>{{ suggestion }}<span class="ai-quote-r">」</span>
          </p>
          <p class="ai-tip-text ai-tip-empty" v-else>点击头像获取旅行灵感 ✨</p>
          <div class="ai-tip-shine"></div>
        </div>
      </div>
    </div>

    <!-- 右侧栏 -->
    <aside class="side-col">
      <!-- 用户数据面板 -->
      <div class="stats-panel">
        <div class="stats-head">
          <span class="stats-seal">迹</span>
          <span class="stats-title">我的行迹</span>
        </div>
        <div class="stats-list">
          <div class="stat-row">
            <span class="sr-icon">💬</span>
            <span class="sr-label">对话次数</span>
            <span class="sr-num">{{ stats ? stats.chat_count : '--' }}<span class="sr-unit"> 次</span></span>
          </div>
          <div class="stat-row">
            <span class="sr-icon">✈️</span>
            <span class="sr-label">完成旅程</span>
            <span class="sr-num">{{ stats ? stats.trip_count : '--' }}<span class="sr-unit"> 趟</span></span>
          </div>
          <div class="stat-row">
            <span class="sr-icon">🏙️</span>
            <span class="sr-label">到过城市</span>
            <span class="sr-num">{{ stats ? stats.city_count : '--' }}<span class="sr-unit"> 座</span></span>
          </div>
          <div class="stat-row">
            <span class="sr-icon">📝</span>
            <span class="sr-label">留下笔记</span>
            <span class="sr-num">{{ stats ? stats.note_count : '--' }}<span class="sr-unit"> 篇</span></span>
          </div>
        </div>
        <div class="stats-rank">
          <p class="rank-text" v-if="stats && stats.better_than > 0">超越了 <strong>{{ stats.better_than }}%</strong> 的行者</p>
          <p class="rank-text" v-else>开启你的第一段旅程吧</p>
          <div class="rank-bar"><div class="rank-fill" :style="{ width: ((stats && stats.better_than) || 0) + '%' }"></div></div>
        </div>
      </div>

      <!-- 个人档案卡片 -->
      <div class="profile-side-card" :class="{ empty: !profileFilled }" @click="showProfile = true">
        <div class="psc-head">
          <span class="psc-seal">档</span>
          <span class="psc-title">{{ profileFilled ? '旅行档案' : '建立档案' }}</span>
        </div>
        <template v-if="profileFilled">
          <div class="psc-row"><span class="psc-dot"></span>{{ pGender || '未填写' }} · {{ pAge || '未填写' }}</div>
          <div class="psc-row"><span class="psc-dot"></span>{{ pMotivation || '未填写' }}</div>
          <div class="psc-row"><span class="psc-dot"></span>{{ pHabits || '未填写' }}</div>
          <div class="psc-row"><span class="psc-dot"></span>{{ pCompanion || '未填写' }}</div>
          <div class="psc-edit-hint">点击修改</div>
        </template>
        <template v-else>
          <p class="psc-empty">填写档案，获得专属推荐</p>
        </template>
      </div>
    </aside>

    <!-- 个人档案弹窗 - 中国风 -->
    <a-modal v-model:open="showProfile" width="560px" :footer="null" :bodyStyle="{ padding: 0 }" wrapClassName="profile-modal">
      <div class="pf-wrap">
        <div class="pf-head">
          <span class="pf-seal">档</span>
          <div><h3>旅行档案</h3><span>写下关于你的旅行故事</span></div>
        </div>
        <div class="pf-body">
          <div class="pf-field">
            <label>性别</label>
            <a-radio-group v-model:value="pGender">
              <a-radio value="男">男</a-radio><a-radio value="女">女</a-radio>
            </a-radio-group>
          </div>
          <div class="pf-field">
            <label>年龄</label>
            <input v-model="pAge" class="pf-input" placeholder="如：28岁 / 90后 / 刚毕业..." />
          </div>
          <div class="pf-field">
            <label>为什么旅行</label>
            <textarea v-model="pMotivation" class="pf-textarea" placeholder="如：工作压力大想放松身心、对各地历史文化充满好奇、喜欢探索小众美食..." rows="2"></textarea>
          </div>
          <div class="pf-field">
            <label>旅行习惯</label>
            <textarea v-model="pHabits" class="pf-textarea" placeholder="如：习惯提前做好详细攻略、喜欢说走就走、偏爱深度慢游、享受打卡集邮..." rows="2"></textarea>
          </div>
          <div class="pf-field">
            <label>通常和谁一起旅行</label>
            <input v-model="pCompanion" class="pf-input" placeholder="如：独自一人 / 和伴侣 / 和三五好友 / 带家人..." />
          </div>
        </div>
        <div class="pf-foot">
          <button class="pf-btn" @click="saveProfile" :disabled="profileSaving">{{ profileSaving ? '保存中...' : '💾 保存档案' }}</button>
        </div>
      </div>
    </a-modal>

    <!-- 城市选择 -->
    <a-modal v-model:open="pickerVisible" title="选择所在城市" width="400px" :footer="null">
      <a-input v-model:value="cityInput" placeholder="输入城市名" size="large" @pressEnter="setCity" />
      <a-button type="primary" size="large" block @click="setCity" style="margin-top: 12px">确认</a-button>
      <div style="margin-top: 14px">
        <a-tag v-for="c in hotCities" :key="c" color="red" style="cursor: pointer; margin: 4px" @click="cityInput = c; setCity()">{{ c }}</a-tag>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  getStoredUser,
  getStats,
  getHomepageSuggestion,
  getHomepageWeather,
  getPlazaRecommendation,
  getUserProfile,
  saveUserProfile,
  listAttractionStates,
  getCurrentTripContext,
  type ApiCacheMeta,
} from '@/services/api'
import { message } from 'ant-design-vue'

type DashboardView = 'home' | 'profile' | 'chat' | 'plan' | 'history' | 'guide' | 'plaza' | 'manual' | 'video'
type AmapResolvedLocation = {
  displayCity: string
  weatherCity: string
  adcode: string
  lat?: number
  lng?: number
}
type AttractionState = {
  name: string
  city?: string
  favorite?: boolean
  want_to_go?: boolean
  visited?: boolean
  checked_in?: boolean
  updated_at?: string
}

const emit = defineEmits<{ navigate: [view: DashboardView | 'resume-current-trip'] }>()

const username = ref(getStoredUser().name || getStoredUser().username || '行者')
const timeStr = ref('')
const dateStr = ref('')
const city = ref('')
const weatherCity = ref('')
const weather = ref('')
const temp = ref('')
const humidity = ref('')
const weatherIcon = ref('☀️')
const suggestion = ref('')
const stats = ref<any>(null)
const pickerVisible = ref(false)
const cityInput = ref('')
const hotCities = ['北京', '上海', '广州', '深圳', '杭州', '成都', '重庆', '西安', '南京', '武汉', '苏州', '大理']
const personalizedRecommendation = ref('等你写下档案后，我会把更适合你的旅行灵感放在这里。')
const recommendationLoading = ref(false)
const recentStates = ref<AttractionState[]>([])
const homeCacheMetas = ref<ApiCacheMeta[]>([])

const greetings = ['行路平安', '旅途愉快', '云游四方', '步履不停', '心向山海']
const poems = ['读万卷书，行万里路', '江山留胜迹，我辈复登临', '踏遍青山人未老', '此心安处是吾乡', '天地一沙鸥']
const greetingChars = computed(() => (greetings[new Date().getDate() % greetings.length] + '，' + username.value).split(''))
const poem = ref('')
let timer: number | null = null
const AMAP_KEY = String(import.meta.env.VITE_AMAP_WEB_KEY || '').trim()
const hasAmapKey = computed(() => !!AMAP_KEY)

const showProfile = ref(false)
const profileFilled = ref(false)
const profileSaving = ref(false)
const pGender = ref('')
const pAge = ref('')
const pMotivation = ref('')
const pHabits = ref('')
const pCompanion = ref('')

const profileSummaryItems = computed(() => [
  { label: '旅行画像', value: `${pGender.value || '未填写'} · ${pAge.value || '未填写'}` },
  { label: '出发动机', value: pMotivation.value || '还没写下这一项' },
  { label: '旅行习惯', value: pHabits.value || '还没写下这一项' },
  { label: '同行方式', value: pCompanion.value || '还没写下这一项' },
])

const preferenceBadge = computed(() => {
  if (pMotivation.value) return pMotivation.value.slice(0, 10)
  if (pHabits.value) return pHabits.value.slice(0, 10)
  if (pCompanion.value) return pCompanion.value.slice(0, 10)
  return '已建立旅行档案'
})

const currentTrip = computed(() => {
  const current = getCurrentTripContext()
  if (!current?.tripId) return null
  const updatedAt = current.updatedAt ? new Date(current.updatedAt) : null
  const updatedAtLabel = updatedAt && !Number.isNaN(updatedAt.getTime())
    ? `${updatedAt.getMonth() + 1}月${updatedAt.getDate()}日 ${String(updatedAt.getHours()).padStart(2, '0')}:${String(updatedAt.getMinutes()).padStart(2, '0')}`
    : ''
  const viewLabelMap: Record<string, string> = {
    history: '上次从行囊记录返回',
    home: '上次在首页查看旅程概览',
    plaza: '上次从灵感广场带回旅程',
    video: '上次从旅行视频回看旅程',
    result: '上次刚保存好这条行程',
  }
  const tabLabelMap: Record<string, string> = {
    itinerary: '行程概览',
    tasks: '行程手札',
    budget: '预算',
    prep: '出发前清单',
    notes: '笔记',
    attraction: '景点详情',
  }
  return {
    ...current,
    title: current.title || `${current.startDate || '这次'} ${current.city || '旅行'}`,
    sourceLabel: current.source === 'result-save'
      ? '刚保存'
      : current.source === 'history-select'
        ? '手动续接'
        : current.source === 'attraction-create'
          ? '景点建旅程'
          : current.source === 'attraction-add'
            ? '景点加入行程'
            : '当前进行中',
    lastViewLabel: viewLabelMap[current.lastView || ''] || '上次正在推进这条旅程',
    lastDetailTabLabel: tabLabelMap[current.lastDetailTab || ''] || '',
    updatedAtLabel,
  }
})

const homeCacheNotice = computed(() => {
  if (!homeCacheMetas.value.length) return null
  const stale = homeCacheMetas.value.some(meta => meta.stale)
  const allFromCache = homeCacheMetas.value.every(meta => meta.fromCache)
  if (!stale && !allFromCache) return null
  const latestCachedAt = [...homeCacheMetas.value]
    .map(meta => meta.cachedAt)
    .filter(Boolean)
    .sort()
    .pop()
  const cachedAtLabel = latestCachedAt ? latestCachedAt.replace('T', ' ').slice(0, 16) : ''
  return {
    stale,
    message: stale
      ? `${cachedAtLabel ? `最近一次成功加载于 ${cachedAtLabel}，` : ''}当前网络不稳定时会先展示首页缓存内容，你仍然可以继续当前旅程、查看历史和最近足迹。`
      : '部分首页摘要已直接从本地缓存恢复，弱网下也能先继续查看当前旅程、档案和最近足迹。',
  }
})

function syncHomeCacheMeta(...metas: Array<ApiCacheMeta | null | undefined>) {
  const next = metas.filter((meta): meta is ApiCacheMeta => !!meta)
  homeCacheMetas.value = next
}

function emitNavigate(view: DashboardView | 'resume-current-trip') {
  emit('navigate', view)
}

function continuePrimaryAction() {
  if (currentTrip.value) {
    emitNavigate('resume-current-trip')
    return
  }
  emitNavigate(stats.value?.trip_count ? 'history' : 'plan')
}

function updateTime() {
  const n = new Date()
  const w = ['日', '一', '二', '三', '四', '五', '六']
  timeStr.value = `${String(n.getHours()).padStart(2, '0')}:${String(n.getMinutes()).padStart(2, '0')}`
  dateStr.value = `${n.getFullYear()}年${n.getMonth() + 1}月${n.getDate()}日 星期${w[n.getDay()]}`
}

async function tryGeolocation(): Promise<AmapResolvedLocation | null> {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve(null)
      return
    }
    navigator.geolocation.getCurrentPosition(async (pos) => {
      const lat = pos.coords.latitude
      const lng = pos.coords.longitude
      if (!hasAmapKey.value) {
        resolve({
          displayCity: '',
          weatherCity: '',
          adcode: '',
          lat,
          lng,
        })
        return
      }
      try {
        const r = await fetch(`https://restapi.amap.com/v3/geocode/regeo?key=${AMAP_KEY}&location=${pos.coords.longitude},${pos.coords.latitude}&extensions=base&output=json`)
        const d = await r.json()
        if (d.status !== '1') {
          resolve({
            displayCity: '',
            weatherCity: '',
            adcode: '',
            lat,
            lng,
          })
          return
        }
        const regeocode = d.regeocode || {}
        const ac = regeocode.addressComponent || {}
        const cityVal = Array.isArray(ac.city) ? ac.city[0] : ac.city
        const displayCity = String(cityVal || ac.district || ac.province || '').trim()
        const weatherCity = String(cityVal || ac.province || displayCity || '').trim()
        const adcode = String(ac.adcode || regeocode?.addressComponent?.adcode || '').trim()
        resolve({
          displayCity: displayCity || weatherCity || '',
          weatherCity: weatherCity || displayCity || '',
          adcode,
          lat,
          lng,
        })
      } catch {
        resolve({
          displayCity: '',
          weatherCity: '',
          adcode: '',
          lat,
          lng,
        })
      }
    }, () => resolve(null), {
      enableHighAccuracy: true,
      timeout: 12000,
      maximumAge: 0,
    })
  })
}

async function applyWeatherFallback(cn: string) {
  const fallbackCity = cn || city.value || weatherCity.value || '北京'
  city.value = fallbackCity
  weatherCity.value = fallbackCity
  weather.value = '暂不可用'
  temp.value = '--°C'
  humidity.value = '--%'
  weatherIcon.value = '🌤'
  await fetchSuggestion()
  await loadRecommendation()
}

async function fetchWeather(locationInput: string | AmapResolvedLocation) {
  const fallbackName = typeof locationInput === 'string'
    ? String(locationInput || '').trim()
    : String(locationInput.displayCity || locationInput.weatherCity || '').trim()
  try {
    const payload = typeof locationInput === 'string'
      ? { city: locationInput }
      : locationInput.lat != null && locationInput.lng != null
        ? { lat: locationInput.lat, lng: locationInput.lng }
        : { city: locationInput.displayCity || locationInput.weatherCity || fallbackName }
    const res = await getHomepageWeather(payload)
    const data = res?.data || {}
    if (res?.success && data) {
      const nextCity = String(data.city || fallbackName || city.value || '北京').trim()
      const nextWeatherCity = String(data.weatherCity || nextCity).trim()
      const nextWeather = String(data.weather || '').trim()
      const nextTemperature = String(data.temperature || '').trim()
      const nextHumidity = String(data.humidity || '').trim()
      city.value = nextCity || '北京'
      weatherCity.value = nextWeatherCity || city.value
      weather.value = nextWeather || '未知'
      temp.value = nextTemperature ? `${nextTemperature}°C` : '--°C'
      humidity.value = nextHumidity ? `${nextHumidity}%` : '--%'
      weatherIcon.value = getIcon(weather.value)
      await fetchSuggestion()
      await loadRecommendation()
      return
    }
  } catch {}

  if (typeof locationInput !== 'string') {
    if (locationInput.displayCity) {
      city.value = locationInput.displayCity
    }
    if (locationInput.weatherCity) {
      weatherCity.value = locationInput.weatherCity
    }
  }
  await applyWeatherFallback(fallbackName)
}

function getIcon(w: string): string {
  if (w.includes('雨')) return '🌧'
  if (w.includes('雪')) return '❄'
  if (w.includes('云') || w.includes('阴')) return '☁'
  if (w.includes('晴')) return '☀'
  if (w.includes('雾') || w.includes('霾')) return '🌫'
  if (w.includes('风')) return '💨'
  return '🌤'
}

function openCityPicker() {
  cityInput.value = city.value || ''
  pickerVisible.value = true
}

function setCity() {
  const c = cityInput.value.trim()
  if (!c) {
    message.warning('请输入城市名')
    return
  }
  pickerVisible.value = false
  fetchWeather(c)
}

async function fetchSuggestion() {
  try {
    const payload = {
      city: city.value || '北京',
      weather: weather.value,
      temp: temp.value,
      time: timeStr.value,
    }
    const d = await getHomepageSuggestion(payload)
    suggestion.value = d.success && d.suggestion ? d.suggestion : '心安之处是吾乡'
  } catch {
    suggestion.value = '心安之处是吾乡'
  }
}

async function refreshSuggestion() {
  try {
    await fetchSuggestion()
  } catch {
    suggestion.value = '读万卷书，行万里路～出发吧！'
  }
}

async function loadRecommendation() {
  recommendationLoading.value = true
  try {
    const [recRes] = await Promise.all([getPlazaRecommendation()])
    syncHomeCacheMeta(...homeCacheMetas.value.filter(meta => meta.cacheKey !== recRes?.__cache?.cacheKey), recRes?.__cache || null)
    const recText = recRes?.recommendation || recRes?.data?.recommendation || ''
    if (recText) {
      personalizedRecommendation.value = recText
      return
    }
    personalizedRecommendation.value = city.value
      ? `${city.value} 现在的天气很适合翻翻灵感广场，看看有没有让你心动的新目的地。`
      : '先写档案、再看看广场，你会更快遇到适合自己的旅程。'
  } catch {
    personalizedRecommendation.value = city.value
      ? `${city.value} 的天气信息已经准备好了，不如顺手去数据广场看看适合今天的灵感。`
      : '先去数据广场逛逛，把想去的地方收藏起来吧。'
  } finally {
    recommendationLoading.value = false
  }
}

async function reloadRecommendation() {
  await loadRecommendation()
}

async function loadProfile() {
  try {
    const d = await getUserProfile()
    syncHomeCacheMeta(...homeCacheMetas.value.filter(meta => meta.cacheKey !== d?.__cache?.cacheKey), d?.__cache || null)
    if (d.data?.filled) {
      profileFilled.value = true
      pGender.value = d.data.gender || ''
      pAge.value = d.data.age || ''
      pMotivation.value = d.data.motivation || ''
      pHabits.value = d.data.habits || ''
      pCompanion.value = d.data.companion || ''
    } else {
      profileFilled.value = false
    }
  } catch {}
}

async function saveProfile() {
  profileSaving.value = true
  try {
    await saveUserProfile({
      gender: pGender.value,
      age: pAge.value,
      motivation: pMotivation.value,
      habits: pHabits.value,
      companion: pCompanion.value,
      preference: '',
    })
    profileFilled.value = true
    showProfile.value = false
    message.success('档案已保存')
    await loadRecommendation()
  } catch {
    message.error('保存失败')
  } finally {
    profileSaving.value = false
  }
}

async function loadStats() {
  try {
    const r = await getStats()
    syncHomeCacheMeta(...homeCacheMetas.value.filter(meta => meta.cacheKey !== r?.__cache?.cacheKey), r?.__cache || null)
    if (r.success) stats.value = r.data
  } catch {}
}

async function loadRecentStates() {
  try {
    const res = await listAttractionStates()
    syncHomeCacheMeta(...homeCacheMetas.value.filter(meta => meta.cacheKey !== res?.__cache?.cacheKey), res?.__cache || null)
    recentStates.value = Array.isArray(res.data) ? res.data.slice(0, 6) : []
  } catch {
    recentStates.value = []
  }
}

function formatStateBadge(item: AttractionState) {
  if (item.checked_in) return '已打卡'
  if (item.visited) return '去过啦'
  if (item.want_to_go) return '想去'
  if (item.favorite) return '已收藏'
  return '旅行足迹'
}

onMounted(async () => {
  updateTime()
  timer = window.setInterval(updateTime, 30000)
  poem.value = poems[Math.floor(Math.random() * poems.length)]
  await Promise.all([loadStats(), loadProfile(), loadRecentStates()])
  await loadRecommendation()
  const gc = await tryGeolocation()
  gc ? fetchWeather(gc) : fetchWeather('北京')
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
/* ========== 布局 ========== */
.homepage { display: flex; gap: 24px; padding: 32px 36px; max-width: 1200px; margin: 0 auto; align-items: flex-start; }
.main-col { flex: 1; min-width: 0; }
.side-col { width: 260px; flex-shrink: 0; position: sticky; top: 24px; display: flex; flex-direction: column; gap: 20px; }

/* ========== 横幅 ========== */
.hero {
  position: relative; overflow: hidden; background: linear-gradient(175deg, #ece1d5 0%, #f2e8da 35%, #faf4ec 100%);
  border-radius: 24px; padding: 30px 32px 24px; margin-bottom: 24px;
  border: 1px solid #e0cfba; box-shadow: 0 4px 24px rgba(139,69,19,0.06); transition: transform 0.3s, box-shadow 0.3s;
}
.hero:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(139,69,19,0.1); }
.hero-bg-deco { position: absolute; inset: 0; pointer-events: none; overflow: hidden; }
.deco-dot { position: absolute; border-radius: 50%; background: rgba(196,59,59,0.06); }
.d1 { width: 80px; height: 80px; top: -20px; left: 10%; animation: floatA 8s infinite ease-in-out; }
.d2 { width: 50px; height: 50px; bottom: 10px; right: 20%; animation: floatA 6s infinite ease-in-out 1s; }
.d3 { width: 30px; height: 30px; top: 40%; right: 5%; animation: floatA 5s infinite ease-in-out .5s; }
@keyframes floatA { 0%,100% { transform: translateY(0) scale(1); } 50% { transform: translateY(-12px) scale(1.15); } }
.hero-mountains { position: absolute; top: -15px; right: 10px; opacity: .25; display: flex; gap: 2px; pointer-events: none; }
.mtn { font-size: 38px; animation: bob 4s infinite ease-in-out; }
@keyframes bob { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
.hero-cloud { position: absolute; opacity: .2; font-size: 22px; pointer-events: none; }
.c1 { top: 8px; right: 120px; animation: drift 7s infinite ease-in-out; }
.c2 { top: 18px; right: 50px; animation: drift 9s infinite ease-in-out 1.5s; }
@keyframes drift { 0%,100% { transform: translateX(0); } 50% { transform: translateX(-30px); } }
.hero-content { display: flex; justify-content: space-between; align-items: flex-start; position: relative; z-index: 1; }
.hero-left { display: flex; align-items: center; gap: 16px; }
.hero-seal { width: 54px; height: 54px; border-radius: 8px; background: #c43b3b; color: #faf0d7; display: flex; align-items: center; justify-content: center; font-size: 30px; font-weight: 900; font-family: 'STKaiti','楷体','KaiTi',serif; flex-shrink: 0; box-shadow: 0 3px 12px rgba(196,59,59,0.25); animation: sealIn .6s cubic-bezier(.34,1.56,.64,1) both; will-change: transform,opacity; }
@keyframes sealIn { from { transform: scale(0) rotate(-15deg); opacity: 0; } to { transform: scale(1) rotate(0); opacity: 1; } }
.hero-greeting { font-size: 26px; font-weight: 700; color: #5c3a21; margin: 0; font-family: 'STKaiti','楷体','KaiTi',serif; display: flex; flex-wrap: wrap; }
.greeting-char { display: inline-block; animation: charIn .35s ease-out both; will-change: transform,opacity; }
@keyframes charIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.hero-poem { font-size: 14px; color: #b8a088; margin: 4px 0 0; font-family: 'STKaiti','楷体','KaiTi',serif; font-style: italic; animation: fadeSlide .5s ease-out .4s both; will-change: transform,opacity; }
@keyframes fadeSlide { from { opacity: 0; transform: translateX(-8px); } to { opacity: 1; transform: translateX(0); } }
.hero-time { text-align: right; flex-shrink: 0; }
.time-val { font-size: 36px; font-weight: 700; color: #5c3a21; display: block; font-variant-numeric: tabular-nums; font-family: 'Georgia',serif; animation: fadeSlide .5s ease-out .2s both; will-change: transform,opacity; }
.time-date { font-size: 13px; color: #b8a088; display: block; margin-top: 4px; animation: fadeSlide .5s ease-out .3s both; will-change: transform,opacity; }

/* ========== 卡片 ========== */
.cards-row { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin-bottom: 20px; }
.card { padding: 16px 14px; border-radius: 14px; background: #fff; border: 1px solid #eadccf; box-shadow: 0 2px 12px rgba(139,69,19,0.03); transition: all .3s; display: flex; flex-direction: column; gap: 8px; animation: cardUp .45s ease-out both; will-change: transform,opacity; }
.card:nth-child(1) { animation-delay: .1s; }.card:nth-child(2) { animation-delay: .18s; }.card:nth-child(3) { animation-delay: .26s; }.card:nth-child(4) { animation-delay: .34s; }
@keyframes cardUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
.card-loc { cursor: pointer; }
.card-loc:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(196,59,59,0.1); border-color: #d4a89a; }
.card-head { display: flex; align-items: center; gap: 8px; }
.card-seal { width: 26px; height: 26px; border-radius: 4px; background: #c43b3b; color: #faf0d7; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 700; font-family: 'STKaiti','楷体','KaiTi',serif; flex-shrink: 0; }
.card-label { font-size: 12px; color: #b8a088; }
.card-val { font-size: 15px; font-weight: 600; color: #5c3a21; }
.card-val-big { font-size: 18px; font-weight: 600; color: #5c3a21; }
.card-hint { font-size: 11px; color: #c43b3b; }
.pulse { animation: pulseHint 2s infinite; }
@keyframes pulseHint { 0%,100% { opacity: 1; } 50% { opacity: .5; } }

/* ========== 快捷入口 ========== */
.shortcuts { display: flex; flex-direction: column; gap: 6px; margin-bottom: 20px; }
.shortcut { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-radius: 14px; cursor: pointer; transition: all .3s; border: 1px solid #eadccf; position: relative; overflow: hidden; }
.shortcut::after { content: ''; position: absolute; inset: 0; background: linear-gradient(90deg,transparent,rgba(196,59,59,0.03),transparent); transform: translateX(-100%); transition: transform .5s; }
.shortcut:hover::after { transform: translateX(100%); }
.chat-s { background: #fdf8f3; }
.plan-s { background: #faf6f1; }
.plaza-s { background: #fbf7f2; }
.hist-s { background: #f9f6f0; }
.shortcut:hover { transform: translateX(6px); box-shadow: 0 3px 16px rgba(139,69,19,0.08); border-color: #d4a89a; }
.s-left { display: flex; align-items: center; gap: 14px; }
.s-icon { font-size: 30px; transition: transform .3s; }
.shortcut:hover .s-icon { transform: scale(1.15) rotate(-5deg); }
.s-title { font-size: 16px; font-weight: 700; color: #5c3a21; display: block; font-family: 'STKaiti','楷体','KaiTi',serif; }
.s-desc { font-size: 12px; color: #b8a088; margin-top: 2px; display: block; }
.s-arrow { font-size: 18px; color: #d4c5b5; transition: all .3s; }
.shortcut:hover .s-arrow { transform: translateX(6px); color: #c43b3b; }

/* ========== 首页特色区域 ========== */
.home-grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 16px; margin-bottom: 16px; }
.feature-panel { background: #fff; border: 1px solid #eadccf; border-radius: 18px; padding: 20px; box-shadow: 0 2px 12px rgba(139,69,19,0.03); }
.panel-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; margin-bottom: 16px; }
.panel-title-row { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.panel-seal { width: 28px; height: 28px; border-radius: 4px; background: #c43b3b; color: #faf0d7; display: flex; align-items: center; justify-content: center; font-size: 15px; font-weight: 700; font-family: 'STKaiti','楷体','KaiTi',serif; flex-shrink: 0; }
.panel-head h3 { margin: 0; font-size: 18px; color: #5c3a21; font-family: 'STKaiti','楷体','KaiTi',serif; }
.panel-head p { margin: 0; font-size: 13px; color: #9d846f; line-height: 1.6; }
.ghost-btn, .primary-btn, .secondary-btn { border: none; border-radius: 12px; cursor: pointer; transition: all .2s; font-size: 14px; }
.ghost-btn { padding: 10px 14px; background: #f8f2ea; color: #8b5a3c; border: 1px solid #eadccf; white-space: nowrap; }
.ghost-btn:hover:not(:disabled) { background: #fff; border-color: #d4a89a; }
.ghost-btn:disabled { opacity: .6; cursor: not-allowed; }
.primary-btn { padding: 11px 18px; background: linear-gradient(135deg,#c43b3b,#a0522d); color: #fff; }
.primary-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(196,59,59,.25); }
.secondary-btn { padding: 11px 18px; background: #f8f2ea; color: #7b573d; border: 1px solid #eadccf; }
.secondary-btn:hover { border-color: #d4a89a; background: #fff; }
.recommend-body { display: flex; flex-direction: column; gap: 14px; }
.recommend-text { margin: 0; font-size: 16px; line-height: 1.85; color: #5c3a21; background: linear-gradient(135deg, #fffaf5, #fdf6ee); border: 1px dashed #eadccf; border-radius: 14px; padding: 16px; }
.recommend-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.rec-tag { display: inline-flex; align-items: center; padding: 6px 10px; border-radius: 999px; background: #faf4ec; color: #8b5a3c; font-size: 12px; border: 1px solid #eadccf; }
.recommend-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.summary-list { display: flex; flex-direction: column; gap: 10px; }
.summary-item { display: flex; flex-direction: column; gap: 4px; padding: 12px 14px; border-radius: 12px; background: #fcfaf7; border: 1px solid #f0e5d9; }
.summary-label { font-size: 12px; color: #b08a72; }
.summary-value { font-size: 14px; color: #5c3a21; line-height: 1.7; }
.summary-empty { display: flex; flex-direction: column; align-items: flex-start; gap: 12px; background: #fcfaf7; border: 1px dashed #eadccf; border-radius: 14px; padding: 16px; }
.summary-empty p { margin: 0; font-size: 14px; color: #6b5344; line-height: 1.7; }
.states-head { margin-bottom: 14px; }
.states-grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 12px; }
.state-card { border: 1px solid #f0e5d9; border-radius: 14px; padding: 14px; background: #fcfaf7; }
.state-main { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 10px; }
.state-name { font-size: 15px; font-weight: 700; color: #5c3a21; }
.state-city { font-size: 12px; color: #b08a72; margin-top: 4px; }
.state-badge { font-size: 12px; color: #c43b3b; background: #fff1ec; border: 1px solid #f2d1c2; padding: 4px 8px; border-radius: 999px; white-space: nowrap; }
.state-flags { display: flex; flex-wrap: wrap; gap: 8px; font-size: 12px; color: #7d624f; }
.states-empty { display: flex; align-items: center; justify-content: space-between; gap: 14px; padding: 14px 16px; border: 1px dashed #eadccf; border-radius: 14px; background: #fcfaf7; }
.states-empty p { margin: 0; color: #6b5344; line-height: 1.7; }

/* ========== AI 旅行锦囊 ========== */
.ai-tip-card {
  margin-top: 12px; position: relative; overflow: hidden;
  background: linear-gradient(135deg,#fdf8f2,#fefaf6);
  border: 1px solid #eadccf; border-radius: 16px;
  transition: all .35s cubic-bezier(.4,0,.2,1);
  animation: cardUp .45s ease-out .32s both;
  cursor: pointer;
}
.ai-tip-card:hover { border-color: #d4a89a; box-shadow: 0 6px 24px rgba(196,59,59,.08); transform: translateY(-2px); }
.ai-tip-card:active { transform: scale(.985); }
.ai-tip-inner { position: relative; z-index: 1; padding: 18px 20px; }
.ai-tip-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.ai-tip-avatar { width: 32px; height: 32px; border-radius: 50%; object-fit: cover; flex-shrink: 0; cursor: pointer; border: 2px solid #eadccf; transition: all .3s; box-shadow: 0 2px 8px rgba(196,59,59,.12); }
.ai-tip-avatar:hover { border-color: #c43b3b; transform: scale(1.1); box-shadow: 0 3px 14px rgba(196,59,59,.25); }
.ai-tip-avatar:active { transform: scale(.95); }
.ai-tip-title { font-size: 15px; font-weight: 700; color: #5c3a21; font-family: 'STKaiti','楷体','KaiTi',serif; flex: 1; }
.ai-tip-text { font-size: 14px; color: #6b5344; line-height: 1.75; margin: 0; padding: 12px 14px; background: rgba(255,255,255,.6); border-radius: 10px; border: 1px dashed #e8d5c5; transition: all .3s; }
.ai-tip-card:hover .ai-tip-text { background: rgba(255,255,255,.85); border-color: #d4a89a; }
.ai-tip-empty { color: #b8a088; text-align: center; font-style: italic; }
.ai-quote-l,.ai-quote-r { color: #d4a89a; font-family: 'STKaiti','楷体','KaiTi',serif; font-size: 16px; }
.ai-tip-shine { position: absolute; top: 0; left: -100%; width: 60%; height: 100%; background: linear-gradient(90deg,transparent,rgba(255,255,255,.4),transparent); transform: skewX(-20deg); transition: none; z-index: 2; pointer-events: none; }
.ai-tip-card:hover .ai-tip-shine { left: 120%; transition: left .6s ease-in-out; }

/* ========== 右侧栏 ========== */
.stats-panel {
  background: #fff; border: 1px solid #eadccf; border-radius: 18px;
  padding: 22px 20px; box-shadow: 0 2px 12px rgba(139,69,19,0.03);
  animation: slideRight .45s ease-out .25s both; will-change: transform,opacity;
}
@keyframes slideRight { from { opacity: 0; transform: translateX(16px); } to { opacity: 1; transform: translateX(0); } }
.stats-head { display: flex; align-items: center; gap: 10px; margin-bottom: 18px; padding-bottom: 14px; border-bottom: 2px solid #eadccf; }
.stats-seal { width: 28px; height: 28px; border-radius: 4px; background: #c43b3b; color: #faf0d7; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: 700; font-family: 'STKaiti','楷体','KaiTi',serif; flex-shrink: 0; }
.stats-title { font-size: 16px; font-weight: 700; color: #5c3a21; font-family: 'STKaiti','楷体','KaiTi',serif; }
.stats-list { display: flex; flex-direction: column; gap: 2px; }
.stat-row { display: flex; align-items: center; gap: 10px; padding: 12px 14px; border-radius: 10px; transition: background 0.2s; }
.stat-row:hover { background: #faf7f2; }
.sr-icon { font-size: 20px; width: 32px; text-align: center; flex-shrink: 0; }
.sr-label { flex: 1; font-size: 14px; color: #6b5344; }
.sr-num { font-size: 18px; font-weight: 700; color: #5c3a21; font-family: 'Georgia',serif; }
.sr-unit { font-size: 12px; color: #b8a088; font-weight: 400; }
.stats-rank { margin-top: 14px; padding-top: 14px; border-top: 1px dashed #eadccf; text-align: center; }
.rank-text { font-size: 13px; color: #6b5344; margin: 0 0 8px 0; }
.rank-text strong { color: #c43b3b; font-size: 20px; font-family: 'Georgia',serif; }
.rank-bar { height: 6px; background: #eadccf; border-radius: 3px; overflow: hidden; }
.rank-fill { height: 100%; background: linear-gradient(90deg, #c43b3b, #d46060); border-radius: 3px; transition: width 1s cubic-bezier(0.4,0,0.2,1); }

/* 侧边档案卡片 */
.profile-side-card { background: #fff; border: 1px solid #eadccf; border-radius: 16px; padding: 16px 18px; cursor: pointer; transition: all .2s; }
.profile-side-card:hover { box-shadow: 0 3px 14px rgba(139,69,19,.08); border-color: #d4a89a; }
.profile-side-card.empty { border-style: dashed; border-color: #d4a89a; }
.psc-head { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.psc-seal { width: 22px; height: 22px; border-radius: 3px; background: #c43b3b; color: #faf0d7; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; font-family: 'STKaiti','楷体','KaiTi',serif; }
.psc-title { font-size: 14px; font-weight: 700; color: #5c3a21; font-family: 'STKaiti','楷体','KaiTi',serif; }
.psc-row { font-size: 13px; color: #6b5344; padding: 3px 0; display: flex; align-items: flex-start; gap: 6px; line-height: 1.5; }
.psc-dot { width: 5px; height: 5px; border-radius: 50%; background: #d4a89a; flex-shrink: 0; margin-top: 6px; }
.psc-edit-hint { font-size: 11px; color: #b8a088; text-align: right; margin-top: 4px; }
.psc-empty { font-size: 13px; color: #b8a088; text-align: center; margin: 8px 0; }

/* 档案弹窗 */
.profile-modal :deep(.ant-modal-content) { border-radius: 16px; overflow: hidden; }
.pf-wrap { display: flex; flex-direction: column; }
.pf-head { display: flex; align-items: center; gap: 12px; padding: 24px 28px; background: linear-gradient(135deg,#fdf8f2,#fefaf6); border-bottom: 1px solid #eadccf; }
.pf-seal { width: 36px; height: 36px; border-radius: 6px; background: #c43b3b; color: #faf0d7; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 900; font-family: 'STKaiti','楷体','KaiTi',serif; }
.pf-head h3 { margin: 0; font-size: 17px; color: #5c3a21; font-family: 'STKaiti','楷体','KaiTi',serif; }
.pf-head span { font-size: 12px; color: #b8a088; }
.pf-body { padding: 24px 28px; display: flex; flex-direction: column; gap: 20px; max-height: 55vh; overflow-y: auto; }
.pf-field { display: flex; flex-direction: column; gap: 6px; }
.pf-field label { font-size: 14px; font-weight: 600; color: #5c3a21; font-family: 'STKaiti','楷体','KaiTi',serif; }
.pf-input { padding: 10px 14px; border: 2px solid #eadccf; border-radius: 10px; font-size: 15px; color: #5c3a21; background: #fefcf8; outline: none; transition: border-color .2s; }
.pf-input:focus { border-color: #c43b3b; background: #fff; }
.pf-input::placeholder { color: #c4b5a5; font-size: 14px; }
.pf-textarea { padding: 10px 14px; border: 2px solid #eadccf; border-radius: 10px; font-size: 15px; color: #5c3a21; background: #fefcf8; outline: none; resize: vertical; font-family: inherit; transition: border-color .2s; }
.pf-textarea:focus { border-color: #c43b3b; background: #fff; }
.pf-textarea::placeholder { color: #c4b5a5; font-size: 14px; }
.pf-foot { padding: 16px 28px; background: #faf7f2; border-top: 1px solid #eadccf; }
.pf-btn { width: 100%; padding: 12px; border: none; border-radius: 14px; background: linear-gradient(135deg,#c43b3b,#a0522d); color: #fff; font-size: 16px; font-weight: 600; cursor: pointer; font-family: 'STKaiti','楷体','KaiTi',serif; transition: all .2s; }
.pf-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 3px 14px rgba(196,59,59,.3); }
.pf-btn:disabled { opacity: .5; cursor: not-allowed; }

/* ========== 响应式 ========== */
@media (min-width: 768px) and (max-width: 1023px) {
  .homepage { padding: 20px; gap: 16px; }
  .side-col { width: 220px; }
  .hero { padding: 24px 22px 20px; }
  .cards-row { grid-template-columns: repeat(2,1fr); }
  .home-grid { grid-template-columns: 1fr; }
  .states-grid { grid-template-columns: 1fr; }
}

@media (max-width: 767px) {
  .homepage { flex-direction: column; padding: 14px; gap: 16px; }
  .side-col { width: 100%; position: static; }
  .main-col { width: 100%; }
  .hero { padding: 20px 16px; border-radius: 18px; }
  .hero-content { flex-direction: column; gap: 10px; }
  .hero-time { text-align: left; }
  .time-val { font-size: 26px; }
  .hero-greeting { font-size: 20px; }
  .hero-seal { width: 42px; height: 42px; font-size: 24px; }
  .hero-mountains { display: none; }
  .cards-row { grid-template-columns: repeat(2,1fr); gap: 8px; }
  .card { padding: 12px 10px; }
  .shortcut { padding: 14px 16px; }
  .s-icon { font-size: 24px; }
  .home-grid { grid-template-columns: 1fr; }
  .panel-head, .states-empty { flex-direction: column; align-items: flex-start; }
  .states-grid { grid-template-columns: 1fr; }
  .stats-panel { padding: 16px; }
  .stats-title { font-size: 15px; margin-bottom: 10px; }
  .stats-list { flex-direction: row; gap: 6px; overflow-x: auto; }
  .stat-row { flex-direction: column; text-align: center; padding: 10px; min-width: 72px; gap: 4px; }
  .sr-icon { font-size: 22px; width: auto; }
  .sr-label { font-size: 11px; }
  .sr-num { font-size: 18px; }
}
</style>
