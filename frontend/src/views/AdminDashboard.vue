<template>
  <div class="admin-dash">
    <aside class="admin-sidebar">
      <div class="as-brand-card">
        <div class="as-brand-top">
          <span class="as-seal">管</span>
          <div>
            <span class="as-name">知行旅行管理台</span>
            <span class="as-desc">运营总览 · 内容维护 · 数据巡检</span>
          </div>
        </div>
        <div class="as-status-row">
          <span class="as-status-dot"></span>
          <span>系统在线</span>
          <span class="as-status-divider">·</span>
          <span>{{ dateStr }}</span>
        </div>
      </div>

      <nav class="as-nav">
        <button
          v-for="item in navItems"
          :key="item.key"
          type="button"
          :class="['as-item', { active: view === item.key }]"
          @click="openView(item.key)"
        >
          <span class="as-item-icon">{{ item.icon }}</span>
          <span class="as-item-text">
            <strong>{{ item.label }}</strong>
            <small>{{ item.desc }}</small>
          </span>
        </button>
      </nav>

      <div class="as-spotlight" @click="router.push('/datascreen')">
        <div>
          <span class="as-spotlight-label">大屏联动</span>
          <strong>进入数据大屏</strong>
          <p>查看更适合展示汇报的可视化大屏页面</p>
        </div>
        <span class="as-spotlight-arrow">↗</span>
      </div>

      <div class="as-footer-card">
        <div class="as-user-meta">
          <span class="as-user-avatar">A</span>
          <div>
            <strong>管理员</strong>
            <p>当前具备后台维护权限</p>
          </div>
        </div>
        <button class="as-logout" @click="logout">退出登录</button>
      </div>
    </aside>

    <main class="admin-main">
      <header class="admin-topbar">
        <div>
          <p class="topbar-eyebrow">Admin Workbench</p>
          <h1>{{ currentViewMeta.label }}</h1>
          <span class="topbar-subtitle">{{ currentViewMeta.desc }}</span>
        </div>
        <div class="topbar-actions">
          <button class="topbar-btn ghost" @click="refreshCurrentView">刷新当前页</button>
          <button class="topbar-btn primary" @click="router.push('/datascreen')">查看数据大屏</button>
        </div>
      </header>

      <section v-if="view === 'home'" class="home-shell">
        <div class="home-hero panel-card">
          <div class="home-hero-copy">
            <span class="panel-badge">今日概览</span>
            <h2>你好，管理员</h2>
            <p>
              当前后台可统一查看用户、广场数据、知识库与 FAQ 内容，
              适合进行日常巡检、内容更新与运营维护。
            </p>
            <div class="home-hero-actions">
              <button class="topbar-btn primary" @click="openView('users')">查看用户概况</button>
              <button class="topbar-btn ghost" @click="openView('knowledge')">管理知识库</button>
            </div>
          </div>
          <div class="home-hero-side">
            <div class="hero-mini-card">
              <span>运行状态</span>
              <strong>稳定在线</strong>
              <p>建议每 30 分钟巡检一次核心数据模块</p>
            </div>
            <div class="hero-mini-card warm">
              <span>重点关注</span>
              <strong>{{ stats.user_count || 0 }} 位用户</strong>
              <p>重点关注近期活跃用户与知识库新增内容</p>
            </div>
          </div>
        </div>

        <div class="stats-grid">
          <div v-for="card in statCards" :key="card.label" class="stats-card panel-card">
            <div class="stats-card-top">
              <span class="stats-icon">{{ card.icon }}</span>
              <span class="stats-trend">{{ card.hint }}</span>
            </div>
            <strong>{{ card.value }}</strong>
            <span>{{ card.label }}</span>
          </div>
        </div>

        <div class="home-content-grid">
          <div class="panel-card quick-panel">
            <div class="section-heading">
              <div>
                <span class="panel-badge soft">快捷入口</span>
                <h3>常用管理动作</h3>
              </div>
            </div>
            <div class="quick-list">
              <button class="quick-item" @click="openView('users')">
                <span class="quick-icon">👥</span>
                <div>
                  <strong>用户管理</strong>
                  <p>查看注册、登录与账号状态</p>
                </div>
                <span class="quick-arrow">→</span>
              </button>
              <button class="quick-item" @click="openView('plaza')">
                <span class="quick-icon">📊</span>
                <div>
                  <strong>广场数据</strong>
                  <p>巡检省市景点数据与统计结构</p>
                </div>
                <span class="quick-arrow">→</span>
              </button>
              <button class="quick-item" @click="openView('faq')">
                <span class="quick-icon">❓</span>
                <div>
                  <strong>FAQ 管理</strong>
                  <p>补充高频问答，优化游客答复效果</p>
                </div>
                <span class="quick-arrow">→</span>
              </button>
            </div>
          </div>

          <div class="panel-card focus-panel">
            <div class="section-heading">
              <div>
                <span class="panel-badge soft">运营提醒</span>
                <h3>本页建议</h3>
              </div>
            </div>
            <ul class="focus-list">
              <li>先查看用户数据，确认近期活跃与异常账号情况。</li>
              <li>如要更新景点资料，优先同步知识库与 FAQ 口径。</li>
              <li>需要做汇报展示时，可直接切换到数据大屏模式。</li>
            </ul>
          </div>
        </div>
      </section>

      <section v-if="view === 'users'" class="view-shell panel-card">
        <div class="section-heading section-heading-spread">
          <div>
            <span class="panel-badge soft">用户管理</span>
            <h3>账号与活跃情况</h3>
            <p>支持搜索、启用/禁用与删除普通用户账号。</p>
          </div>
          <div class="section-metric">共 {{ filteredUsers.length }} 位用户</div>
        </div>
        <div class="toolbar-row">
          <input v-model="userSearch" placeholder="搜索用户名..." class="field-input" />
        </div>
        <div class="user-list">
          <div v-for="u in filteredUsers" :key="u.username" :class="['user-row', { disabled: u.disabled }]">
            <div class="user-main">
              <span class="ur-name">
                {{ u.username }}
                <span v-if="u.username === 'admin'" class="ur-admin">管理员</span>
              </span>
              <span class="ur-meta">{{ u.trip_count }} 行程 · {{ u.chat_count }} 对话</span>
            </div>
            <span class="ur-time">{{ u.last_login?.slice(0, 16) || '未登录' }}</span>
            <div class="user-actions">
              <button class="chip-btn" @click="toggleUser(u)" v-if="u.username !== 'admin'">
                {{ u.disabled ? '🔓 启用' : '🔒 禁用' }}
              </button>
              <button class="chip-btn danger" @click="deleteUser(u)" v-if="u.username !== 'admin'">🗑️ 删除</button>
            </div>
          </div>
        </div>
      </section>

      <section v-if="view === 'plaza'" class="view-shell panel-card am-plaza">
        <div class="section-heading section-heading-spread">
          <div>
            <span class="panel-badge soft">广场数据</span>
            <h3>省市景点统计结构</h3>
            <p>支持按层级查看省份、城市与景点数据，并可清理省级数据。</p>
          </div>
          <div class="section-metric">{{ plazaTotal.toLocaleString() }} 条记录</div>
        </div>
        <div class="toolbar-row toolbar-row-split">
          <input v-model="plazaSearch" placeholder="搜索省份 / 城市 / 景点..." class="field-input" />
          <span class="toolbar-hint">点击条目可展开详情</span>
        </div>
        <div class="plaza-visual">
          <div v-for="prov in filteredPlaza" :key="prov.name" class="pv-prov">
            <div class="pv-prov-head" @click="prov._open = !prov._open">
              <span class="pv-prov-arrow">{{ prov._open ? '▾' : '▸' }}</span>
              <span class="pv-prov-name">{{ prov.name }}</span>
              <span class="pv-prov-count">{{ prov.count.toLocaleString() }}</span>
              <span class="pv-prov-cities">{{ prov.cities?.length || 0 }} 城</span>
              <button class="chip-btn danger slim" @click.stop="deletePlazaProvince(prov.name)">删除</button>
            </div>
            <div v-if="prov._open" class="pv-cities">
              <div v-for="city in prov.cities || []" :key="city.name" class="pv-city">
                <div class="pv-city-head" @click="city._open = !city._open">
                  <span class="pv-city-arrow">{{ city._open ? '▾' : '▸' }}</span>
                  <span class="pv-city-name">{{ city.name }}</span>
                  <span class="pv-city-count">{{ city.count.toLocaleString() }}</span>
                </div>
                <div v-if="city._open" class="pv-attrs">
                  <div v-for="a in city.attractions || []" :key="a.name" class="pv-ad-detail">
                    <div class="pv-ad-head" @click="a._detail = !a._detail">
                      <span class="pv-ad-name" @click.stop="viewAttrDetail(a.name, city.name)">{{ a.name }}</span>
                      <span class="pv-ad-count">{{ a.count.toLocaleString() }}</span>
                      <span class="pv-ad-avg">¥{{ a.avg_cost }}</span>
                      <span class="pv-ad-arrow">{{ a._detail ? '▾' : '▸' }}</span>
                    </div>
                    <div v-if="a._detail" class="pv-ad-body">
                      <div class="pv-ad-row"><span class="pv-ad-label">消费</span><span>均 ¥{{ a.avg_cost }} · 逗留 {{ a.avg_stay }}h · ⭐{{ a.avg_satisfaction }}</span></div>
                      <div class="pv-ad-row"><span class="pv-ad-label">性别</span><span>👨{{ a.gender_dist?.男 || 0 }} · 👩{{ a.gender_dist?.女 || 0 }}</span></div>
                      <div class="pv-ad-row"><span class="pv-ad-label">年龄</span><span>青年 {{ a.age_groups?.['青年(19-30)'] || 0 }} · 中年 {{ a.age_groups?.['中年(31-45)'] || 0 }} · 熟龄 {{ a.age_groups?.['熟龄(46+)'] || 0 }}</span></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section v-if="view === 'knowledge'" class="view-shell panel-card">
        <div class="section-heading section-heading-spread">
          <div>
            <span class="panel-badge soft">知识库</span>
            <h3>知识资料上传与检索</h3>
            <p>支持拖拽上传文档，由 AI 自动解析并分类归档。</p>
          </div>
          <div class="section-metric">{{ knowledge.length }} 条资料</div>
        </div>
        <div class="kb-upload-zone" @drop.prevent="handleDrop" @dragover.prevent @click="fileInput?.click()">
          <span>📁</span>
          <p>拖拽文件到这里，或点击上传资料</p>
          <span class="kb-upload-hint">支持 PDF · DOCX · TXT · JPG · PNG</span>
          <input type="file" ref="fileInput" multiple accept=".pdf,.docx,.txt,.jpg,.jpeg,.png" @change="handleFiles" style="display:none" />
        </div>
        <div v-if="kbUploading" class="kb-progress">🤖 AI 正在解析与分类文件，请稍候...</div>
        <div class="toolbar-row">
          <input v-model="kbSearch" placeholder="搜索景点、城市或省份..." class="field-input" />
        </div>
        <div class="knowledge-list">
          <div v-for="k in filteredKnowledge" :key="k.id" class="kb-row">
            <div class="kb-main">
              <span class="kb-name" @click="viewAttrDetail(k.name, k.city)">{{ k.name }}</span>
              <span class="kb-meta">{{ k.province }} · {{ k.city }} · {{ k.category }}</span>
            </div>
            <span class="kb-tags">{{ (k.tags || []).join('、') }}</span>
            <span class="kb-count" v-if="k.count > 1">×{{ k.count }}</span>
            <button class="chip-btn danger" @click="deleteKnowledge(k.id)">删除</button>
          </div>
        </div>
      </section>

      <SentimentReport v-if="view === 'sentiment'" />

      <section v-if="view === 'faq'" class="view-shell panel-card">
        <div class="section-heading section-heading-spread">
          <div>
            <span class="panel-badge soft">FAQ 管理</span>
            <h3>常见问答维护</h3>
            <p>补充热门问题与标准答案，统一游客问答口径。</p>
          </div>
          <div class="section-metric">{{ faqList.length }} 条 FAQ</div>
        </div>
        <div class="faq-add-form">
          <input v-model="faqForm.question" placeholder="问题（必填）" class="field-input faq-field" />
          <input v-model="faqForm.answer" placeholder="答案（必填）" class="field-input faq-field faq-field-wide" />
          <input v-model="faqForm.category" placeholder="分类" class="field-input faq-field faq-field-small" />
          <input v-model="faqForm.tagsStr" placeholder="标签（逗号分隔）" class="field-input faq-field faq-field-small" />
          <button class="topbar-btn primary faq-submit" @click="addFAQ" :disabled="!faqForm.question || !faqForm.answer">＋ 添加</button>
        </div>
        <div class="faq-categories" v-if="faqCategories.length">
          <span :class="['faq-cat-chip', { active: faqCatFilter === '' }]" @click="faqCatFilter = ''">全部</span>
          <span v-for="c in faqCategories" :key="c" :class="['faq-cat-chip', { active: faqCatFilter === c }]" @click="faqCatFilter = c">{{ c }}</span>
        </div>
        <div class="faq-list">
          <div v-for="f in filteredFAQ" :key="f.id" class="faq-row">
            <div class="faq-row-main">
              <span class="faq-q">❓ {{ f.question }}</span>
              <span class="faq-a">💡 {{ f.answer?.slice(0, 80) }}{{ f.answer?.length > 80 ? '...' : '' }}</span>
            </div>
            <div class="faq-row-meta">
              <span class="faq-cat-tag">{{ f.category }}</span>
              <span v-for="t in f.tags || []" :key="t" class="faq-tag">{{ t }}</span>
            </div>
            <div class="faq-row-actions">
              <span class="faq-time">{{ f.created_at?.slice(0, 10) }}</span>
              <button class="chip-btn slim" @click="editFAQ(f)">编辑</button>
              <button class="chip-btn danger slim" @click="deleteFAQ(f.id)">删除</button>
            </div>
          </div>
        </div>
        <a-modal v-model:open="faqEditVisible" title="编辑 FAQ" :footer="null">
          <div class="faq-edit-form" v-if="faqEditing">
            <label>问题</label>
            <input v-model="faqEditing.question" class="field-input modal-field" />
            <label>答案</label>
            <textarea v-model="faqEditing.answer" rows="4" class="field-input modal-field textarea-field"></textarea>
            <label>分类</label>
            <input v-model="faqEditing.category" class="field-input modal-field" />
            <label>标签（逗号分隔）</label>
            <input v-model="faqEditing.tagsStr" class="field-input modal-field" />
            <button class="topbar-btn primary" @click="saveFAQ">保存</button>
          </div>
        </a-modal>
      </section>
    </main>

    <a-modal
      v-model:open="detailVisible"
      :title="'🏛️ ' + detailName"
      width="860px"
      :footer="null"
      :bodyStyle="{ maxHeight: '70vh', overflowY: 'auto', padding: '24px 32px' }"
    >
      <div v-if="detailLoading" class="detail-loading">
        <div class="think-seal">行</div>
        <div class="think-dots"><span></span><span></span><span></span></div>
        <p class="think-text">行知正在查阅资料...</p>
      </div>
      <div v-else-if="detailContent" class="attr-intro" v-html="renderMd(detailContent)"></div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { isLoggedIn, logout as apiLogout } from '@/services/api'
