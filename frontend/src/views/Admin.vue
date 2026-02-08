<template>
  <div class="admin-layout">
    <el-container>
      <el-header class="admin-header">
        <h2>House Detective Management</h2>
        <div class="header-right">
          <el-button @click="$router.push('/')" style="margin-right: 15px;">Back To Map</el-button>
          <el-dropdown trigger="hover">
            <span class="user-info">
              <el-avatar :icon="UserFilled" :size="30" />
              <span class="username-text">{{ adminName }}</span>
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="$router.push('/change-password')">
                  Update Password
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout" style="color: #f56c6c;">
                  Logout
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-main>
        <el-tabs type="border-card">
          <el-tab-pane label="🍪 Cookie Pool Management">
            <el-card class="box-card">
              <template #header>
                <div class="card-header">
                  <span>Realtor.ca Cookie Pool (Active: {{ activeCount }})</span>
                  <el-button type="success" size="small" @click="openCookieDialog()">
                    + Add New Cookie
                  </el-button>
                </div>
              </template>

              <el-table :data="cookieList" stripe style="width: 100%" v-loading="loading">
                <el-table-column label="Status" width="120">
                  <template #default="scope">
                    <el-tag :type="scope.row.status === 'active' ? 'success' : 'danger'">
                      {{ scope.row.status.toUpperCase() }}
                    </el-tag>
                  </template>
                </el-table-column>

                <el-table-column label="Cookie Preview" min-width="300">
                  <template #default="scope">
                    <code class="cookie-code">{{ scope.row.cookie.substring(0, 60) }}...</code>
                  </template>
                </el-table-column>

                <el-table-column label="Last Updated" width="180">
                  <template #default="scope">
                    <span class="time-text">{{ formatTime(scope.row.last_updated) }}</span>
                  </template>
                </el-table-column>

                <el-table-column label="Control" width="180">
                  <template #default="scope">
                    <el-button type="primary" size="small" link @click="openCookieDialog(scope.row)">Edit</el-button>
                    <el-popconfirm 
                      title="Are you sure to delete this cookie?"
                      @confirm="deleteCookie(scope.row._id.$oid)"
                    >
                      <template #reference>
                        <el-button 
                          type="danger" 
                          size="small" 
                          link 
                          :disabled="cookieList.length <= 1"
                        >Delete</el-button>
                      </template>
                    </el-popconfirm>
                  </template>
                </el-table-column>
              </el-table>
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

            <el-card header="Map Picker (Draw Rectangle to Get Coords)">
              <div id="adminMapDiv" style="height: 500px; width: 100%;"></div>
              <div style="margin-top: 10px; color: #666; font-size: 13px;">
                Using the rectangle tool from the top-right, draw a rectangle on the map to auto-fill the coordinate fields when adding a new region.
              </div>
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
        
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">Cancel</el-button>
          <el-button type="primary" @click="addRegion">Confirm Add</el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog 
      v-model="cookieDialogVisible" 
      :title="isEdit ? 'Edit Existing Cookie' : 'Add New Cookie to Pool'" 
      width="600px"
    >
      <el-form label-position="top">
        <el-form-item label="Cookie String">
          <el-input 
            v-model="cookieForm.cookie" 
            type="textarea" 
            :rows="8" 
            placeholder="Paste raw cookie string from browser..." 
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cookieDialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="saveCookie" :loading="submitLoading">Save Configuration</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted,computed } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import Map from '@arcgis/core/Map';
import MapView from '@arcgis/core/views/MapView';
import GraphicsLayer from '@arcgis/core/layers/GraphicsLayer';
import Sketch from '@arcgis/core/widgets/Sketch';
import * as webMercatorUtils from "@arcgis/core/geometry/support/webMercatorUtils";
import Graphic from '@arcgis/core/Graphic';
import { useRouter } from 'vue-router';

import { UserFilled, ArrowDown } from '@element-plus/icons-vue'
const API_URL = '/api';

const router = useRouter();

const adminName = ref('');
const handleLogout = () => {
  // 清除本地存储的登录状态
  localStorage.removeItem('isAdminAuthenticated');
  localStorage.removeItem('Username');  
  ElMessage.success('Successfully logged out');
  router.push('/login');
};

// 区域管理
const regions = ref([])
const dialogVisible = ref(false)
const newRegion = ref({ name: '', lat_min: '', lat_max: '', lng_min: '', lng_max: '' })

onMounted(() => {
  adminName.value = localStorage.getItem('Username')
  fetchCookieConfig()
  fetchRegions()
})

// --- Cookie Pool Logic ---
const cookieList = ref([])
const loading = ref(false)
const submitLoading = ref(false)
const cookieDialogVisible = ref(false)
const isEdit = ref(false)
const cookieForm = ref({ id: null, cookie: '' })

const activeCount = computed(() => {
  return cookieList.value.filter(c => c.status === 'active').length
})

