import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import Admin from './views/Admin.vue'
import Login from './views/Login.vue'
import ChangePassword from './views/ChangePassword.vue'
const routes = [
  { path: '/', component: Home },
  { path: '/login', component: Login },
  { 
    path: '/change-password', 
    component: ChangePassword, 
    meta: { requiresAuth: true } 
  },
  { path: '/admin', component: Admin, meta: { requiresAuth: true } } // 标记需要登录
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('isAdminAuthenticated') === 'true';
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login'); // 未登录则强制去登录页
  } else {
    next();
  }
});

export default router