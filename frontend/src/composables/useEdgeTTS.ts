/**
 * Edge TTS 语音合成 composable
 *
 * 使用后端 Edge TTS API（红美铃同款 XiaoyiNeural 语音），
 * 通过 Web Audio API 播放，绕过浏览器 autoplay 限制。
 */

import { ref } from 'vue'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

// ── 音频缓存（text → ArrayBuffer / AudioBuffer） ──
const audioCache = new Map<string, ArrayBuffer>()
const decodedAudioCache = new Map<string, AudioBuffer>()
const pendingAudioRequests = new Map<string, Promise<ArrayBuffer>>()
const pendingDecodedRequests = new Map<string, Promise<AudioBuffer | null>>()
const MAX_CACHE_SIZE = 60

// ── 并发控制 ──
let pendingRequests = 0
const MAX_CONCURRENT = 2
const requestQueue: Array<() => void> = []

// ── 预热状态 ──
let warmupDone = false
let warmupPromise: Promise<void> | null = null

// ── 共享 AudioContext（单例，模块加载时立即创建） ──
const audioCtx = new AudioContext()

// 每次用户交互时尝试恢复（idempotent，已运行则无操作）
function setupAudioUnlock() {
  const resume = () => { audioCtx.resume() }
  document.addEventListener('click', resume)
  document.addEventListener('touchstart', resume)
  document.addEventListener('keydown', resume)
}
setupAudioUnlock()

/** 确保 AudioContext 处于可播放状态 */
async function ensureAudioRunning(): Promise<void> {
  if (audioCtx.state === 'suspended') {
    try { await audioCtx.resume() } catch { /* ok */ }
  }
}

function trimCacheMap<T>(cache: Map<string, T>) {
  if (cache.size < MAX_CACHE_SIZE) return
  const keys = Array.from(cache.keys())
  for (let i = 0; i < 20 && i < keys.length; i++) cache.delete(keys[i])
}

function touchCacheEntry<T>(cache: Map<string, T>, key: string, value: T): T {
  if (cache.has(key)) cache.delete(key)
  cache.set(key, value)
  return value
}

function getCacheKey(text: string, voice = 'zh-CN-XiaoyiNeural') {
  return `${voice}::${text}`
}

function releaseRequestSlot() {
  pendingRequests--
  const next = requestQueue.shift()
  if (next) next()
}

