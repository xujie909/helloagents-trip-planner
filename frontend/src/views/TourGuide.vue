<template>
  <div class="guide-root">
    <div v-if="!activeTrip" class="guide-select">
      <div class="guide-select-card">
        <div class="guide-seal">导</div>
        <h2>旅行导览</h2>
        <p>选择一个已保存的行程，开启实时语音导览</p>
        <div class="guide-trip-list" v-if="trips.length">
          <div v-for="t in trips" :key="t.id" class="guide-trip-item" @click="startGuide(t)">
            <span class="gti-icon">📍</span><div class="gti-info"><span class="gti-name">{{ t.title||t.start_date+' '+t.city }}</span><span class="gti-meta">{{ t.days }}天 · {{ t.task_done }}/{{ t.task_total }} 已完成</span></div>
            <span class="gti-arrow">→</span>
          </div>
        </div>
        <div v-else class="guide-empty"><p>暂无保存的行程</p><span>去「行程规划」创建一趟旅程吧</span></div>
      </div>
    </div>

    <div v-else class="guide-active">
      <div v-if="!gpsReady" class="gps-banner">
        <span class="gps-banner-icon">📍</span>
        <div class="gps-banner-text">
          <strong>{{ gpsDenied ? 'GPS权限已被拒绝' : '需要获取你的位置信息' }}</strong>
          <span>{{ gpsDenied ? '请在浏览器设置中允许位置权限后点击重试' : '点击授权按钮以开启实时语音导览' }}</span>
        </div>
        <button class="gps-banner-btn" @click="requestGPSPermission">
          {{ gpsDenied ? '🔄 重新授权' : '🔓 开启GPS定位' }}
        </button>
      </div>

      <div class="guide-topbar">
        <div class="gt-left">
          <span class="gt-dot" :class="{on:gpsReady}"></span>
          <span>{{ gpsReady?'GPS已就绪':(userLoc?'IP定位中（精度低）':'等待授权...') }}</span>
        </div>
        <div class="gt-center">{{ activeTrip.title }}</div>
        <button class="gt-close" @click="stopGuide">✕ 结束导览</button>
      </div>
      <div class="guide-map" ref="mapContainer"></div>

      <div class="guide-info-grid">
        <div class="info-card">
          <span class="info-kicker">当前导览状态</span>
          <h3>{{ activeTrip.title || `${activeTrip.start_date} ${activeTrip.city}` }}</h3>
          <div class="info-stat-row">
            <div class="info-stat">
              <span class="label">城市</span>
              <strong>{{ activeTrip.city || '未设置' }}</strong>
            </div>
            <div class="info-stat">
              <span class="label">进度</span>
              <strong>{{ doneList.length }}/{{ allAttractions.length }}</strong>
            </div>
            <div class="info-stat">
              <span class="label">剩余</span>
              <strong>{{ remainingAttractions.length }}</strong>
            </div>
          </div>
          <p class="info-desc">{{ nearestAttraction ? `你当前更接近 ${nearestAttraction.name}，系统会结合当前位置持续更新播报。` : '正在根据当前位置与行程景点计算最合适的下一站。' }}</p>
        </div>

        <div class="info-card" v-if="nearestAttraction">
          <span class="info-kicker">下一站卡</span>
          <h3>🏛️ {{ nearestAttraction.name }}</h3>
          <div class="next-meta-row">
            <span class="next-badge">{{ nearestAttraction.distance < 1000 ? `${Math.round(nearestAttraction.distance)}m` : `${(nearestAttraction.distance / 1000).toFixed(1)}km` }}</span>
            <span class="next-badge soft">{{ nearestAttraction.distance < 500 ? '已接近' : '前往中' }}</span>
          </div>
          <p class="info-desc clamp-3">{{ currentAttractionIntro || '该景点介绍正在后台预加载中，稍后会自动支持讲解与问答。' }}</p>
        </div>

        <div class="info-card replan-card">
          <span class="info-kicker">调整建议卡</span>
          <h3>{{ replanSummaryTitle }}</h3>
          <p class="info-desc">{{ replanSuggestionText }}</p>
          <label class="replan-field">
            <span>重规划模式</span>
            <select v-model="replanMode" class="replan-select">
              <option value="nearby-first">优先最近景点</option>
              <option value="light-first">后半程更轻松</option>
              <option value="compact">压缩剩余行程</option>
            </select>
          </label>
          <label class="replan-field">
            <span>补充说明（可选）</span>
            <textarea v-model="replanNote" class="replan-textarea" rows="3" placeholder="例如：我现在有点累，想少走路；或今晚只想再去两个点。"></textarea>
          </label>
          <div class="replan-actions">
            <button class="replan-btn primary" :disabled="replanLoading || !activeTrip?.id || !remainingAttractions.length" @click="previewReplan">
              {{ replanLoading ? '生成中…' : '生成重规划建议' }}
            </button>
            <button class="replan-btn" :disabled="applyReplanLoading || !replanPreview?.orderedRemainingNames?.length" @click="applyReplanResult">
              {{ applyReplanLoading ? '应用中…' : '应用当前建议' }}
            </button>
          </div>
        </div>
      </div>

      <div class="guide-status">
        <div class="gs-card" v-if="nearestAttraction">
          <span class="gs-label">下一站</span><span class="gs-name">🏛️ {{ nearestAttraction.name }}</span>
          <span class="gs-dist">{{ nearestAttraction.distance<1000?Math.round(nearestAttraction.distance)+'m':(nearestAttraction.distance/1000).toFixed(1)+'km' }}</span>
          <div class="gs-bar"><div :style="{width:Math.min(100,Math.max(0,100-nearestAttraction.distance/10))+'%'}"></div></div>
        </div>
        <div class="gs-card" v-else-if="allAttractions.length">
          <span class="gs-label">📍 行程景点（{{ doneList.length }}/{{ allAttractions.length }} 已完成）</span>
          <div class="gs-all-attrs">
            <span v-for="a in allAttractions" :key="a.name" class="gs-all-tag" :class="{done:doneList.includes(a.name)}">{{ doneList.includes(a.name)?'✅':'' }} {{ a.name }}</span>
          </div>
          <p v-if="!gpsReady" style="font-size:11px;color:#b8a088;margin:8px 0 0">💡 桌面端无法获取GPS，在手机上打开即可体验实时追踪和自动语音播报</p>
        </div>
        <div class="gs-card" v-else><span class="gs-label">状态</span><span class="gs-name">正在搜索周边景点...</span></div>
        <div class="gs-done" v-if="doneList.length"><span class="gs-done-label">✅ 已游览</span><span v-for="d in doneList" :key="d" class="gs-done-tag">{{ d }}</span></div>
      </div>

      <div v-if="replanPreview" class="replan-preview-card">
        <div class="replan-preview-head">
          <div>
            <span class="info-kicker">建议预览</span>
            <h3>{{ replanPreview.summary || '已生成新的后续路线建议' }}</h3>
          </div>
          <span class="preview-mode-tag">{{ replanModeLabel }}</span>
        </div>
        <div class="preview-columns">
          <div class="preview-column">
            <h4>建议后的后续顺序</h4>
            <ol>
              <li v-for="name in replanPreview.orderedRemainingNames || []" :key="`ordered-${name}`">{{ name }}</li>
            </ol>
          </div>
          <div class="preview-column">
            <h4>本次判断依据</h4>
            <ul>
              <li v-for="reason in replanPreview.reasons || []" :key="reason">{{ reason }}</li>
              <li v-if="!(replanPreview.reasons || []).length">已根据当前位置和剩余景点生成建议。</li>
            </ul>
          </div>
        </div>
        <div class="preview-footer">
          <span>剩余景点：{{ replanPreview.remainingCount ?? remainingAttractions.length }} 个</span>
          <span>{{ replanPreview.changed ? '这次建议会调整你的后续顺序。' : '这次建议与当前顺序接近，可直接保持。' }}</span>
        </div>
      </div>

      <div class="guide-prep">
        <span class="gp-icon">📡</span>
        <span v-if="!ttsReady">后台预加载中：{{ preloaded }}/{{ totalAttractions }} 个景区介绍已就绪</span>
        <span v-else class="gp-ready">🎙️ 全部 {{ totalAttractions }} 个景区语音已就绪</span>
      </div>

      <div class="guide-ai" v-if="activeTrip">
        <div class="guide-ai-bubble" v-if="guideSuggestion" @click="openGuideHuman">{{ guideSuggestion }}</div>
        <div class="guide-ai-btn" @click="openGuideHuman"><span>🤖</span></div>
      </div>

      <ScenicDigitalHuman
        v-if="showGuideHuman"
        :visible="showGuideHuman"
        mode="guide"
        title="旅行导览助手"
        :subtitle="activeTrip.city || '结合当前位置与行程回答问题'"
        welcome-text="你好，我是你的旅行导览助手。你可以直接问我现在到哪了、下一个景点是什么，或者这个景点有什么亮点。"
        :city="activeTrip.city || ''"
        :guide-payload="guideHumanPayload"
        @close="closeGuideHuman"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { applyGuideReplan, getHistory, getHistoryDetail, previewGuideReplan } from '@/services/api'
