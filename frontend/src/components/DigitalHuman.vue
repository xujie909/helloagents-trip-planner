<template>
  <!-- 浮窗（可拖动） -->
  <div class="dh-float" v-if="!expanded"
    :style="{ left: floatX+'px', top: floatY+'px' }"
    @mousedown="startDrag" @touchstart="startDrag"
    @click="onFloatClick">
    <span class="dh-float-icon">🤖</span>
    <div class="dh-float-ring"></div>
  </div>

  <!-- 淡色遮罩数字人 -->
  <Transition name="dh-fade">
    <div v-if="expanded" class="dh-overlay" @click.self="close">
      <button class="dh-x" @click="close">✕</button>

      <!-- 立绘 -->
      <div class="dh-body">
        <img :src="currentImage" class="dh-img"/>
        <div class="dh-tag">
          <span class="dh-tag-name">红美玲</span>
          <span class="dh-tag-sub">红魔馆门番 · 旅行管家</span>
        </div>
      </div>

      <!-- 聊天记录气泡区 -->
      <div class="dh-history" ref="historyEl">
        <div v-for="(m,i) in chatHistory" :key="i" :class="['dh-bubble', m.role]">
          <span>{{ m.content }}</span>
        </div>
      </div>

      <!-- 当前大对话框 / 流式输出 -->
      <div class="dh-comic-bubble" v-if="currentSegment || streaming || streamStatus">
        <div class="dh-comic-status" v-if="streamStatus && !streaming">{{ streamStatus }}</div>
        <div class="dh-comic-text">{{ currentSegment || streamText }}<i v-if="streaming">|</i></div>
        <div class="dh-comic-hint" v-if="!streaming && currentSegment" @click="nextSegment">点击继续 ▸</div>
      </div>

      <!-- 输入区 -->
      <div class="dh-input-bar">
        <button :class="['dh-mic',{on:listening}]" @click="toggleMic">🎤</button>
        <input v-model="text" class="dh-inp" placeholder="和红美玲聊天～" @keydown.enter="send"/>
        <button class="dh-send" @click="send" :disabled="!text.trim()||streaming">发送</button>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { getAuthUsername, getDisplayName, isLoggedIn, getMe, hydrateAuthUser, getAuthHeaders } from '@/services/api'

const props = defineProps<{ currentPage?: string }>()

const expanded = ref(false); const text = ref(''); const streaming = ref(false)
const streamStatus = ref('')

// ---- 拖动浮窗 ----
const defaultFloatX = typeof window !== 'undefined' ? window.innerWidth - 92 : 24
const defaultFloatY = typeof window !== 'undefined' ? window.innerHeight - 180 : 120
const floatX = ref(defaultFloatX)
const floatY = ref(defaultFloatY)
let dragging = false, dragStartX = 0, dragStartY = 0, origX = 0, origY = 0
let dragMoved = false

function clampFloatPosition() {
  if (typeof window === 'undefined') return
  const maxX = Math.max(12, window.innerWidth - 64)
  const maxY = Math.max(12, window.innerHeight - 64)
  floatX.value = Math.max(12, Math.min(maxX, floatX.value))
  floatY.value = Math.max(12, Math.min(maxY, floatY.value))
}

function resetFloatPosition() {
  if (typeof window === 'undefined') return
  floatX.value = window.innerWidth - 92
  floatY.value = window.innerHeight - 180
  clampFloatPosition()
}

function startDrag(e: MouseEvent | TouchEvent) {
  dragging = true; dragMoved = false
  const p = 'touches' in e ? e.touches[0] : e
  dragStartX = p.clientX; dragStartY = p.clientY
  origX = floatX.value; origY = floatY.value
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.addEventListener('touchmove', onDrag, { passive: false })
  document.addEventListener('touchend', stopDrag)
}
function onDrag(e: MouseEvent | TouchEvent) {
  if (!dragging) return
  e.preventDefault()
  const p = 'touches' in e ? e.touches[0] : e
  const dx = p.clientX - dragStartX, dy = p.clientY - dragStartY
  if (Math.abs(dx) > 3 || Math.abs(dy) > 3) dragMoved = true
  floatX.value = origX + dx
  floatY.value = origY + dy
  clampFloatPosition()
}
function stopDrag() {
  dragging = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
  // 长距离拖动不触发点击
  if (dragMoved) {
    setTimeout(() => { dragMoved = false }, 200)
  }
}
// 点击事件手动处理，区分拖拽
function onFloatClick() {
  if (dragMoved) return
  open()
}

