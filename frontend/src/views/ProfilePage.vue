<template>
  <div class="profile-root">
    <!-- 顶部个人信息卡 -->
    <div class="pf-hero">
      <div class="pf-hero-bg"></div>
      <div class="pf-hero-content">
        <div class="pf-avatar-area">
          <div class="pf-avatar-circle" @click="cycleAvatar" v-if="!customAvatar">
            <span class="pf-avatar-emoji">{{ currentAvatar }}</span>
            <div class="pf-avatar-overlay"><span>点击换</span></div>
          </div>
          <div class="pf-avatar-circle custom" v-else>
            <img :src="customAvatar" class="pf-avatar-img"/>
            <div class="pf-avatar-overlay" @click="removeAvatar"><span>移除</span></div>
          </div>
          <label class="pf-upload-link">
            <input type="file" accept="image/*" @change="uploadAvatar" style="display:none"/>
            📷 {{ customAvatar ? '换照片' : '上传头像' }}
          </label>
        </div>
        <div class="pf-hero-info">
          <input v-model="displayName" class="pf-hero-name" @blur="saveName" placeholder="你的名字"/>
          <span class="pf-hero-id">@{{ username }}</span>
        </div>
      </div>
    </div>

    <!-- 偏好表单 -->
    <div class="pf-card">
      <div class="pf-card-title"><span class="pf-dot"></span>旅行偏好</div>
      <p class="pf-card-desc">完善以下信息，AI 助手将为你提供更精准的个性化建议</p>

      <div class="pf-grid">
        <div class="pf-field">
          <label>性别</label>
          <div class="pf-radio-group">
            <div :class="['pf-radio',{on:pGender==='男'}]" @click="pGender='男';autoSave()">👨 男</div>
            <div :class="['pf-radio',{on:pGender==='女'}]" @click="pGender='女';autoSave()">👩 女</div>
          </div>
        </div>
        <div class="pf-field">
          <label>年龄</label>
          <input v-model="pAge" class="pf-inp" placeholder="如：28岁 / 90后" @blur="autoSave"/>
        </div>
      </div>

      <div class="pf-field">
        <label>为什么旅行</label>
        <textarea v-model="pMotivation" class="pf-textarea" placeholder="说说你为什么喜欢旅行？放松身心、探索未知、还是寻找美食..." rows="2" @blur="autoSave"></textarea>
      </div>

      <div class="pf-field">
        <label>旅行习惯</label>
        <div class="pf-tags">
          <span v-for="h in allHabits" :key="h" :class="['pf-tag',{on:currentHabits.includes(h)}]" @click="toggleHabit(h)">{{ h }}<i class="pf-tag-del" @click.stop="removeHabitOption(h)">×</i></span>
          <span v-if="!addingHabit" class="pf-tag pf-tag-add" @click="addingHabit=true">＋ 新增标签</span>
          <input v-else ref="newHabitInp" v-model="customHabit" class="pf-tag-inp" placeholder="输入标签名" @keydown.enter="addCustomHabit" @blur="cancelAddHabit"/>
        </div>
      </div>

      <div class="pf-field">
        <label>通常和谁一起旅行</label>
        <input v-model="pCompanion" class="pf-inp" placeholder="如：独自一人 / 和伴侣 / 和三五好友 / 带家人" @blur="autoSave"/>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getStoredUser, getUserProfile, saveUserProfile } from '@/services/api'
import { message } from 'ant-design-vue'

const avatars = ['😊','🌟','🎒','🗺️','🏔️','🌊','🎯','✈️','🌍','🧳','🏮','🌸','🍜','🎨','🚲','🏕️']
const habitOptions = ref<string[]>([])
const username = ref(getStoredUser().username || '')
const displayName = ref(getStoredUser().name || getStoredUser().username || '行者')
const currentAvatar = ref(avatars[0]); const customAvatar = ref('')
const pGender = ref(''); const pAge = ref('')
const pMotivation = ref(''); const pHabits = ref(''); const pCompanion = ref('')
const customHabit = ref(''); const addingHabit = ref(false); const newHabitInp = ref<HTMLInputElement>()

const currentHabits = computed(() => pHabits.value ? pHabits.value.split('、').filter(Boolean) : [])
const allHabits = computed(() => {
  const set = new Set([...habitOptions.value, ...currentHabits.value])
  return [...set]
})
function removeHabitOption(h: string) {
  habitOptions.value = habitOptions.value.filter(x => x !== h)
  pHabits.value = currentHabits.value.filter(x => x !== h).join('、')
  autoSave()
}

