<template>
  <div class="login-page">
    <div class="login-bg-img"></div>
    <div class="login-overlay"></div>
    <div class="float-orb orb-1"></div>
    <div class="float-orb orb-2"></div>
    <div class="float-orb orb-3"></div>

    <div class="login-center">
      <div class="login-brand-top">
        <span class="brand-seal">行</span>
        <h1>知行旅行</h1>
        <p>读万卷书 · 行万里路</p>
      </div>

      <div class="login-card">
        <div class="card-header">
          <h2>{{ isRegister ? '创建账号' : '欢迎回来' }}</h2>
          <p class="card-subtitle">{{ isRegister ? '系统将自动为你生成一个独特的旅行者昵称' : '登录你的账号，继续探索旅途' }}</p>
        </div>

        <a-form :model="form" @finish="handleSubmit" layout="vertical" class="login-form">
          <a-form-item name="username" :rules="[{ required: true, message: '请输入用户名' }]">
            <a-input v-model:value="form.username" placeholder="用户名" size="large">
              <template #prefix><span class="input-icon">👤</span></template>
            </a-input>
          </a-form-item>

          <a-form-item name="password" :rules="[{ required: true, message: '请输入密码' }]">
            <a-input-password v-model:value="form.password" placeholder="密码" size="large">
              <template #prefix><span class="input-icon">🔒</span></template>
            </a-input-password>
          </a-form-item>

          <a-form-item>
            <a-button type="primary" html-type="submit" block size="large" :loading="loading" class="submit-btn">
              {{ isRegister ? '注 册' : '登 录' }}
            </a-button>
          </a-form-item>
        </a-form>

        <div class="card-footer">
          <span v-if="!isRegister">还没有账号？<a @click="isRegister=true;form.password=''">立即注册</a></span>
          <span v-else>已有账号？<a @click="isRegister=false;form.password=''">返回登录</a></span>
        </div>
      </div>

      <p class="login-hint">🌍 探索中国，从知行开始</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { login, register } from '@/services/api'

const router = useRouter()
const loading = ref(false)
const isRegister = ref(false)
const form = reactive({ username: '', password: '' })

async function handleSubmit() {
  if (!form.username.trim() || !form.password.trim()) return
  loading.value = true
  try {
    if (isRegister.value) {
      await register(form.username.trim(), form.password.trim())
      message.success('注册成功！系统已为你生成旅行者昵称 ✨')
      isRegister.value = false; form.password = ''
    } else {
      await login(form.username.trim(), form.password.trim())
      message.success('登录成功')
      // 只有后端明确返回 is_admin 才跳管理后台
      if (localStorage.getItem('is_admin') === '1') { router.replace('/admin'); return }
      router.replace('/dashboard')
    }
  } catch (err: any) {
    message.error(err.response?.data?.detail || err.message || '操作失败')
  } finally { loading.value = false }
}
</script>

<style scoped>
.login-page{min-height:100vh;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden}
.login-bg-img{position:absolute;inset:0;background:url('/login-bg.png') center/cover no-repeat;filter:brightness(.45)}
.login-overlay{position:absolute;inset:0;background:radial-gradient(ellipse at center,transparent 40%,rgba(0,0,0,.4) 100%)}
.float-orb{position:absolute;border-radius:50%;background:rgba(255,255,255,.06);backdrop-filter:blur(10px);animation:float 8s infinite ease-in-out}
.orb-1{width:300px;height:300px;top:-80px;left:-80px}.orb-2{width:200px;height:200px;bottom:-40px;right:-40px;animation-delay:2s}.orb-3{width:150px;height:150px;top:40%;left:10%;animation-delay:4s}
@keyframes float{0%,100%{transform:translateY(0)scale(1)}50%{transform:translateY(-30px)scale(1.05)}}

.login-center{display:flex;flex-direction:column;align-items:center;position:relative;z-index:2;width:420px;max-width:92vw}

.login-brand-top{text-align:center;margin-bottom:28px;animation:fadeDown .8s ease-out both}
@keyframes fadeDown{from{opacity:0;transform:translateY(-20px)}to{opacity:1;transform:translateY(0)}}
.brand-seal{display:inline-flex;width:56px;height:56px;border-radius:12px;background:#c43b3b;color:#faf0d7;align-items:center;justify-content:center;font-size:28px;font-weight:900;font-family:'STKaiti','楷体','KaiTi',serif;margin-bottom:12px;animation:sealIn .6s cubic-bezier(.34,1.56,.64,1) both}
@keyframes sealIn{from{transform:scale(0)rotate(-15deg);opacity:0}to{transform:scale(1)rotate(0);opacity:1}}
.login-brand-top h1{font-size:30px;font-weight:800;color:#fff;margin:0;text-shadow:0 2px 12px rgba(0,0,0,.3);font-family:'STKaiti','楷体','KaiTi',serif}
.login-brand-top p{font-size:16px;color:rgba(255,255,255,.8);margin:4px 0 0}

.login-card{width:100%;padding:40px 36px 32px;background:rgba(255,255,255,.95);backdrop-filter:blur(20px);border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,.25);animation:fadeUp .8s ease-out .2s both}
@keyframes fadeUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
.card-header{text-align:center;margin-bottom:28px}
.card-header h2{font-size:24px;font-weight:700;color:#1a1a1a;margin:0}
.card-subtitle{font-size:14px;color:#999;margin:6px 0 0}
.login-form :deep(.ant-form-item){margin-bottom:18px}
.login-form :deep(.ant-input-affix-wrapper){border-radius:12px;border:2px solid #e8e8e8;padding:10px 14px;font-size:15px;transition:all .3s}
.login-form :deep(.ant-input-affix-wrapper:hover){border-color:#c43b3b}
.login-form :deep(.ant-input-affix-wrapper-focused){border-color:#c43b3b;box-shadow:0 0 0 4px rgba(196,59,59,.08)}
.input-icon{font-size:16px}
.submit-btn{height:48px!important;border-radius:12px!important;font-size:17px!important;font-weight:600!important;background:linear-gradient(135deg,#c43b3b,#a0522d)!important;border:none!important;margin-top:6px!important;transition:all .3s!important;color:#fff!important}
.submit-btn:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(196,59,59,.35)!important}
.card-footer{text-align:center;font-size:14px;color:#999;margin-top:4px}
.card-footer a{color:#c43b3b;font-weight:600;cursor:pointer;transition:color .2s}
.card-footer a:hover{color:#a0522d}
.login-hint{font-size:13px;color:rgba(255,255,255,.6);margin-top:20px;animation:fadeUp .8s ease-out .4s both}
@media(max-width:480px){.login-card{padding:28px 20px 24px}.login-brand-top h1{font-size:24px}}
</style>