import { message } from 'ant-design-vue'
import SentimentReport from './SentimentReport.vue'

const router = useRouter()
const view = ref('home')
const userSearch = ref('')
const kbSearch = ref('')
const plazaSearch = ref('')
const users = ref<any[]>([])
const stats = ref<any>({})
const plazaList = ref<any[]>([])
const knowledge = ref<any[]>([])
const fileInput = ref<HTMLInputElement>()
const kbUploading = ref(false)
const detailVisible = ref(false)
const detailName = ref('')
const detailContent = ref('')
const detailLoading = ref(false)
const faqList = ref<any[]>([])
const faqCategories = ref<string[]>([])
const faqCatFilter = ref('')
const faqForm = ref({ question: '', answer: '', category: '通用', tagsStr: '' })
const faqEditVisible = ref(false)
const faqEditing = ref<any>(null)
let statsTimer: any = null

const navItems = [
  { key: 'home', icon: '🏠', label: '管理首页', desc: '查看总览工作台' },
  { key: 'users', icon: '👥', label: '用户管理', desc: '巡检账号状态' },
  { key: 'plaza', icon: '📊', label: '广场数据', desc: '查看统计结构' },
  { key: 'knowledge', icon: '📚', label: '知识库', desc: '上传资料内容' },
  { key: 'faq', icon: '❓', label: 'FAQ 管理', desc: '维护高频问答' },
  { key: 'sentiment', icon: '🧭', label: '感受度报告', desc: '查看游客反馈趋势' },
]

