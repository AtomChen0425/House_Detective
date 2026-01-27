<template>
  <div class="admin-layout">
    <el-container>
      <el-header class="admin-header">
        <h2>🕵️‍♀️ House Detective Management</h2>
        <el-button @click="$router.push('/')">Back To Map</el-button>
      </el-header>
      
      <el-main>
        <el-tabs type="border-card">
          
          <el-tab-pane label="🍪 Crawler Config (Cookie)">
            <el-card class="box-card">
              <template #header>
                <div class="card-header">
                  <span>Realtor.ca Cookie Status</span>
                  <el-tag :type="cookieStatus === 'active' ? 'success' : 'danger'">
                    {{ cookieStatus === 'active' ? 'Active' : 'Inactive/Unknown' }}
                  </el-tag>
                </div>
              </template>
              
              <!-- <el-alert 
                title="Cookie info" 
                type="info" 
                description="Realtor API 需要有效的 Cookie 才能抓取。请从浏览器 (F12 -> Network) 复制最新的 Cookie 粘贴于此。"
                show-icon :closable="false" style="margin-bottom: 20px;"
              /> -->

              <el-form label-width="120px">
                <el-form-item label="Current Cookie">
                  <el-input 
                    v-model="cookieForm.cookie" 
                    type="textarea" 
                    :rows="4" 
                    placeholder="Paste long Cookie string here..." 
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveCookie" :loading="loading">Update Configuration</el-button>
                </el-form-item>
              </el-form>
              <div v-if="lastUpdated" style="margin-top:10px; color:#999; font-size:12px;">
                Last updated: {{ new Date(lastUpdated).toLocaleString() }}
              </div>
            </el-card>
          </el-tab-pane>

          <el-tab-pane label="🗺️ Collection Region Management">
            <el-card>
              <div style="margin-bottom: 15px;">
                 <el-button type="success" @click="dialogVisible = true">+ Add New Region</el-button>
              </div>
              
              <el-table :data="regions" stripe style="width: 100%">
                <el-table-column prop="name" label="Region Name" width="180" />
                <el-table-column label="Coordinate Range (Lat/Lng)">
                  <template #default="scope">
                    <span style="font-size:12px;">
                      Lat: {{ scope.row.coords.lat_min }} ~ {{ scope.row.coords.lat_max }}<br>
                      Lng: {{ scope.row.coords.lng_min }} ~ {{ scope.row.coords.lng_max }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column label="Status" width="100">
                  <template #default="scope">
                    <el-tag v-if="scope.row.active">Active</el-tag>
                    <el-tag type="info" v-else>Inactive</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="Control" width="120">
                  <template #default="scope">
                    <el-button type="danger" size="small" @click="deleteRegion(scope.row._id.$oid)">Delete</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-tab-pane>
        </el-tabs>
      </el-main>
    </el-container>

    <el-dialog v-model="dialogVisible" title="Add New Region" width="500px">
      <el-form :model="newRegion" label-width="100px">
        <el-form-item label="Region Name">
          <el-input v-model="newRegion.name" placeholder="Exp: Downtown Toronto" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
             <el-form-item label="Minimum Latitude">
               <el-input v-model="newRegion.lat_min" placeholder="43.xxx" />
             </el-form-item>
          </el-col>
           <el-col :span="12">
             <el-form-item label="Maximum Latitude">
               <el-input v-model="newRegion.lat_max" placeholder="43.xxx" />
             </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
             <el-form-item label="Minimum Longitude">
               <el-input v-model="newRegion.lng_min" placeholder="-79.xxx" />
             </el-form-item>
          </el-col>
           <el-col :span="12">
             <el-form-item label="Maximum Longitude">
               <el-input v-model="newRegion.lng_max" placeholder="-79.xxx" />
             </el-form-item>
          </el-col>
        </el-row>
        <!-- <el-alert title="提示：可在 Realtor.ca 抓包 Request Payload 中找到对应坐标" type="warning" :closable="false" /> -->
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">Cancel</el-button>
          <el-button type="primary" @click="addRegion">Confirm Add</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const API_URL = '/api';

// Cookie 状态
const cookieForm = ref({ cookie: '' })
const cookieStatus = ref('unknown')
const lastUpdated = ref(null)
const loading = ref(false)

// 区域管理
const regions = ref([])
const dialogVisible = ref(false)
const newRegion = ref({ name: '', lat_min: '', lat_max: '', lng_min: '', lng_max: '' })

onMounted(() => {
  fetchCookieConfig()
  fetchRegions()
})

// --- Cookie Logic ---
const fetchCookieConfig = async () => {
  try {
    const res = await axios.get(`${API_URL}/config/cookie`)
    if (res.data) {
      cookieForm.value.cookie = res.data.cookie
      cookieStatus.value = res.data.status
      lastUpdated.value = res.data.last_updated?.$date || res.data.last_updated
    }
  } catch (e) {
    console.error(e)
  }
}

const saveCookie = async () => {
  loading.value = true
  try {
    await axios.post(`${API_URL}/config/cookie`, { cookie: cookieForm.value.cookie })
    ElMessage.success('Cookie Updated Successfully')
    fetchCookieConfig()
  } catch (e) {
    ElMessage.error('Update Failed')
  } finally {
    loading.value = false
  }
}

// --- Region Logic ---
const fetchRegions = async () => {
  try {
    const res = await axios.get(`${API_URL}/config/regions`)
    regions.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const addRegion = async () => {
  try {
    await axios.post(`${API_URL}/config/regions`, newRegion.value)
    ElMessage.success('Region added successfully')
    dialogVisible.value = false
    newRegion.value = { name: '', lat_min: '', lat_max: '', lng_min: '', lng_max: '' }
    fetchRegions()
  } catch (e) {
    ElMessage.error('Add failed, please check parameters')
  }
}

const deleteRegion = async (id) => {
  try {
    await axios.delete(`${API_URL}/config/regions`, { params: { id } })
    ElMessage.success('Region deleted successfully')
    fetchRegions()
  } catch (e) {
    ElMessage.error('Delete failed')
  }
}
</script>

<style scoped>
.admin-header {
  background-color: #004575;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>