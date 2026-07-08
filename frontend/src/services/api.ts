import axios from 'axios'
import type { TripFormData, TripPlanResponse, CurrentFields, ParseResponse } from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const CURRENT_TRIP_KEY = 'currentTripContext'
const LOCAL_CACHE_PREFIX = 'helloagents-cache'
const DEFAULT_CACHE_STALE_MINUTES = 180

export type LocalCacheEnvelope<T> = {
  data: T
  cachedAt: string
  staleAt: string
  key: string
}

export type CachedResult<T> = {
  data: T
  fromCache: boolean
  stale: boolean
  cachedAt: string
  staleAt: string
  cacheKey: string
}

export type CacheFallbackError<T = unknown> = Error & {
  cacheFallback?: CachedResult<T> | null
}

export type CurrentTripContext = {
  tripId: string
  title?: string
  city?: string
  startDate?: string
  source?: string
  lastView?: string
  lastDetailTab?: string
  updatedAt?: string
}

function normalizeCurrentTripContext(value: any): CurrentTripContext | null {
  const tripId = String(value?.tripId || '').trim()
  if (!tripId) return null
  return {
    tripId,
    title: String(value?.title || '').trim(),
    city: String(value?.city || '').trim(),
    startDate: String(value?.startDate || '').trim(),
    source: String(value?.source || '').trim(),
    lastView: String(value?.lastView || '').trim(),
    lastDetailTab: String(value?.lastDetailTab || '').trim(),
    updatedAt: String(value?.updatedAt || '').trim() || new Date().toISOString(),
  }
}

export function getCurrentTripContext(): CurrentTripContext | null {
  try {
    const raw = localStorage.getItem(CURRENT_TRIP_KEY)
    if (!raw) return null
    return normalizeCurrentTripContext(JSON.parse(raw))
  } catch {
    return null
  }
}

export function setCurrentTripContext(payload: CurrentTripContext | null) {
  if (!payload?.tripId) {
    localStorage.removeItem(CURRENT_TRIP_KEY)
    return
  }
  const nextValue = normalizeCurrentTripContext({
    ...getCurrentTripContext(),
    ...payload,
    updatedAt: new Date().toISOString(),
  })
  if (!nextValue) {
    localStorage.removeItem(CURRENT_TRIP_KEY)
    return
  }
  localStorage.setItem(CURRENT_TRIP_KEY, JSON.stringify(nextValue))
}

export function clearCurrentTripContext() {
  localStorage.removeItem(CURRENT_TRIP_KEY)
}

export function markCurrentTripViewed(lastView: string) {
  const current = getCurrentTripContext()
  if (!current?.tripId) return
  setCurrentTripContext({
    ...current,
    lastView,
  })
}

export function setCurrentTripDetailTab(lastDetailTab: string) {
  const current = getCurrentTripContext()
  if (!current?.tripId) return
  setCurrentTripContext({
    ...current,
    lastDetailTab,
  })
}

export function buildCurrentTripContext(payload: {
  tripId: string
  title?: string
  city?: string
  startDate?: string
  source?: string
  lastView?: string
  lastDetailTab?: string
}): CurrentTripContext {
  return {
    tripId: String(payload.tripId || '').trim(),
    title: String(payload.title || '').trim(),
    city: String(payload.city || '').trim(),
    startDate: String(payload.startDate || '').trim(),
    source: String(payload.source || '').trim(),
    lastView: String(payload.lastView || '').trim(),
    lastDetailTab: String(payload.lastDetailTab || '').trim(),
    updatedAt: new Date().toISOString(),
  }
}

export type ApiCacheMeta = {
  fromCache: boolean
  stale: boolean
  cachedAt: string
  staleAt: string
  cacheKey: string
}

function buildCacheStorageKey(key: string) {
  const username = getAuthUsername() || 'guest'
  return `${LOCAL_CACHE_PREFIX}:${username}:${String(key || '').trim()}`
}

function normalizeCacheMeta(payload: Partial<ApiCacheMeta> & { cacheKey: string }): ApiCacheMeta {
  return {
    fromCache: !!payload.fromCache,
    stale: !!payload.stale,
    cachedAt: String(payload.cachedAt || '').trim() || new Date().toISOString(),
    staleAt: String(payload.staleAt || '').trim() || new Date().toISOString(),
    cacheKey: String(payload.cacheKey || '').trim(),
  }
}