const dateStr = new Date().toLocaleDateString('zh-CN', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  weekday: 'long'
})

const currentViewMeta = computed(() =>
  navItems.find((item) => item.key === view.value) || navItems[0]
)

const statCards = computed(() => [
  {
    label: '注册用户',
    value: stats.value.user_count ?? 0,
    hint: '账号总量',
    icon: '👥'
  },
  {
    label: '总行程',
    value: stats.value.trip_count ?? 0,
    hint: '行程沉淀',
    icon: '🗺️'
  },
  {
    label: '广场数据',
    value: (stats.value.plaza_records || 0).toLocaleString(),
    hint: '内容记录',
    icon: '📊'
  },
  {
    label: '知识库条目',
    value: stats.value.knowledge_count ?? 0,
    hint: '资料储备',
    icon: '📚'
  }
])

const plazaTotal = computed(() => plazaList.value.reduce((s: number, p: any) => s + (p.count || 0), 0))
const filteredPlaza = computed(() => {
  if (!plazaSearch.value) return plazaList.value
  const q = plazaSearch.value.toLowerCase()
  return plazaList.value.filter((p: any) => {
    if (p.name.toLowerCase().includes(q)) return true
    for (const c of p.cities || []) {
      if (c.name.toLowerCase().includes(q)) return true
      for (const a of c.attractions || []) {
        if (a.name.toLowerCase().includes(q)) return true
      }
    }
    return false
  })
})
const filteredUsers = computed(() =>
  userSearch.value ? users.value.filter((u: any) => u.username.includes(userSearch.value)) : users.value
)
const filteredKnowledge = computed(() =>
  kbSearch.value
    ? knowledge.value.filter((k: any) => k.name.includes(kbSearch.value) || (k.province || '').includes(kbSearch.value))
    : knowledge.value
)
const filteredFAQ = computed(() => {
  if (!faqCatFilter.value) return faqList.value
  return faqList.value.filter((f: any) => f.category === faqCatFilter.value)
})

