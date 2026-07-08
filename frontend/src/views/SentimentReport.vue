<template>
  <div class="sr-root">
    <div class="sr-header">
      <h2>📊 游客感受度报告</h2>
      <div class="sr-actions">
        <button class="sr-btn" @click="triggerAnalysis" :disabled="analyzing">
          {{ analyzing ? '⏳ 分析中...' : '🔍 生成新报告' }}
        </button>
        <span class="sr-info" v-if="report">生成时间：{{ report.generated_at }}</span>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="!report && !loading" class="sr-empty">
      <div class="sr-empty-icon">📊</div>
      <p>暂无感受度报告</p>
      <p class="sr-empty-hint">点击「生成新报告」开始分析游客交互数据</p>
    </div>

    <div v-if="loading" class="sr-loading">
      <div class="sr-spinner"></div>
      <p>正在分析游客交互数据...</p>
    </div>

    <template v-if="report && !loading">
      <!-- 概览卡片 -->
      <section class="sr-cards">
        <div class="src-card">
          <div class="src-val">{{ report.summary?.total_messages || 0 }}</div>
          <div class="src-label">分析消息数</div>
        </div>
        <div class="src-card">
          <div class="src-val">{{ report.summary?.unique_users || 0 }}</div>
          <div class="src-label">活跃游客</div>
        </div>
        <div class="src-card">
          <div class="src-val">{{ report.summary?.analyzed_days || 0 }}</div>
          <div class="src-label">覆盖天数</div>
        </div>
        <div class="src-card src-card-highlight">
          <div class="src-val">{{ report.sentiment_overview?.positive_rate || 0 }}%</div>
          <div class="src-label">好评率</div>
        </div>
      </section>

      <!-- 情感分布 -->
      <section class="sr-section">
        <h3>😊 情感分布</h3>
        <div class="sr-sentiment-bars">
          <div class="ssb-row">
            <span class="ssb-label">😊 正面</span>
            <div class="ssb-track">
              <div class="ssb-fill ssb-pos" :style="{width: sentimentPosPercent+'%'}"></div>
            </div>
            <span class="ssb-val">{{ report.sentiment_overview?.positive || 0 }}</span>
          </div>
          <div class="ssb-row">
            <span class="ssb-label">😐 中性</span>
            <div class="ssb-track">
              <div class="ssb-fill ssb-neu" :style="{width: sentimentNeuPercent+'%'}"></div>
            </div>
            <span class="ssb-val">{{ report.sentiment_overview?.neutral || 0 }}</span>
          </div>
          <div class="ssb-row">
            <span class="ssb-label">😞 负面</span>
            <div class="ssb-track">
              <div class="ssb-fill ssb-neg" :style="{width: sentimentNegPercent+'%'}"></div>
            </div>
            <span class="ssb-val">{{ report.sentiment_overview?.negative || 0 }}</span>
          </div>
        </div>
      </section>

      <!-- 关注点 -->
      <section class="sr-section" v-if="report.topics?.length">
        <h3>🔍 游客关注点 TOP</h3>
        <div class="sr-topics">
          <div v-for="(t,i) in report.topics" :key="i" class="srt-item">
            <span class="srt-rank">{{ i+1 }}</span>
            <span class="srt-name">{{ t.name }}</span>
            <span class="srt-count">{{ t.count }}</span>
            <span :class="['srt-sentiment', t.sentiment==='正面'?'srt-pos':t.sentiment==='负面'?'srt-neg':'srt-neu']">{{ t.sentiment }}</span>
          </div>
        </div>
      </section>

      <!-- 每日趋势 -->
      <section class="sr-section" v-if="report.daily_trend?.length">
        <h3>📈 情感趋势（最近14天）</h3>
        <div class="sr-trend">
          <div v-for="(d,i) in report.daily_trend" :key="i" class="srt-day">
            <div class="srt-day-bar">
              <div class="srt-bar-pos" :style="{height: dayBarHeight(d, 'positive')+'px'}"></div>
              <div class="srt-bar-neu" :style="{height: dayBarHeight(d, 'neutral')+'px'}"></div>
              <div class="srt-bar-neg" :style="{height: dayBarHeight(d, 'negative')+'px'}"></div>
            </div>
            <span class="srt-day-label">{{ d.date?.slice(5) }}</span>
          </div>
        </div>
        <div class="srt-legend">
          <span><span class="srt-dot srt-dot-pos"></span> 正面</span>
          <span><span class="srt-dot srt-dot-neu"></span> 中性</span>
          <span><span class="srt-dot srt-dot-neg"></span> 负面</span>
        </div>
      </section>

      <!-- 改进建议 -->
      <section class="sr-section" v-if="report.suggestions?.length">
        <h3>💡 服务改进建议</h3>
        <div class="sr-suggestions">
          <div v-for="(s,i) in report.suggestions" :key="i" class="srs-item">
            <span class="srs-num">{{ i+1 }}</span>
            <span class="srs-text">{{ s }}</span>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { isLoggedIn } from '@/services/api'