import { message } from 'ant-design-vue'
import ScenicDigitalHuman from '@/components/ScenicDigitalHuman.vue'

const trips = ref<any[]>([]); const activeTrip = ref<any>(null)
const gpsReady = ref(false); const gpsDenied = ref(false); const mapContainer = ref<HTMLElement>(); const userLoc = ref<{lat:number;lng:number}|null>(null)
const guideSuggestion = ref('')
const showGuideHuman = ref(false)
const replanLoading = ref(false)
const applyReplanLoading = ref(false)
const replanMode = ref('nearby-first')
const replanNote = ref('')
const replanPreview = ref<any>(null)
let mapInstance: any = null; let userMarker: any = null; let attrMarkers: any[] = []
const nearestAttraction = ref<any>(null); const doneList = ref<string[]>([])
const preloaded = ref(0); const totalAttractions = ref(0); const ttsReady = ref(false)
const attractionData = ref<Map<string,{intro:string;utterance:SpeechSynthesisUtterance|null}>>(new Map())
let gpsTimer: any = null; let syncTimer: any = null; let synth: SpeechSynthesis|null = null
let lastAlertDist: Record<string,number> = {}
const amapKey = import.meta.env.VITE_AMAP_WEB_JS_KEY || ''

const allAttractions = computed(() => {
  if (!activeTrip.value?.data?.days) return []
  const list: any[] = []
  for (const day of activeTrip.value.data.days) {
    for (const a of day.attractions||[]) {
      list.push({
        name:a.name,
        lat:a.location?.latitude||0,
        lng:a.location?.longitude||0,
        hasCoord:!!(a.location?.longitude&&a.location?.latitude)
      })
    }
  }
  return list
})

