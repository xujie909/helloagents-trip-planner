<template>
  <div class="ds-screen">
    <!-- 顶部 -->
    <header class="ds-header">
      <div class="ds-h-left">
        <span class="ds-h-seal">行</span>
        <span class="ds-h-title">知行旅行 · 运营数据大屏</span>
      </div>
      <div class="ds-h-right">
        <span class="ds-h-time">{{ nowStr }}</span>
        <span class="ds-h-dot">●</span>
        <span class="ds-h-status">实时监控中</span>
      </div>
    </header>

    <!-- 指标卡片 -->
    <section class="ds-cards">
      <div class="dsc-card">
        <div class="dsc-icon">👥</div>
        <div class="dsc-val">{{ data.user_count }}</div>
        <div class="dsc-label">注册用户</div>
        <div class="dsc-sub">活跃 {{ data.active_users }} 人</div>
      </div>
      <div class="dsc-card">
        <div class="dsc-icon">📋</div>
        <div class="dsc-val">{{ data.trip_total }}</div>
        <div class="dsc-label">总行程</div>
        <div class="dsc-sub">本周 +{{ data.week_trips }}</div>
      </div>
      <div class="dsc-card">
        <div class="dsc-icon">💬</div>
        <div class="dsc-val">{{ data.chat_total }}</div>
        <div class="dsc-label">总对话</div>
        <div class="dsc-sub">今日 {{ data.today_chats }} 条</div>
      </div>
      <div class="dsc-card">
        <div class="dsc-icon">📚</div>
        <div class="dsc-val">{{ data.knowledge_count }}</div>
        <div class="dsc-label">知识库条目</div>
        <div class="dsc-sub">FAQ {{ data.faq_count }} 条</div>
      </div>
      <div class="dsc-card">
        <div class="dsc-icon">😊</div>
        <div class="dsc-val">{{ data.satisfaction_rate }}<span class="dsc-unit">%</span></div>
        <div class="dsc-label">游客满意度</div>
        <div class="dsc-sub">好评 {{ data.pos_count }} · 差评 {{ data.neg_count }}</div>
      </div>
      <div class="dsc-card">
        <div class="dsc-icon">🗺️</div>
        <div class="dsc-val">{{ (data.plaza_records||0).toLocaleString() }}</div>
        <div class="dsc-label">广场数据</div>
        <div class="dsc-sub">覆盖全国景点</div>
      </div>
    </section>

    <!-- 中间：图表区 -->
    <section class="ds-charts">
      <!-- 热门景点 -->
      <div class="ds-panel ds-hot-attrs">
        <h3 class="ds-panel-title">🏆 热门景点 TOP10</h3>
        <div class="ds-bar-list">
          <div v-for="(a,i) in data.hot_attractions||[]" :key="a[0]" class="ds-bar-row">
            <span class="ds-bar-rank" :class="'rank-'+i">{{ i+1 }}</span>
            <span class="ds-bar-name">{{ a[0] }}</span>
            <div class="ds-bar-track">
              <div class="ds-bar-fill" :style="{width: barWidth(a[1], (data.hot_attractions||[])[0]?.[1]||1)+'%'}"></div>
            </div>
            <span class="ds-bar-val">{{ a[1].toLocaleString() }}</span>
          </div>
        </div>
      </div>

      <!-- 满意度饼图 -->
      <div class="ds-panel ds-sentiment">
        <h3 class="ds-panel-title">😊 游客满意度分布</h3>
        <div class="ds-pie-wrap">
          <svg viewBox="0 0 200 200" class="ds-pie-svg">
            <circle cx="100" cy="100" r="80" fill="none" stroke="#f0ece6" stroke-width="30" />
            <template v-for="seg in pieSegments" :key="seg.label">
              <circle cx="100" cy="100" r="80" fill="none"
                :stroke="seg.color" stroke-width="30"
                :stroke-dasharray="seg.dashArray"
                :stroke-dashoffset="seg.dashOffset"
                transform="rotate(-90 100 100)"
                style="transform-origin:100px 100px;transition:all 1s ease-out" />
            </template>
          </svg>
          <div class="ds-pie-legend">
            <div v-for="(seg,si) in pieSegments" :key="si" class="ds-pl-item">
              <span class="ds-pl-dot" :style="{background:seg.color}"></span>
              <span class="ds-pl-label">{{ seg.label }}</span>
              <span class="ds-pl-val">{{ seg.value }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 热门问答 -->
      <div class="ds-panel ds-hot-qa">
        <h3 class="ds-panel-title">🔥 热门问答</h3>
        <div class="ds-qa-list">
          <div v-for="(q,i) in (data.hot_questions||[]).slice(-10).reverse()" :key="i" class="ds-qa-item">
            <span class="ds-qa-idx">{{ i+1 }}</span>
            <span class="ds-qa-text">{{ q }}</span>
          </div>
          <div v-if="!(data.hot_questions||[]).length" class="ds-empty">暂无数据</div>
        </div>
      </div>
    </section>

    <!-- 底部：趋势 -->
    <section class="ds-bottom">
      <div class="ds-panel ds-trend">
        <h3 class="ds-panel-title">📈 本周趋势</h3>
        <div class="ds-trend-cards">
          <div class="ds-tc-item">
            <span class="ds-tc-val">{{ data.week_trips }}</span>
            <span class="ds-tc-label">本周行程</span>
          </div>
          <div class="ds-tc-item">
            <span class="ds-tc-val">{{ data.week_chats }}</span>
            <span class="ds-tc-label">本周对话</span>
          </div>
          <div class="ds-tc-item">
            <span class="ds-tc-val">{{ data.today_trips }}</span>
            <span class="ds-tc-label">今日行程</span>
          </div>
          <div class="ds-tc-item">
            <span class="ds-tc-val">{{ data.today_chats }}</span>
            <span class="ds-tc-label">今日对话</span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { isLoggedIn } from '@/services/api'

const router = useRouter()
const nowStr = ref('')
let timer: any = null; let dataTimer: any = null

const data = ref<any>({
  user_count: 0, active_users: 0, trip_total: 0, chat_total: 0,
  today_trips: 0, today_chats: 0, week_trips: 0, week_chats: 0,
  knowledge_count: 0, faq_count: 0, plaza_records: 0,
  satisfaction_rate: 0, pos_count: 0, neg_count: 0,
  hot_attractions: [], hot_questions: [], sentiment_data: []
})

const pieSegments = computed(() => {
  const sd = data.value.sentiment_data || []
  if (!sd.length) return []
  const total = sd.reduce((s: number, x: any) => s + x.value, 0) || 1
  const circumference = 2 * Math.PI * 80
  let offset = 0
  return sd.map((seg: any) => {
    const ratio = seg.value / total
    const dashArray = `${ratio * circumference} ${(1 - ratio) * circumference}`
    const dashOffset = -offset
    offset += ratio * circumference
    return { ...seg, dashArray, dashOffset }
  })
})

function barWidth(val: number, max: number): number {
  return max > 0 ? Math.round((val / max) * 100) : 0
}

function updateTime() {
  const n = new Date()
  nowStr.value = n.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
    + ' ' + n.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

async function loadData() {
  try {
    const r = await fetch('/api/admin/dashboard', { headers: { 'X-Username': 'admin' } })
    const d = await r.json()
    if (d.success) data.value = d.data
  } catch {}
}

onMounted(async () => {
  if (!isLoggedIn()) { router.replace('/login'); return }
  const isAdmin = localStorage.getItem('is_admin') === '1'
  if (!isAdmin) { router.replace('/dashboard'); return }
  updateTime()
  timer = setInterval(updateTime, 1000)
  loadData()
  dataTimer = setInterval(loadData, 15000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (dataTimer) clearInterval(dataTimer)
})
</script>

<style scoped>
.ds-screen {
  min-height: 100vh;
  background: #faf7f2;
  color: #5c3a21;
  padding: 24px 32px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'STKaiti', '楷体', sans-serif;
  overflow-y: auto;
}

/* 头部 */
.ds-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 28px;
  background: linear-gradient(135deg, #fef8f5, #fdf5ee);
  border: 1px solid #eadccf;
  border-radius: 16px;
  margin-bottom: 20px;
}
.ds-h-left { display: flex; align-items: center; gap: 12px; }
.ds-h-seal {
  width: 44px; height: 44px; border-radius: 8px;
  background: linear-gradient(135deg, #c43b3b, #a0522d);
  color: #faf0d7; display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 900; font-family: 'STKaiti', '楷体', 'KaiTi', serif;
  animation: sealIn .5s cubic-bezier(.34,1.56,.64,1) both;
}
@keyframes sealIn { from{transform:scale(0)rotate(-15deg);opacity:0} to{transform:scale(1)rotate(0);opacity:1} }
.ds-h-title { font-size: 22px; font-weight: 700; color: #5c3a21; font-family: 'STKaiti', '楷体', 'KaiTi', serif; }
.ds-h-right { display: flex; align-items: center; gap: 10px; font-size: 14px; color: #b8a088; }
.ds-h-dot { color: #52c41a; animation: dotPulse 2s infinite; }
@keyframes dotPulse { 0%,100%{opacity:1} 50%{opacity:.3} }
.ds-h-status { color: #52c41a; font-weight: 500; }

/* 指标卡片 */
.ds-cards {
  display: grid; grid-template-columns: repeat(6, 1fr); gap: 14px;
  margin-bottom: 20px;
}
.dsc-card {
  background: #fff;
  border: 1px solid #eadccf;
  border-radius: 14px; padding: 20px 16px;
  text-align: center; transition: all .3s;
}
.dsc-card:hover {
  transform: translateY(-4px);
  border-color: #d4a89a;
  box-shadow: 0 6px 20px rgba(139,69,19,0.06);
}
.dsc-icon { font-size: 28px; margin-bottom: 6px; }
.dsc-val { font-size: 30px; font-weight: 800; color: #c43b3b; }
.dsc-unit { font-size: 15px; color: #b8a088; margin-left: 2px; }
.dsc-label { font-size: 13px; color: #6b5344; margin-top: 4px; font-weight: 500; }
.dsc-sub { font-size: 11px; color: #b8a088; margin-top: 4px; }

/* 图表区 */
.ds-charts {
  display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 14px;
  margin-bottom: 20px;
}
.ds-panel {
  background: #fff;
  border: 1px solid #eadccf;
  border-radius: 14px; padding: 20px 24px;
}
.ds-panel-title { font-size: 16px; font-weight: 700; margin: 0 0 16px; color: #5c3a21; font-family: 'STKaiti', '楷体', 'KaiTi', serif; }

/* 柱状图 */
.ds-bar-list { display: flex; flex-direction: column; gap: 10px; }
.ds-bar-row { display: flex; align-items: center; gap: 8px; }
.ds-bar-rank {
  width: 22px; height: 22px; border-radius: 6px; display: flex;
  align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0;
}
.rank-0 { background: #c43b3b; color: #fff; }
.rank-1,.rank-2 { background: #e85050; color: #fff; }
.rank-3,.rank-4,.rank-5 { background: #fdf0e8; color: #c43b3b; }
.ds-bar-rank:not(.rank-0):not(.rank-1):not(.rank-2):not(.rank-3):not(.rank-4):not(.rank-5) { background: #faf7f2; color: #b8a088; }
.ds-bar-name { width: 60px; font-size: 13px; color: #5c3a21; flex-shrink: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 500; }
.ds-bar-track { flex: 1; height: 8px; background: #f0ece6; border-radius: 4px; overflow: hidden; }
.ds-bar-fill { height: 100%; background: linear-gradient(90deg, #c43b3b, #e85050); border-radius: 4px; transition: width 1.2s ease-out; min-width: 4px; }
.ds-bar-val { width: 50px; text-align: right; font-size: 12px; color: #b8a088; flex-shrink: 0; }

/* 饼图 */
.ds-pie-wrap { display: flex; align-items: center; gap: 20px; }
.ds-pie-svg { width: 150px; height: 150px; flex-shrink: 0; }
.ds-pie-legend { display: flex; flex-direction: column; gap: 8px; }
.ds-pl-item { display: flex; align-items: center; gap: 6px; }
.ds-pl-dot { width: 10px; height: 10px; border-radius: 50%; }
.ds-pl-label { font-size: 13px; color: #5c3a21; }
.ds-pl-val { font-size: 13px; color: #b8a088; margin-left: auto; }

/* 热门问答 */
.ds-qa-list { display: flex; flex-direction: column; gap: 6px; max-height: 350px; overflow-y: auto; }
.ds-qa-item { display: flex; align-items: flex-start; gap: 8px; padding: 8px 10px; background: #faf7f2; border-radius: 8px; }
.ds-qa-idx { width: 18px; height: 18px; border-radius: 50%; background: #fdf0e8; color: #c43b3b; font-size: 11px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-weight: 600; }
.ds-qa-text { font-size: 13px; color: #6b5344; line-height: 1.5; }
.ds-empty { text-align: center; color: #b8a088; padding: 24px; font-size: 13px; }

/* 底部 */
.ds-bottom { display: grid; grid-template-columns: 1fr; gap: 14px; }
.ds-trend-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.ds-tc-item { text-align: center; padding: 20px; background: #fefcf8; border: 1px solid #eadccf; border-radius: 12px; transition: all .2s; }
.ds-tc-item:hover { border-color: #d4a89a; background: #fef8f5; }
.ds-tc-val { font-size: 30px; font-weight: 800; color: #c43b3b; display: block; }
.ds-tc-label { font-size: 12px; color: #b8a088; margin-top: 4px; }

@media (max-width: 1100px) {
  .ds-screen { padding: 16px; }
  .ds-cards { grid-template-columns: repeat(3, 1fr); }
  .ds-charts { grid-template-columns: 1fr; }
  .ds-trend-cards { grid-template-columns: repeat(2, 1fr); }
  .ds-header { flex-direction: column; gap: 8px; text-align: center; }
}
@media (max-width: 600px) {
  .ds-cards { grid-template-columns: repeat(2, 1fr); }
}
</style>