function handleResize() {
  clampFloatPosition()
}

// 初始定位
onMounted(() => {
  resetFloatPosition()
  window.addEventListener('resize', handleResize)
})
onBeforeUnmount(() => {
  closeStream()
  if (synth) synth.cancel()
  if (recognition && listening.value) recognition.stop()
  window.removeEventListener('resize', handleResize)
})
const streamText = ref(''); const listening = ref(false)
const chatHistory = ref<{role:string;content:string}[]>([])
const currentSegment = ref('')
const currentImage = ref('/digital-human/自信.PNG')
const historyEl = ref<HTMLElement>()
let recognition: any = null; let synth: SpeechSynthesis|null = null; let convId = ''
let currentEventSource: EventSource | null = null
let currentStreamController: AbortController | null = null
let fallbackConvId = ''
let pendingSegments: string[] = []; let segIdx = 0
let pendingReplyFull = ''
let lastStreamError = ''

function resolveUsername(){
  return getAuthUsername()
}

function resolveDisplayName(){
  return getDisplayName() || '旅行者'
}

async function ensureAuthUsername(){
  const cached = resolveUsername()
  if (cached) return cached
  if (!isLoggedIn()) return ''
  try {
    const res = await getMe()
    if (res.user) {
      hydrateAuthUser({
        username: res.user.username,
        name: res.user.name,
        last_login: res.user.last_login,
        login_count: res.user.login_count,
      })
      return resolveUsername()
    }
  } catch {}
  return ''
}

function setStatus(message = ''){
  streamStatus.value = message
}

function closeStream(){
  if(currentEventSource){
    currentEventSource.close()
    currentEventSource = null
  }
  if (currentStreamController) {
    currentStreamController.abort()
    currentStreamController = null
  }
}

function describeStageError(stage: string, detail = ''){
  const hint = detail ? `（${detail}）` : ''
  switch (stage) {
    case 'stream_connect': return `流式连接失败${hint}`
    case 'stream_empty_body': return `流式连接成功，但没有可读内容${hint}`
    case 'stream_parse': return `流式数据解析失败${hint}`
    case 'stream_empty_reply': return `流式连接结束，但没有收到有效回复${hint}`
    case 'fallback_create': return `直连回退创建会话失败${hint}`
    case 'fallback_send': return `直连回退发送消息失败${hint}`
    case 'fallback_empty_reply': return `直连回退成功，但回复内容为空${hint}`
    default: return detail || stage || '未知错误'
  }
}

function parseStageError(error: unknown){
  const raw = error instanceof Error ? error.message : String(error || '')
  const message = raw || 'unknown_error'
  if (message.startsWith('stream_failed_')) {
    const status = message.replace('stream_failed_', '')
    return { stage: 'stream_connect', detail: `HTTP ${status}` }
  }
  if (message.startsWith('stream_empty_body_')) {
    const status = message.replace('stream_empty_body_', '')
    return { stage: 'stream_empty_body', detail: `HTTP ${status}` }
  }
  if (message.startsWith('stream_parse_')) {
    return { stage: 'stream_parse', detail: message.replace('stream_parse_', '') }
  }
  if (message.startsWith('fallback_create_')) {
    const status = message.replace('fallback_create_', '')
    return { stage: 'fallback_create', detail: `HTTP ${status}` }
  }
  if (message.startsWith('fallback_send_')) {
    const status = message.replace('fallback_send_', '')
    return { stage: 'fallback_send', detail: `HTTP ${status}` }
  }
  if (message === 'fallback_missing_id') {
    return { stage: 'fallback_create', detail: '服务端没有返回会话 id' }
  }
  if (message === 'fallback_empty_reply') {
    return { stage: 'fallback_empty_reply', detail: '' }
  }
  return { stage: 'unknown', detail: message }
}