const remainingAttractions = computed(() => allAttractions.value.filter(a => !doneList.value.includes(a.name)).map(a => a.name))
const currentAttractionIntro = computed(() => {
  const name = nearestAttraction.value?.name
  if (!name) return ''
  return attractionData.value.get(name)?.intro || ''
})
const guideHumanPayload = computed(() => ({
  tripId: activeTrip.value?.id || '',
  city: activeTrip.value?.city || '',
  currentLocation: userLoc.value,
  nearestAttraction: nearestAttraction.value ? {
    name: nearestAttraction.value.name,
    distance: nearestAttraction.value.distance ?? null,
  } : null,
  doneAttractions: doneList.value,
  remainingAttractions: remainingAttractions.value,
  currentAttractionIntro: currentAttractionIntro.value,
}))
const replanModeLabel = computed(() => ({
  'nearby-first': '优先最近景点',
  'light-first': '后半程更轻松',
  compact: '压缩剩余行程',
}[replanMode.value] || '重规划建议'))
const replanSummaryTitle = computed(() => {
  if (replanMode.value === 'light-first') return '让后半程更轻松'
  if (replanMode.value === 'compact') return '压缩后续安排'
  return '优先最近景点'
})
const replanSuggestionText = computed(() => {
  if (replanPreview.value?.summary) return replanPreview.value.summary
  if (replanMode.value === 'light-first') return '适合你现在有点累、想把后面安排得更松弛一点的时候使用。'
  if (replanMode.value === 'compact') return '适合时间不够，只想保留后续更值得立刻去的少量景点。'
  return '根据你现在的位置，把更近、更顺路的景点排到后半程前面。'
})