export function readLocalCache<T>(key: string): CachedResult<T> | null {
  try {
    const storageKey = buildCacheStorageKey(key)
    const raw = localStorage.getItem(storageKey)
    if (!raw) return null
    const parsed = JSON.parse(raw) as LocalCacheEnvelope<T>
    if (!parsed || typeof parsed !== 'object') return null
    const cachedAt = String(parsed.cachedAt || '').trim()
    const staleAt = String(parsed.staleAt || '').trim()
    return {
      data: parsed.data,
      fromCache: true,
      stale: true,
      cachedAt: cachedAt || new Date().toISOString(),
      staleAt: staleAt || cachedAt || new Date().toISOString(),
      cacheKey: String(parsed.key || storageKey || '').trim() || storageKey,
    }
  } catch {
    return null
  }
}

export function writeLocalCache<T>(key: string, data: T, staleMinutes = DEFAULT_CACHE_STALE_MINUTES): CachedResult<T> {
  const storageKey = buildCacheStorageKey(key)
  const cachedAt = new Date().toISOString()
  const staleAt = new Date(Date.now() + Math.max(staleMinutes, 1) * 60 * 1000).toISOString()
  const payload: LocalCacheEnvelope<T> = {
    data,
    cachedAt,
    staleAt,
    key: storageKey,
  }
  try {
    localStorage.setItem(storageKey, JSON.stringify(payload))
  } catch {}
  return {
    data,
    fromCache: false,
    stale: false,
    cachedAt,
    staleAt,
    cacheKey: storageKey,
  }
}

export function clearLocalCache(key: string) {
  try {
    localStorage.removeItem(buildCacheStorageKey(key))
  } catch {}
}

function attachCacheMeta<T>(payload: T, meta: ApiCacheMeta): T & { __cache: ApiCacheMeta } {
  if (Array.isArray(payload)) {
    return Object.assign([...payload], { __cache: meta }) as unknown as T & { __cache: ApiCacheMeta }
  }
  if (payload && typeof payload === 'object') {
    return {
      ...(payload as Record<string, unknown>),
      __cache: meta,
    } as T & { __cache: ApiCacheMeta }
  }
  return {
    data: payload,
    __cache: meta,
  } as unknown as T & { __cache: ApiCacheMeta }
}

export async function withLocalCache<T>(key: string, request: () => Promise<T>, staleMinutes = DEFAULT_CACHE_STALE_MINUTES) {
  try {
    const fresh = writeLocalCache(key, await request(), staleMinutes)
    return attachCacheMeta(fresh.data, normalizeCacheMeta(fresh))
  } catch (error) {
    const fallback = readLocalCache<T>(key)
    if (fallback) {
      return attachCacheMeta(fallback.data, normalizeCacheMeta(fallback))
    }
    throw error as CacheFallbackError<T>
  }
}

export function getAuthUsername(): string {
  return (localStorage.getItem('username') || '').trim()
}

export function getDisplayName(): string {
  return (
    localStorage.getItem('display_name') ||
    localStorage.getItem('user_name') ||
    getAuthUsername() ||
    ''
  ).trim()
}

export function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('token') || ''
  const username = getAuthUsername()
  return {
    'Authorization': token ? `Bearer ${token}` : '',
    'X-Username': username
  }
}

export function setAuth(token: string, username: string) {
  localStorage.setItem('token', token)
  localStorage.setItem('username', username)
}

export function hydrateAuthUser(user?: {
  username?: string
  name?: string
  last_login?: string
  login_count?: number
  is_admin?: boolean
}) {
  if (!user) return
  const username = (user.username || '').trim()
  const displayName = (user.name || username).trim()

  if (username) localStorage.setItem('username', username)
  if (displayName) {
    localStorage.setItem('display_name', displayName)
    localStorage.setItem('user_name', displayName)
  }
  if (user.last_login) localStorage.setItem('last_login', user.last_login)
  if (typeof user.login_count === 'number') localStorage.setItem('login_count', String(user.login_count))
  if (user.is_admin) localStorage.setItem('is_admin', '1')
}

export function clearAuth() {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('is_admin')
  localStorage.removeItem('user_name')
  localStorage.removeItem('user_email')
}

export function isLoggedIn(): boolean {
  return !!localStorage.getItem('token')
}

export function getStoredUser(): { username: string; name?: string; last_login?: string } {
  return {
    username: getAuthUsername() || '',
    name: getDisplayName() || getAuthUsername() || '',
    last_login: localStorage.getItem('last_login') || ''
  }
}

// ---- API Client ----
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' }
})

apiClient.interceptors.request.use((config) => {
  const auth = getAuthHeaders()
  if (auth.Authorization) config.headers.Authorization = auth.Authorization
  if (auth['X-Username']) config.headers['X-Username'] = auth['X-Username']
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearAuth()
      window.location.assign('/login')
    }
    return Promise.reject(error)
  }
)

