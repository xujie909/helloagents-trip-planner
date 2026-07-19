<template>
  <div class="chat-root">
    <!-- 侧边会话列表 -->
    <aside :class="['chat-sidebar', { open: sidebarOpen }]">
      <div class="sidebar-head">
        <img src="/meiling-avatar.png" class="sidebar-seal-img"/>
        <span class="sidebar-title">红美玲</span>
      </div>
      <button class="btn-new" @click="newConv">＋ 新对话</button>
      <div class="conv-list">
        <div v-for="c in convs" :key="c.id"
          :class="['conv-item', { active: currentId === c.id }]"
          @click="switchConv(c.id)">
          <span class="conv-title">{{ c.title }}</span>
          <span class="conv-meta">{{ c.msg_count }}条 · {{ c.updated_at?.slice(5,16) }}</span>
          <span class="conv-del" @click.stop="delConv(c.id)" title="删除">✕</span>
        </div>
        <div v-if="convs.length===0" class="conv-empty">暂无对话</div>
      </div>
    </aside>

    <!-- 遮罩 -->
    <div v-if="sidebarOpen" class="overlay" @click="sidebarOpen=false"></div>

    <!-- 主聊天区 -->
    <div class="chat-main">
      <header class="main-top">
        <span class="menu-btn" @click="sidebarOpen=!sidebarOpen">☰</span>
        <div class="top-info">
          <span class="top-title">{{ currentTitle }}</span>
        </div>
        <button v-if="geoPoints.length" class="map-toggle-btn" @click="showMap=!showMap" :class="{active:showMap}">
          🗺️ {{ showMap?'收起地图':'查看地图' }}
        </button>
      </header>

      <!-- 地图视图 -->
      <div v-if="showMap && geoPoints.length" class="map-view">
        <div class="map-container" ref="mapContainer"></div>
      </div>

      <div class="main-body" ref="bodyEl">
        <div v-if="!currentId" class="body-empty">
          <div class="empty-seal">山</div>
          <p>新建一段对话，开始探索旅途</p>
        </div>
        <div v-else-if="messages.length===0 && !loading" class="body-empty">
          <div class="empty-seal">山</div>
          <p>开始对话吧</p>
        </div>

        <TransitionGroup name="msg-anim" tag="div" class="msg-list">
          <div v-for="(m,i) in messages" :key="m._key||i" :class="['msg', m.role==='user'?'msg-r':'msg-l']">
            <div class="msg-avatar">
              <img v-if="m.role==='user'&&userAvatarImg" :src="userAvatarImg" class="msg-avatar-img"/>
              <img v-else-if="m.role==='bot'||m.role==='assistant'" src="/meiling-avatar.png" class="msg-avatar-img"/>
              <span v-else>{{ userAvatarEmoji }}</span>
            </div>
            <div :class="['msg-bubble', m.role==='user'?'bub-u':'bub-b', { welcome: m._welcome, streaming: m._streaming }]">
              <template v-if="m._loading">
                <span class="dot"></span><span class="dot"></span><span class="dot"></span>
                <span class="think-label">思考中</span>
              </template>
              <template v-else>
                <div v-if="m._welcome" class="welcome-wrap">
                  <div v-for="(line, li) in m.content.split('\n')" :key="li"
                    class="welcome-line" :style="{animationDelay: 0.3+li*0.08+'s'}">{{ line }}</div>
                </div>
                <img v-if="m._image" :src="m._image" class="msg-image" />
                <div v-if="m.content" class="msg-text" v-html="renderMd(m.content)"></div>
                <div class="msg-time">{{ m.time }}</div>
              </template>
            </div>
          </div>
        </TransitionGroup>
      </div>

      <div class="main-foot" v-if="currentId">
        <!-- 图片预览 -->
        <div v-if="uploadedImage" class="img-preview-row">
          <img :src="uploadedImage" class="img-preview" />
          <span class="img-preview-remove" @click="clearImage">✕</span>
        </div>
        <div class="foot-row">
          <button :class="['vbtn',{on:voiceEnabled}]" @click="toggleVoice">{{ voiceEnabled?'🔊':'🔇' }}</button>
          <button v-if="voiceEnabled" :class="['vbtn','mic',{active:isListening}]" @click="toggleMic" :disabled="loading"><span :class="{pulse:isListening}">🎤</span></button>
          <button class="vbtn img-btn" @click="triggerImageUpload" title="上传图片让红美玲看看">
            <span v-if="uploadingImage">⏳</span><span v-else>📷</span>
          </button>
          <input ref="imageInput" type="file" accept="image/jpeg,image/png,image/webp,image/gif" @change="handleImageSelect" style="display:none" />
          <input v-model="inputText" class="foot-inp" :placeholder="isListening?'聆听中...':'输入问题...'" :disabled="loading" @keydown.enter="send" />
          <button class="foot-send" :disabled="(!inputText.trim() && !uploadedImage) || loading" @click="send">发送</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { isLoggedIn } from '@/services/api'
