<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <h2>Admin Login</h2>
      </template>
      <el-form :model="loginForm" label-position="top">
        <el-form-item label="Username">
          <el-input v-model="loginForm.username" placeholder="Input the Username" />
        </el-form-item>
        <el-form-item label="Password">
          <el-input v-model="loginForm.password" type="password" placeholder="Input the Password" show-password />
        </el-form-item>
        <el-button type="primary" style="width: 100%" @click="handleLogin">Login</el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
const router = useRouter()
const loginForm = ref({ username: '', password: '' })

const handleLogin = async () => {
  try {
    const res = await axios.post(`/api/login`, loginForm.value);
    if (res.data.status === 'success') {
      localStorage.setItem('isAdminAuthenticated', 'true');
      localStorage.setItem('Username', loginForm.value.username);
      ElMessage.success('Login successful');
      await router.push('/admin');
    }
  } catch (e) {
    // 捕获 401 错误并显示后端返回的错误信息
    const msg = e.response?.data?.message || 'Server error';
    ElMessage.error(msg);
  }
};
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
}
.login-card {
  width: 400px;
}
</style>