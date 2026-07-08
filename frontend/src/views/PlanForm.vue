<template>
  <div class="plan-page">
    <div class="plan-header">
      <div class="header-icon">📜</div>
      <h1 class="plan-title">行程规划</h1>
      <p class="plan-subtitle">千里之行 · 始于足下 — 填写信息，AI 为你量身打造旅行计划</p>
    </div>

    <a-card class="form-card" :bordered="false">
      <a-form :model="form" layout="vertical" @finish="handleSubmit">
        <!-- 目的地与日期 -->
        <div class="section">
          <div class="section-head"><span class="section-seal">地</span><span class="section-title">目的地与日期</span></div>
          <a-row :gutter="[16,16]">
            <a-col :xs="24" :sm="8">
              <a-form-item name="city" :rules="[{ required: true, message: '请输入目的地' }]">
                <template #label><span class="field-label">目的地城市</span></template>
                <a-input v-model:value="form.city" placeholder="例如：北京" size="large" class="chinese-input" />
              </a-form-item>
            </a-col>
            <a-col :xs="12" :sm="6">
              <a-form-item name="start_date" :rules="[{ required: true, message: '请选择' }]">
                <template #label><span class="field-label">出发日期</span></template>
                <a-date-picker v-model:value="form.start_date" style="width:100%" size="large" placeholder="选择日期" />
              </a-form-item>
            </a-col>
            <a-col :xs="12" :sm="6">
              <a-form-item name="end_date" :rules="[{ required: true, message: '请选择' }]">
                <template #label><span class="field-label">结束日期</span></template>
                <a-date-picker v-model:value="form.end_date" style="width:100%" size="large" placeholder="选择日期" />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :sm="4">
              <a-form-item label="行程天数">
                <div class="days-badge">{{ form.travel_days }} 天</div>
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <!-- 偏好 -->
        <div class="section">
          <div class="section-head"><span class="section-seal">好</span><span class="section-title">偏好设置</span></div>
          <a-row :gutter="[16,16]">
            <a-col :xs="24" :sm="8">
              <a-form-item><template #label><span class="field-label">交通方式</span></template>
                <a-select v-model:value="form.transportation" size="large">
                  <a-select-option value="公共交通">🚇 公共交通</a-select-option>
                  <a-select-option value="自驾">🚗 自驾</a-select-option>
                  <a-select-option value="步行">🚶 步行</a-select-option>
                  <a-select-option value="混合">🔀 混合</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :xs="24" :sm="8">
              <a-form-item><template #label><span class="field-label">住宿偏好</span></template>
                <a-select v-model:value="form.accommodation" size="large">
                  <a-select-option value="经济型酒店">💰 经济型</a-select-option>
                  <a-select-option value="舒适型酒店">🏨 舒适型</a-select-option>
                  <a-select-option value="豪华酒店">⭐ 豪华型</a-select-option>
                  <a-select-option value="民宿">🏡 民宿</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :xs="24" :sm="8">
              <a-form-item><template #label><span class="field-label">旅行偏好</span></template>
                <a-checkbox-group v-model:value="form.preferences" style="display:flex;flex-wrap:wrap;gap:6px">
                  <a-checkbox value="历史文化">🏛️ 历史文化</a-checkbox>
                  <a-checkbox value="自然风光">🏞️ 自然风光</a-checkbox>
                  <a-checkbox value="美食">🍜 美食</a-checkbox>
                  <a-checkbox value="购物">🛍️ 购物</a-checkbox>
                  <a-checkbox value="艺术">🎨 艺术</a-checkbox>
                  <a-checkbox value="休闲">☕ 休闲</a-checkbox>
                </a-checkbox-group>
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <!-- 额外要求 -->
        <div class="section">
          <div class="section-head"><span class="section-seal">言</span><span class="section-title">额外要求（选填）</span></div>
          <a-textarea v-model:value="form.free_text_input" placeholder="例如：想去博物馆、对海鲜过敏、需要无障碍设施..." :rows="3" size="large" />
        </div>

        <!-- 提交 -->
        <a-button type="primary" html-type="submit" :loading="loading" size="large" block class="submit-btn">
          <template v-if="!loading"><span class="btn-text">🚀 生成旅行计划</span></template>
          <template v-else><span class="btn-text">正在生成中...</span></template>
        </a-button>

        <Transition name="progress">
          <div v-if="loading" class="progress-area">
            <a-progress :percent="progress" :stroke-color="{ '0%': '#c43b3b', '100%': '#8b4513' }" :stroke-width="8" />
            <p class="progress-text">{{ statusText }}</p>
          </div>
        </Transition>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { generateTripPlan } from '@/services/api'
import type { TripFormData } from '@/types'
import type { Dayjs } from 'dayjs'

const router = useRouter()
const loading = ref(false); const progress = ref(0); const statusText = ref('')

const form = reactive<{
  city: string; start_date: Dayjs | null; end_date: Dayjs | null
  travel_days: number; transportation: string; accommodation: string
  preferences: string[]; free_text_input: string
}>({
  city: '', start_date: null, end_date: null, travel_days: 1,
  transportation: '公共交通', accommodation: '经济型酒店',
  preferences: [], free_text_input: ''
})