function removeAvatar() { customAvatar.value = ''; localStorage.removeItem('user_avatar_img'); saveProfile() }

function cycleAvatar() {
  const idx = avatars.indexOf(currentAvatar.value)
  currentAvatar.value = avatars[(idx + 1) % avatars.length]
  localStorage.setItem('user_avatar', currentAvatar.value)
  saveProfile()
}
function uploadAvatar(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  const file = input.files[0]
  if (file.size > 2*1024*1024) { message.warning('图片不超过2MB'); return }
  const reader = new FileReader()
  reader.onload = () => { customAvatar.value = reader.result as string; localStorage.setItem('user_avatar_img', customAvatar.value); saveProfile() }
  reader.readAsDataURL(file)
}

async function saveName() {
  if (!displayName.value.trim()) return
  const name = displayName.value.trim()
  localStorage.setItem('display_name', name)
  localStorage.setItem('user_name', name)
  try {
    const uname = localStorage.getItem('username') || ''
    await fetch('/api/auth/update-name', { method:'PUT', headers:{'Content-Type':'application/json','X-Username':uname}, body:JSON.stringify({name, username:uname}) })
    message.success('名字已更新，AI助手会立即知晓')
  } catch {}
}

let saveTimer: any = null
function autoSave() { clearTimeout(saveTimer); saveTimer = setTimeout(saveProfile, 500) }
async function saveProfile() {
  try {
    await saveUserProfile({
      gender: pGender.value,
      age: pAge.value,
      motivation: pMotivation.value,
      habits: pHabits.value,
      companion: pCompanion.value,
    })
  } catch {}
}
function toggleHabit(h: string) {
  const arr = pHabits.value ? pHabits.value.split('、').filter(Boolean) : []
  const idx = arr.indexOf(h)
  if (idx >= 0) arr.splice(idx, 1); else arr.push(h)
  pHabits.value = arr.join('、')
  autoSave()
}
function cancelAddHabit() { addingHabit.value = false; customHabit.value = '' }
function addCustomHabit() {
  const v = customHabit.value.trim(); if (!v) { cancelAddHabit(); return }
  const arr = pHabits.value ? pHabits.value.split('、').filter(Boolean) : []
  if (!arr.includes(v)) { arr.push(v); if (!habitOptions.value.includes(v)) habitOptions.value.push(v) }
  pHabits.value = arr.join('、')
  customHabit.value = ''; addingHabit.value = false
  autoSave()
}

async function loadProfile() {
  try {
    const d = await getUserProfile()
    if (d.data?.filled) {
      pGender.value = d.data.gender || ''
      pAge.value = d.data.age || ''
      pMotivation.value = d.data.motivation || ''
      pHabits.value = d.data.habits || ''
      pCompanion.value = d.data.companion || ''
    }
  } catch {}
  const saved = localStorage.getItem('user_avatar'); if (saved) currentAvatar.value = saved
  const savedImg = localStorage.getItem('user_avatar_img'); if (savedImg) customAvatar.value = savedImg
  const dn = localStorage.getItem('display_name')||localStorage.getItem('user_name'); if (dn) displayName.value = dn
}

onMounted(loadProfile)
</script>

<style scoped>
.profile-root{padding:24px 32px;max-width:640px;margin:0 auto;animation:viewIn .35s ease-out both}
@keyframes viewIn{from{opacity:0;transform:scale(.98) translateY(6px)}to{opacity:1;transform:scale(1) translateY(0)}}