// ---- Auth APIs ----
export async function login(username: string, password: string) {
  const res = await apiClient.post('/api/auth/login', { username, password })
  // username 用于 X-Username header（必须是登录账号名）
  setAuth(res.data.token, username)
  hydrateAuthUser({
    username,
    name: res.data.user?.name || username,
    last_login: res.data.user?.last_login,
    login_count: res.data.user?.login_count,
    is_admin: res.data.is_admin,
  })
  return res.data
}

export async function register(username: string, password: string) {
  return apiClient.post('/api/auth/register', { username, password })
}

export async function getMe() {
  const res = await apiClient.get('/api/auth/me')
  return res.data
}

export async function logout() {
  try { await apiClient.post('/api/auth/logout') } catch {}
  clearAuth()
}

// ---- Trip APIs ----
export async function generateTripPlan(formData: TripFormData): Promise<TripPlanResponse> {
  const response = await apiClient.post<TripPlanResponse>('/api/trip/plan', formData)
  return response.data
}

export async function parseUserMessage(message: string, currentFields: CurrentFields): Promise<ParseResponse> {
  try {
    const response = await apiClient.post<ParseResponse>('/api/trip/parse', {
      message, current_fields: currentFields
    })
    return response.data
  } catch {
    return {
      success: true, extracted: {},
      bot_reply: '抱歉，解析服务暂时不可用。请按格式输入：「北京，6月20号，3天，公交，舒适型酒店，历史文化」',
      is_complete: false
    }
  }
}

export async function saveTripPlan(tripPlan: any) {
  const res = await apiClient.post('/api/trip/save', { trip_plan: tripPlan })
  return res.data
}

export async function getHistory() {
  return withLocalCache('trip-history', async () => {
    const res = await apiClient.get('/api/trip/history')
    return res.data
  })
}

export async function getHistoryDetail(id: string) {
  return withLocalCache(`trip-history-detail:${String(id || '').trim()}`, async () => {
    const res = await apiClient.get(`/api/trip/history/${id}`)
    return res.data
  })
}

export async function updateTripTasks(id: string, tasks: any[]) {
  const res = await apiClient.put(`/api/trip/history/${id}/tasks`, { tasks })
  return res.data
}

export async function updateHistory(id: string, payload: {
  notes?: string
  images?: string[]
  files?: any[]
  prep_checklist?: any[]
  trip_info?: {
    hotel?: string
    transport?: string
    tickets?: string
    contact?: string
    meetingPoint?: string
  }
}) {
  const res = await apiClient.put(`/api/trip/history/${id}`, payload)
  return res.data
}

export async function deleteHistory(id: string) {
  const res = await apiClient.delete(`/api/trip/history/${id}`)
  return res.data
}

export async function getTripSuggestion(city: string) {
  const res = await apiClient.post('/api/trip/suggest', {
    city,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  })
  return res.data
}

export async function getHomepageSuggestion(payload: {
  city: string
  weather?: string
  temp?: string
  time?: string
}) {
  const res = await apiClient.post('/api/trip/suggest', payload)
  return res.data
}

export async function getHomepageWeather(payload: {
  city?: string
  lat?: number
  lng?: number
}) {
  const res = await apiClient.post('/api/trip/homepage-weather', payload)
  return res.data
}

export async function getStats() {
  return withLocalCache('trip-stats', async () => {
    const res = await apiClient.get('/api/trip/stats')
    return res.data
  }, 60)
}

export async function healthCheck() {
  const res = await apiClient.get('/health')
  return res.data
}

// ---- Plaza APIs ----
export async function getPlazaProvinces() {
  const res = await apiClient.get('/api/plaza/provinces')
  return res.data
}

export async function getPlazaProvinceDetail(province: string) {
  const res = await apiClient.get(`/api/plaza/provinces/${encodeURIComponent(province)}`)
  return res.data
}

export async function searchPlazaAttractions(query: string) {
  const res = await apiClient.get('/api/plaza/attractions', {
    params: { q: query }
  })
  return res.data
}

export async function getPlazaInsights() {
  const res = await apiClient.get('/api/plaza/insights')
  return res.data
}

export async function syncTripToPlaza(city: string, attractions: string[]) {
  const res = await apiClient.post('/api/plaza/sync', {
    city,
    province: city,
    attractions
  })
  return res.data
}

export async function getPlazaRecommendation() {
  return withLocalCache('plaza-recommendation', async () => {
    const res = await apiClient.post('/api/plaza/recommend', {})
    return res.data
  }, 120)
}

export async function getUserProfile() {
  return withLocalCache('plaza-profile', async () => {
    const res = await apiClient.get('/api/plaza/profile')
    return res.data
  }, 180)
}