import { useEdgeTTS } from '@/composables/useEdgeTTS'

const sidebarOpen = ref(false)
const bodyEl = ref<HTMLElement>(); const inputText = ref(''); const loading = ref(false)
const voiceEnabled = ref(false); const isListening = ref(false)
const convs = ref<any[]>([]); const currentId = ref('')
const userAvatarImg = ref(localStorage.getItem('user_avatar_img')||'')
const userAvatarEmoji = ref(localStorage.getItem('user_avatar')||'🎒')
const messages = ref<any[]>([])
const geoPoints = ref<any[]>([]); const showMap = ref(false); const mapContainer = ref<HTMLElement>()
const imageInput = ref<HTMLInputElement>(); const uploadedImage = ref(''); const uploadingImage = ref(false)
let recognition: any = null
const { speak: edgeSpeak, stop: edgeStop } = useEdgeTTS()

const username = computed(() => localStorage.getItem('username')||'')
const currentTitle = computed(() => {
  const c = convs.value.find(x => x.id === currentId.value)
  return c ? c.title : '红美玲 · 旅行管家'
})

function scrollDown() { nextTick(() => { const e=bodyEl.value; if(e) e.scrollTop=e.scrollHeight }) }

// ---- 语音 ----
function ensureMic() {
  const w=window as any; const SR=w.SpeechRecognition||w.webkitSpeechRecognition
  if(SR&&!recognition){ recognition=new SR(); recognition.lang='zh-CN'; recognition.interimResults=true
    recognition.onresult=(e:any)=>{ inputText.value=e.results[0][0].transcript.trim(); if(e.results[0].isFinal){ isListening.value=false; if(inputText.value)send() } }
    recognition.onerror=()=>{isListening.value=false};recognition.onend=()=>{isListening.value=false} }
}
function toggleVoice(){ voiceEnabled.value=!voiceEnabled.value; if(voiceEnabled.value) ensureMic(); else edgeStop() }
function toggleMic(){ ensureMic(); if(!recognition)return; isListening.value?recognition.stop():(()=>{try{recognition.start();isListening.value=true}catch{isListening.value=false}})() }
function speak(t:string){ if(!voiceEnabled.value)return; edgeStop(); const c=t.replace(/[\u{1F000}-\u{1FFFF}\u{2600}-\u{27BF}*#`\[\]()]/gu,'').trim(); if(!c)return; edgeSpeak(c) }

// ---- API helpers ----
const H = ():Record<string,string> => ({'Content-Type':'application/json','X-Username':username.value})

async function loadConvs() {
  try { const r=await fetch('/api/chat/conversations',{headers:H()}); const d=await r.json(); convs.value=(d.data||[]).filter((c:any)=>!c.id.startsWith('dh_')) } catch {}
}
async function loadConv(id:string) {
  try { const r=await fetch(`/api/chat/conversations/${id}`,{headers:H()}); const d=await r.json()
    if(d.success){
      let msgs = (d.data.messages||[]).filter((m:any)=>m.content!=='欢迎消息').map((m:any)=>({...m,_loading:false}))
      if (msgs.length===0) {
        msgs = [{role:'assistant',content:welcomeMsg(),time:'',_loading:false,_welcome:true,_key:'welcome'}]
      }
      messages.value = msgs
      scrollDown()
    }
  } catch {}
}
function welcomeMsg() {
  const hour=new Date().getHours()
  let greet='上午好'
  if(hour>=12&&hour<18) greet='下午好'
  else if(hour>=18||hour<6) greet='晚上好'
  return `🏮 **${greet}～我是红美玲，红魔馆的门番，现在回中国老家探亲，顺路当你的旅行管家啦！**

很高兴认识你呢～我可以帮你：

- 🗺️ **推荐目的地** — 告诉我你的喜好，帮你找到最棒的旅行地哦
- 📍 **景点介绍** — 接入高德地图，真实的景点信息加实时天气呢
- 🗓️ **行程规划** — 帮你安排每一天的路线，保证玩得尽兴～
- 🍜 **美食住宿** — 中国好吃的太多啦，我帮你挑最地道的！
- 🧭 **路线查询** — 两地多远、怎么走，门番我可是很熟路的～

你可以直接问我，比如：
- 「夏天带孩子去哪里玩呢？」
- 「北京三日游怎么安排呀？」
- 「杭州有什么必去的景点嘛？」

如果需要生成完整的旅行计划，记得去侧边栏的「**行程规划**」哦～`
}

async function newConv() {
  try { const r=await fetch('/api/chat/conversations',{method:'POST',headers:H()}); const d=await r.json()
    if(d.success){
      await loadConvs()
      currentId.value=d.data.id
      messages.value=[{role:'assistant',content:welcomeMsg(),time:now(),_loading:false,_welcome:true,_key:'welcome'}]
      sidebarOpen.value=false
    }
  } catch {}
}
async function switchConv(id:string) {
  currentId.value=id; messages.value=[]; geoPoints.value=[]; showMap.value=false; await loadConv(id); sidebarOpen.value=false
}
async function delConv(id:string) {
  if(!confirm('删除此对话？'))return
  try { await fetch(`/api/chat/conversations/${id}`,{method:'DELETE',headers:H()}); await loadConvs()
    if(currentId.value===id){ currentId.value=''; messages.value=[] } } catch {}
}

// ---- 图片上传 ----
function triggerImageUpload() { imageInput.value?.click() }
function handleImageSelect(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (file.size > 10 * 1024 * 1024) { alert('图片不能超过10MB'); return }
  const reader = new FileReader()
  reader.onload = () => { uploadedImage.value = reader.result as string }
  reader.readAsDataURL(file)
}
function clearImage() { uploadedImage.value = ''; if (imageInput.value) imageInput.value.value = '' }

async function send() {
  const t=inputText.value.trim(); const hasImage = !!uploadedImage.value
  if((!t && !hasImage) || loading.value || !currentId.value) return

  // 如果有图片，使用多模态视觉问答
  if (hasImage) {
    inputText.value = ''
    const imgSrc = uploadedImage.value
    messages.value.push({role:'user',content:`📷 ${t || '帮我看看这张图片～'}`,time:now(),_loading:false,_image:imgSrc}); scrollDown()
    clearImage()

    const streamIdx = messages.value.length
    messages.value.push({role:'assistant',content:'',time:'',_loading:true,_streaming:true,_thinking:true,_key:'v'+Date.now()}); scrollDown()
    loading.value = true

    try {
      // 使用 FormData 发送图片 + 文本到 vision 端点
      const formData = new FormData()
      // 将 base64 转为 blob
      const resp = await fetch(imgSrc)
      const blob = await resp.blob()
      formData.append('image', blob, 'photo.jpg')
      formData.append('message', t || '请详细介绍这张图片')

      const apiResp = await fetch('/api/chat/vision', {
        method: 'POST',
        headers: { 'X-Username': username.value },
        body: formData
      })
      const data = await apiResp.json()
      if (data.success) {
        messages.value[streamIdx].content = data.reply
        messages.value[streamIdx]._streaming = false
        messages.value[streamIdx]._loading = false
        messages.value[streamIdx]._thinking = false
        messages.value[streamIdx].time = now()
        speak(data.reply)
      } else {
        messages.value[streamIdx].content = '抱歉，图片分析失败了，请重试～'
        messages.value[streamIdx]._streaming = false
      }
    } catch(e) {
      messages.value[streamIdx].content = '抱歉，网络出问题了，请重试～'
      messages.value[streamIdx]._streaming = false
    }
    loading.value = false
    scrollDown()
    return
  }

  // 纯文本模式（原有逻辑）
  if(!t) return
  inputText.value=''
  messages.value.push({role:'user',content:t,time:now(),_loading:false}); scrollDown()

  const streamIdx=messages.value.length
  messages.value.push({role:'assistant',content:'',time:'',_loading:true,_streaming:true,_thinking:true,_key:'s'+Date.now()}); scrollDown()
  loading.value=true

  try {
    // 用 EventSource 实现可靠流式
    const params = new URLSearchParams({msg:t, u:username.value})
    const esUrl = `/api/chat/conversations/${currentId.value}/stream?${params}`
    const es = new EventSource(esUrl)

    let fullText=''
    es.onmessage = (e) => {
      try{
        const d=JSON.parse(e.data)
        if(d.t==='text'){ fullText+=d.c; messages.value[streamIdx].content=fullText; messages.value[streamIdx]._loading=false; messages.value[streamIdx]._thinking=false; scrollDown() }
        else if(d.t==='done'){
          messages.value[streamIdx]._streaming=false; messages.value[streamIdx].time=now()
          if(d.geo?.length){geoPoints.value=d.geo;renderMap()}
          speak(fullText)
          es.close()
          loading.value=false
          loadConvs()
        }
      }catch{}
    }
    es.onerror = () => {
      es.close()
      if(!fullText) messages.value[streamIdx].content='网络异常'
      messages.value[streamIdx]._streaming=false
      loading.value=false
    }
  } catch(e) { console.error(e) }
}
function renderMd(t: string): string {
  if (!t) return ''
  // 转义 HTML
  let h = t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
  // 粗体
  h = h.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
  // 斜体
  h = h.replace(/\*(.+?)\*/g,'<em>$1</em>')
  // 行内代码
  h = h.replace(/`(.+?)`/g,'<code>$1</code>')
  // 标题
  h = h.replace(/^### (.+)$/gm,'<h4>$1</h4>')
  h = h.replace(/^## (.+)$/gm,'<h3>$1</h3>')
  h = h.replace(/^# (.+)$/gm,'<h2>$1</h2>')
  // 无序列表
  h = h.replace(/^- (.+)$/gm,'<li>$1</li>')
  h = h.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
  // 有序列表
  h = h.replace(/^\d+\. (.+)$/gm,'<li>$1</li>')
  // 换行
  h = h.replace(/\n\n/g,'<br><br>')
  h = h.replace(/\n/g,'<br>')
  return h
}

async function renderMap() {
  await nextTick()
  if (!mapContainer.value || !geoPoints.value.length) return
  // 用高德静态图展示位置
  const pts = geoPoints.value
  const center = pts[0]
  const markers = pts.map(p => `${p.lng},${p.lat}`).join('|')
  const names = pts.map(p => p.name).join('|')
  const amapKey = import.meta.env.VITE_AMAP_WEB_KEY || ''
  const imgUrl = `https://restapi.amap.com/v3/staticmap?key=${amapKey}&size=800*300&markers=mid,,A:${markers}&labels=${names}&zoom=12&center=${center.lng},${center.lat}&scale=2`
  mapContainer.value.innerHTML = `<div style="position:relative;border-radius:12px;overflow:hidden">
    <img src="${imgUrl}" style="width:100%;height:280px;object-fit:cover" />
    <div style="position:absolute;bottom:0;left:0;right:0;background:linear-gradient(transparent,rgba(0,0,0,.6));padding:16px;color:#fff">
      ${pts.map(p => `<span style="margin-right:12px;font-size:13px">📍${p.name}</span>`).join('')}
    </div>
  </div>`
}

function now(){ const n=new Date(); return `${String(n.getHours()).padStart(2,'0')}:${String(n.getMinutes()).padStart(2,'0')}` }

onMounted(async ()=>{
  if(!isLoggedIn())return
  await loadConvs()
  if(convs.value.length===0){
    await newConv()
  }
})
</script>

<style scoped>
.chat-root { display:flex; height:100%; background:#faf7f2; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'STKaiti','楷体',sans-serif; animation: viewIn .35s ease-out both }
@keyframes viewIn { from{opacity:0;transform:scale(.98) translateY(6px)} to{opacity:1;transform:scale(1) translateY(0)} }

/* ---- 侧边栏 ---- */
.chat-sidebar { width:240px; background:#fff; border-right:1px solid #eadccf; display:flex;flex-direction:column;flex-shrink:0;transition:transform .25s;z-index:50 }
.sidebar-head { display:flex;align-items:center;gap:10px;padding:18px 16px;border-bottom:1px solid #eadccf }
.sidebar-seal { width:32px;height:32px;border-radius:5px;background:#c43b3b;color:#faf0d7;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:900;font-family:'STKaiti','楷体','KaiTi',serif }
.sidebar-seal-img { width:38px;height:38px;border-radius:6px;object-fit:cover;box-shadow:0 2px 8px rgba(196,59,59,.15) }
.sidebar-title { font-size:15px;font-weight:700;color:#5c3a21;font-family:'STKaiti','楷体','KaiTi',serif }
.btn-new { margin:12px;padding:10px;border:1px dashed #c43b3b;border-radius:10px;background:#fdf5ee;color:#c43b3b;font-size:14px;cursor:pointer;transition:all .2s;font-family:'STKaiti','楷体','KaiTi',serif }
.btn-new:hover { background:#fef0e6 }
.conv-list { flex:1;overflow-y:auto;padding:0 8px }
.conv-item { display:flex;flex-direction:column;padding:12px 14px;border-radius:10px;cursor:pointer;margin-bottom:2px;position:relative;transition:background .15s }
.conv-item:hover { background:#faf7f2 }
.conv-item.active { background:#fdf0e8;border:1px solid #f0d5c0 }
.conv-title { font-size:14px;color:#5c3a21;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis }
.conv-meta { font-size:11px;color:#b8a088;margin-top:3px }
.conv-del { position:absolute;right:12px;top:50%;transform:translateY(-50%);font-size:14px;color:#ccc;opacity:0;transition:opacity .15s }
.conv-item:hover .conv-del { opacity:1 }
.conv-del:hover { color:#c43b3b }
.conv-empty { text-align:center;color:#b8a088;font-size:13px;padding:30px 0 }
.overlay { display:none;position:fixed;inset:0;background:rgba(0,0,0,.3);z-index:40 }

/* ---- 主区 ---- */
.chat-main { flex:1;display:flex;flex-direction:column;min-width:0 }
.main-top { display:flex;align-items:center;padding:12px 18px;background:#fff;border-bottom:1px solid #eadccf;gap:12px;flex-shrink:0 }
.menu-btn { display:none;font-size:20px;cursor:pointer;color:#5c3a21 }
.top-title { font-size:15px;font-weight:600;color:#5c3a21;font-family:'STKaiti','楷体','KaiTi',serif }
.top-time { margin-left:auto;font-size:12px;color:#b8a088 }

.main-body { flex:1;overflow-y:auto;padding:18px }
.body-empty { flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#b8a088 }
.empty-seal { width:56px;height:56px;border-radius:10px;background:#c43b3b;color:#faf0d7;display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:900;font-family:'STKaiti','楷体','KaiTi',serif;margin-bottom:12px;animation:sealIn .5s cubic-bezier(.34,1.56,.64,1) both }
@keyframes sealIn { from{transform:scale(0)rotate(-15deg);opacity:0} to{transform:scale(1)rotate(0);opacity:1} }
.body-empty p { animation:fadeSlide .5s ease-out .2s both }
@keyframes fadeSlide { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }

/* ---- 地图 ---- */
.map-view { flex-shrink:0;border-bottom:1px solid #eadccf;background:#faf7f2;padding:12px 18px }
.map-container { border-radius:12px;overflow:hidden }
.map-toggle-btn { padding:6px 14px;border:1px solid #eadccf;border-radius:14px;background:#fff;color:#5c3a21;font-size:13px;cursor:pointer;transition:all .2s;font-family:'STKaiti','楷体','KaiTi',serif }
.map-toggle-btn:hover { border-color:#c43b3b;color:#c43b3b;background:#fdf5ee }
.map-toggle-btn.active { background:#fdf0e8;border-color:#c43b3b;color:#c43b3b }

/* 消息列表 TransitionGroup */
.msg-list { display:flex;flex-direction:column;gap:14px }
.msg-anim-enter-active { transition:all .4s cubic-bezier(.34,1.56,.64,1) }
.msg-anim-leave-active { transition:all .2s ease-in }
.msg-anim-enter-from { opacity:0;transform:translateY(16px) scale(.96) }
.msg-anim-leave-to { opacity:0;transform:translateX(-20px) }

/* 欢迎消息 */
.msg-bubble.welcome { padding:20px 24px;max-width:100%!important }
.welcome-wrap { display:flex;flex-direction:column;gap:4px }
.welcome-line {
  opacity:0;animation:welcomeIn .5s ease-out both;
  font-size:15px;line-height:1.8;color:#5c3a21;
}
.welcome-line:first-child { font-size:18px;font-weight:700 }
@keyframes welcomeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }

/* ---- 消息 ---- */
.msg { display:flex;gap:10px;max-width:78% }
.msg-l { align-self:flex-start }.msg-r { align-self:flex-end;flex-direction:row-reverse }
.msg-avatar { width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0;overflow:hidden }
.msg-avatar-img { width:100%;height:100%;object-fit:cover;display:block }
.msg-l .msg-avatar { background:#c43b3b;border:2px solid #8b0000;padding:1px }
.msg-avatar-star { color:#ffd700;font-size:22px;font-weight:700;display:flex;align-items:center;justify-content:center;width:100%;height:100% }
.msg-r .msg-avatar { background:#f0f0f0;border:2px solid #ddd;padding:1px }
.msg-bubble { padding:12px 16px;border-radius:14px;line-height:1.6;font-size:15px }
.bub-b { background:#fff;color:#5c3a21;border:1px solid #eadccf;border-bottom-left-radius:4px;box-shadow:0 1px 3px rgba(139,69,19,0.04) }
.bub-u { background:linear-gradient(135deg,#c43b3b,#a0522d);color:#fff;border-bottom-right-radius:4px }
.msg-text { white-space:pre-wrap;word-break:break-word }
.msg-image { max-width:240px;max-height:240px;border-radius:10px;margin-bottom:8px;display:block;object-fit:cover }
.msg-text :deep(strong) { font-weight:700;color:inherit }
.msg-text :deep(em) { font-style:italic }
.msg-text :deep(h2),.msg-text :deep(h3),.msg-text :deep(h4) { margin:8px 0 4px;font-weight:700;line-height:1.4 }
.msg-text :deep(h2) { font-size:18px }.msg-text :deep(h3) { font-size:16px }.msg-text :deep(h4) { font-size:14px }
.msg-text :deep(ul),.msg-text :deep(ol) { margin:4px 0;padding-left:18px }
.msg-text :deep(li) { margin:2px 0;line-height:1.6 }
.msg-text :deep(code) { background:rgba(0,0,0,.06);padding:2px 6px;border-radius:4px;font-size:13px }
/* 流式输出光标 */
.msg-bubble:has(.msg-text:empty)::after,.msg-bubble.streaming::after { content:'|';animation:blink 1s infinite;color:#c43b3b;font-weight:700 }
@keyframes blink { 0%,50%{opacity:1} 51%,100%{opacity:0} }
.msg-time { font-size:10px;color:#b8a088;margin-top:4px;text-align:right }
.bub-u .msg-time { color:rgba(255,255,255,.6) }

/* 思考气泡 */
.bub-b:has(.dot) { display:flex;align-items:center;gap:5px;padding:14px 18px;min-height:40px }
.dot { width:7px;height:7px;border-radius:50%;background:#d4a89a;animation:tb 1.4s infinite ease-in-out both }
.dot:nth-child(2){animation-delay:.16s}.dot:nth-child(3){animation-delay:.32s}
.think-label { margin-left:8px;font-size:13px;color:#b8a088 }
@keyframes tb { 0%,80%,100%{opacity:.3;transform:scale(.8)} 40%{opacity:1;transform:scale(1)} }

/* ---- 输入 ---- */
.main-foot { padding:12px 18px;background:#fff;border-top:1px solid #eadccf;flex-shrink:0 }
.foot-row { display:flex;gap:8px;align-items:center }
.vbtn { width:36px;height:36px;border:1px solid #eadccf;border-radius:50%;background:#fff;font-size:15px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:all .2s }
.vbtn:hover { border-color:#c43b3b }
.vbtn.on { background:#fdf0e8;border-color:#c43b3b }
.vbtn.mic.active { background:#fff0f0;border-color:#d46060 }
.pulse { animation:mp .6s infinite ease-in-out;display:inline-block }
@keyframes mp { 0%,100%{transform:scale(1)} 50%{transform:scale(1.25)} }
.foot-inp { flex:1;padding:10px 16px;border:2px solid #eadccf;border-radius:20px;font-size:15px;outline:none;background:#faf7f2;transition:border-color .2s;min-width:0 }
.img-btn { font-size:18px }
.img-btn:hover { background:#fdf0e8;border-color:#c43b3b }
.img-preview-row { display:flex;align-items:center;gap:8px;padding:8px 0 }
.img-preview { width:80px;height:80px;border-radius:10px;object-fit:cover;border:2px solid #eadccf }
.img-preview-remove { width:24px;height:24px;border-radius:50%;background:#ff4d4f;color:#fff;display:flex;align-items:center;justify-content:center;font-size:12px;cursor:pointer }
.foot-inp:focus { border-color:#c43b3b;background:#fff }
.foot-inp:disabled { opacity:.6 }
.foot-send { padding:10px 22px;border:none;border-radius:20px;background:linear-gradient(135deg,#c43b3b,#a0522d);color:#fff;font-size:15px;font-weight:600;cursor:pointer;flex-shrink:0;transition:all .2s;font-family:'STKaiti','楷体','KaiTi',serif }
.foot-send:hover:not(:disabled) { transform:translateY(-1px);box-shadow:0 3px 12px rgba(196,59,59,0.3) }
.foot-send:disabled { opacity:.4;cursor:not-allowed }

/* 移动端 */
@media (max-width:767px) {
  .chat-sidebar { position:fixed;top:0;left:0;bottom:0;z-index:50;transform:translateX(-100%);box-shadow:4px 0 20px rgba(0,0,0,.15) }
  .chat-sidebar.open { transform:translateX(0) }
  .overlay { display:block }
  .menu-btn { display:block }
  .msg { max-width:88% }
}
</style>