/* 个人信息卡 */
.pf-hero{position:relative;border-radius:20px;overflow:hidden;margin-bottom:24px;box-shadow:0 4px 20px rgba(139,69,19,.08)}
.pf-hero-bg{position:absolute;inset:0;background:linear-gradient(135deg,#c43b3b 0%,#8b4513 100%)}
.pf-hero-content{position:relative;z-index:1;display:flex;align-items:center;gap:24px;padding:36px 32px}
.pf-avatar-area{display:flex;flex-direction:column;align-items:center;gap:10px}
.pf-avatar-circle{width:80px;height:80px;border-radius:50%;background:rgba(255,255,255,.2);display:flex;align-items:center;justify-content:center;cursor:pointer;position:relative;overflow:hidden;border:3px solid rgba(255,255,255,.4);transition:all .2s}
.pf-avatar-circle:hover{border-color:#fff}
.pf-avatar-circle.custom{border-color:#fff}
.pf-avatar-emoji{font-size:40px}.pf-avatar-img{width:100%;height:100%;object-fit:cover}
.pf-avatar-overlay{position:absolute;inset:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;opacity:0;transition:opacity .2s;color:#fff;font-size:12px}
.pf-avatar-circle:hover .pf-avatar-overlay{opacity:1}
.pf-upload-link{font-size:12px;color:rgba(255,255,255,.8);cursor:pointer;transition:color .2s}.pf-upload-link:hover{color:#fff}
.pf-hero-info{display:flex;flex-direction:column;gap:4px}
.pf-hero-name{font-size:26px;font-weight:700;color:#fff;border:none;background:transparent;padding:4px 8px;border-radius:8px;outline:none;width:200px;border-bottom:2px dashed rgba(255,255,255,.3);transition:border-color .2s}
.pf-hero-name:focus{border-bottom-color:#fff;background:rgba(255,255,255,.1)}
.pf-hero-id{font-size:14px;color:rgba(255,255,255,.7)}

/* 偏好卡片 */
.pf-card{background:#fff;border:1px solid #eadccf;border-radius:16px;padding:28px 32px;box-shadow:0 2px 12px rgba(139,69,19,.04)}
.pf-card-title{display:flex;align-items:center;gap:8px;font-size:18px;font-weight:700;color:#5c3a21;margin-bottom:4px;font-family:'STKaiti','楷体','KaiTi',serif}
.pf-dot{width:8px;height:8px;border-radius:50%;background:#c43b3b}
.pf-card-desc{font-size:13px;color:#b8a088;margin:0 0 24px}

.pf-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:4px}
.pf-field{margin-bottom:20px}.pf-field label{display:block;font-size:14px;font-weight:600;color:#5c3a21;margin-bottom:8px;font-family:'STKaiti','楷体','KaiTi',serif}
.pf-inp{width:100%;padding:10px 14px;border:2px solid #eadccf;border-radius:10px;font-size:15px;color:#5c3a21;background:#fefcf8;outline:none;transition:border-color .2s;box-sizing:border-box}
.pf-inp:focus{border-color:#c43b3b;background:#fff}
.pf-textarea{width:100%;padding:10px 14px;border:2px solid #eadccf;border-radius:10px;font-size:15px;color:#5c3a21;background:#fefcf8;outline:none;resize:vertical;font-family:inherit;transition:border-color .2s;box-sizing:border-box}
.pf-textarea:focus{border-color:#c43b3b;background:#fff}

.pf-radio-group{display:flex;gap:8px}
.pf-radio{padding:10px 20px;border:2px solid #eadccf;border-radius:10px;cursor:pointer;font-size:15px;transition:all .2s;background:#fff}
.pf-radio:hover{border-color:#c43b3b}.pf-radio.on{background:#fdf0e8;border-color:#c43b3b;color:#c43b3b;font-weight:600}

.pf-tags{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.pf-tag{padding:8px 16px;border:2px solid #eadccf;border-radius:20px;cursor:pointer;font-size:14px;transition:all .2s;background:#fff}
.pf-tag:hover{border-color:#c43b3b}.pf-tag.on{background:#fdf0e8;border-color:#c43b3b;color:#c43b3b;font-weight:600}
.pf-tag-inp{padding:8px 14px;border:2px dashed #eadccf;border-radius:20px;font-size:14px;outline:none;width:120px;background:transparent}.pf-tag-inp:focus{border-color:#c43b3b}
.pf-tag-add{padding:8px 16px;border:2px dashed #d4a89a;border-radius:20px;cursor:pointer;font-size:14px;color:#b8a088;background:transparent;transition:all .2s}.pf-tag-add:hover{border-color:#c43b3b;color:#c43b3b}
.pf-tag-del{font-style:normal;margin-left:4px;font-size:12px;color:#ccc;cursor:pointer}.pf-tag-del:hover{color:#ff4d4f}

@media(max-width:767px){.profile-root{padding:16px}.pf-grid{grid-template-columns:1fr}.pf-hero-content{flex-direction:column;text-align:center;padding:28px 20px}}
</style>