async function initMap() {
  if(!mapContainer.value) return
  const AMap = (window as any).AMap
  if(!AMap){
    await new Promise<void>((resolve)=>{
      const script=document.createElement('script')
      script.src=`https://webapi.amap.com/maps?v=2.0&key=${amapKey}&callback=onAMapLoad`
      ;(window as any).onAMapLoad=()=>resolve()
      document.head.appendChild(script)
    })
  }
  const AM= (window as any).AMap
  mapInstance=new AM.Map(mapContainer.value,{zoom:14,center:[114.3,30.5],viewMode:'2D'})
  userMarker=new AM.Marker({position:[114.3,30.5],title:'我的位置',icon:new AM.Icon({size:new AM.Size(24,24),image:'https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png',imageSize:new AM.Size(24,24)})})
  mapInstance.add(userMarker)
  updateMap()
}

function updateMap(){
  if(!mapInstance) return
  const AM=(window as any).AMap

  if(userLoc.value){
    const pos=[userLoc.value.lng,userLoc.value.lat]
    mapInstance.setCenter(pos)
    userMarker?.setPosition(pos)
  }

  attrMarkers.forEach(m=>mapInstance.remove(m)); attrMarkers=[]
  for(const a of allAttractions.value){
    if(!a.hasCoord) continue
    const m=new AM.Marker({position:[a.lng,a.lat],title:a.name,offset:new AM.Pixel(-10,-10),
      icon:new AM.Icon({size:new AM.Size(20,20),image:'https://webapi.amap.com/theme/v1.3/markers/n/mark_r.png',imageSize:new AM.Size(20,20)})})
    m.on('click',()=>{if(!doneList.value.includes(a.name))playIntro(a.name)})
    attrMarkers.push(m); mapInstance.add(m)
  }
}

async function loadTrips() { try{const r=await getHistory();trips.value=(r.data||[]).filter((t:any)=>t.task_total>0&&t.progress<100).sort((a:any,b:any)=>b.created_at.localeCompare(a.created_at))}catch{} }

async function startGuide(trip: any) {
  try {
    const r=await getHistoryDetail(trip.id); activeTrip.value=r.data
    doneList.value=(r.data.tasks||[]).filter((t:any)=>t.done).map((t:any)=>t.name)
    totalAttractions.value=allAttractions.value.length; lastAlertDist={}; replanPreview.value=null; replanNote.value=''; replanMode.value='nearby-first'
    startGPS(); setTimeout(()=>startPreload(),100); setTimeout(()=>initMap(),200)
    setTimeout(()=>fetchGuideSuggestion(),500)
    syncTimer=setInterval(syncDoneList,30000)
  } catch { message.error('加载行程失败') }
}

