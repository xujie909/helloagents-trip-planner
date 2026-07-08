<template>
  <div class="dashboard">
    <!-- 移动端顶部条 -->
    <header class="mobile-bar" @click="sidebarOpen = !sidebarOpen">
      <span class="mobile-brand">🏮 知行旅行</span>
      <span class="mobile-hamburger">☰</span>
    </header>
    <div v-if="sidebarOpen" class="sidebar-overlay" @click="sidebarOpen = false"></div>

    <!-- 侧边栏 -->
    <aside :class="['sidebar', { open: sidebarOpen }]">
      <div class="sidebar-brand">
        <span class="brand-seal">行</span>
        <div class="brand-text">
          <span class="brand-name">知行旅行</span>
          <span class="brand-desc">中国之旅</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div :class="['nav-item', { active: currentView === 'home' }]" @click="navigate('home')">
          <span class="nav-icon">🏮</span><span>首页</span>
        </div>
        <div :class="['nav-item', { active: currentView === 'profile' }]" @click="navigate('profile')">
          <span class="nav-icon">👤</span><span>个人档案</span>
        </div>
        <div :class="['nav-item', { active: currentView === 'chat' }]" @click="navigate('chat')">
          <span class="nav-icon">💬</span><span>旅行顾问</span>
        </div>
        <div :class="['nav-item', { active: currentView === 'plan' }]" @click="navigate('plan')">
          <span class="nav-icon">📜</span><span>行程规划</span>
        </div>
        <div :class="['nav-item', { active: currentView === 'history' }]" @click="navigate('history')">
          <span class="nav-icon">📋</span><span>行囊记录</span>
        </div>
        <div :class="['nav-item', { active: currentView === 'guide' }]" @click="navigate('guide')">
          <span class="nav-icon">🧭</span><span>旅行导览</span>
        </div>
        <div :class="['nav-item plaza-nav', { active: currentView === 'plaza' }]" @click="navigate('plaza')">
          <span class="nav-icon">📊</span><span>数据广场</span>
        </div>
        <div :class="['nav-item', { active: currentView === 'video' }]" @click="navigate('video')">
          <span class="nav-icon">🎬</span><span>旅行视频</span>
        </div>
        <div :class="['nav-item', { active: currentView === 'manual' }]" @click="navigate('manual')">
          <span class="nav-icon">📖</span><span>使用手记</span>
        </div>
      </nav>

      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-avatar">🎒</div>
          <div class="user-detail">
            <div class="user-name">{{ username }}</div>
          </div>
        </div>
        <div class="logout-btn" @click="handleLogout" title="退出">🚪</div>
      </div>
    </aside>

    <main class="main-content">
      <Transition name="view-fade" mode="out-in">
        <HomePage v-if="currentView === 'home'" key="home" @navigate="handleHomeAction" />
        <ProfilePage v-else-if="currentView === 'profile'" key="profile" />
        <HomeView v-else-if="currentView === 'chat'" key="chat" />
        <PlanForm v-else-if="currentView === 'plan'" key="plan" />
        <HistoryView v-else-if="currentView === 'history'" key="history" @goPlan="navigate('plan')" />
      <TourGuide v-else-if="currentView === 'guide'" key="guide" />
      <DataPlaza v-else-if="currentView === 'plaza'" key="plaza" />
      <VideoGenerate v-else-if="currentView === 'video'" key="video" />
      <GuidePage v-else-if="currentView === 'manual'" key="manual" />
      </Transition>
    </main>

    <!-- 全局数字人助手 -->
    <DigitalHuman :currentPage="currentView" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  isLoggedIn,
  logout,
  getStoredUser,
  getMe,
  hydrateAuthUser,
  getCurrentTripContext,
  markCurrentTripViewed,
} from '@/services/api'
import HomePage from './HomePage.vue'
import ProfilePage from './ProfilePage.vue'
import HomeView from './Home.vue'
import PlanForm from './PlanForm.vue'
import HistoryView from './History.vue'
import TourGuide from './TourGuide.vue'
import DataPlaza from './DataPlaza.vue'
import GuidePage from './GuidePage.vue'
import VideoGenerate from './VideoGenerate.vue'
import DigitalHuman from '../components/DigitalHuman.vue'

const router = useRouter()
const route = useRoute()
const currentView = ref<'home' | 'profile' | 'chat' | 'plan' | 'history' | 'guide' | 'plaza' | 'manual' | 'video'>('home')
const sidebarOpen = ref(false)
const username = computed(() => getStoredUser().name || getStoredUser().username || '行者')
const VALID_VIEWS = ['home', 'profile', 'chat', 'plan', 'history', 'guide', 'plaza', 'manual', 'video'] as const

type DashboardView = typeof VALID_VIEWS[number]

function isDashboardView(view: string): view is DashboardView {
  return VALID_VIEWS.includes(view as DashboardView)
}

function syncViewFromRoute() {
  const queryView = String(route.query.view || '')
  if (isDashboardView(queryView)) currentView.value = queryView
}