async function runFallbackChat(message: string, uname: string, page: string){
  const headers = {
    ...getAuthHeaders(),
    'Content-Type': 'application/json',
  }

  if (!fallbackConvId) {
    fallbackConvId = convId || `dh_${uname || 'guest'}`
    const createRes = await fetch('/api/chat/conversations', {
      method: 'POST',
      headers,
      body: JSON.stringify({ conv_id: fallbackConvId }),
    })
    if (!createRes.ok) throw new Error(`fallback_create_${createRes.status}`)
    const createData = await createRes.json()
    fallbackConvId = createData?.data?.id || fallbackConvId
    if (!fallbackConvId) throw new Error('fallback_missing_id')
  }

  const history = chatHistory.value
    .filter(m => m.content && m.content !== '欢迎消息')
    .slice(-8)
    .map(m => ({
      role: m.role === 'bot' ? 'assistant' : 'user',
      content: m.content,
    }))

  const sendRes = await fetch(`/api/chat/conversations/${fallbackConvId}/send`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      message,
      history,
      page,
    }),
  })
  if (!sendRes.ok) throw new Error(`fallback_send_${sendRes.status}`)
  const sendData = await sendRes.json()
  const reply = (sendData?.reply || '').trim()
  if (!reply) throw new Error('fallback_empty_reply')
  return reply
}

// 情绪映射：文本分析（灵敏度增强版 — 加权匹配+启发式兜底）
const emotionKeywords: [string[],string,number][] = [
  [['！','太','非常','超级','绝了','美','好吃','棒','赞','厉害','牛','完美','爽','爱了','喜欢','哈哈','嘿嘿','哇塞','好极了','太棒了','真不错','好评','绝美','过瘾','刺激'],'兴奋',2],
  [['？','怎么','什么','哪','吗','呢','为啥','为什么','不懂','不明白','奇怪','难道','真的吗','确定吗','不会吧','啥','什么意思','搞不懂','咋回事'],'疑惑',2],
  [['推荐','建议','可以','应该','值得','当然','肯定','一定','相信我','没错','绝对','必须','保证','放心','没问题','包你','准没错','靠谱','地道'],'自信',2],
  [['抱歉','对不起','遗憾','可惜','失望','难过','伤心','呜呜','唉','叹气','不好意思','没办法','可惜了','错失','错过'],'委屈',2],
  [['哇','咦','诶','啊','天哪','不是吧','居然','竟然','震惊','吓','不可思议','没想到','真没想到','我的天','乖乖','不得了'],'惊讶',2],
  [['害羞','不好意思','讨厌','别夸','脸红','羞涩','羞羞','别笑话','过奖','谬赞'],'害羞',3],
  [['首先','其次','总结','注意','重要','关键','请','提醒','记住','小心','务必','切记','谨记','须知','提示'],'认真',3],
  [['谢谢','感谢','多谢','辛苦','麻烦','拜托','求求','感恩','比心','笔芯'],'开心',1],
]
function imageFor(e:string){
  const map:Record<string,string>={
    '兴奋':'开心6（兴奋）.PNG','开心':'开心2.PNG','疑惑':'疑惑.PNG',
    '自信':'自信.PNG','委屈':'委屈.PNG','惊讶':'惊讶.PNG',
    '害羞':'开心1（自信）.PNG','认真':'开心5.PNG','思考':'思考1.PNG'
  }
  return '/digital-human/'+(map[e]||'自信.PNG')
}
function guessEmotion(txt:string):string{
  // 短文本启发式：单个！结尾 → 兴奋，单个？结尾 → 疑惑
  if(txt.length<=4){
    if(txt.endsWith('！')||txt.endsWith('!')) return '兴奋'
    if(txt.endsWith('？')||txt.endsWith('?')) return '疑惑'
  }
  // 加权匹配：统计每种情绪的命中权重，取最高分
  const scores:Record<string,number>={}
  for(const [kws,e,w] of emotionKeywords){
    for(const kw of kws){
      if(txt.includes(kw)){ scores[e]=(scores[e]||0)+w }
    }
  }
  let best='',max=0
  for(const [e,s] of Object.entries(scores)){
    if(s>max){ max=s; best=e }
  }
  if(best) return best
  // 兜底启发式：多个感叹号→兴奋，多个问号→疑惑，长文本→认真
  const exclam=(txt.match(/[！!]/g)||[]).length
  const quest=(txt.match(/[？?]/g)||[]).length
  if(exclam>=2) return '兴奋'
  if(quest>=2) return '疑惑'
  if(txt.length>80) return '认真'
  return '开心'
}
function setEmotion(seg:string){ currentImage.value=imageFor(guessEmotion(seg)) }
function scrollHistory(){ nextTick(()=>{ const el=historyEl.value; if(el) el.scrollTop=el.scrollHeight }) }