async function startPreload() {
  if(!synth)synth=window.speechSynthesis
  for(const a of allAttractions.value){
    if(!a.hasCoord&&a.name){
      try{
        const gr=await fetch(`https://restapi.amap.com/v3/geocode/geo?key=${amapKey}&address=${encodeURIComponent(a.name)}&city=${encodeURIComponent(activeTrip.value.city||'')}&output=json`)
        const gd=await gr.json()
        if(gd.status==='1'&&gd.geocodes?.length){
          const loc=gd.geocodes[0].location.split(',')
          a.lat=parseFloat(loc[1]);a.lng=parseFloat(loc[0]);a.hasCoord=true
          updateMap()
        }
      }catch{}
    }
  }
  const pending=allAttractions.value.filter(a=>!doneList.value.includes(a.name))
  totalAttractions.value=pending.length
  for(const a of pending){
    try{
      const r=await fetch(`/api/plaza/attraction/${encodeURIComponent(a.name)}?city=${encodeURIComponent(activeTrip.value.city||'')}`)
      const d=await r.json()
      if(d.success){const clean=d.data.intro.replace(/[*#\[\]()`>_]/g,'').replace(/###.*\n/g,'').replace(/##.*\n/g,'').trim();const u=new SpeechSynthesisUtterance(clean);u.lang='zh-CN';u.rate=1.05;u.pitch=1.3;attractionData.value.set(a.name,{intro:d.data.intro,utterance:u});preloaded.value++;if(preloaded.value===totalAttractions.value)ttsReady.value=true}
    }catch{}
  }
  if(pending.length===0)ttsReady.value=true
}

async function requestGPSPermission() {
  gpsDenied.value = false
  if(!navigator.geolocation){gpsDenied.value=true;return}

  navigator.geolocation.getCurrentPosition(
    p=>{
      userLoc.value={lat:p.coords.latitude,lng:p.coords.longitude}
      gpsReady.value=true;gpsDenied.value=false
      checkProximity()
      startGPSTracking()
    },
    (err)=>{
      if(err.code===1){gpsDenied.value=true;gpsReady.value=false}
      else{gpsReady.value=false}
    },
    {enableHighAccuracy:true,timeout:10000}
  )
}

function startGPSTracking(){
  if(gpsTimer)clearInterval(gpsTimer)
  gpsTimer=setInterval(()=>{
    navigator.geolocation.getCurrentPosition(
      p=>{userLoc.value={lat:p.coords.latitude,lng:p.coords.longitude};gpsReady.value=true;checkProximity();updateMap()},
      ()=>{},
      {enableHighAccuracy:true,timeout:5000}
    )
  },5000)
}

async function startGPS() {
  try{
    const ipR=await fetch(`https://restapi.amap.com/v3/ip?key=${amapKey}`)
    const ipD=await ipR.json()
    if(ipD.status==='1'&&ipD.rectangle){
      const [lng,lat]=ipD.rectangle.split(';')[0].split(',')
      userLoc.value={lat:parseFloat(lat),lng:parseFloat(lng)}
      checkProximity(); updateMap()
    }
  }catch{}
}

function checkProximity() {
  if(!userLoc.value)return;let nearest:any=null,min=Infinity
  for(const a of allAttractions.value){if(doneList.value.includes(a.name)||!a.hasCoord)continue;const d=calcDist(userLoc.value.lat,userLoc.value.lng,a.lat,a.lng);if(d<min){min=d;nearest={name:a.name,distance:d}};if(d<500&&(!lastAlertDist[a.name]||d<lastAlertDist[a.name]-100)){lastAlertDist[a.name]=d;speakAlert(`您距离${a.name}还有${Math.round(d)}米`)};if(d<50&&!doneList.value.includes(a.name)){playIntro(a.name);doneList.value.push(a.name)}}
  if(!nearest&&allAttractions.value.length)nearest={name:allAttractions.value[0].name,distance:99999}
  nearestAttraction.value=nearest
}
function calcDist(lat1:number,lng1:number,lat2:number,lng2:number):number{const R=6371000;const dLat=(lat2-lat1)*Math.PI/180;const dLng=(lng2-lng1)*Math.PI/180;const a=Math.sin(dLat/2)*Math.sin(dLat/2)+Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLng/2)*Math.sin(dLng/2);return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a))}