watch([() => form.start_date, () => form.end_date], ([s, e]) => {
  if (s && e) { const d = e.diff(s, 'day') + 1; if (d>0&&d<=30) form.travel_days=d; else { message.warning('日期范围需在 1-30 天内'); form.end_date=null } }
})

async function handleSubmit() {
  if (!form.start_date || !form.end_date) { message.error('请选择日期'); return }
  loading.value=true; progress.value=0
  const interval = setInterval(() => {
    if (progress.value<90) { progress.value+=7; const p=progress.value
      if (p<=25) statusText.value='🔍 搜索景点...'
      else if (p<=50) statusText.value='🌤️ 查询天气...'
      else if (p<=75) statusText.value='🏨 推荐酒店...'
      else statusText.value='📋 生成行程...' }
  },600)
  try {
    const req: TripFormData = {
      city:form.city, start_date:form.start_date!.format('YYYY-MM-DD'), end_date:form.end_date!.format('YYYY-MM-DD'),
      travel_days:form.travel_days, transportation:form.transportation, accommodation:form.accommodation,
      preferences:form.preferences, free_text_input:form.free_text_input
    }
    const res=await generateTripPlan(req); clearInterval(interval); progress.value=100; statusText.value='✅ 完成'
    if (res.success&&res.data) {
      sessionStorage.setItem('tripPlan',JSON.stringify(res.data))
      sessionStorage.removeItem('tripRecordId')
      sessionStorage.removeItem('tripRecordSnapshot')
      message.success('生成成功')
      setTimeout(()=>router.push('/result'),600)
    }
    else { message.error(res.message||'生成失败') }
  } catch(e:any) { clearInterval(interval); message.error(e.message||'生成失败') }
  finally { setTimeout(()=>{loading.value=false;progress.value=0;statusText.value=''},1000) }
}
</script>

<style scoped>
.plan-page { padding: 32px 40px; max-width: 900px; margin: 0 auto; animation: pageIn .4s ease-out both; will-change:transform,opacity }
@keyframes pageIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }

.plan-header { text-align: center; margin-bottom: 28px; }
.header-icon { font-size: 44px; animation: bounceIn 0.6s cubic-bezier(0.34,1.56,0.64,1); }
@keyframes bounceIn { from{transform:scale(0)} to{transform:scale(1)} }
.plan-title { font-size: 30px; font-weight: 800; color: #5c3a21; margin: 8px 0 6px; font-family: 'STKaiti','楷体','KaiTi',serif; }
.plan-subtitle { font-size: 14px; color: #b8a088; margin: 0; }

.form-card { border-radius: 18px; box-shadow: 0 4px 24px rgba(139,69,19,0.05); border: 1px solid #eadccf; }

.section { margin-bottom: 20px; padding: 20px 22px; background: #faf7f2; border-radius: 14px; border: 1px solid #eadccf; transition: box-shadow 0.3s; }
.section:hover { box-shadow: 0 2px 12px rgba(139,69,19,0.06); }
.section-head { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
.section-seal {
  width: 26px; height: 26px; border-radius: 4px; background: #c43b3b; color: #faf0d7;
  display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 700;
  font-family: 'STKaiti','楷体','KaiTi',serif;
}
.section-title { font-size: 16px; font-weight: 700; color: #5c3a21; }
.field-label { font-weight: 500; color: #6b5344; font-size: 14px; }

.chinese-input :deep(.ant-input) { border-radius: 10px; border-color: #e8dccf; }
.chinese-input :deep(.ant-input:hover), .chinese-input :deep(.ant-input:focus) { border-color: #c43b3b; box-shadow: 0 0 0 3px rgba(196,59,59,0.08); }

.days-badge {
  display: flex; align-items: center; justify-content: center; height: 40px;
  background: linear-gradient(135deg, #c43b3b, #8b4513); border-radius: 10px;
  color: #faf0d7; font-size: 20px; font-weight: 700; transition: transform 0.3s;
}

.submit-btn {
  height: 52px; border-radius: 26px; font-size: 17px; font-weight: 600;
  background: linear-gradient(135deg, #c43b3b, #8b4513); border: none;
  box-shadow: 0 6px 20px rgba(196,59,59,0.25); margin-top: 4px;
  transition: all 0.3s;
}
.submit-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 8px 26px rgba(196,59,59,0.35); }
.submit-btn:active:not(:disabled) { transform: translateY(0); }
.btn-text { letter-spacing: 2px; }

.progress-area { margin-top: 20px; text-align: center; }
.progress-text { margin-top: 10px; color: #c43b3b; font-size: 16px; font-weight: 500; }
.progress-enter-active { transition: all 0.4s ease-out; }
.progress-leave-active { transition: all 0.2s ease-in; }
.progress-enter-from { opacity: 0; transform: translateY(-10px); }
.progress-leave-to { opacity: 0; }

/* ========== 手机端 ========== */
@media (max-width: 767px) {
  .plan-page { padding: 14px; }
  .plan-title { font-size: 24px; }
  .section { padding: 14px; }
  .days-badge { height: 36px; font-size: 17px; }
}
</style>