// 拆分文本为小段
function splitSegments(text:string):string[]{
  // 按句号、感叹号、问号、换行拆分，每段不超过40字
  const raw = text.split(/(?<=[。！？\n])/g).filter(s=>s.trim())
  const segs: string[] = []
  for(const s of raw){
    if(s.length<=40){ segs.push(s.trim()); continue }
    // 按逗号再拆
    const sub = s.split(/[,，]/g).filter(x=>x.trim())
    let buf = ''
    for(const ss of sub){
      if(buf.length+ss.length>40 && buf){ segs.push(buf.trim()); buf=ss }
      else buf+=ss
    }
    if(buf.trim()) segs.push(buf.trim())
  }
  return segs.filter(s=>s.length>0)
}

function playSegment(idx:number){
  if(idx>=pendingSegments.length){
    if (pendingReplyFull.trim()) {
      chatHistory.value.push({ role:'bot', content: pendingReplyFull.trim() })
    }
    currentSegment.value=''
    pendingSegments=[]
    pendingReplyFull=''
    setStatus('这次回答完啦，还可以继续问我～')
    return
  }
  segIdx=idx
  const seg=pendingSegments[idx]
  currentSegment.value=seg; setEmotion(seg); scrollHistory()

  if(!synth){
    if(idx+1 < pendingSegments.length) playSegment(idx+1)
    else {
      if (pendingReplyFull.trim()) {
        chatHistory.value.push({ role:'bot', content: pendingReplyFull.trim() })
      }
      currentSegment.value=''
      pendingSegments=[]
      pendingReplyFull=''
      setStatus('这次回答完啦，还可以继续问我～')
    }
    return
  }

  synth.cancel()
  const u=new SpeechSynthesisUtterance(seg); u.lang='zh-CN'; u.rate=1.0; u.pitch=1.2
  u.onend=()=>{
    if(idx+1 < pendingSegments.length) playSegment(idx+1)
    else {
      if (pendingReplyFull.trim()) {
        chatHistory.value.push({ role:'bot', content: pendingReplyFull.trim() })
      }
      currentSegment.value=''
      pendingSegments=[]
      pendingReplyFull=''
      setStatus('这次回答完啦，还可以继续问我～')
    }
  }
  synth.speak(u)
}
function nextSegment(){
  if(!pendingSegments.length) return
  if(synth) synth.cancel()
  if(segIdx+1 < pendingSegments.length) playSegment(segIdx+1)
  else {
    if (pendingReplyFull.trim()) {
      chatHistory.value.push({ role:'bot', content: pendingReplyFull.trim() })
    }
    currentSegment.value=''
    pendingSegments=[]
    pendingReplyFull=''
    setStatus('这次回答完啦，还可以继续问我～')
  }
}

// 页面名称映射
const pageNames:Record<string,string> = {
  home:'首页', profile:'个人档案', chat:'旅行顾问', plan:'行程规划',
  history:'行囊记录', guide:'旅行导览', plaza:'数据广场', manual:'使用手记', video:'旅行视频'
}
function currentPageName(){ return pageNames[props.currentPage||'']||'首页' }

