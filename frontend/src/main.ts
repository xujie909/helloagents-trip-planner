import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import App from './App.vue'
import Login from './views/Login.vue'
import Dashboard from './views/Dashboard.vue'
import AdminDashboard from './views/AdminDashboard.vue'
import DataScreen from './views/DataScreen.vue'
import Result from './views/Result.vue'
import HistoryDetail from './views/HistoryDetail.vue'
import { isLoggedIn } from './services/api'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: Login
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: Dashboard,
      meta: { requiresAuth: true }
    },
    {
      path: '/admin',
      name: 'Admin',
      component: AdminDashboard,
      meta: { requiresAuth: true }
    },
    {
      path: '/datascreen',
      name: 'DataScreen',
      component: DataScreen,
      meta: { requiresAuth: true }
    },
    {
      path: '/result',
      name: 'Result',
      component: Result,
      meta: { requiresAuth: true }
    },
    {
      path: '/history/:id',
      name: 'HistoryDetail',
      component: HistoryDetail,
      meta: { requiresAuth: true }
    },
    {
      path: '/',
      redirect: '/dashboard'
    }
  ]
})

// 路由守卫：未登录跳转到登录页
router.beforeEach((to, _from, next) => {
  if (to.meta.requiresAuth && !isLoggedIn()) {
    next('/login')
  } else if (to.path === '/login' && isLoggedIn()) {
    next('/dashboard')
  } else {
    next()
  }
})

const app = createApp(App)
app.use(router)
app.use(Antd)
app.mount('#app')
