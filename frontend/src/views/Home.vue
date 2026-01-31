<template>
  <div class="home-container">
    <div class="nav-overlay">
      <h1>🇨🇦 House Detective</h1>
      <el-button type="primary" round @click="$router.push('/admin')">Go to Admin</el-button>
    </div>
    <MapView />
  </div>
</template>
<script setup>
import MapView from '../components/MapView.vue'
</script>

<style scoped>
.home-container {
  position: relative;
  height: 100vh;
  width: 100vw;
}
.nav-overlay {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 99;
  background: rgba(255, 255, 255, 0.9);
  padding: 10px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 20px;
}
h1 { margin: 0; font-size: 1.2rem; color: #004575; }
</style>