// ---- 生命周期 ----
async function open(){
  initSpeech()
  expanded.value=true
  setStatus('')
  lastStreamError = ''
  const name=resolveDisplayName()
  const pn = currentPageName()
  if(!chatHistory.value.length){
    chatHistory.value.push({role:'bot',content:`你好呀 ${name}！我是红美玲，知行旅行的智能引导员哦～你现在在「${pn}」页面，有什么不懂的可以问我呢！我可以帮你快速了解每个功能怎么用～`})
  }
  const uname = await ensureAuthUsername()
  convId='dh_'+(uname||'guest')
  if (isLoggedIn() && !uname) {
    setStatus('登录信息还没恢复完整，先刷新了身份，发问试试～')
  }
  scrollHistory()
}
function close(){
  expanded.value=false
  streaming.value=false
  streamText.value=''
  currentSegment.value=''
  pendingSegments=[]
  pendingReplyFull=''
  setStatus('')
  closeStream()
  if(synth) synth.cancel()
  if(recognition && listening.value){
    recognition.stop()
  }
  listening.value=false
}

// 语音
function initSpeech(){
  const w=window as any; const SR=w.SpeechRecognition||w.webkitSpeechRecognition
  if(SR&&!recognition){ recognition=new SR(); recognition.lang='zh-CN'; recognition.interimResults=true
    recognition.onresult=(e:any)=>{text.value=e.results[0][0].transcript.trim();if(e.results[0].isFinal){listening.value=false;send()}}
    recognition.onerror=()=>{listening.value=false};recognition.onend=()=>{listening.value=false} }
  if(w.speechSynthesis&&!synth) synth=w.speechSynthesis
}
function toggleMic(){ initSpeech(); if(!recognition)return; listening.value?recognition.stop():(()=>{try{recognition.start();listening.value=true}catch{listening.value=false}})() }

// 发送
async function send(){
  const t=text.value.trim(); if(!t||streaming.value)return; text.value=''
  initSpeech()
  const uname = await ensureAuthUsername()
  if(!convId) convId='dh_'+(uname||'guest')
  fallbackConvId = convId
  lastStreamError = ''
  chatHistory.value.push({role:'user',content:t}); scrollHistory(); setEmotion('思考')
  streaming.value=true; streamText.value=''
  currentSegment.value=''
  pendingSegments=[]
  pendingReplyFull=''
  setStatus('正在连接红美玲…')

  if(!isLoggedIn() || !uname){
    streaming.value=false
    currentSegment.value='请先登录后再和我聊天哦～'
    chatHistory.value.push({role:'bot',content:currentSegment.value})
    setStatus('当前还没有拿到有效登录身份，首页数字人没法连上问答服务。')
    setEmotion('委屈')
    return
  }

  try{
    closeStream()
    const p=props.currentPage||''
    const params = new URLSearchParams({ msg: t, u: uname, page: p })
    const headers = getAuthHeaders()
    const controller = new AbortController()
    currentStreamController = controller
    let full=''
    let finished = false

    const response = await fetch(`/api/chat/conversations/${convId}/stream?${params.toString()}`,
      { method:'GET', headers, signal: controller.signal }
    )

    if (!response.ok) {
      throw new Error(`stream_failed_${response.status}`)
    }
    if (!response.body) {
      throw new Error(`stream_empty_body_${response.status}`)
    }

    setStatus('已经连上问答服务，正在生成回答…')

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const events = buffer.split('\n\n')
      buffer = events.pop() || ''

      for (const eventText of events) {
        const line = eventText.split('\n').find(line => line.startsWith('data:'))
        if (!line) continue
        const raw = line.slice(5).trim()
        if (!raw) continue
        let d: any
        try {
          d = JSON.parse(raw)
        } catch {
          throw new Error('stream_parse_invalid_json')
        }
        if(d.t==='text'){
          if(!full) setStatus('已经收到回答，正在继续生成…')
          full += d.c || ''
          streamText.value = full
        }
        else if(d.t==='done'){
          finished = true
          break
        }
      }

      if (finished) break
    }

    if (!finished && buffer.trim()) {
      const line = buffer.split('\n').find(line => line.startsWith('data:'))
      if (line) {
        let d: any
        try {
          d = JSON.parse(line.slice(5).trim())
        } catch {
          throw new Error('stream_parse_tail_json')
        }
        if (d.t === 'text') {
          if(!full) setStatus('已经收到回答，正在继续生成…')
          full += d.c || ''
          streamText.value = full
        } else if (d.t === 'done') {
          finished = true
        }
      }
    }

    closeStream()
    streaming.value=false
    streamText.value=''

    if (!full.trim()) {
      throw new Error('stream_empty_reply')
    }

    pendingReplyFull = full.trim()
    pendingSegments=splitSegments(full)
    if(pendingSegments.length) playSegment(0)
    else {
      currentSegment.value=full.trim()
      chatHistory.value.push({role:'bot',content:full.trim()})
      pendingReplyFull=''
      setStatus('这次回答完啦，还可以继续问我～')
    }
  }catch(error:any){
    const aborted = error?.name === 'AbortError'
    closeStream()
    streaming.value=false
    streamText.value=''
    if (aborted) return

    const streamIssue = parseStageError(error)
    lastStreamError = describeStageError(streamIssue.stage, streamIssue.detail)

    try {
      setStatus(`${lastStreamError}，正在切换直连回答…`)
      const fallbackReply = await runFallbackChat(t, uname, props.currentPage || '')
      setStatus(`流式暂时没接通，已切到直连回答。${lastStreamError}`)
      pendingReplyFull = fallbackReply.trim()
      pendingSegments = splitSegments(fallbackReply)
      if (pendingSegments.length) playSegment(0)
      else {
        currentSegment.value = fallbackReply
        chatHistory.value.push({role:'bot',content:fallbackReply})
        pendingReplyFull = ''
        setStatus(`这次回答完啦（已走直连回退）。${lastStreamError}`)
      }
      return
    } catch (fallbackError) {
      const fallbackIssue = parseStageError(fallbackError)
      const fallbackText = describeStageError(fallbackIssue.stage, fallbackIssue.detail)
      currentSegment.value='抱歉呀，我这会儿没有连上模型，请先确认已经登录，再问我一次试试哦～'
      chatHistory.value.push({role:'bot',content:currentSegment.value})
      setStatus(`首页数字人建连失败：${lastStreamError}；直连回退也失败：${fallbackText}。`)
      setEmotion('委屈')
    }
  }
}
</script>

