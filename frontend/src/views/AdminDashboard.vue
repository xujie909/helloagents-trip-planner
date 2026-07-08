<template>
  <div class="admin-dash">
    <!-- 侧边栏 -->
    <aside class="admin-sidebar">
      <div class="as-brand">
        <span class="as-seal">管</span>
        <div><span class="as-name">管理后台</span><span class="as-desc">知行旅行</span></div>
      </div>
      <nav class="as-nav">
        <div :class="['as-item',{active:view==='home'}]" @click="view='home'"><span>🏠</span> 管理首页</div>
        <div :class="['as-item',{active:view==='users'}]" @click="view='users'"><span>👥</span> 用户管理</div>
        <div :class="['as-item',{active:view==='plaza'}]" @click="view='plaza';loadPlaza()"><span>📊</span> 广场数据</div>
        <div :class="['as-item',{active:view==='knowledge'}]" @click="view='knowledge';loadKnowledge()"><span>📚</span> 知识库</div>
        <div :class="['as-item',{active:view==='faq'}]" @click="view='faq';loadFAQ()"><span>❓</span> FAQ管理</div>
        <div :class="['as-item',{active:view==='sentiment'}]" @click="view='sentiment'"><span>📊</span> 感受度报告</div>
        <div class="as-item ds-link" @click="router.push('/datascreen')"><span>📺</span> 数据大屏</div>
      </nav>
      <div class="as-footer">
        <div class="as-user"><span>👤</span> 管理员</div>
        <button class="as-logout" @click="logout">🚪</button>
      </div>
    </aside>

    <!-- 主内容 -->
    <main class="admin-main">
      <!-- 管理首页 -->
      <div v-if="view==='home'" class="am-home">
        <div class="am-welcome">
          <div class="am-welcome-seal">管</div>
          <div><h1>你好，管理员</h1><p>{{ dateStr }} · 知行旅行管理后台</p></div>
        </div>
        <div class="am-stats">
          <div class="ams-card"><span class="ams-num">{{ stats.user_count }}</span><span class="ams-label">注册用户</span></div>
          <div class="ams-card"><span class="ams-num">{{ stats.trip_count }}</span><span class="ams-label">总行程</span></div>
          <div class="ams-card"><span class="ams-num">{{ (stats.plaza_records||0).toLocaleString() }}</span><span class="ams-label">广场数据</span></div>
          <div class="ams-card"><span class="ams-num">{{ stats.knowledge_count }}</span><span class="ams-label">知识库条目</span></div>
        </div>
        <div class="am-quick">
          <div class="amq-item" @click="view='users'"><span>👥</span><div><strong>用户管理</strong><p>查看、禁用、删除用户账号</p></div><span class="amq-arrow">→</span></div>
          <div class="amq-item" @click="view='plaza';loadPlaza()"><span>📊</span><div><strong>广场数据</strong><p>可视化编辑省份/城市/景点统计</p></div><span class="amq-arrow">→</span></div>
          <div class="amq-item" @click="view='knowledge';loadKnowledge()"><span>📚</span><div><strong>知识库</strong><p>导入文件，AI自动分类归档</p></div><span class="amq-arrow">→</span></div>
        </div>
      </div>

      <!-- 用户管理 -->
      <div v-if="view==='users'" class="am-section">
        <h3>👥 用户管理</h3>
        <div class="asearch"><input v-model="userSearch" placeholder="搜索用户..." class="asearch-inp"/></div>
        <div class="user-list">
          <div v-for="u in filteredUsers" :key="u.username" :class="['user-row',{disabled:u.disabled}]">
            <span class="ur-name">{{ u.username }}<span v-if="u.username==='admin'" class="ur-admin">管理员</span></span>
            <span class="ur-meta">{{ u.trip_count }}行程 · {{ u.chat_count }}对话</span>
            <span class="ur-time">{{ u.last_login?.slice(0,16)||'未登录' }}</span>
            <button class="ur-btn" @click="toggleUser(u)" v-if="u.username!=='admin'">{{ u.disabled?'🔓 启用':'🔒 禁用' }}</button>
            <button class="ur-btn del" @click="deleteUser(u)" v-if="u.username!=='admin'">🗑️</button>
          </div>
        </div>
      </div>

      <!-- 广场数据 -->
      <div v-if="view==='plaza'" class="am-section am-plaza">
        <h3>📊 广场数据</h3>
        <div class="plaza-toolbar">
          <input v-model="plazaSearch" placeholder="搜索省份/城市/景点..." class="asearch-inp" style="flex:1"/>
          <span class="plaza-total">{{ plazaTotal.toLocaleString() }} 条记录</span>
        </div>
        <div class="plaza-visual">
          <div v-for="prov in filteredPlaza" :key="prov.name" class="pv-prov">
            <div class="pv-prov-head" @click="prov._open=!prov._open">
              <span class="pv-prov-arrow">{{ prov._open?'▾':'▸' }}</span>
              <span class="pv-prov-name">{{ prov.name }}</span>
              <span class="pv-prov-count">{{ prov.count.toLocaleString() }}</span>
              <span class="pv-prov-cities">{{ prov.cities?.length||0 }} 城</span>
              <button class="pv-del-btn" @click.stop="deletePlazaProvince(prov.name)">🗑️</button>
            </div>
            <div v-if="prov._open" class="pv-cities">
              <div v-for="city in (prov.cities||[])" :key="city.name" class="pv-city">
                <div class="pv-city-head" @click="city._open=!city._open">
                  <span class="pv-city-arrow">{{ city._open?'▾':'▸' }}</span>
                  <span class="pv-city-name">{{ city.name }}</span>
                  <span class="pv-city-count">{{ city.count.toLocaleString() }}</span>
                </div>
                <div v-if="city._open" class="pv-attrs">
                  <div v-for="a in (city.attractions||[])" :key="a.name" class="pv-ad-detail">
                    <div class="pv-ad-head" @click="a._detail=!a._detail">
                      <span class="pv-ad-name" style="color:#c43b3b;cursor:pointer" @click.stop="viewAttrDetail(a.name,city.name)">{{ a.name }}</span>
                      <span class="pv-ad-count">{{ a.count.toLocaleString() }}</span>
                      <span class="pv-ad-avg">¥{{ a.avg_cost }}</span>
                      <span class="pv-ad-arrow">{{ a._detail?'▾':'▸' }}</span>
                    </div>
                    <div v-if="a._detail" class="pv-ad-body">
                      <div class="pv-ad-row"><span class="pv-ad-label">消费</span><span>均¥{{ a.avg_cost }} · 逗留{{ a.avg_stay }}h · ⭐{{ a.avg_satisfaction }}</span></div>
                      <div class="pv-ad-row"><span class="pv-ad-label">性别</span><span>👨{{ a.gender_dist?.男||0 }} 👩{{ a.gender_dist?.女||0 }}</span></div>
                      <div class="pv-ad-row"><span class="pv-ad-label">年龄</span><span>青年{{ a.age_groups?.['青年(19-30)']||0 }} 中年{{ a.age_groups?.['中年(31-45)']||0 }} 熟龄{{ a.age_groups?.['熟龄(46+)']||0 }}</span></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 知识库 -->
      <div v-if="view==='knowledge'" class="am-section">
        <h3>📚 知识库（{{ knowledge.length }} 条）</h3>
        <div class="kb-upload-zone" @drop.prevent="handleDrop" @dragover.prevent @click="fileInput?.click()">
          <span>📁</span><p>拖拽文件或点击上传</p><span class="kb-upload-hint">PDF · DOCX · TXT · 图片</span>
          <input type="file" ref="fileInput" multiple accept=".pdf,.docx,.txt,.jpg,.jpeg,.png" @change="handleFiles" style="display:none"/>
        </div>
        <div v-if="kbUploading" class="kb-progress">🤖 AI正在解析分类...</div>
        <div class="kb-search"><input v-model="kbSearch" placeholder="搜索知识库..." class="asearch-inp"/></div>
        <div v-for="k in filteredKnowledge" :key="k.id" class="kb-row">
          <span class="kb-name" style="cursor:pointer;color:#c43b3b" @click="viewAttrDetail(k.name,k.city)">{{ k.name }}</span>
          <span class="kb-meta">{{ k.province }} · {{ k.city }} · {{ k.category }}</span>
          <span class="kb-tags">{{ (k.tags||[]).join('、') }}</span>
          <span class="kb-count" v-if="k.count>1">×{{ k.count }}</span>
          <button class="ur-btn del" @click="deleteKnowledge(k.id)">🗑️</button>
        </div>
      </div>

      <!-- 感受度报告 -->
      <SentimentReport v-if="view==='sentiment'" />

      <!-- FAQ管理 -->
      <div v-if="view==='faq'" class="am-section">
        <h3>❓ FAQ 常见问答管理（{{ faqList.length }} 条）</h3>
        <div class="faq-add-form">
          <input v-model="faqForm.question" placeholder="问题 (必填)" class="faq-inp" />
          <input v-model="faqForm.answer" placeholder="答案 (必填)" class="faq-inp faq-inp-ans" />
          <input v-model="faqForm.category" placeholder="分类" class="faq-inp faq-inp-cat" />
          <input v-model="faqForm.tagsStr" placeholder="标签 (逗号分隔)" class="faq-inp faq-inp-tags" />
          <button class="faq-add-btn" @click="addFAQ" :disabled="!faqForm.question||!faqForm.answer">＋ 添加</button>
        </div>
        <div class="faq-categories" v-if="faqCategories.length">
          <span :class="['faq-cat-chip',{active:faqCatFilter===''}]" @click="faqCatFilter=''">全部</span>
          <span v-for="c in faqCategories" :key="c" :class="['faq-cat-chip',{active:faqCatFilter===c}]" @click="faqCatFilter=c">{{ c }}</span>
        </div>
        <div v-for="f in filteredFAQ" :key="f.id" class="faq-row">
          <div class="faq-row-main">
            <span class="faq-q">❓ {{ f.question }}</span>
            <span class="faq-a">💡 {{ f.answer?.slice(0,80) }}{{ f.answer?.length>80?'...':'' }}</span>
          </div>
          <div class="faq-row-meta">
            <span class="faq-cat-tag">{{ f.category }}</span>
            <span v-for="t in (f.tags||[])" :key="t" class="faq-tag">{{ t }}</span>
          </div>
          <div class="faq-row-actions">
            <span class="faq-time">{{ f.created_at?.slice(0,10) }}</span>
            <button class="faq-edit-btn" @click="editFAQ(f)">✏️</button>
            <button class="faq-del-btn" @click="deleteFAQ(f.id)">🗑️</button>
          </div>
        </div>
        <!-- FAQ编辑弹窗 -->
        <a-modal v-model:open="faqEditVisible" title="编辑 FAQ" :footer="null">
          <div class="faq-edit-form" v-if="faqEditing">
            <label>问题</label>
            <input v-model="faqEditing.question" class="faq-inp" style="width:100%;margin-bottom:8px" />
            <label>答案</label>
            <textarea v-model="faqEditing.answer" rows="4" class="faq-inp" style="width:100%;margin-bottom:8px"></textarea>
            <label>分类</label>
            <input v-model="faqEditing.category" class="faq-inp" style="width:100%;margin-bottom:8px" />
            <label>标签 (逗号分隔)</label>
            <input v-model="faqEditing.tagsStr" class="faq-inp" style="width:100%;margin-bottom:12px" />
            <button class="faq-add-btn" @click="saveFAQ">💾 保存</button>
          </div>
        </a-modal>
      </div>
    </main>

    <!-- RAG详情弹窗 -->
    <a-modal v-model:open="detailVisible" :title="'🏛️ '+detailName" width="860px" :footer="null" :bodyStyle="{maxHeight:'70vh',overflowY:'auto',padding:'24px 32px'}">
      <div v-if="detailLoading" style="text-align:center;padding:40px"><div class="think-seal">行</div><div class="think-dots"><span></span><span></span><span></span></div><p class="think-text">行知正在查阅资料...</p></div>
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
const view = ref('home'); const userSearch = ref(''); const kbSearch = ref(''); const plazaSearch = ref('')
const users = ref<any[]>([]); const stats = ref<any>({}); const plazaList = ref<any[]>([]); const knowledge = ref<any[]>([])
const fileInput = ref<HTMLInputElement>(); const kbUploading = ref(false)
const detailVisible=ref(false); const detailName=ref(''); const detailContent=ref(''); const detailLoading=ref(false)
// FAQ
const faqList = ref<any[]>([]); const faqCategories = ref<string[]>([]); const faqCatFilter = ref('')
const faqForm = ref({question:'',answer:'',category:'通用',tagsStr:''})
const faqEditVisible = ref(false); const faqEditing = ref<any>(null)
let statsTimer:any=null