function openView(nextView: string) {
  view.value = nextView
  if (nextView === 'plaza') loadPlaza()
  if (nextView === 'knowledge') loadKnowledge()
  if (nextView === 'faq') loadFAQ()
}

function refreshCurrentView() {
  if (view.value === 'home') {
    loadStats()
    loadUsers()
    return
  }
  if (view.value === 'users') return loadUsers()
  if (view.value === 'plaza') return loadPlaza()
  if (view.value === 'knowledge') return loadKnowledge()
  if (view.value === 'faq') return loadFAQ()
  if (view.value === 'sentiment') return loadStats()
}

async function loadStats() {
  try {
    const r = await fetch('/api/admin/stats', { headers: { 'X-Username': 'admin' } })
    const d = await r.json()
    if (d.success) stats.value = d.data
  } catch {}
}
async function loadUsers() {
  try {
    const r = await fetch('/api/admin/users', { headers: { 'X-Username': 'admin' } })
    const d = await r.json()
    if (d.success) users.value = d.data
  } catch {}
}
async function toggleUser(u: any) {
  await fetch(`/api/admin/users/${u.username}/toggle`, { method: 'PUT', headers: { 'X-Username': 'admin' } })
  loadUsers()
}
async function deleteUser(u: any) {
  if (!confirm(`删除 ${u.username}？`)) return
  await fetch(`/api/admin/users/${u.username}`, { method: 'DELETE', headers: { 'X-Username': 'admin' } })
  loadUsers()
  loadStats()
}

async function loadPlaza() {
  try {
    const r = await fetch('/api/admin/plaza', { headers: { 'X-Username': 'admin' } })
    const d = await r.json()
    if (d.success) {
      plazaList.value = Object.entries(d.data)
        .filter(([k]: [string, any]) => d.data[k].count > 0)
        .sort((a: any, b: any) => b[1].count - a[1].count)
        .map(([k, v]: [string, any]) => ({ name: k, ...v, _open: false }))
    }
  } catch {}
}
async function deletePlazaProvince(name: string) {
  if (!confirm(`删除 ${name}？`)) return
  const plaza: any = {}
  for (const p of plazaList.value) {
    if (p.name !== name) plaza[p.name] = { count: p.count, cities: p.cities }
  }
  await fetch('/api/admin/plaza/update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Username': 'admin' },
    body: JSON.stringify({ data: plaza })
  })
  loadPlaza()
  loadStats()
}