function stopNarration(){if(!synth)synth=window.speechSynthesis;synth?.cancel()}
function speakAlert(text:string){if(showGuideHuman.value)return;if(!synth)synth=window.speechSynthesis;synth.cancel();const u=new SpeechSynthesisUtterance(text);u.lang='zh-CN';u.rate=1.1;u.pitch=1.4;synth.speak(u)}
async function playIntro(name:string){if(showGuideHuman.value)return;if(!synth)synth=window.speechSynthesis;synth.cancel();const alert=new SpeechSynthesisUtterance(`您已到达${name}，下面为您介绍`);alert.lang='zh-CN';alert.rate=1.1;alert.pitch=1.4;synth.speak(alert);let utter=attractionData.value.get(name)?.utterance;if(!utter){try{const r=await fetch(`/api/plaza/attraction/${encodeURIComponent(name)}?city=${encodeURIComponent(activeTrip.value.city||'')}`);const d=await r.json();if(d.success){const clean=d.data.intro.replace(/[*#\[\]()`>_]/g,'').replace(/###.*\n/g,'').replace(/##.*\n/g,'').trim();utter=new SpeechSynthesisUtterance(clean);utter.lang='zh-CN';utter.rate=1.05;utter.pitch=1.3;attractionData.value.set(name,{intro:d.data.intro,utterance:utter})}}catch{}}if(utter)synth.speak(utter);if(!doneList.value.includes(name)){doneList.value.push(name);try{const tr=await fetch(`/api/trip/history/${activeTrip.value.id}`,{headers:{'X-Username':localStorage.getItem('username')||''}});const td=await tr.json();if(td.success){const tasks=(td.data.tasks||[]).map((t:any)=>{if(t.name===name||(t.type==='attraction'&&t.name.includes(name)))return{...t,done:true};return t});await fetch(`/api/trip/history/${activeTrip.value.id}/tasks`,{method:'PUT',headers:{'Content-Type':'application/json','X-Username':localStorage.getItem('username')||''},body:JSON.stringify({tasks})})}}catch{}}}
async function syncDoneList(){
  if(!activeTrip.value) return
  try{
    const r=await fetch(`/api/trip/history/${activeTrip.value.id}`,{headers:{'X-Username':localStorage.getItem('username')||''}})
    const d=await r.json()
    if(d.success){doneList.value=(d.data.tasks||[]).filter((t:any)=>t.done).map((t:any)=>t.name)}
  }catch{}
}
async function fetchGuideSuggestion() {
  if (!activeTrip.value) return
  try {
    const r = await fetch('/api/trip/suggest', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ city: activeTrip.value.city, weather: '', temp: '', time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) })
    })
    const d = await r.json()
    if (d.success) guideSuggestion.value = d.suggestion
  } catch { guideSuggestion.value = '旅途愉快，注意安全～' }
}

async function previewReplan(){
  if(!activeTrip.value?.id) return
  replanLoading.value = true
  try {
    const res = await previewGuideReplan({
      tripId: activeTrip.value.id,
      mode: replanMode.value,
      note: replanNote.value.trim(),
      currentLocation: userLoc.value,
      doneAttractions: doneList.value,
    })
    if(res?.success){
      replanPreview.value = res.data
      message.success('已生成新的后续路线建议')
    } else {
      message.error(res?.message || '生成重规划建议失败')
    }
  } catch {
    message.error('生成重规划建议失败，请稍后再试')
  } finally {
    replanLoading.value = false
  }
}

async function applyReplanResult(){
  if(!activeTrip.value?.id || !replanPreview.value?.orderedRemainingNames?.length) return
  applyReplanLoading.value = true
  try {
    const res = await applyGuideReplan({
      tripId: activeTrip.value.id,
      orderedRemainingNames: replanPreview.value.orderedRemainingNames || [],
      doneNames: replanPreview.value.doneNames || doneList.value,
    })
    if(res?.success){
      activeTrip.value = res.data
      doneList.value = (res.data.tasks||[]).filter((t:any)=>t.done).map((t:any)=>t.name)
      replanPreview.value = null
      updateMap()
      checkProximity()
      message.success(res.message || '已应用新的后续路线')
    } else {
      message.error(res?.message || '应用重规划失败')
    }
  } catch {
    message.error('应用重规划失败，请稍后再试')
  } finally {
    applyReplanLoading.value = false
  }
}

function openGuideHuman(){
  stopNarration()
  showGuideHuman.value=false
  requestAnimationFrame(()=>{showGuideHuman.value=true})
}
function closeGuideHuman(){showGuideHuman.value=false}

function stopGuide(){if(gpsTimer)clearInterval(gpsTimer);if(syncTimer)clearInterval(syncTimer);stopNarration();if(mapInstance)mapInstance.destroy();mapInstance=null;userMarker=null;attrMarkers=[];activeTrip.value=null;userLoc.value=null;gpsReady.value=false;gpsDenied.value=false;guideSuggestion.value='';showGuideHuman.value=false;attractionData.value.clear();preloaded.value=0;ttsReady.value=false;replanPreview.value=null;replanNote.value='';replanMode.value='nearby-first'}

onMounted(async()=>{if(window.speechSynthesis)synth=window.speechSynthesis;await loadTrips()})
onUnmounted(()=>{if(gpsTimer)clearInterval(gpsTimer);if(syncTimer)clearInterval(syncTimer);if(synth)synth.cancel()})
</script>

<style scoped>
.guide-root{padding:24px 32px;max-width:900px;margin:0 auto;animation:viewIn .35s ease-out both}
@keyframes viewIn{from{opacity:0;transform:scale(.98) translateY(6px)}to{opacity:1;transform:scale(1) translateY(0)}}
.guide-select{display:flex;align-items:center;justify-content:center;min-height:60vh}
.guide-select-card{text-align:center;max-width:500px;width:100%}
.guide-seal{width:64px;height:64px;border-radius:12px;background:#c43b3b;color:#faf0d7;display:flex;align-items:center;justify-content:center;font-size:32px;font-weight:900;font-family:'STKaiti','楷体','KaiTi',serif;margin:0 auto 16px;animation:sealIn .5s cubic-bezier(.34,1.56,.64,1) both}
@keyframes sealIn{from{transform:scale(0) rotate(-15deg);opacity:0}to{transform:scale(1) rotate(0);opacity:1}}
.guide-select-card h2{font-size:24px;color:#5c3a21;margin:0 0 4px;font-family:'STKaiti','楷体','KaiTi',serif}
.guide-select-card p{font-size:14px;color:#b8a088;margin:0 0 24px}
.guide-trip-list{display:flex;flex-direction:column;gap:8px}
.guide-trip-item{display:flex;align-items:center;gap:12px;padding:16px 18px;background:#fff;border:1px solid #eadccf;border-radius:14px;cursor:pointer;transition:all .2s;text-align:left}
.guide-trip-item:hover{border-color:#c43b3b;box-shadow:0 3px 12px rgba(196,59,59,.08);transform:translateX(4px)}
.gti-icon{font-size:24px}.gti-info{flex:1}.gti-name{font-size:15px;font-weight:600;color:#5c3a21;display:block}.gti-meta{font-size:12px;color:#b8a088}.gti-arrow{font-size:18px;color:#d4c5b5}
.guide-empty{padding:40px;color:#b8a088}
.guide-active{display:flex;flex-direction:column;gap:16px}
.guide-topbar{display:flex;align-items:center;justify-content:space-between;padding:12px 18px;background:#fff;border:1px solid #eadccf;border-radius:12px}
.gt-left{display:flex;align-items:center;gap:8px;font-size:13px;color:#6b5344}
.gt-dot{width:10px;height:10px;border-radius:50%;background:#ccc}.gt-dot.on{background:#52c41a;animation:pulse 2s infinite}
.gps-banner{display:flex;align-items:center;gap:12px;padding:14px 18px;background:linear-gradient(135deg,#fff8f0,#fff5eb);border:2px solid #f0c080;border-radius:14px;margin-bottom:12px;animation:pulse 2s infinite}
.gps-banner-icon{font-size:28px;flex-shrink:0}
.gps-banner-text{flex:1;display:flex;flex-direction:column;gap:2px}
.gps-banner-text strong{font-size:14px;color:#8b4513}
.gps-banner-text span{font-size:12px;color:#b8a088}
.gps-banner-btn{padding:10px 20px;border:none;border-radius:20px;background:linear-gradient(135deg,#c43b3b,#a0522d);color:#fff;font-size:14px;font-weight:600;cursor:pointer;white-space:nowrap;transition:all .2s;box-shadow:0 3px 12px rgba(196,59,59,.25)}
.gps-banner-btn:hover{transform:scale(1.05);box-shadow:0 4px 16px rgba(196,59,59,.35)}
.guide-ai{position:fixed;bottom:24px;right:24px;display:flex;flex-direction:column;align-items:flex-end;gap:8px;z-index:200}
.guide-ai-bubble{background:#fff;border-radius:12px;padding:10px 16px;max-width:220px;box-shadow:0 4px 16px rgba(139,69,19,.1);font-size:13px;color:#6b5344;line-height:1.5;cursor:pointer;animation:floatIn .4s ease-out;border:1px solid #eadccf}
@keyframes floatIn{from{opacity:0;transform:translateY(8px) scale(.95)}to{opacity:1;transform:translateY(0) scale(1)}}
.guide-ai-btn{width:42px;height:42px;border-radius:50%;background:linear-gradient(135deg,#c43b3b,#a0522d);display:flex;align-items:center;justify-content:center;font-size:20px;cursor:pointer;box-shadow:0 3px 12px rgba(196,59,59,.3);transition:all .2s}
.guide-ai-btn:hover{transform:scale(1.1)}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.gt-center{font-size:15px;font-weight:600;color:#5c3a21;font-family:'STKaiti','楷体','KaiTi',serif}
.gt-close{padding:6px 16px;border:1px solid #c43b3b;border-radius:14px;background:#fff;color:#c43b3b;cursor:pointer;font-size:13px;transition:all .2s;font-family:'STKaiti','楷体','KaiTi',serif}
.gt-close:hover{background:#c43b3b;color:#fff}
.guide-map{border-radius:12px;overflow:hidden;border:1px solid #eadccf;height:240px;background:#faf7f2}
.guide-info-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.info-card{padding:16px 18px;background:#fff;border:1px solid #eadccf;border-radius:14px;display:flex;flex-direction:column;gap:10px}
.info-kicker{font-size:11px;color:#b8a088;display:block}
.info-card h3{margin:0;color:#5c3a21;font-size:18px;font-family:'STKaiti','楷体','KaiTi',serif}
.info-stat-row{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
.info-stat{background:#faf7f2;border-radius:12px;padding:10px 12px;display:flex;flex-direction:column;gap:4px}
.info-stat .label{font-size:11px;color:#b8a088}.info-stat strong{font-size:16px;color:#5c3a21}
.info-desc{margin:0;color:#6b5344;font-size:13px;line-height:1.7}
.next-meta-row{display:flex;gap:8px;flex-wrap:wrap}.next-badge{display:inline-flex;align-items:center;padding:5px 10px;border-radius:999px;background:#fff1ec;color:#c43b3b;font-size:12px}.next-badge.soft{background:#f5eee8;color:#8b6a52}.clamp-3{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.replan-card{gap:12px}.replan-field{display:flex;flex-direction:column;gap:6px;font-size:13px;color:#6b5344}.replan-select,.replan-textarea{border:1px solid #eadccf;border-radius:12px;padding:10px 12px;font-size:14px;color:#5c3a21;background:#fff}.replan-textarea{resize:vertical;min-height:84px}
.replan-actions{display:flex;gap:10px;flex-wrap:wrap}.replan-btn{border:none;border-radius:999px;padding:10px 16px;background:#f8eee4;color:#8b5e3c;cursor:pointer;transition:all .2s}.replan-btn.primary{background:linear-gradient(135deg,#c43b3b,#a0522d);color:#fff}.replan-btn:disabled{opacity:.55;cursor:not-allowed}
.guide-status{display:flex;gap:12px;flex-wrap:wrap}
.gs-card{flex:1;min-width:200px;padding:16px 18px;background:#fff;border:1px solid #eadccf;border-radius:14px}
.gs-label{font-size:11px;color:#b8a088;display:block}.gs-name{font-size:16px;font-weight:600;color:#5c3a21;display:block;margin:4px 0}
.gs-dist{font-size:20px;font-weight:800;color:#c43b3b}
.gs-bar{height:5px;background:#eadccf;border-radius:3px;margin-top:8px;overflow:hidden}.gs-bar div{height:100%;background:linear-gradient(90deg,#c43b3b,#52c41a);border-radius:3px;transition:width .5s}
.gs-done{width:100%;display:flex;align-items:center;gap:6px;flex-wrap:wrap}.gs-done-label{font-size:13px;color:#52c41a;font-weight:600}.gs-done-tag{font-size:12px;color:#b8a088;background:#f5f5f5;padding:2px 8px;border-radius:8px}
.gs-all-attrs{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}.gs-all-tag{font-size:13px;padding:4px 10px;background:#faf7f2;border:1px solid #eadccf;border-radius:10px;color:#6b5344}.gs-all-tag.done{color:#b8a088;background:#f5f5f5;text-decoration:line-through}
.replan-preview-card{padding:18px;background:#fff;border:1px solid #eadccf;border-radius:16px;display:flex;flex-direction:column;gap:14px}.replan-preview-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.replan-preview-head h3{margin:4px 0 0;color:#5c3a21;font-size:20px;font-family:'STKaiti','楷体','KaiTi',serif}.preview-mode-tag{font-size:12px;padding:6px 10px;border-radius:999px;background:#fff1ec;color:#c43b3b}.preview-columns{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.preview-column{background:#faf7f2;border-radius:14px;padding:14px}.preview-column h4{margin:0 0 10px;color:#5c3a21;font-size:15px}.preview-column ol,.preview-column ul{margin:0;padding-left:18px;color:#6b5344;line-height:1.8;font-size:13px}.preview-footer{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;font-size:12px;color:#b08d74}
.guide-prep{display:flex;align-items:center;gap:8px;padding:10px 16px;background:#fdf5ee;border:1px solid #e8d0bf;border-radius:10px;font-size:13px;color:#6b5344}.gp-icon{font-size:16px;animation:pulse 2s infinite}.gp-ready{margin-left:auto;color:#52c41a;font-weight:600}
@media(max-width:767px){.guide-root{padding:14px}.guide-map{height:180px}.gs-card{min-width:140px}.guide-info-grid{grid-template-columns:1fr}.info-stat-row,.preview-columns{grid-template-columns:1fr}}
</style>
