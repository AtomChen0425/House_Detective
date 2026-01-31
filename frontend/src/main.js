import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import '@arcgis/core/assets/esri/themes/light/main.css'
import App from './App.vue'
import router from './router'

import './style.css' // 可以放一些全局样式

const app = createApp(App)
app.use(router)
app.use(ElementPlus)
app.mount('#app')