function navigate(view: DashboardView) {
  currentView.value = view
  sidebarOpen.value = false
  if (view !== 'plan') {
    markCurrentTripViewed(view)
  }
  if (route.query.view !== view) router.replace({ path: '/dashboard', query: { view } })
}

function openCurrentTripFromHome() {
  const currentTrip = getCurrentTripContext()
  if (!currentTrip?.tripId) {
    navigate('history')
    return
  }
  markCurrentTripViewed('history')
  router.push({ path: `/history/${currentTrip.tripId}` })
}

function handleHomeAction(payload?: string) {
  if (payload === 'resume-current-trip') {
    openCurrentTripFromHome()
    return
  }
  if (payload && isDashboardView(payload)) {
    navigate(payload)
  }
}

watch(() => route.query.view, syncViewFromRoute)

onMounted(async () => {
  if (!isLoggedIn()) { router.replace('/login'); return }
  syncViewFromRoute()
  try {
    const res = await getMe()
    if (res.user) {
      hydrateAuthUser({
        username: res.user.username,
        name: res.user.name,
        last_login: res.user.last_login,
        login_count: res.user.login_count,
      })
    }
  } catch {}
})

async function handleLogout() { await logout(); router.replace('/login') }
</script>

<style scoped>
.dashboard { display: flex; height: 100vh; background: #faf7f2; }

.mobile-bar { display: none; align-items: center; justify-content: space-between; padding: 12px 16px; background: #fff; border-bottom: 1px solid #e8dccf; cursor: pointer; }
.mobile-brand { font-size: 16px; font-weight: 700; color: #8b4513; }
.mobile-hamburger { font-size: 22px; color: #8b4513; }
.sidebar-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.3); z-index: 90; }

/* ---- 侧边栏 ---- */
.sidebar {
  width: 220px; background: linear-gradient(180deg, #fdf8f2 0%, #faf5ee 100%);
  display: flex; flex-direction: column; border-right: 1px solid #e8dccf; flex-shrink: 0;
  transition: transform 0.25s; z-index: 100;
}
.sidebar-brand { padding: 28px 20px 22px; display: flex; align-items: center; gap: 12px; border-bottom: 2px solid #e8dccf; }
.brand-seal {
  width: 44px; height: 44px; border-radius: 8px; background: #c43b3b; color: #faf0d7;
  display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 900;
  font-family: 'STKaiti','楷体','KaiTi',serif; flex-shrink: 0; box-shadow: 0 2px 8px rgba(196,59,59,0.3);
}
.brand-text { display: flex; flex-direction: column; }
.brand-name { font-size: 17px; font-weight: 700; color: #5c3a21; font-family: 'STKaiti','楷体','KaiTi',serif; }
.brand-desc { font-size: 11px; color: #b8a088; margin-top: 2px; }

.sidebar-nav { flex: 1; padding: 16px 10px; display: flex; flex-direction: column; gap: 2px; }
.nav-item {
  display: flex; align-items: center; gap: 10px; padding: 12px 16px;
  border-radius: 10px; cursor: pointer; font-size: 15px; color: #6b5344; transition: all 0.2s;
}
.nav-item:hover { background: #f5ede0; color: #5c3a21; }
.nav-item.active { background: linear-gradient(135deg, #fdf0e8, #fef5ec); color: #c43b3b; font-weight: 600; border: 1px solid #f0d5c0; }
.nav-icon { font-size: 18px; }

.sidebar-footer { padding: 14px 16px; border-top: 1px solid #e8dccf; display: flex; align-items: center; gap: 8px; }
.user-info { flex: 1; display: flex; align-items: center; gap: 10px; min-width: 0; }
.user-avatar { width: 36px; height: 36px; border-radius: 50%; background: #f5ede0; display: flex; align-items: center; justify-content: center; font-size: 18px; }
.user-name { font-size: 14px; font-weight: 600; color: #5c3a21; }
.logout-btn { font-size: 18px; cursor: pointer; padding: 6px; border-radius: 8px; }
.logout-btn:hover { background: #fde8e8; }

.main-content { flex: 1; overflow: hidden auto; display: flex; flex-direction: column; }
.view-fade-enter-active { transition: all .25s ease-out; }
.view-fade-leave-active { transition: all .15s ease-in; }
.view-fade-enter-from { opacity: 0; transform: translateY(8px); }
.view-fade-leave-to { opacity: 0; transform: translateY(-4px); }

@media (max-width: 767px) {
  .dashboard { flex-direction: column; }
  .mobile-bar { display: flex; }
  .sidebar-overlay { display: block; }
  .sidebar { position: fixed; top: 0; left: 0; bottom: 0; z-index: 100; transform: translateX(-100%); box-shadow: 4px 0 24px rgba(0,0,0,0.15); }
  .sidebar.open { transform: translateX(0); }
  .main-content { flex: 1; overflow-y: auto; }
}
</style>