export async function saveUserProfile(payload: {
  gender?: string
  age?: string
  motivation?: string
  habits?: string
  companion?: string
  preference?: string
}) {
  const res = await apiClient.post('/api/plaza/profile', payload)
  return res.data
}

export async function getAttractionDetail(name: string, city = '') {
  const res = await apiClient.get(`/api/plaza/attraction/${encodeURIComponent(name)}`, {
    params: { city }
  })
  return res.data
}

export async function askAttractionQuestion(name: string, question: string, city = '') {
  const res = await apiClient.post('/api/plaza/attraction/ask', {
    name,
    city,
    question
  })
  return res.data
}

export async function askGuideQuestion(payload: {
  tripId: string
  question: string
  city?: string
  currentLocation?: { lat: number; lng: number } | null
  nearestAttraction?: { name: string; distance?: number | null } | null
  doneAttractions?: string[]
  remainingAttractions?: string[]
  currentAttractionIntro?: string
}) {
  const res = await apiClient.post('/api/trip/guide/ask', payload)
  return res.data
}

export async function getAttractionState(name: string, city = '') {
  const res = await apiClient.get('/api/plaza/attraction/state', { params: { name, city } })
  return res.data
}

export async function updateAttractionState(payload: {
  name: string
  city?: string
  favorite?: boolean
  want_to_go?: boolean
  visited?: boolean
  checked_in?: boolean
}) {
  const res = await apiClient.post('/api/plaza/attraction/state', payload)
  return res.data
}

export async function listAttractionStates() {
  return withLocalCache('plaza-attraction-states', async () => {
    const res = await apiClient.get('/api/plaza/attraction/states')
    return res.data
  }, 90)
}

export async function addAttractionToTrip(payload: {
  tripId: string
  dayIndex?: number
  attraction: {
    name: string
    city?: string
    intro?: string
    image?: string
    location?: { lat?: number | null; lng?: number | null } | null
  }
}) {
  const res = await apiClient.post('/api/trip/add-attraction', payload)
  return res.data
}

export async function createTripWithAttraction(payload: {
  city: string
  startDate: string
  attraction: {
    name: string
    city?: string
    intro?: string
    image?: string
    location?: { lat?: number | null; lng?: number | null } | null
  }
}) {
  const res = await apiClient.post('/api/trip/create-with-attraction', payload)
  return res.data
}

export async function previewGuideReplan(payload: {
  tripId: string
  mode: string
  note?: string
  currentLocation?: { lat: number; lng: number } | null
  doneAttractions?: string[]
}) {
  const res = await apiClient.post('/api/trip/replan/preview', payload)
  return res.data
}

export async function applyGuideReplan(payload: {
  tripId: string
  orderedRemainingNames: string[]
  doneNames?: string[]
}) {
  const res = await apiClient.post('/api/trip/replan/apply', payload)
  return res.data
}

export type VideoTripContextInput = {
  tripId?: string
  tripTitle?: string
  tripCity?: string
  sourceAttraction?: string
}

export type VideoTaskStatus = {
  task_id?: string
  status: string
  progress: number
  message: string
  video_url?: string | null
  trip_id?: string | null
  trip_title?: string | null
  trip_city?: string | null
  source_attraction?: string | null
}

export type VideoHistoryItem = {
  task_id: string
  scenic_name: string
  status: string
  progress: number
  message: string
  created_at?: string
  updated_at?: string
  video_url?: string | null
  file_exists?: boolean
  trip_id?: string | null
  trip_title?: string | null
  trip_city?: string | null
  source_attraction?: string | null
}

export async function generateVideo(scenicName: string, tripContext: VideoTripContextInput = {}) {
  const res = await apiClient.post('/api/video/generate', {
    scenic_name: scenicName,
    trip_id: tripContext.tripId || undefined,
    trip_title: tripContext.tripTitle || undefined,
    trip_city: tripContext.tripCity || undefined,
    source_attraction: tripContext.sourceAttraction || undefined,
  }, {
    timeout: 600000, // 10 min - 视频生成（TTS + 渲染）需要较长时间
  })
  return res.data
}

export async function getVideoStatus(taskId: string) {
  const res = await apiClient.get(`/api/video/status/${taskId}`)
  return res.data
}

export async function getVideoHistory() {
  return withLocalCache('video-history', async () => {
    const res = await apiClient.get('/api/video/history')
    return res.data
  }, 60)
}

export async function deleteVideoHistory(taskId: string) {
  const res = await apiClient.delete(`/api/video/history/${taskId}`)
  return res.data
}

export default apiClient