async function loadKnowledge() {
  try {
    const r = await fetch('/api/admin/knowledge', { headers: { 'X-Username': 'admin' } })
    const d = await r.json()
    if (d.success) knowledge.value = d.data
  } catch {}
}
async function deleteKnowledge(id: string) {
  await fetch(`/api/admin/knowledge/${id}`, { method: 'DELETE', headers: { 'X-Username': 'admin' } })
  loadKnowledge()
  loadStats()
}
async function handleFiles(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (!files?.length) return
  await uploadFiles(Array.from(files))
}
async function handleDrop(e: DragEvent) {
  const files = e.dataTransfer?.files
  if (!files?.length) return
  await uploadFiles(Array.from(files))
}
async function uploadFiles(files: File[]) {
  kbUploading.value = true
  for (const file of files) {
    if (file.size > 10 * 1024 * 1024) {
      message.warning(`${file.name}>10MB`)
      continue
    }
    const form = new FormData()
    form.append('file', file)
    try {
      const r = await fetch('/api/admin/knowledge/upload', {
        method: 'POST',
        headers: { 'X-Username': 'admin' },
        body: form
      })
      const d = await r.json()
      if (d.success) message.success(`${file.name} 导入成功`)
    } catch {
      message.error(`${file.name} 失败`)
    }
  }
  kbUploading.value = false
  loadKnowledge()
  loadStats()
}