const report = ref<any>(null)
const loading = ref(false)
const analyzing = ref(false)

const sentimentPosPercent = computed(() => {
  const tot = (report.value?.sentiment_overview?.positive || 0) + (report.value?.sentiment_overview?.neutral || 0) + (report.value?.sentiment_overview?.negative || 0)
  return tot > 0 ? Math.round((report.value?.sentiment_overview?.positive || 0) / tot * 100) : 0
})
const sentimentNeuPercent = computed(() => {
  const tot = (report.value?.sentiment_overview?.positive || 0) + (report.value?.sentiment_overview?.neutral || 0) + (report.value?.sentiment_overview?.negative || 0)
  return tot > 0 ? Math.round((report.value?.sentiment_overview?.neutral || 0) / tot * 100) : 0
})
const sentimentNegPercent = computed(() => {
  const tot = (report.value?.sentiment_overview?.positive || 0) + (report.value?.sentiment_overview?.neutral || 0) + (report.value?.sentiment_overview?.negative || 0)
  return tot > 0 ? Math.round((report.value?.sentiment_overview?.negative || 0) / tot * 100) : 0
})

function dayBarHeight(d: any, key: string): number {
  const max = Math.max(...(report.value?.daily_trend || []).map((x: any) => x.total || 0), 1)
  return Math.round((d[key] || 0) / max * 80)
}

async function loadLatest() {
  loading.value = true
  try {
    const r = await fetch('/api/admin/sentiment/report?latest=true', { headers: { 'X-Username': 'admin' } })
    const d = await r.json()
    if (d.success) report.value = d.data
  } catch {}
  loading.value = false
}

async function triggerAnalysis() {
  analyzing.value = true
  try {
    const r = await fetch('/api/admin/sentiment/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Username': 'admin' },
      body: JSON.stringify({ days: 30 })
    })
    const d = await r.json()
    if (d.success) { report.value = d.data }
    else { alert(d.message || '分析失败') }
  } catch {}
  analyzing.value = false
}

onMounted(() => {
  if (!isLoggedIn()) return
  loadLatest()
})
</script>