const dateStr = new Date().toLocaleDateString('zh-CN',{year:'numeric',month:'long',day:'numeric',weekday:'long'})

const plazaTotal = computed(() => plazaList.value.reduce((s:number,p:any)=>s+(p.count||0),0))
const filteredPlaza = computed(() => {
  if(!plazaSearch.value) return plazaList.value
  const q=plazaSearch.value.toLowerCase()
  return plazaList.value.filter((p:any)=>{
    if(p.name.toLowerCase().includes(q)) return true
    for(const c of (p.cities||[])){if(c.name.toLowerCase().includes(q)) return true; for(const a of (c.attractions||[])){if(a.name.toLowerCase().includes(q)) return true}}
    return false
  })
})
const filteredUsers = computed(() => userSearch.value?users.value.filter((u:any)=>u.username.includes(userSearch.value)):users.value)
const filteredKnowledge = computed(() => kbSearch.value?knowledge.value.filter((k:any)=>k.name.includes(kbSearch.value)||(k.province||'').includes(kbSearch.value)):knowledge.value)

async function loadStats(){try{const r=await fetch('/api/admin/stats',{headers:{'X-Username':'admin'}});const d=await r.json();if(d.success)stats.value=d.data}catch{}}
async function loadUsers(){try{const r=await fetch('/api/admin/users',{headers:{'X-Username':'admin'}});const d=await r.json();if(d.success)users.value=d.data}catch{}}
async function toggleUser(u:any){await fetch(`/api/admin/users/${u.username}/toggle`,{method:'PUT',headers:{'X-Username':'admin'}});loadUsers()}
async function deleteUser(u:any){if(!confirm(`删除 ${u.username}？`))return;await fetch(`/api/admin/users/${u.username}`,{method:'DELETE',headers:{'X-Username':'admin'}});loadUsers();loadStats()}