const fetchCookieConfig = async () => {
  loading.value = true
  try {
    const res = await axios.get(`${API_URL}/config/cookie`)
    cookieList.value = Array.isArray(res.data) ? res.data : [res.data]
  } catch (e) {
    ElMessage.error('Failed to load cookie pool')
  } finally {
    loading.value = false
  }
}

const openCookieDialog = (row = null) => {
  if (row) {
    isEdit.value = true
    cookieForm.value = { id: row._id.$oid, cookie: row.cookie }
  } else {
    isEdit.value = false
    cookieForm.value = { id: null, cookie: '' }
  }
  cookieDialogVisible.value = true
}

const saveCookie = async () => {
  if (!cookieForm.value.cookie) return ElMessage.warning('Cookie is required')
  submitLoading.value = true
  try {
    await axios.post(`${API_URL}/config/cookie`, cookieForm.value)
    ElMessage.success(isEdit.value ? 'Cookie updated' : 'New cookie added')
    cookieDialogVisible.value = false
    fetchCookieConfig()
  } catch (e) {
    ElMessage.error('Operation failed')
  } finally {
    submitLoading.value = false
  }
}

const deleteCookie = async (id) => {
  try {
    const res = await axios.delete(`${API_URL}/config/cookie`, { params: { id } })
    if (res.data.status === 'success') {
      ElMessage.success('Cookie removed from pool')
      fetchCookieConfig()
    } else {
      ElMessage.error(res.data.message)
    }
  } catch (e) {
    ElMessage.error('Delete action failed')
  }
}

const formatTime = (timeData) => {
  if (!timeData) return 'N/A'
  const date = timeData.$date ? new Date(timeData.$date) : new Date(timeData)
  return date.toLocaleString()
}

// --- Region Logic ---
const fetchRegions = async () => {
  try {
    const res = await axios.get(`${API_URL}/config/regions`)
    regions.value = res.data
    displayStoredRegions()
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
    await fetchRegions() 
    displayStoredRegions() 
  } catch (e) {
    ElMessage.error('Delete failed')
  }
}

let adminView = null;
const sketchLayer = new GraphicsLayer();
const storedRegionsLayer = new GraphicsLayer(); 
onMounted(() => {
  fetchCookieConfig()
  fetchRegions()
  initAdminMap() 
})

const initAdminMap = () => {
  const map = new Map({
    basemap: "streets-navigation-vector",
    layers: [storedRegionsLayer,sketchLayer]
  });

  adminView = new MapView({
    container: "adminMapDiv",
    map: map,
    center: [-79.393, 43.646],
    zoom: 11
  });

  const sketch = new Sketch({
    view: adminView,
    layer: sketchLayer,
    visibleElements: {
      createTools: { point: false, polyline: false, polygon: false, circle: false }, 
      selectionTools: { "las-selection": false, "rectangle-selection": false }
    },
    creationMode: "update",
    updateOnGraphicClick: true
  });
  
  adminView.ui.add(sketch, "top-right");
  const updateFormCoordinates = (geometry) => {
    const geoGeometry = webMercatorUtils.webMercatorToGeographic(geometry);
    const extent = geoGeometry.extent;
    newRegion.value.lat_min = extent.ymin.toFixed(6);
    newRegion.value.lat_max = extent.ymax.toFixed(6);
    newRegion.value.lng_min = extent.xmin.toFixed(6);
    newRegion.value.lng_max = extent.xmax.toFixed(6);
  };
  sketch.on("create", (event) => {
    if (event.state === "complete") {
      updateFormCoordinates(event.graphic.geometry);
      dialogVisible.value = true;
    }
  });
  sketch.on("update", (event) => {
    if (event.state === "active" || event.state === "complete") {
      const currentGraphic = event.graphics[0];
      if (currentGraphic) {
        updateFormCoordinates(currentGraphic.geometry);
      }
    }
  });
};
const displayStoredRegions = () => {
  storedRegionsLayer.removeAll(); 

  regions.value.forEach(region => {
    if (!region.coords) return;

    const { lat_min, lat_max, lng_min, lng_max } = region.coords;
    
    const polygon = {
      type: "polygon",
      rings: [
        [ [lng_min, lat_min], [lng_min, lat_max], [lng_max, lat_max], [lng_max, lat_min], [lng_min, lat_min] ]
      ]
    };

    const fillSymbol = {
      type: "simple-fill",
      color: [0, 69, 117, 0.2], 
      outline: {
        color: [0, 69, 117, 0.8],
        width: 1
      }
    };

    const graphic = new Graphic({
      geometry: polygon,
      symbol: fillSymbol,
      attributes: { name: region.name },
      popupTemplate: {
        title: "{name}",
        content: "Existing collection region"
      }
    });

    storedRegionsLayer.add(graphic);
  });
};
</script>

<style scoped>
.admin-header {
  background-color: #0D1F62;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 30px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
#adminMapDiv {
  border: 1px solid #ddd;
  border-radius: 4px;
}
.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: rgb(255, 255, 255);
  outline: none; 
}

.username-text {
  margin: 0 8px;
  font-size: 14px;
}

:deep(.el-dropdown-menu__item) {
  padding: 8px 20px;
}
</style>