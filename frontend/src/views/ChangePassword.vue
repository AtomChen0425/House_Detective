<template>
  <div class="change-password-container">
    <el-card class="password-card" header="Update Password">
      <el-form :model="form" label-position="top">
        <el-form-item label="Current User">
          <el-input v-model="username" disabled />
        </el-form-item>
        <el-form-item label="Old Password">
          <el-input v-model="form.oldPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="New Password">
          <el-input v-model="form.newPassword" type="password" show-password />
        </el-form-item>
        <div style="margin-top: 20px;">
          <el-button type="primary" @click="handleSubmit">Confirm Update</el-button>
          <el-button @click="$router.go(-1)">Cancel</el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const router = useRouter()
const username = ref(localStorage.getItem('Username'))
const form = ref({ oldPassword: '', newPassword: '' })

const handleSubmit = async () => {
  if (!form.value.oldPassword || !form.value.newPassword) {
    return ElMessage.warning('Please fill in all required fields')
  }
  try {
    const res = await axios.post('/api/config/update-password', {
      username: username.value,
      ...form.value
    })
    if (res.data.status === 'success') {
      ElMessage.success('Password updated successfully. Please log in again.')
      localStorage.clear() // 修改后清理状态
      router.push('/login')
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.message || 'Update failed')
  }
}
</script>

<style scoped>
.change-password-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f0f2f5;
}
.password-card {
  width: 450px;
}
</style>