<style scoped>
.sr-root { padding: 28px 36px; max-width: 960px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'STKaiti', '楷体', sans-serif; background: #faf7f2; min-height: 100vh; }
.sr-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; flex-wrap: wrap; gap: 12px; }
.sr-header h2 { font-size: 22px; color: #5c3a21; margin: 0; font-family: 'STKaiti', '楷体', 'KaiTi', serif; }
.sr-actions { display: flex; align-items: center; gap: 12px; }
.sr-btn { padding: 10px 22px; border: none; border-radius: 10px; background: linear-gradient(135deg, #c43b3b, #a0522d); color: #fff; font-weight: 600; cursor: pointer; font-family: 'STKaiti', '楷体', 'KaiTi', serif; font-size: 14px; transition: all .2s; }
.sr-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 3px 12px rgba(196,59,59,.3); }
.sr-btn:disabled { opacity: .5; cursor: not-allowed; }
.sr-info { font-size: 13px; color: #b8a088; }

.sr-empty, .sr-loading { text-align: center; padding: 60px; color: #b8a088; }
.sr-empty-icon { font-size: 48px; margin-bottom: 12px; }
.sr-empty-hint { font-size: 13px; }
.sr-spinner { width: 40px; height: 40px; border: 3px solid #eadccf; border-top-color: #c43b3b; border-radius: 50%; margin: 0 auto 16px; animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.sr-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.src-card { text-align: center; padding: 20px; background: #fff; border: 1px solid #eadccf; border-radius: 14px; }
.src-card-highlight { border-color: #c43b3b; background: #fef8f5; }
.src-val { font-size: 28px; font-weight: 800; color: #c43b3b; display: block; }
.src-label { font-size: 13px; color: #b8a088; margin-top: 4px; }

.sr-section { background: #fff; border: 1px solid #eadccf; border-radius: 14px; padding: 20px 24px; margin-bottom: 16px; }
.sr-section h3 { font-size: 16px; color: #5c3a21; margin: 0 0 14px; font-family: 'STKaiti', '楷体', 'KaiTi', serif; }

.sr-sentiment-bars { display: flex; flex-direction: column; gap: 10px; }
.ssb-row { display: flex; align-items: center; gap: 10px; }
.ssb-label { width: 60px; font-size: 14px; flex-shrink: 0; }
.ssb-track { flex: 1; height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden; }
.ssb-fill { height: 100%; border-radius: 10px; transition: width 1s ease-out; }
.ssb-pos { background: linear-gradient(90deg, #52c41a, #73d13d); }
.ssb-neu { background: linear-gradient(90deg, #faad14, #ffc53d); }
.ssb-neg { background: linear-gradient(90deg, #ff4d4f, #ff7875); }
.ssb-val { width: 40px; text-align: right; font-size: 13px; color: #6b5344; flex-shrink: 0; }

.sr-topics { display: flex; flex-direction: column; gap: 6px; }
.srt-item { display: flex; align-items: center; gap: 10px; padding: 8px 12px; background: #faf7f2; border-radius: 8px; }
.srt-rank { width: 22px; height: 22px; border-radius: 6px; background: #c43b3b; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; }
.srt-name { flex: 1; font-size: 14px; color: #5c3a21; font-weight: 500; }
.srt-count { font-size: 13px; color: #6b5344; }
.srt-sentiment { font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.srt-pos { background: #f6ffed; color: #52c41a; }
.srt-neu { background: #fffbe6; color: #faad14; }
.srt-neg { background: #fff2f0; color: #ff4d4f; }

.sr-trend { display: flex; align-items: flex-end; gap: 6px; height: 120px; padding: 10px 0; }
.srt-day { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.srt-day-bar { width: 24px; height: 80px; background: #f0f0f0; border-radius: 6px; display: flex; flex-direction: column-reverse; overflow: hidden; }
.srt-bar-pos { background: #52c41a; border-radius: 2px 2px 0 0; }
.srt-bar-neu { background: #faad14; }
.srt-bar-neg { background: #ff4d4f; border-radius: 0 0 2px 2px; }
.srt-day-label { font-size: 10px; color: #b8a088; }
.srt-legend { display: flex; gap: 16px; margin-top: 8px; font-size: 12px; color: #6b5344; }
.srt-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 4px; vertical-align: middle; }
.srt-dot-pos { background: #52c41a; } .srt-dot-neu { background: #faad14; } .srt-dot-neg { background: #ff4d4f; }

.sr-suggestions { display: flex; flex-direction: column; gap: 8px; }
.srs-item { display: flex; gap: 10px; padding: 12px 16px; background: #fef8f5; border-radius: 10px; border: 1px solid #f0d5c0; }
.srs-num { width: 24px; height: 24px; border-radius: 50%; background: #c43b3b; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; flex-shrink: 0; }
.srs-text { font-size: 14px; color: #5c3a21; line-height: 1.6; }

@media (max-width: 767px) {
  .sr-root { padding: 16px; }
  .sr-cards { grid-template-columns: repeat(2, 1fr); }
  .sr-header { flex-direction: column; align-items: flex-start; }
}
</style>