async function viewAttrDetail(name: string, city: string) {
  detailName.value = name
  detailVisible.value = true
  detailLoading.value = true
  detailContent.value = ''
  try {
    const r = await fetch(`/api/plaza/attraction/${encodeURIComponent(name)}?city=${encodeURIComponent(city || '')}`)
    const d = await r.json()
    if (d.success) detailContent.value = d.data.intro
  } catch {
    detailContent.value = '获取失败'
  } finally {
    detailLoading.value = false
  }
}
function renderMd(t: string): string {
  if (!t) return ''
  let h = t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  h = h.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  h = h.replace(/\*(.+?)\*/g, '<em>$1</em>')
  h = h.replace(/^### (.+)$/gm, '<h4>$1</h4>')
  h = h.replace(/^## (.+)$/gm, '<h3>$1</h3>')
  h = h.replace(/^- (.+)$/gm, '<li>$1</li>')
  h = h.replace(/\n\n/g, '<br><br>')
  h = h.replace(/\n/g, '<br>')
  return h
}

function logout() {
  apiLogout()
  router.replace('/login')
}

async function loadFAQ() {
  try {
    const r = await fetch('/api/admin/faq', { headers: { 'X-Username': 'admin' } })
    const d = await r.json()
    if (d.success) {
      faqList.value = d.data
      faqCategories.value = d.categories || []
    }
  } catch {}
}
async function addFAQ() {
  const tags = faqForm.value.tagsStr.split(',').map((t: string) => t.trim()).filter(Boolean)
  try {
    const r = await fetch('/api/admin/faq', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Username': 'admin' },
      body: JSON.stringify({
        question: faqForm.value.question,
        answer: faqForm.value.answer,
        category: faqForm.value.category || '通用',
        tags
      })
    })
    const d = await r.json()
    if (d.success) {
      faqForm.value = { question: '', answer: '', category: '通用', tagsStr: '' }
      loadFAQ()
      loadStats()
    }
  } catch {}
}
async function deleteFAQ(id: string) {
  if (!confirm('删除此FAQ？')) return
  await fetch(`/api/admin/faq/${id}`, { method: 'DELETE', headers: { 'X-Username': 'admin' } })
  loadFAQ()
  loadStats()
}
function editFAQ(f: any) {
  faqEditing.value = { ...f, tagsStr: (f.tags || []).join(', ') }
  faqEditVisible.value = true
}
async function saveFAQ() {
  if (!faqEditing.value) return
  const f = faqEditing.value
  const tags = f.tagsStr.split(',').map((t: string) => t.trim()).filter(Boolean)
  try {
    await fetch(`/api/admin/faq/${f.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'X-Username': 'admin' },
      body: JSON.stringify({ question: f.question, answer: f.answer, category: f.category, tags })
    })
    faqEditVisible.value = false
    faqEditing.value = null
    loadFAQ()
  } catch {}
}

onMounted(async () => {
  if (!isLoggedIn()) {
    router.replace('/login')
    return
  }
  const isAdmin = localStorage.getItem('is_admin') === '1'
  if (!isAdmin) {
    router.replace('/dashboard')
    return
  }
  loadStats()
  loadUsers()
  statsTimer = setInterval(loadStats, 30000)
})
onUnmounted(() => {
  if (statsTimer) clearInterval(statsTimer)
})
</script>

<style scoped>
.admin-dash {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  background:
    radial-gradient(circle at top left, rgba(255, 228, 205, 0.55), transparent 26%),
    linear-gradient(180deg, #fffaf5 0%, #f7efe7 100%);
}

.admin-sidebar {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 22px 18px;
  border-right: 1px solid rgba(203, 171, 149, 0.35);
  background: rgba(255, 252, 248, 0.82);
  backdrop-filter: blur(16px);
}

.as-brand-card,
.as-footer-card,
.as-spotlight,
.panel-card {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(226, 206, 190, 0.95);
  box-shadow: 0 18px 50px rgba(121, 79, 51, 0.08);
}

.as-brand-card {
  border-radius: 22px;
  padding: 18px;
}

.as-brand-top {
  display: flex;
  align-items: center;
  gap: 12px;
}

.as-seal,
.think-seal {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #faf0d7;
  background: linear-gradient(135deg, #c43b3b, #8e3c22);
  font-family: 'STKaiti', '楷体', 'KaiTi', serif;
}

.as-seal {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  font-size: 22px;
  font-weight: 900;
  box-shadow: 0 12px 30px rgba(196, 59, 59, 0.22);
}

.as-name {
  display: block;
  font-size: 17px;
  font-weight: 800;
  color: #5c3a21;
}

.as-desc {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #ae8d74;
}

.as-status-row {
  margin-top: 14px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 12px;
  color: #8f7461;
}

.as-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #3cb179;
  box-shadow: 0 0 0 4px rgba(60, 177, 121, 0.14);
}

.as-status-divider {
  color: #d4baa5;
}

.as-nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.as-item {
  width: 100%;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 12px;
  text-align: left;
  padding: 14px 14px;
  border-radius: 18px;
  cursor: pointer;
  color: #6b5344;
  transition: all 0.22s ease;
}

.as-item:hover {
  background: rgba(250, 240, 232, 0.78);
  transform: translateX(2px);
}

.as-item.active {
  background: linear-gradient(135deg, #fff1e5, #fbe6d8);
  border: 1px solid rgba(230, 182, 154, 0.9);
  color: #bf3f31;
  box-shadow: 0 10px 24px rgba(196, 59, 59, 0.1);
}

.as-item-icon {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  background: rgba(250, 243, 236, 0.95);
  flex-shrink: 0;
}

.as-item.active .as-item-icon {
  background: rgba(255, 255, 255, 0.72);
}

.as-item-text {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.as-item-text strong {
  font-size: 14px;
}

.as-item-text small {
  font-size: 11px;
  color: #a3836a;
}

.as-spotlight {
  border-radius: 22px;
  padding: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.as-spotlight:hover {
  transform: translateY(-2px);
  box-shadow: 0 20px 48px rgba(121, 79, 51, 0.12);
}

.as-spotlight-label {
  display: inline-block;
  margin-bottom: 8px;
  font-size: 11px;
  color: #c43b3b;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(249, 228, 216, 0.95);
}

.as-spotlight strong {
  display: block;
  color: #5c3a21;
  font-size: 16px;
}

.as-spotlight p {
  margin: 6px 0 0;
  font-size: 12px;
  line-height: 1.6;
  color: #9b7e67;
}

.as-spotlight-arrow {
  font-size: 24px;
  color: #c43b3b;
}

.as-footer-card {
  margin-top: auto;
  border-radius: 22px;
  padding: 16px;
}

.as-user-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.as-user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f8d8c4, #efb195);
  color: #7d3426;
  font-weight: 800;
}

.as-user-meta strong {
  display: block;
  color: #5c3a21;
}

.as-user-meta p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #9b7e67;
}

.as-logout {
  width: 100%;
  margin-top: 14px;
  padding: 11px 14px;
  border: 1px solid #eadccf;
  border-radius: 14px;
  background: #fff;
  color: #7a5640;
  cursor: pointer;
  transition: all 0.2s ease;
}

.as-logout:hover {
  border-color: #d98c7b;
  color: #c43b3b;
  background: #fff8f6;
}

.admin-main {
  min-width: 0;
  padding: 26px 30px 34px;
  overflow-y: auto;
}

.admin-topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 24px;
}

.topbar-eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #bf7b59;
}

.admin-topbar h1 {
  margin: 0;
  font-size: 32px;
  color: #5c3a21;
  font-family: 'STKaiti', '楷体', 'KaiTi', serif;
}

.topbar-subtitle {
  display: inline-block;
  margin-top: 8px;
  color: #987960;
  font-size: 14px;
}

.topbar-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.topbar-btn {
  border: none;
  border-radius: 14px;
  padding: 11px 16px;
  cursor: pointer;
  font-size: 14px;
  transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
}

.topbar-btn:hover {
  transform: translateY(-1px);
}

.topbar-btn.primary {
  background: linear-gradient(135deg, #c43b3b, #9a4b2c);
  color: #fff;
  box-shadow: 0 14px 32px rgba(196, 59, 59, 0.2);
}

.topbar-btn.ghost {
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid #eadccf;
  color: #7a5844;
}

.topbar-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.home-shell,
.view-shell {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.home-hero,
.panel-card {
  border-radius: 28px;
}

.home-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(280px, 0.9fr);
  gap: 18px;
  padding: 28px;
}

.home-hero-copy h2,
.section-heading h3 {
  margin: 10px 0 0;
  color: #5c3a21;
  font-family: 'STKaiti', '楷体', 'KaiTi', serif;
}

.home-hero-copy h2 {
  font-size: 32px;
}

.home-hero-copy p {
  margin: 14px 0 0;
  max-width: 720px;
  line-height: 1.8;
  color: #816451;
}

.home-hero-actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.home-hero-side {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.hero-mini-card {
  border-radius: 22px;
  padding: 18px;
  background: linear-gradient(180deg, #fff8f3, #fff);
  border: 1px solid rgba(235, 212, 194, 0.95);
}

.hero-mini-card.warm {
  background: linear-gradient(135deg, #fff2e7, #fff9f5);
}

.hero-mini-card span {
  font-size: 12px;
  color: #bf7b59;
}

.hero-mini-card strong {
  display: block;
  margin-top: 8px;
  font-size: 22px;
  color: #5c3a21;
}

.hero-mini-card p {
  margin: 8px 0 0;
  line-height: 1.7;
  font-size: 13px;
  color: #8f7461;
}

.panel-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: linear-gradient(135deg, #f8dfcf, #fdf2e9);
  color: #c43b3b;
  font-size: 12px;
  font-weight: 700;
}

.panel-badge.soft {
  background: #fbf1e7;
  color: #af6242;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.stats-card {
  padding: 20px;
}

.stats-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.stats-icon {
  width: 42px;
  height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: #fbf1e7;
  font-size: 20px;
}

.stats-trend {
  font-size: 12px;
  color: #b1896e;
}

.stats-card strong {
  display: block;
  font-size: 30px;
  color: #bf3f31;
}

.stats-card span:last-child {
  display: inline-block;
  margin-top: 8px;
  color: #8f7461;
  font-size: 13px;
}

.home-content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.9fr);
  gap: 16px;
}

.quick-panel,
.focus-panel,
.view-shell {
  padding: 24px;
}

.section-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.section-heading h3 {
  font-size: 24px;
}

.section-heading p {
  margin: 8px 0 0;
  color: #9a7a64;
  font-size: 14px;
  line-height: 1.7;
}

.section-heading-spread {
  margin-bottom: 18px;
}

.section-metric {
  padding: 10px 14px;
  border-radius: 14px;
  background: #fbf4ee;
  color: #a26745;
  font-size: 13px;
  white-space: nowrap;
}

.quick-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.quick-item {
  width: 100%;
  border: 1px solid #eadccf;
  background: linear-gradient(180deg, #fffdfb, #fff7f1);
  border-radius: 18px;
  padding: 18px;
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
  text-align: left;
  transition: all 0.22s ease;
}

.quick-item:hover {
  transform: translateX(3px);
  border-color: #d9a68b;
}

.quick-icon {
  font-size: 26px;
}

.quick-item strong {
  display: block;
  color: #5c3a21;
}

.quick-item p {
  margin: 6px 0 0;
  color: #9a7a64;
  font-size: 13px;
}

.quick-arrow {
  margin-left: auto;
  color: #c43b3b;
  font-size: 18px;
}

.focus-list {
  margin: 18px 0 0;
  padding-left: 18px;
  color: #7f624d;
  line-height: 1.9;
}

.toolbar-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
  flex-wrap: wrap;
}

.toolbar-row-split {
  justify-content: space-between;
}

.toolbar-hint {
  color: #ad8870;
  font-size: 12px;
}

.field-input {
  width: 100%;
  min-width: 0;
  padding: 12px 15px;
  border-radius: 14px;
  border: 1px solid #e8d8cb;
  outline: none;
  background: #fefcf9;
  color: #5c3a21;
  transition: all 0.2s ease;
}

.field-input:focus {
  border-color: #d17b58;
  box-shadow: 0 0 0 4px rgba(209, 123, 88, 0.08);
}

.user-list,
.knowledge-list,
.faq-list,
.plaza-visual {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.user-row,
.kb-row,
.faq-row,
.pv-prov {
  border: 1px solid #eadccf;
  border-radius: 18px;
  background: linear-gradient(180deg, #fffefc, #fff9f5);
}

.user-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 180px auto;
  align-items: center;
  gap: 16px;
  padding: 16px 18px;
}

.user-row.disabled {
  opacity: 0.55;
}

.user-main {
  min-width: 0;
}

.ur-name {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  color: #5c3a21;
}

.ur-admin {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 999px;
  background: #fdf0e8;
  color: #c43b3b;
}

.ur-meta,
.ur-time,
.kb-meta,
.faq-a {
  color: #9a7a64;
}

.ur-meta {
  display: block;
  margin-top: 6px;
  font-size: 13px;
}

.ur-time {
  font-size: 13px;
}

.user-actions,
.faq-row-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.chip-btn {
  border: 1px solid #eadccf;
  background: #fff;
  color: #6b5344;
  border-radius: 999px;
  padding: 8px 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.chip-btn:hover {
  border-color: #cf7a59;
  color: #c43b3b;
}

.chip-btn.slim {
  padding: 6px 12px;
  font-size: 12px;
}

.chip-btn.danger:hover {
  border-color: #ff7875;
  color: #ff4d4f;
}

.pv-prov {
  overflow: hidden;
}

.pv-prov-head,
.pv-city-head,
.pv-ad-head {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.pv-prov-head {
  padding: 14px 16px;
  background: linear-gradient(135deg, #fcf5ef, #fff);
}

.pv-prov-name {
  font-weight: 800;
  color: #5c3a21;
}

.pv-prov-arrow,
.pv-city-arrow,
.pv-ad-arrow {
  color: #a98a73;
}

.pv-prov-count {
  color: #c43b3b;
  font-weight: 700;
}

.pv-prov-cities {
  color: #9a7a64;
  font-size: 12px;
}

.pv-cities {
  padding: 0 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.pv-city {
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid #efdfd3;
  background: rgba(255, 255, 255, 0.8);
}

.pv-city-head {
  padding: 12px 14px;
}

.pv-city-name,
.pv-ad-name {
  font-weight: 700;
  color: #6b5344;
}

.pv-city-count {
  margin-left: auto;
  color: #a38168;
}

.pv-attrs {
  padding: 0 12px 12px;
}

.pv-ad-detail {
  border-radius: 14px;
  border: 1px solid #f0e4da;
  background: #fff;
  overflow: hidden;
}

.pv-ad-detail + .pv-ad-detail {
  margin-top: 8px;
}

.pv-ad-head {
  padding: 10px 12px;
  font-size: 13px;
}

.pv-ad-name {
  flex: 1;
  color: #c43b3b;
  cursor: pointer;
}

.pv-ad-count {
  color: #6b5344;
}

.pv-ad-avg {
  color: #a38168;
}

.pv-ad-body {
  border-top: 1px solid #f0e4da;
  padding: 10px 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.pv-ad-row {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: #6b5344;
  line-height: 1.7;
}

.pv-ad-label {
  min-width: 42px;
  color: #a38168;
}

.kb-upload-zone {
  border: 2px dashed #d9af9f;
  border-radius: 22px;
  padding: 30px 20px;
  text-align: center;
  cursor: pointer;
  margin-bottom: 18px;
  background: linear-gradient(180deg, #fffdfb, #fef6f0);
  transition: all 0.2s ease;
}

.kb-upload-zone:hover {
  border-color: #c43b3b;
  background: linear-gradient(180deg, #fff8f3, #fdf0e6);
}

.kb-upload-zone span {
  font-size: 34px;
}

.kb-upload-zone p {
  margin: 8px 0 6px;
  color: #6b5344;
}

.kb-upload-hint {
  font-size: 12px;
  color: #a38168;
}

.kb-progress {
  margin-bottom: 14px;
  padding: 12px 14px;
  border-radius: 14px;
  background: #fff4ea;
  color: #c43b3b;
  font-weight: 700;
}

.kb-row {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
}

.kb-main {
  min-width: 0;
}

.kb-name {
  display: inline-block;
  font-weight: 700;
  color: #c43b3b;
  cursor: pointer;
}

.kb-meta {
  display: block;
  margin-top: 6px;
  font-size: 13px;
}

.kb-tags {
  color: #7b604d;
  font-size: 13px;
}

.kb-count {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 999px;
  background: #fdf0e8;
  color: #c43b3b;
}

.faq-add-form {
  display: grid;
  grid-template-columns: minmax(180px, 1.2fr) minmax(240px, 2fr) 140px 180px auto;
  gap: 10px;
  margin-bottom: 16px;
}

.faq-field,
.faq-field-wide,
.faq-field-small {
  min-width: 0;
}

.faq-submit {
  white-space: nowrap;
}

.faq-categories {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.faq-cat-chip {
  padding: 7px 14px;
  border-radius: 999px;
  border: 1px solid #eadccf;
  background: #fff;
  color: #6b5344;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.faq-cat-chip:hover,
.faq-cat-chip.active {
  border-color: #cf7a59;
  background: #fdf0e8;
  color: #c43b3b;
}

.faq-row {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(180px, auto) auto;
  align-items: center;
  gap: 14px;
  padding: 16px;
}

.faq-row-main {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.faq-q {
  font-weight: 700;
  color: #5c3a21;
}

.faq-row-meta {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.faq-cat-tag,
.faq-tag {
  border-radius: 999px;
  font-size: 11px;
}

.faq-cat-tag {
  padding: 4px 10px;
  background: #fdf0e8;
  color: #c43b3b;
}

.faq-tag {
  padding: 4px 8px;
  background: #faf2eb;
  color: #765b47;
}

.faq-time {
  font-size: 12px;
  color: #b1947a;
}

.faq-edit-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.modal-field {
  margin-bottom: 6px;
}

.textarea-field {
  resize: vertical;
  border-radius: 16px;
}

.detail-loading {
  text-align: center;
  padding: 40px;
}

.think-seal {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  font-size: 24px;
  font-weight: 900;
  margin: 0 auto 12px;
  animation: pulse 2s infinite ease-in-out;
}

.think-dots {
  display: flex;
  gap: 6px;
  justify-content: center;
  margin-bottom: 8px;
}

.think-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d4a89a;
  animation: dotBounce 1.4s infinite ease-in-out both;
}

.think-dots span:nth-child(2) {
  animation-delay: 0.16s;
}

.think-dots span:nth-child(3) {
  animation-delay: 0.32s;
}

.think-text {
  margin: 0;
  text-align: center;
  color: #b08d74;
  font-family: 'STKaiti', '楷体', 'KaiTi', serif;
}

.attr-intro {
  font-size: 15px;
  color: #5c3a21;
  line-height: 2;
}

.attr-intro :deep(h2) {
  font-size: 22px;
  font-weight: 700;
  margin: 20px 0 12px;
  color: #5c3a21;
  border-bottom: 2px solid #eadccf;
  padding-bottom: 8px;
}

.attr-intro :deep(h3) {
  font-size: 18px;
  font-weight: 700;
  margin: 16px 0 8px;
  color: #6b5344;
}

.attr-intro :deep(strong) {
  color: #c43b3b;
}

.attr-intro :deep(li) {
  margin: 4px 0;
}

.attr-intro :deep(ul) {
  padding-left: 20px;
  margin: 8px 0;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.08);
    opacity: 0.72;
  }
}

@keyframes dotBounce {
  0%,
  80%,
  100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  40% {
    opacity: 1;
    transform: scale(1.2);
  }
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .home-content-grid,
  .home-hero {
    grid-template-columns: 1fr;
  }

  .faq-add-form,
  .kb-row,
  .faq-row,
  .user-row {
    grid-template-columns: 1fr;
  }

  .user-actions,
  .faq-row-actions {
    justify-content: flex-start;
  }
}

@media (max-width: 900px) {
  .admin-dash {
    grid-template-columns: 1fr;
  }

  .admin-sidebar {
    border-right: none;
    border-bottom: 1px solid rgba(203, 171, 149, 0.35);
  }

  .admin-main {
    padding: 18px 16px 28px;
  }

  .admin-topbar {
    flex-direction: column;
  }

  .topbar-actions {
    justify-content: flex-start;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .admin-sidebar {
    padding: 14px;
  }

  .as-brand-card,
  .as-spotlight,
  .as-footer-card,
  .home-hero,
  .quick-panel,
  .focus-panel,
  .view-shell {
    border-radius: 20px;
  }

  .as-nav {
    gap: 6px;
  }

  .as-item {
    padding: 12px;
  }

  .section-heading,
  .section-heading-spread {
    flex-direction: column;
  }

  .toolbar-row-split {
    align-items: stretch;
  }
}
</style>
