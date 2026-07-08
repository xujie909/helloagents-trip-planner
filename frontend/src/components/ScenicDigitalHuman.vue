<template>
  <Teleport to="body">
    <Transition name="scenic-fade">
      <div v-if="visible" class="scenic-overlay" @click.self="close">
        <button class="scenic-close" @click="close">✕</button>

        <div class="scenic-shell">
          <div class="scenic-figure">
            <img :src="currentImage" class="scenic-img" />
            <div class="scenic-tag">
              <span class="scenic-name">红美玲</span>
              <span class="scenic-sub">{{ props.mode === 'guide' ? '旅行导览数字助手' : '景区数字讲解员' }}</span>
            </div>
          </div>

          <div class="scenic-panel">
            <div class="scenic-panel-head">
              <div>
                <h3>{{ resolvedTitle }}</h3>
                <p>{{ resolvedSubtitle }}</p>
              </div>
              <div class="scenic-actions">
                <button class="ghost-btn" @click="stopSpeaking">停止播报</button>
              </div>
            </div>

            <div class="scenic-history" ref="historyEl">
              <div v-for="(m, i) in chatHistory" :key="i" :class="['bubble', m.role]">
                {{ m.content }}
              </div>
              <div v-if="streamingText" class="bubble bot streaming">{{ streamingText }}</div>
            </div>

            <div class="scenic-current" v-if="currentSegment">
              <span class="label">正在播报</span>
              <p>{{ currentSegment }}</p>
            </div>

            <div class="scenic-input">
              <button :class="['mic-btn', { on: listening }]" @click="toggleMic" title="语音提问">🎤</button>
              <input
                ref="inputEl"
                v-model="text"
                class="question-input"
                :placeholder="speechSupported ? '你可以语音或文字提问…' : '输入你想了解的问题…'"
                @keydown.enter="send"
              />
              <button class="send-btn" :disabled="!text.trim() || asking" @click="send">
                {{ asking ? '请稍候' : '发送' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { askAttractionQuestion, askGuideQuestion } from '@/services/api'

const props = withDefaults(defineProps<{
  visible: boolean
  attractionName?: string
  city?: string
  introText?: string
  mode?: 'attraction' | 'guide'
  title?: string
  subtitle?: string
  welcomeText?: string
  guidePayload?: {
    tripId: string
    city?: string
    currentLocation?: { lat: number; lng: number } | null
    nearestAttraction?: { name: string; distance?: number | null } | null
    doneAttractions?: string[]
    remainingAttractions?: string[]
    currentAttractionIntro?: string
  } | null
}>(), {
  attractionName: '',
  city: '',
  introText: '',
  mode: 'attraction',
  title: '',
  subtitle: '',
  welcomeText: '',
  guidePayload: null,
})

const emit = defineEmits<{
  close: []
}>()

const text = ref('')
const asking = ref(false)
const listening = ref(false)
const currentSegment = ref('')
const streamingText = ref('')
const currentImage = ref('/digital-human/自信.PNG')
const historyEl = ref<HTMLElement>()
const inputEl = ref<HTMLInputElement>()
const chatHistory = ref<{ role: 'user' | 'bot'; content: string }[]>([])

const resolvedTitle = computed(() => {
  if (props.title) return props.title
  if (props.mode === 'guide') return '旅行导览助手'
  return props.attractionName || '景区讲解'
})

const resolvedSubtitle = computed(() => {
  if (props.subtitle) return props.subtitle
  if (props.mode === 'guide') return props.city || '结合你当前导览进度回答问题'
  return props.city || '正在为你讲解当前景区'
})

const resolvedWelcomeText = computed(() => {
  if (props.welcomeText) return props.welcomeText
  if (props.mode === 'guide') {
    return '你好，我是你的旅行导览助手。你可以直接问我当前到哪了、下一个景点是什么，或者附近还有什么值得看。'
  }
  return props.attractionName
    ? `你好，我是${props.attractionName}的数字讲解员。你可以直接问我这个景点的问题。`
    : '你好，我是景区数字讲解员。你可以直接问我这个景点的问题。'
})

let recognition: any = null
let synth: SpeechSynthesis | null = null
let pendingSegments: string[] = []

const speechSupported = typeof window !== 'undefined' && !!((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition)

const emotionKeywords: [string[], string, number][] = [
  [['！', '太', '非常', '超级', '绝了', '美', '棒', '赞', '厉害', '好玩', '震撼'], '兴奋', 2],
  [['？', '怎么', '什么', '哪', '吗', '呢', '为什么', '为啥', '不懂'], '疑惑', 2],
  [['推荐', '建议', '可以', '应该', '值得', '当然', '一定', '放心'], '自信', 2],
  [['抱歉', '对不起', '遗憾', '可惜', '唉', '不好意思'], '委屈', 2],
  [['哇', '咦', '啊', '天哪', '居然', '竟然', '没想到'], '惊讶', 2],
  [['首先', '其次', '总结', '注意', '重要', '关键', '请', '提醒'], '认真', 3],
  [['谢谢', '感谢', '多谢', '开心', '喜欢'], '开心', 1],
]

function imageFor(e: string) {
  const map: Record<string, string> = {
    兴奋: '开心6（兴奋）.PNG',
    开心: '开心2.PNG',
    疑惑: '疑惑.PNG',
    自信: '自信.PNG',
    委屈: '委屈.PNG',
    惊讶: '惊讶.PNG',
    害羞: '开心1（自信）.PNG',
    认真: '开心5.PNG',
    思考: '思考1.PNG',
  }
  return '/digital-human/' + (map[e] || '自信.PNG')
}

function guessEmotion(txt: string) {
  if (txt.length <= 4) {
    if (txt.endsWith('！') || txt.endsWith('!')) return '兴奋'
    if (txt.endsWith('？') || txt.endsWith('?')) return '疑惑'
  }
  const scores: Record<string, number> = {}
  for (const [kws, e, w] of emotionKeywords) {
    for (const kw of kws) {
      if (txt.includes(kw)) scores[e] = (scores[e] || 0) + w
    }
  }
  let best = ''
  let max = 0
  for (const [e, s] of Object.entries(scores)) {
    if (s > max) {
      max = s
      best = e
    }
  }
  if (best) return best
  if ((txt.match(/[！!]/g) || []).length >= 2) return '兴奋'
  if ((txt.match(/[？?]/g) || []).length >= 2) return '疑惑'
  if (txt.length > 80) return '认真'
  return '开心'
}

function setEmotion(seg: string) {
  currentImage.value = imageFor(guessEmotion(seg))
}

function scrollHistory() {
  nextTick(() => {
    const el = historyEl.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function splitSegments(content: string) {
  const raw = content.split(/(?<=[。！？\n])/g).filter((s) => s.trim())
  const segs: string[] = []
  for (const s of raw) {
    if (s.length <= 40) {
      segs.push(s.trim())
      continue
    }
    const sub = s.split(/[,，]/g).filter((x) => x.trim())
    let buf = ''
    for (const ss of sub) {
      if (buf.length + ss.length > 40 && buf) {
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

function ensureSpeech() {
  const w = window as any
  const SR = w.SpeechRecognition || w.webkitSpeechRecognition
  if (SR && !recognition) {
    recognition = new SR()
    recognition.lang = 'zh-CN'
    recognition.interimResults = true
    recognition.onresult = (e: any) => {
      const result = e.results[e.results.length - 1]
      text.value = result[0].transcript.trim()
      if (result.isFinal) {
        listening.value = false
        send()
      }
    }
    recognition.onerror = () => {
      listening.value = false
    }
    recognition.onend = () => {
      listening.value = false
    }
  }
  if (w.speechSynthesis && !synth) synth = w.speechSynthesis
}

function stopSpeaking() {
  if (synth) synth.cancel()
  currentSegment.value = ''
  pendingSegments = []
}

function playSegments(segments: string[], pushToHistory = true) {
  pendingSegments = segments.slice()
  if (!pendingSegments.length) return
  ensureSpeech()
  playSegmentAt(0, pushToHistory)
}

function playSegmentAt(index: number, pushToHistory = true) {
  if (index >= pendingSegments.length) {
    currentSegment.value = ''
    pendingSegments = []
    return
  }
  const seg = pendingSegments[index]
  currentSegment.value = seg
  setEmotion(seg)
  scrollHistory()

  if (!synth) {
    if (pushToHistory) chatHistory.value.push({ role: 'bot', content: seg })
    playSegmentAt(index + 1, pushToHistory)
    return
  }

  synth.cancel()
  const u = new SpeechSynthesisUtterance(seg)
  u.lang = 'zh-CN'
  u.rate = 1.02
  u.pitch = 1.15
  u.onend = () => {
    if (pushToHistory) chatHistory.value.push({ role: 'bot', content: seg })
    scrollHistory()
    playSegmentAt(index + 1, pushToHistory)
  }
  synth.speak(u)
}

function toggleMic() {
  ensureSpeech()
  if (!recognition) return
  if (listening.value) {
    recognition.stop()
    return
  }
  try {
    recognition.start()
    listening.value = true
  } catch {
    listening.value = false
  }
}

async function send() {
  const question = text.value.trim()
  if (!question || asking.value) return
  text.value = ''
  stopSpeaking()
  asking.value = true
  streamingText.value = '正在思考你的问题…'
  chatHistory.value.push({ role: 'user', content: question })
  setEmotion('思考')
  scrollHistory()

  try {
    const res = props.mode === 'guide'
      ? await askGuideQuestion({
          tripId: props.guidePayload?.tripId || '',
          question,
          city: props.guidePayload?.city || props.city || '',
          currentLocation: props.guidePayload?.currentLocation || null,
          nearestAttraction: props.guidePayload?.nearestAttraction || null,
          doneAttractions: props.guidePayload?.doneAttractions || [],
          remainingAttractions: props.guidePayload?.remainingAttractions || [],
          currentAttractionIntro: props.guidePayload?.currentAttractionIntro || '',
        })
      : await askAttractionQuestion(props.attractionName || '', question, props.city || '')
    const answer = res?.data?.answer || res?.message || '抱歉，我暂时没有获取到答案。'
    streamingText.value = ''
    playSegments(splitSegments(answer))
  } catch {
    const fallback = props.mode === 'guide'
      ? '抱歉，我暂时没法继续导览。你可以稍后再试，或者先看看当前行程和地图信息。'
      : '抱歉，我暂时没法继续讲解。你可以稍后再试，或者先看看图文介绍。'
    streamingText.value = ''
    playSegments(splitSegments(fallback))
  } finally {
    asking.value = false
  }
}

function close() {
  stopSpeaking()
  if (recognition && listening.value) recognition.stop()
  emit('close')
}

function resetSession() {
  stopSpeaking()
  text.value = ''
  asking.value = false
  listening.value = false
  streamingText.value = ''
  currentImage.value = '/digital-human/自信.PNG'
  chatHistory.value = [
    {
      role: 'bot',
      content: resolvedWelcomeText.value
    }
  ]
}

watch(
  () => props.visible,
  (visible) => {
    ensureSpeech()
    if (visible) {
      resetSession()
      nextTick(() => {
        inputEl.value?.focus()
      })
      return
    }
    stopSpeaking()
    listening.value = false
  },
  { immediate: true }
)

watch(
  () => `${props.mode}|${props.attractionName || ''}|${props.city || ''}|${props.introText || ''}|${props.guidePayload?.tripId || ''}|${props.guidePayload?.nearestAttraction?.name || ''}|${(props.guidePayload?.doneAttractions || []).join(',')}|${(props.guidePayload?.remainingAttractions || []).join(',')}`,
  () => {
    if (props.visible) {
      resetSession()
      nextTick(() => {
        inputEl.value?.focus()
      })
    }
  }
)

onBeforeUnmount(() => {
  stopSpeaking()
  if (recognition && listening.value) recognition.stop()
})
</script>

<style scoped>
.scenic-overlay {
  position: fixed;
  inset: 0;
  z-index: 2100;
  background: rgba(18, 12, 8, 0.72);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28px;
}
.scenic-close {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.24);
  background: rgba(0, 0, 0, 0.38);
  color: #fff;
  cursor: pointer;
}
.scenic-shell {
  width: min(1180px, 100%);
  height: min(780px, calc(100vh - 56px));
  display: grid;
  grid-template-columns: minmax(280px, 420px) 1fr;
  gap: 18px;
}
.scenic-figure,
.scenic-panel {
  border-radius: 24px;
  overflow: hidden;
}
.scenic-figure {
  background: radial-gradient(circle at top, rgba(255, 229, 189, 0.2), rgba(43, 24, 16, 0.92));
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  padding: 24px 16px 0;
}
.scenic-img {
  width: 100%;
  max-height: calc(100% - 64px);
  object-fit: contain;
  filter: drop-shadow(0 0 28px rgba(255, 213, 138, 0.25));
}
.scenic-tag {
  width: 100%;
  padding: 14px 18px 18px;
  text-align: center;
}
.scenic-name {
  display: block;
  color: #ffd700;
  font-size: 20px;
  font-weight: 700;
}
.scenic-sub {
  display: block;
  margin-top: 4px;
  color: rgba(255, 255, 255, 0.62);
  font-size: 12px;
}
.scenic-panel {
  background: linear-gradient(180deg, #fffaf5, #fff);
  padding: 20px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.scenic-panel-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 14px;
}
.scenic-panel-head h3 {
  margin: 0;
  font-size: 24px;
  color: #5c3a21;
  font-family: 'STKaiti', '楷体', 'KaiTi', serif;
}
.scenic-panel-head p {
  margin: 6px 0 0;
  color: #b08d74;
  font-size: 13px;
}
.scenic-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.ghost-btn,
.send-btn,
.mic-btn {
  border: none;
  cursor: pointer;
}
.ghost-btn {
  padding: 9px 14px;
  border-radius: 999px;
  background: #f8eee4;
  color: #8b5e3c;
}
.scenic-history {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-right: 4px;
}
.bubble {
  max-width: 84%;
  padding: 11px 14px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.7;
  animation: bubbleIn 0.24s ease-out;
}
.bubble.user {
  align-self: flex-end;
  background: linear-gradient(135deg, #c43b3b, #a0522d);
  color: #fff;
  border-bottom-right-radius: 6px;
}
.bubble.bot {
  align-self: flex-start;
  background: #fff3e8;
  color: #5f4839;
  border: 1px solid #f0decd;
  border-bottom-left-radius: 6px;
}
.bubble.streaming {
  opacity: 0.82;
}
.scenic-current {
  margin-top: 12px;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(92, 58, 33, 0.06);
  border: 1px solid rgba(92, 58, 33, 0.08);
}
.scenic-current .label {
  display: inline-block;
  margin-bottom: 8px;
  font-size: 12px;
  color: #b08d74;
}
.scenic-current p {
  margin: 0;
  color: #5c3a21;
  line-height: 1.8;
}
.scenic-input {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
}
.mic-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f7e5d9;
  font-size: 17px;
  color: #8b5e3c;
}
.mic-btn.on {
  background: #c43b3b;
  color: #fff;
}
.question-input {
  flex: 1;
  min-width: 0;
  padding: 11px 14px;
  border-radius: 999px;
  border: 1px solid #eadccf;
  outline: none;
  color: #5c3a21;
  background: #fff;
}
.question-input:focus {
  border-color: #c43b3b;
}
.send-btn {
  padding: 11px 18px;
  border-radius: 999px;
  background: linear-gradient(135deg, #c43b3b, #a0522d);
  color: #fff;
}
.send-btn:disabled,
.ghost-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.scenic-fade-enter-active,
.scenic-fade-leave-active {
  transition: all 0.24s ease;
}
.scenic-fade-enter-from,
.scenic-fade-leave-to {
  opacity: 0;
}
@keyframes bubbleIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
@media (max-width: 900px) {
  .scenic-overlay { padding: 12px; }
  .scenic-shell {
    width: min(100%, 560px);
    height: min(100%, calc(100vh - 24px));
    grid-template-columns: 1fr;
  }
  .scenic-figure {
    min-height: 220px;
    max-height: 30vh;
  }
  .scenic-panel-head {
    flex-direction: column;
  }
  .scenic-actions {
    justify-content: flex-start;
  }
}
</style>