<style scoped>
/* 浮窗 */
.dh-float{position:fixed;width:52px;height:52px;border-radius:50%;background:linear-gradient(135deg,#c43b3b,#a0522d);display:flex;align-items:center;justify-content:center;cursor:grab;z-index:1001;box-shadow:0 4px 18px rgba(196,59,59,.35);user-select:none;-webkit-user-select:none}
.dh-float:hover{transform:scale(1.1)}.dh-float-icon{font-size:26px;z-index:1}
.dh-float-ring{position:absolute;inset:-4px;border-radius:50%;border:2px solid rgba(196,59,59,.25);animation:ring 2s infinite}
@keyframes ring{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(1.12);opacity:.3}}

/* 遮罩 */
.dh-overlay{position:fixed;inset:0;z-index:2000;background:rgba(0,0,0,.55);display:flex;flex-direction:column;align-items:center;justify-content:flex-end;overflow:hidden}
.dh-x{position:absolute;top:16px;right:20px;z-index:10;border:1px solid rgba(255,255,255,.25);background:rgba(0,0,0,.4);color:#fff;width:34px;height:34px;border-radius:50%;font-size:15px;cursor:pointer}.dh-x:hover{background:rgba(255,0,0,.5)}

/* 桌面端：恢复偏侧边的初始布局 */
.dh-body{position:absolute;bottom:-20px;left:6%;display:flex;flex-direction:column;align-items:center;z-index:1;width:auto;pointer-events:none}
.dh-img{height:90vh;max-height:800px;max-width:min(34vw,420px);object-fit:contain;filter:drop-shadow(0 0 30px rgba(255,200,150,.35));transform:scale(1.18) translateY(220px)}
.dh-tag{text-align:center;margin-top:250px}
.dh-tag-name{display:block;color:#ffd700;font-size:20px;font-weight:700;font-family:'STKaiti','楷体','KaiTi',serif;text-shadow:0 0 10px rgba(255,200,0,.4)}
.dh-tag-sub{display:block;color:rgba(255,255,255,.5);font-size:12px;margin-top:2px}

/* 聊天记录 - 恢复人物右侧布局 */
.dh-history{position:absolute;left:34%;right:4%;top:4%;bottom:20%;overflow-y:auto;-webkit-overflow-scrolling:touch;display:flex;flex-direction:column;gap:10px;padding:4px 10px 4px 4px;z-index:2}
.dh-history::-webkit-scrollbar{width:4px}.dh-history::-webkit-scrollbar-thumb{background:rgba(255,255,255,.15);border-radius:2px}.dh-history::-webkit-scrollbar-track{background:rgba(255,255,255,.03);border-radius:2px}
.dh-bubble{max-width:92%;padding:10px 16px;border-radius:16px;font-size:14px;line-height:1.6;animation:fadeIn .3s ease-out}
.dh-bubble.user{align-self:flex-end;background:rgba(196,59,59,.7);color:#fff;border-bottom-right-radius:4px}
.dh-bubble.bot{align-self:flex-start;background:rgba(255,255,255,.12);color:#f5e6d8;border:1px solid rgba(255,255,255,.1);border-bottom-left-radius:4px;backdrop-filter:blur(4px)}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}

/* 当前对话框 - 保持底部偏中，但不做绝对居中主视觉 */
.dh-comic-bubble{position:absolute;left:24%;right:4%;max-width:620px;bottom:100px;background:rgba(18,8,4,.93);border:2px solid rgba(255,215,0,.2);border-radius:18px;padding:20px 28px;z-index:3;animation:popIn .3s ease-out;backdrop-filter:blur(10px)}
@keyframes popIn{from{opacity:0;transform:scale(.96) translateY(6px)}to{opacity:1;transform:scale(1) translateY(0)}}
.dh-comic-text{color:#f5e6d8;font-size:18px;line-height:2;font-family:'STKaiti','楷体','KaiTi',serif;min-height:48px;text-align:center}
.dh-comic-status{text-align:center;color:rgba(255,215,0,.78);font-size:12px;letter-spacing:.5px;margin-bottom:10px}
.dh-comic-text i{animation:blink 1s infinite;color:#ffd700;font-style:normal}@keyframes blink{0%,50%{opacity:1}51%,100%{opacity:0}}
.dh-comic-hint{text-align:center;color:rgba(255,215,0,.4);font-size:13px;cursor:pointer;margin-top:10px;transition:color .2s}.dh-comic-hint:hover{color:#ffd700}

/* 输入栏 - 底部居中 */
.dh-input-bar{position:absolute;bottom:24px;left:50%;transform:translateX(-50%);width:50%;max-width:560px;display:flex;gap:8px;align-items:center;z-index:4}
.dh-mic{width:38px;height:38px;border-radius:50%;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.06);color:#fff;font-size:16px;cursor:pointer;flex-shrink:0}.dh-mic.on{background:rgba(255,77,79,.3);border-color:#ff4d4f}
.dh-inp{flex:1;padding:9px 14px;border:1px solid rgba(255,255,255,.18);border-radius:20px;font-size:14px;color:#fff;background:rgba(255,255,255,.12);outline:none}.dh-inp:focus{border-color:rgba(255,215,0,.4)}.dh-inp::placeholder{color:rgba(255,255,255,.25)}
.dh-send{padding:9px 20px;border:none;border-radius:20px;background:linear-gradient(135deg,#c43b3b,#a0522d);color:#fff;font-size:14px;cursor:pointer;font-family:'STKaiti','楷体','KaiTi',serif}.dh-send:hover:not(:disabled){transform:translateY(-1px)}.dh-send:disabled{opacity:.4}

.dh-fade-enter-active,.dh-fade-leave-active{transition:all .3s ease}.dh-fade-enter-from,.dh-fade-leave-to{opacity:0}

@media (max-width: 1180px){
  .dh-body{left:3%}
  .dh-img{max-width:min(40vw,360px);transform:scale(1.08) translateY(180px)}
  .dh-history{left:38%;right:3%;top:5%;bottom:22%}
  .dh-comic-bubble{left:30%;right:3%;max-width:none}
  .dh-input-bar{width:60%;max-width:600px}
}

/* 手机 — 视觉小说风格：人物居中，记录在身后屏幕，对话框在底部 */
@media(max-width:767px){
  /* 遮罩 — 深色背景 */
  .dh-overlay{justify-content:center;background:rgba(0,0,0,.88);overflow:hidden}

  /* 关闭按钮 */
  .dh-x{top:10px;right:10px;width:38px;height:38px;font-size:17px;background:rgba(0,0,0,.5);border-color:rgba(255,255,255,.3);z-index:20}

  /* ====== 身后屏幕 - 聊天记录 ====== */
  .dh-history{
    position:absolute;left:50%;top:6%;transform:translateX(-50%);
    width:82%;max-height:32vh;z-index:1;
    overflow-y:auto;-webkit-overflow-scrolling:touch;display:flex;flex-direction:column;gap:6px;
    padding:12px 14px;border-radius:10px;
    background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.06);
    backdrop-filter:blur(2px);
    mask-image:linear-gradient(to bottom,rgba(0,0,0,0) 0%,rgba(0,0,0,1) 12%,rgba(0,0,0,1) 78%,rgba(0,0,0,0) 100%);
    -webkit-mask-image:linear-gradient(to bottom,rgba(0,0,0,0) 0%,rgba(0,0,0,1) 12%,rgba(0,0,0,1) 78%,rgba(0,0,0,0) 100%);
  }
  .dh-history::-webkit-scrollbar{width:3px}
  .dh-history::-webkit-scrollbar-thumb{background:rgba(255,255,255,.12);border-radius:1px}
  .dh-bubble{
    font-size:12px;padding:6px 10px;max-width:88%;line-height:1.5;
    animation:fadeIn .25s ease-out;
  }
  .dh-bubble.user{align-self:flex-end;background:rgba(196,59,59,.55);color:#fff}
  .dh-bubble.bot{align-self:flex-start;background:rgba(255,255,255,.06);color:#e8dac8;border:1px solid rgba(255,255,255,.12)}

  /* ====== 人物 - 居中，在记录前面 ====== */
  .dh-body{
    position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
    display:flex;flex-direction:column;align-items:center;z-index:2;
    width:100%;height:55vh;max-height:500px;overflow:visible;pointer-events:none;
  }
  .dh-img{
    height:100%;max-height:100%;object-fit:contain;
    filter:drop-shadow(0 0 25px rgba(255,200,150,.3));
    transform:scale(1.25) translateY(70px);
  }
  .dh-tag{display:none}
  .dh-tag-name{font-size:17px;color:#ffd700;display:block;font-weight:700;text-shadow:0 0 8px rgba(255,200,0,.5)}
  .dh-tag-sub{font-size:11px;color:rgba(255,255,255,.4);display:block;margin-top:2px}

  /* ====== 对话框 - 底部居中，视觉小说文字框 ====== */
  .dh-comic-bubble{
    position:absolute;left:50%;transform:translateX(-50%);bottom:80px;
    width:88%;max-width:100%;z-index:3;
    background:rgba(10,4,2,.92);border:2px solid rgba(255,215,0,.18);
    border-radius:16px;padding:16px 20px;
    backdrop-filter:blur(10px);
    animation:popIn .3s ease-out;
  }
  .dh-comic-text{font-size:15px;line-height:1.8;min-height:32px;text-align:center;color:#f5e6d8}
  .dh-comic-hint{font-size:12px;margin-top:8px}

  /* ====== 输入栏 - 屏幕底部 ====== */
  .dh-input-bar{
    position:absolute;bottom:12px;left:50%;transform:translateX(-50%);
    width:92%;max-width:100%;z-index:4;
    display:flex;gap:6px;align-items:center;
  }
  .dh-inp{font-size:13px;padding:8px 12px;flex:1}
  .dh-send{padding:8px 16px;font-size:13px;flex-shrink:0}
  .dh-mic{width:34px;height:34px;font-size:14px;flex-shrink:0}
}
</style>
