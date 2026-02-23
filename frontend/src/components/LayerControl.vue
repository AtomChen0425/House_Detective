<template>
  <div class="control-panel">
    <div class="panel-header">Layer Control</div>
    
    <div class="control-item">
      <el-switch
        v-model="isAnalysisMode"
        active-text="Region Avg Price"
        inactive-text="All Listings"
        @change="onModeChange"
      />
    </div>

    <transition name="fade">
      <div v-if="isAnalysisMode" class="legend-area">
        <div class="legend-title">Region Average Price ($/m²)</div>
        <div class="legend-bar-container">
          <span class="label">Low</span>
          <div class="color-bar"></div>
          <span class="label">High</span>
        </div>
        
        <div class="slider-container">
          <div class="slider-row">
            <span class="slider-label">Highest Price Threshold: {{ maxPrice }}</span>
          </div>
          <el-slider 
            v-model="maxPrice" 
            :min="5000" 
            :max="30000" 
            :step="1000" 
            size="small"
            @change="onIntensityChange"
          />
        </div>
      </div>
    </transition>

    <div class="panel-header" style="margin-top: 20px;">POI Layers</div>
    <div class="control-item">
      <el-switch
        v-model="poiSwitches.supermarket"
        active-text="🛒 Supermarkets"
        @change="(val) => onPoiToggle('supermarket', val)"
      />
    </div>
    <div class="control-item">
      <el-switch
        v-model="poiSwitches.transit_station"
        active-text="🚇 Transit Stations"
        @change="(val) => onPoiToggle('transit_station', val)"
      />
    </div>
    <div class="control-item">
      <el-switch
        v-model="poiSwitches.highway"
        active-text="🛣️ Highways"
        @change="(val) => onPoiToggle('highway', val)"
      />
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, defineEmits } from 'vue';

const emit = defineEmits(['toggle-mode', 'update-intensity']);

const isAnalysisMode = ref(false);
const maxPrice = ref(15000); 

const poiSwitches = reactive({
  supermarket: false,
  transit_station: false,
  highway: false
});

const onModeChange = (val) => {
  emit('toggle-mode', val);
};

const onIntensityChange = (val) => {
  emit('update-intensity', val);
};

const onPoiToggle = (type, isVisible) => {
  emit('toggle-poi', { type, isVisible });
};
</script>

<style scoped>
.control-panel {
  position: absolute;
  bottom: 30px;
  right: 30px;
  background: rgba(255, 255, 255, 0.95);
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 99;
  width: 360px;
}

.panel-header { font-weight: bold; margin-bottom: 15px; color: #004575; border-bottom: 1px solid #eee; padding-bottom: 8px; }
.control-item { margin-bottom: 10px; }
.legend-area { margin-top: 15px; background: #f8f9fa; padding: 10px; border-radius: 4px; }
.legend-title { font-size: 12px; color: #666; margin-bottom: 5px; }
.legend-bar-container { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #666; }
.color-bar { flex: 1; height: 8px; border-radius: 4px; background: linear-gradient(to right, #445588, #55aa77, #eebb22, #dd4444); }
.slider-container { margin-top: 10px; }
.slider-label { font-size: 11px; color: #999; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>