async function loadPlaza(){try{const r=await fetch('/api/admin/plaza',{headers:{'X-Username':'admin'}});const d=await r.json();if(d.success)plazaList.value=Object.entries(d.data).filter(([k]:[string,any])=>d.data[k].count>0).sort((a:any,b:any)=>b[1].count-a[1].count).map(([k,v]:[string,any])=>({name:k,...v,_open:false}))}catch{}}
async function deletePlazaProvince(name:string){if(!confirm(`删除 ${name}？`))return;const plaza:any={};for(const p of plazaList.value)if(p.name!==name)plaza[p.name]={count:p.count,cities:p.cities};await fetch('/api/admin/plaza/update',{method:'POST',headers:{'Content-Type':'application/json','X-Username':'admin'},body:JSON.stringify({data:plaza})});loadPlaza();loadStats()}

async function loadKnowledge(){try{const r=await fetch('/api/admin/knowledge',{headers:{'X-Username':'admin'}});const d=await r.json();if(d.success)knowledge.value=d.data}catch{}}
async function deleteKnowledge(id:string){await fetch(`/api/admin/knowledge/${id}`,{method:'DELETE',headers:{'X-Username':'admin'}});loadKnowledge();loadStats()}
async function handleFiles(e:Event){const files=(e.target as HTMLInputElement).files;if(!files?.length)return;await uploadFiles(Array.from(files))}
async function handleDrop(e:DragEvent){const files=e.dataTransfer?.files;if(!files?.length)return;await uploadFiles(Array.from(files))}
async function uploadFiles(files:File[]){kbUploading.value=true;for(const file of files){if(file.size>10*1024*1024){message.warning(`${file.name}>10MB`);continue};const form=new FormData();form.append('file',file);try{const r=await fetch('/api/admin/knowledge/upload',{method:'POST',headers:{'X-Username':'admin'},body:form});const d=await r.json();if(d.success)message.success(`${file.name} 导入成功`)}catch{message.error(`${file.name} 失败`)}};kbUploading.value=false;loadKnowledge();loadStats()}