/** 获取文本对应的音频数据，带缓存和并发控制 */
async function fetchTTSAudio(text: string, voice = 'zh-CN-XiaoyiNeural'): Promise<ArrayBuffer> {
  const cacheKey = getCacheKey(text, voice)
  const cached = audioCache.get(cacheKey)
  if (cached) return touchCacheEntry(audioCache, cacheKey, cached)

  const pending = pendingAudioRequests.get(cacheKey)
  if (pending) return pending

  const request = (async () => {
    if (pendingRequests >= MAX_CONCURRENT) {
      await new Promise<void>((resolve) => requestQueue.push(resolve))
    }
    pendingRequests++

    try {
      const resp = await fetch(`${API_BASE}/api/chat/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice }),
      })

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: resp.statusText }))
        throw new Error(err.detail || `TTS 请求失败 (${resp.status})`)
      }

      const arrayBuffer = await resp.arrayBuffer()

      trimCacheMap(audioCache)
      return touchCacheEntry(audioCache, cacheKey, arrayBuffer)
    } finally {
      pendingAudioRequests.delete(cacheKey)
      releaseRequestSlot()
    }
  })()

  pendingAudioRequests.set(cacheKey, request)
  return request
}

async function getDecodedAudio(
  arrayBuffer: ArrayBuffer,
  cacheKey?: string,
): Promise<AudioBuffer | null> {
  if (!cacheKey) {
    await ensureAudioRunning()
    return await audioCtx.decodeAudioData(arrayBuffer.slice(0))
  }

  const cached = decodedAudioCache.get(cacheKey)
  if (cached) return touchCacheEntry(decodedAudioCache, cacheKey, cached)

  const pending = pendingDecodedRequests.get(cacheKey)
  if (pending) return pending

  const request = (async () => {
    try {
      await ensureAudioRunning()
      const decoded = await audioCtx.decodeAudioData(arrayBuffer.slice(0))
      trimCacheMap(decodedAudioCache)
      return touchCacheEntry(decodedAudioCache, cacheKey, decoded)
    } finally {
      pendingDecodedRequests.delete(cacheKey)
    }
  })()

  pendingDecodedRequests.set(cacheKey, request)
  return request
}

async function primeDecodedAudio(text: string, voice = 'zh-CN-XiaoyiNeural'): Promise<void> {
  const cacheKey = getCacheKey(text, voice)
  if (decodedAudioCache.has(cacheKey)) {
    touchCacheEntry(decodedAudioCache, cacheKey, decodedAudioCache.get(cacheKey)!)
    return
  }
  try {
    const arrayBuffer = await fetchTTSAudio(text, voice)
    await getDecodedAudio(arrayBuffer, cacheKey)
  } catch {
    // 预解码失败不影响后续正常播放
  }
}

// ──────────────────────────────────────────────

export function useEdgeTTS() {
  const isSpeaking = ref(false)
  const error = ref<string | null>(null)

  let currentSource: AudioBufferSourceNode | null = null
  let currentAbortController: AbortController | null = null
  let playId = 0

  function isAborted(myPlayId: number): boolean {
    if (myPlayId !== playId) return true
    if (currentAbortController?.signal.aborted) return true
    return false
  }

  /** 停止当前播放并中止请求 */
  function stop() {
    playId++
    if (currentSource) {
      try { currentSource.stop() } catch { /* ok */ }
      currentSource = null
    }
    if (currentAudio) {
      currentAudio.pause()
      currentAudio.currentTime = 0
      currentAudio = null
    }
    if (currentAbortController) {
      currentAbortController.abort()
      currentAbortController = null
    }
    isSpeaking.value = false
  }

  /** 解码 ArrayBuffer → AudioBuffer，失败时返回 null */
  async function decode(
    arrayBuffer: ArrayBuffer,
    myPlayId: number,
    cacheKey?: string,
  ): Promise<AudioBuffer | null> {
    if (cacheKey) {
      const cached = decodedAudioCache.get(cacheKey)
      if (cached) return touchCacheEntry(decodedAudioCache, cacheKey, cached)
    }
    if (isAborted(myPlayId)) return null
    try {
      const decoded = await getDecodedAudio(arrayBuffer, cacheKey)
      if (isAborted(myPlayId)) return null
      return decoded
    } catch (e) {
      console.warn('[EdgeTTS] AudioContext 解码失败，回退到 <audio> 播放:', e)
      return null
    }
  }

  /**
   * 通过 Web Audio API 播放 AudioBuffer。
   * 返回 { source, ended }，若已中止返回 null。
   */
  function playViaAudioContext(
    audioBuffer: AudioBuffer,
    myPlayId: number,
  ): { source: AudioBufferSourceNode; ended: Promise<void> } | null {
    if (isAborted(myPlayId)) return null

    const source = audioCtx.createBufferSource()
    source.buffer = audioBuffer
    source.connect(audioCtx.destination)

    const ended = new Promise<void>((resolve) => {
      source.onended = () => {
        if (currentSource === source) currentSource = null
        resolve()
      }
    })

    currentAbortController!.signal.addEventListener(
      'abort',
      () => { try { source.stop() } catch { /* ok */ } },
      { once: true },
    )

    source.start()
    return { source, ended }
  }

  /**
   * <audio> 标签回退播放（当 AudioContext 解码失败时使用）。
   */
  function playViaAudioElement(
    arrayBuffer: ArrayBuffer,
    myPlayId: number,
  ): { audio: HTMLAudioElement; ended: Promise<void> } | null {
    if (isAborted(myPlayId)) return null

    const blob = new Blob([arrayBuffer], { type: 'audio/mpeg' })
    const url = URL.createObjectURL(blob)
    const audio = new Audio(url)

    let finished = false
    // 把 resolve 提取出来，确保 play() 被拒时也能 resolve
    let promiseResolve!: () => void
    const ended = new Promise<void>((resolve) => {
      promiseResolve = resolve
    })

    const finish = () => {
      if (finished) return
      finished = true
      URL.revokeObjectURL(url)
      if (currentAudio === audio) currentAudio = null
      promiseResolve()
    }

    audio.onended = finish
    audio.onerror = () => {
      console.error('[EdgeTTS] <audio> 播放失败')
      finish()
    }

    currentAbortController!.signal.addEventListener(
      'abort',
      () => { audio.pause(); audio.currentTime = 0; finish() },
      { once: true },
    )

    audio.play().catch((e) => {
      console.warn('[EdgeTTS] <audio>.play() 被浏览器拦截（autoplay）:', e)
      // play() 被拒时 onended/onerror 都不会触发，主动 resolve
      finish()
    })

    return { audio, ended }
  }

  // 用于 <audio> 回退的引用
  let currentAudio: HTMLAudioElement | null = null

  /** 播放单句文本 */
  async function speak(text: string, voice?: string): Promise<void> {
    if (!text?.trim()) return

    stop()
    isSpeaking.value = true
    error.value = null

    const myPlayId = playId
    currentAbortController = new AbortController()

    try {
      const arrayBuffer = await fetchTTSAudio(text, voice)
      if (isAborted(myPlayId)) return

      const cacheKey = getCacheKey(text, voice)
      // 优先 AudioContext，失败回退 <audio>
      const audioBuffer = await decode(arrayBuffer, myPlayId, cacheKey)
      if (audioBuffer && !isAborted(myPlayId)) {
        const result = playViaAudioContext(audioBuffer, myPlayId)
        if (result) {
          currentSource = result.source
          await result.ended
          if (!isAborted(myPlayId)) isSpeaking.value = false
          return
        }
      }

      // <audio> 回退
      if (isAborted(myPlayId)) return
      const fallback = playViaAudioElement(arrayBuffer, myPlayId)
      if (!fallback) return
      currentAudio = fallback.audio
      await fallback.ended
      if (!isAborted(myPlayId)) isSpeaking.value = false
    } catch (err: any) {
      if (err?.name === 'AbortError' || isAborted(myPlayId)) return
      error.value = err?.message || 'TTS 播放失败'
      console.error('[EdgeTTS] speak 失败:', err)
      isSpeaking.value = false
    }
  }

  /** 分段连续播放 — 第一段加载即播，其余段后台并行预加载 */
  async function speakSegments(
    segments: string[],
    voice?: string,
    onSegmentChange?: (index: number) => void,
  ): Promise<void> {
    if (!segments?.length) return

    stop()
    isSpeaking.value = true
    error.value = null

    const myPlayId = playId
    currentAbortController = new AbortController()

    const valid = segments
      .map((text, i) => ({ text: text.trim(), idx: i }))
      .filter((s) => s.text)

    if (!valid.length) { isSpeaking.value = false; return }

    // 判断模式：第一段先试 AudioContext，失败则全部走 <audio>
    let useAudioElement = false

    try {
      // 第一段：加载 → 尝试 AudioContext 解码
      const first = valid[0]
      const firstData = await fetchTTSAudio(first.text, voice)
      if (isAborted(myPlayId)) return

      const firstCacheKey = getCacheKey(first.text, voice)
      const firstBuffer = await decode(firstData, myPlayId, firstCacheKey)
      // 其余段后台并行预加载
      for (let i = 1; i < valid.length; i++) {
        fetchTTSAudio(valid[i].text, voice)
      }

      useAudioElement = !firstBuffer

      if (useAudioElement) {
        // ── <audio> 回退路径 ──
        onSegmentChange?.(first.idx)
        const fallback = playViaAudioElement(firstData, myPlayId)
        if (!fallback) return
        currentAudio = fallback.audio
        await fallback.ended
        if (isAborted(myPlayId)) return

        for (let i = 1; i < valid.length; i++) {
          if (isAborted(myPlayId)) break
          const { text, idx } = valid[i]
          const data = await fetchTTSAudio(text, voice)
          if (isAborted(myPlayId)) break
          onSegmentChange?.(idx)
          const fb = playViaAudioElement(data, myPlayId)
          if (!fb) break
          currentAudio = fb.audio
          await fb.ended
        }
      } else {
        // ── AudioContext 路径 ──
        if (!firstBuffer || isAborted(myPlayId)) return
        onSegmentChange?.(first.idx)

        const firstResult = playViaAudioContext(firstBuffer, myPlayId)
        if (!firstResult) return
        currentSource = firstResult.source
        await firstResult.ended
        if (isAborted(myPlayId)) return

        for (let i = 1; i < valid.length; i++) {
          if (isAborted(myPlayId)) break
          const { text, idx } = valid[i]
          const data = await fetchTTSAudio(text, voice)
          if (isAborted(myPlayId)) break

          const cacheKey = getCacheKey(text, voice)
          const buffer = await decode(data, myPlayId, cacheKey)
          if (!buffer || isAborted(myPlayId)) break

          onSegmentChange?.(idx)
          const result = playViaAudioContext(buffer, myPlayId)
          if (!result) break
          currentSource = result.source
          await result.ended
        }
      }
    } catch (err: any) {
      if (err?.name === 'AbortError' || isAborted(myPlayId)) return
      error.value = err?.message || 'TTS 播放失败'
      console.error('[EdgeTTS] speakSegments 失败:', err)
    } finally {
      if (playId === myPlayId) {
        currentAbortController = null
        currentAudio = null
        isSpeaking.value = false
      }
    }
  }

  /** 预热 — 后台静默请求一次 TTS 建立 WebSocket 连接 */
  async function warmup(voice = 'zh-CN-XiaoyiNeural'): Promise<void> {
    if (warmupDone) return
    if (warmupPromise) { await warmupPromise; return }

    warmupPromise = (async () => {
      try {
        await fetchTTSAudio('嗯', voice)
        warmupDone = true
      } catch { /* 预热失败不影响正常使用 */ }
    })()
    await warmupPromise
  }

  /** 后台预加载 — 提前将多个文本段的 TTS 音频拉入缓存
   *  在 DataPlaza 等场景中，景点详情加载后立即调用，用户点「播放」时即可零延迟开播。
   */
  function prefetchSegments(texts: string[], voice?: string): void {
    for (const t of texts) {
      const text = t.trim()
      if (!text) continue
      fetchTTSAudio(text, voice) // fire-and-forget
      primeDecodedAudio(text, voice)
    }
  }

  return { speak, speakSegments, stop, isSpeaking, error, warmup, prefetchSegments }
}