async function viewAttrDetail(name:string,city:string){detailName.value=name;detailVisible.value=true;detailLoading.value=true;detailContent.value='';try{const r=await fetch(`/api/plaza/attraction/${encodeURIComponent(name)}?city=${encodeURIComponent(city||'')}`);const d=await r.json();if(d.success)detailContent.value=d.data.intro}catch{detailContent.value='获取失败'}finally{detailLoading.value=false}}
function renderMd(t:string):string{if(!t)return'';let h=t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');h=h.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');h=h.replace(/\*(.+?)\*/g,'<em>$1</em>');h=h.replace(/^### (.+)$/gm,'<h4>$1</h4>');h=h.replace(/^## (.+)$/gm,'<h3>$1</h3>');h=h.replace(/^- (.+)$/gm,'<li>$1</li>');h=h.replace(/\n\n/g,'<br><br>');h=h.replace(/\n/g,'<br>');return h}

function logout(){apiLogout();router.replace('/login')}

// --- FAQ 管理 ---
const filteredFAQ = computed(() => {
  if (!faqCatFilter.value) return faqList.value
  return faqList.value.filter((f:any) => f.category === faqCatFilter.value)
})
async function loadFAQ() {
  try { const r = await fetch('/api/admin/faq', { headers: { 'X-Username': 'admin' } }); const d = await r.json()
    if (d.success) { faqList.value = d.data; faqCategories.value = d.categories || [] }
  } catch {}
}
async function addFAQ() {
  const tags = faqForm.value.tagsStr.split(',').map((t:string) => t.trim()).filter(Boolean)
  try {
    const r = await fetch('/api/admin/faq', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Username': 'admin' }, body: JSON.stringify({ question: faqForm.value.question, answer: faqForm.value.answer, category: faqForm.value.category || '通用', tags }) })
    const d = await r.json()
    if (d.success) { faqForm.value = { question: '', answer: '', category: '通用', tagsStr: '' }; loadFAQ(); loadStats() }
  } catch {}
}
async function deleteFAQ(id: string) { if (!confirm('删除此FAQ？')) return; await fetch(`/api/admin/faq/${id}`, { method: 'DELETE', headers: { 'X-Username': 'admin' } }); loadFAQ(); loadStats() }
function editFAQ(f: any) { faqEditing.value = { ...f, tagsStr: (f.tags || []).join(', ') }; faqEditVisible.value = true }
async function saveFAQ() {
  if (!faqEditing.value) return
  const f = faqEditing.value
  const tags = f.tagsStr.split(',').map((t: string) => t.trim()).filter(Boolean)
  try {
    await fetch(`/api/admin/faq/${f.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json', 'X-Username': 'admin' }, body: JSON.stringify({ question: f.question, answer: f.answer, category: f.category, tags }) })
    faqEditVisible.value = false; faqEditing.value = null; loadFAQ()
  } catch {}
}

onMounted(async()=>{
  if(!isLoggedIn()){router.replace('/login');return}
  const isAdmin = localStorage.getItem('is_admin') === '1'
  if(!isAdmin){router.replace('/dashboard');return}
  loadStats();loadUsers();statsTimer=setInterval(loadStats,30000)
})
onUnmounted(()=>{if(statsTimer)clearInterval(statsTimer)})
</script>

<style scoped>
.admin-dash{display:flex;height:100vh;background:#faf7f2}
.admin-sidebar{width:220px;background:#fff;border-right:1px solid #eadccf;display:flex;flex-direction:column;flex-shrink:0}
.as-brand{display:flex;align-items:center;gap:10px;padding:22px 16px;border-bottom:1px solid #eadccf}
.as-seal{width:38px;height:38px;border-radius:6px;background:#c43b3b;color:#faf0d7;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:900;font-family:'STKaiti','楷体','KaiTi',serif}
.as-name{font-size:15px;font-weight:700;color:#5c3a21;display:block}.as-desc{font-size:11px;color:#b8a088}
.as-nav{flex:1;padding:12px 10px;display:flex;flex-direction:column;gap:2px}
.as-item{display:flex;align-items:center;gap:8px;padding:12px 14px;border-radius:10px;cursor:pointer;font-size:14px;color:#6b5344;transition:all .2s}
.as-item:hover{background:#faf7f2;color:#5c3a21}.as-item.active{background:#fdf0e8;color:#c43b3b;font-weight:600;border:1px solid #f0d5c0}
.as-item.ds-link{border-top:1px solid #eadccf;margin-top:8px;padding-top:14px}
.as-footer{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-top:1px solid #eadccf;font-size:14px}
.as-logout{padding:4px 10px;border:1px solid #eadccf;border-radius:10px;background:#fff;cursor:pointer;font-size:16px}.as-logout:hover{background:#fde8e8}

.admin-main{flex:1;overflow-y:auto;padding:28px 36px}

.am-home{max-width:800px}
.am-welcome{display:flex;align-items:center;gap:16px;padding:32px;background:linear-gradient(135deg,#fdf5ee,#fef9f4);border:1px solid #e8d0bf;border-radius:18px;margin-bottom:24px}
.am-welcome-seal{width:52px;height:52px;border-radius:8px;background:#c43b3b;color:#faf0d7;display:flex;align-items:center;justify-content:center;font-size:26px;font-weight:900;font-family:'STKaiti','楷体','KaiTi',serif;animation:sealIn .5s cubic-bezier(.34,1.56,.64,1) both}
@keyframes sealIn{from{transform:scale(0)rotate(-15deg);opacity:0}to{transform:scale(1)rotate(0);opacity:1}}
.am-welcome h1{font-size:22px;color:#5c3a21;margin:0;font-family:'STKaiti','楷体','KaiTi',serif}.am-welcome p{font-size:13px;color:#b8a088;margin:4px 0 0}

.am-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px}
.ams-card{text-align:center;padding:20px;background:#fff;border:1px solid #eadccf;border-radius:14px;transition:transform .2s}
.ams-card:hover{transform:translateY(-3px);box-shadow:0 3px 12px rgba(139,69,19,.06)}
.ams-num{font-size:28px;font-weight:800;color:#c43b3b;display:block}.ams-label{font-size:12px;color:#b8a088}

.am-quick{display:flex;flex-direction:column;gap:8px}
.amq-item{display:flex;align-items:center;gap:14px;padding:18px 20px;background:#fff;border:1px solid #eadccf;border-radius:14px;cursor:pointer;transition:all .2s}
.amq-item:hover{transform:translateX(4px);border-color:#c43b3b;box-shadow:0 2px 10px rgba(196,59,59,.06)}
.amq-item span{font-size:28px}.amq-item strong{font-size:15px;color:#5c3a21;display:block}.amq-item p{font-size:12px;color:#b8a088;margin:2px 0 0}.amq-arrow{font-size:18px;color:#d4c5b5;margin-left:auto}

.am-section{background:#fff;border:1px solid #eadccf;border-radius:14px;padding:24px;max-height:calc(100vh - 120px);overflow-y:auto}
.am-section h3{font-size:18px;color:#5c3a21;margin:0 0 16px;font-family:'STKaiti','楷体','KaiTi',serif}

.asearch{margin-bottom:14px}.asearch-inp{width:100%;padding:10px 16px;border:2px solid #eadccf;border-radius:10px;font-size:14px;outline:none;background:#fefcf8}.asearch-inp:focus{border-color:#c43b3b}
.user-list{display:flex;flex-direction:column;gap:4px}
.user-row{display:flex;align-items:center;gap:12px;padding:10px 14px;border-radius:8px;font-size:14px}.user-row:hover{background:#faf7f2}.user-row.disabled{opacity:.5}
.ur-name{font-weight:600;color:#5c3a21;min-width:100px}.ur-admin{font-size:11px;background:#fdf0e8;color:#c43b3b;padding:1px 6px;border-radius:6px;margin-left:6px}
.ur-meta{flex:1;color:#b8a088;font-size:13px}.ur-time{color:#b8a088;font-size:12px;width:130px}
.ur-btn{padding:4px 12px;border:1px solid #eadccf;border-radius:14px;background:#fff;color:#6b5344;font-size:12px;cursor:pointer;font-family:'STKaiti','楷体','KaiTi',serif}.ur-btn:hover{border-color:#c43b3b;color:#c43b3b}.ur-btn.del:hover{border-color:#ff4d4f;color:#ff4d4f}

.plaza-toolbar{display:flex;align-items:center;gap:10px;margin-bottom:14px}.plaza-total{font-size:13px;color:#b8a088;white-space:nowrap}
.plaza-visual{display:flex;flex-direction:column;gap:6px}
.pv-prov{background:#faf7f2;border:1px solid #eadccf;border-radius:10px;overflow:hidden}
.pv-prov-head{display:flex;align-items:center;gap:10px;padding:10px 14px;cursor:pointer;font-size:14px}.pv-prov-head:hover{background:#f5f0eb}
.pv-prov-arrow{color:#b8a088}.pv-prov-name{font-weight:700;color:#5c3a21;min-width:50px}.pv-prov-count{color:#c43b3b;font-weight:600}.pv-prov-cities{color:#b8a088;font-size:12px}
.pv-del-btn{padding:2px 8px;border:1px solid #eadccf;border-radius:10px;background:#fff;color:#b8a088;font-size:12px;cursor:pointer;margin-left:auto}.pv-del-btn:hover{color:#ff4d4f;border-color:#ff4d4f}
.pv-cities{padding:0 14px 10px;display:flex;flex-direction:column;gap:4px}
.pv-city{background:#fff;border:1px solid #eadccf;border-radius:8px;overflow:hidden}
.pv-city-head{display:flex;align-items:center;gap:8px;padding:8px 10px;cursor:pointer;font-size:13px}.pv-city-head:hover{background:#fefcf8}
.pv-city-arrow{color:#b8a088;font-size:12px}.pv-city-name{font-weight:600;color:#6b5344}.pv-city-count{color:#b8a088;margin-left:auto}
.pv-ad-detail{background:#fff;border:1px solid #eadccf;border-radius:6px;overflow:hidden;margin:2px 0}
.pv-ad-head{display:flex;align-items:center;gap:8px;padding:6px 10px;cursor:pointer;font-size:12px}.pv-ad-head:hover{background:#fefcf8}
.pv-ad-name{font-weight:600;flex:1}.pv-ad-count{color:#6b5344}.pv-ad-avg{color:#b8a088}.pv-ad-arrow{color:#b8a088}
.pv-ad-body{padding:6px 10px 8px;border-top:1px solid #eadccf;display:flex;flex-direction:column;gap:3px}
.pv-ad-row{display:flex;gap:6px;font-size:11px;color:#6b5344}.pv-ad-label{color:#b8a088;min-width:40px;flex-shrink:0}

.kb-upload-zone{border:2px dashed #d4a89a;border-radius:12px;padding:24px;text-align:center;cursor:pointer;margin-bottom:16px;background:#fefcf8}.kb-upload-zone:hover{border-color:#c43b3b;background:#fdf5ee}
.kb-upload-zone span{font-size:32px}.kb-upload-zone p{font-size:14px;color:#6b5344;margin:4px 0}.kb-upload-hint{font-size:11px;color:#b8a088}
.kb-progress{text-align:center;padding:12px;color:#c43b3b;font-weight:600;animation:pulse 1.5s infinite}
.kb-search{margin-bottom:10px}
.kb-row{display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:8px;font-size:13px}.kb-row:hover{background:#faf7f2}
.kb-name{font-weight:600;color:#5c3a21;min-width:80px}.kb-meta{color:#b8a088}.kb-tags{flex:1;color:#6b5344}.kb-count{font-size:11px;background:#fdf0e8;color:#c43b3b;padding:1px 6px;border-radius:8px}

.think-seal{width:48px;height:48px;border-radius:10px;background:#c43b3b;color:#faf0d7;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:900;font-family:'STKaiti','楷体','KaiTi',serif;margin:0 auto 12px;animation:pulse 2s infinite ease-in-out}
@keyframes pulse{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(1.08);opacity:.7}}
.think-dots{display:flex;gap:6px;justify-content:center;margin-bottom:8px}
.think-dots span{width:8px;height:8px;border-radius:50%;background:#d4a89a;animation:dotBounce 1.4s infinite ease-in-out both}
.think-dots span:nth-child(2){animation-delay:.16s}.think-dots span:nth-child(3){animation-delay:.32s}
@keyframes dotBounce{0%,80%,100%{opacity:.3;transform:scale(.8)}40%{opacity:1;transform:scale(1.2)}}
.think-text{font-size:15px;color:#b8a088;font-family:'STKaiti','楷体','KaiTi',serif;margin:0;text-align:center}
.attr-intro{font-size:15px;color:#5c3a21;line-height:2}
.attr-intro :deep(h2){font-size:22px;font-weight:700;margin:20px 0 12px;color:#5c3a21;border-bottom:2px solid #eadccf;padding-bottom:8px}
.attr-intro :deep(h3){font-size:18px;font-weight:700;margin:16px 0 8px;color:#6b5344}
.attr-intro :deep(strong){color:#c43b3b}.attr-intro :deep(li){margin:4px 0}.attr-intro :deep(ul){padding-left:20px;margin:8px 0}

/* FAQ样式 */
.faq-add-form{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.faq-inp{padding:8px 12px;border:2px solid #eadccf;border-radius:10px;font-size:13px;outline:none;background:#fefcf8;flex:1;min-width:140px}.faq-inp:focus{border-color:#c43b3b}
.faq-inp-ans{flex:2}.faq-inp-cat{flex:0 0 80px}.faq-inp-tags{flex:0 0 120px}
.faq-add-btn{padding:8px 18px;border:none;border-radius:10px;background:linear-gradient(135deg,#c43b3b,#a0522d);color:#fff;font-weight:600;cursor:pointer;white-space:nowrap;font-family:'STKaiti','楷体','KaiTi',serif}.faq-add-btn:disabled{opacity:.4;cursor:not-allowed}
.faq-categories{display:flex;gap:6px;margin-bottom:14px;flex-wrap:wrap}
.faq-cat-chip{padding:4px 14px;border-radius:14px;border:1px solid #eadccf;font-size:12px;cursor:pointer;color:#6b5344;background:#fff;transition:all .2s}.faq-cat-chip:hover{border-color:#c43b3b}.faq-cat-chip.active{background:#fdf0e8;border-color:#c43b3b;color:#c43b3b;font-weight:600}
.faq-row{display:flex;align-items:center;gap:12px;padding:12px;border:1px solid #eadccf;border-radius:10px;margin-bottom:6px;background:#fff}.faq-row:hover{background:#fefcf8}
.faq-row-main{flex:1;display:flex;flex-direction:column;gap:4px;min-width:0}
.faq-q{font-weight:600;color:#5c3a21;font-size:14px}.faq-a{font-size:12px;color:#b8a088}
.faq-row-meta{display:flex;gap:4px;flex-wrap:wrap;min-width:120px}
.faq-cat-tag{font-size:11px;padding:2px 8px;background:#fdf0e8;color:#c43b3b;border-radius:10px;font-weight:600}
.faq-tag{font-size:10px;padding:1px 6px;background:#faf7f2;color:#6b5344;border-radius:8px}
.faq-row-actions{display:flex;align-items:center;gap:6px;flex-shrink:0}
.faq-time{font-size:11px;color:#d4c5b5}
.faq-edit-btn,.faq-del-btn{padding:4px 8px;border:1px solid #eadccf;border-radius:8px;background:#fff;font-size:14px;cursor:pointer}.faq-edit-btn:hover{border-color:#c43b3b;color:#c43b3b}.faq-del-btn:hover{border-color:#ff4d4f;color:#ff4d4f}

@media(max-width:767px){.admin-dash{flex-direction:column}.admin-sidebar{width:100%;flex-direction:row;overflow-x:auto;padding:8px;gap:4px}.as-brand,.as-footer{display:none}.as-nav{flex-direction:row}.as-item{font-size:12px;padding:8px 10px;white-space:nowrap}.admin-main{padding:16px}.am-stats{grid-template-columns:repeat(2,1fr)}.faq-add-form{flex-direction:column}.faq-inp-cat,.faq-inp-tags{flex:1}}
</style>
