<template>
  <div class="map-container">
    <div id="viewDiv"></div>
    <LayerControl 
      @toggle-mode="handleLayerToggle" 
      @update-intensity="handleIntensityUpdate"
      @toggle-poi="handlePoiToggle"
    />
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import LayerControl from './LayerControl.vue';
import Map from '@arcgis/core/Map';
import MapView from '@arcgis/core/views/MapView';
import FeatureLayer from '@arcgis/core/layers/FeatureLayer';
import Graphic from '@arcgis/core/Graphic';
import GraphicsLayer from '@arcgis/core/layers/GraphicsLayer'; 
import axios from 'axios';

const API_URL = '/api';

let map = null;
let view = null;
let housingLayer = null;
let globalChartFields = []; 
const poiLayers = {
  highway: new GraphicsLayer({ visible: false, opacity: 0.6 }),
  supermarket: new GraphicsLayer({ visible: false }),
  transit_station: new GraphicsLayer({ visible: false })
};
onMounted(() => {
  map = new Map({
    basemap: "streets-navigation-vector" 
  });
  map.addMany([poiLayers.highway, poiLayers.transit_station, poiLayers.supermarket]);
  view = new MapView({
    container: "viewDiv",
    map: map,
    center: [-79.393, 43.646], 
    zoom: 12
  });

  loadListings();
  loadPOIs();
});

const loadPOIs = async () => {
  try {
    const res = await axios.get(`${API_URL}/pois`);
    const pois = res.data;
    
    if (!pois || pois.length === 0) return;

    pois.forEach(poi => {
      let graphic;
      const attributes = {
        name: poi.name || 'Unknown',
        category: poi.category
      };

      const popupTemplate = {
        title: "{name}",
        content: "<b>Type:</b> {category}"
      };

      // 1. 处理点数据 (超市、车站)
      if (poi.location && poi.location.type === 'Point') {
        const [lng, lat] = poi.location.coordinates;
        
        let symbol;
        if (poi.category === 'supermarket') {
          symbol = {
            type: "simple-marker",
            color: "#67C23A", 
            path: "M288 0c6.6 0 12.9 2.7 17.4 7.5l144 152 .5 .5 78.1 0c17.7 0 32 14.3 32 32 0 14.5-9.6 26.7-22.8 30.7L491.1 429.9c-6.5 29.3-32.5 50.1-62.5 50.1l-281.3 0c-30 0-56-20.8-62.5-50.1l-46-207.2c-13.2-3.9-22.8-16.2-22.8-30.7 0-17.7 14.3-32 32-32l78.1 0 .5-.5 144-152C275.1 2.7 281.4 0 288 0zm0 58.9L192.2 160 383.8 160 288 58.9zM208 264c0-13.3-10.7-24-24-24s-24 10.7-24 24l0 112c0 13.3 10.7 24 24 24s24-10.7 24-24l0-112zm80-24c-13.3 0-24 10.7-24 24l0 112c0 13.3 10.7 24 24 24s24-10.7 24-24l0-112c0-13.3-10.7-24-24-24zm128 24c0-13.3-10.7-24-24-24s-24 10.7-24 24l0 112c0 13.3 10.7 24 24 24s24-10.7 24-24l0-112z",
            size: 16,
            // outline: { color: "white", width: 1.5 } 
          };
        } else if (poi.category === 'transit_station') {
          symbol = {
            type: "simple-marker",
            color: "#409EFF", 
            path: "M320 0H192C86 0 0 86 0 192v192c0 82 51.5 151.7 122.9 178.5L92 613.8c-7.6 17.5 7.1 36.3 25.4 31.8l103.4-25.9h66.5l103.4 25.9c18.3 4.6 33-14.3 25.4-31.8l-30.9-51.3C460.5 535.7 512 466 512 384V192C512 86 426 0 320 0zM128 416c-17.7 0-32-14.3-32-32s14.3-32 32-32 32 14.3 32 32-14.3 32-32 32zm256 0c-17.7 0-32-14.3-32-32s14.3-32 32-32 32 14.3 32 32-14.3 32-32 32zM416 256H96V128h320v128z",
            size: 16,
            // outline: { color: "white", width: 1.5 }
          };
        }

        graphic = new Graphic({
          geometry: { type: "point", longitude: lng, latitude: lat },
          symbol: symbol,
          attributes: attributes,
          popupTemplate: popupTemplate
        });
      } 
      // 2. 处理线数据 (高速公路)
      else if (poi.location && poi.location.type === 'LineString') {
        // ArcGIS 要求 paths 是一个二维数组的数组: [ [ [lon, lat], [lon, lat] ] ]
        graphic = new Graphic({
          geometry: { type: "polyline", paths: [poi.location.coordinates] },
          symbol: { type: "simple-line", color: "#F56C6C", width: 3, style: "solid" },
          attributes: attributes,
          popupTemplate: popupTemplate
        });
      }

      // 放入对应的图层
      if (graphic) {
        if (poi.category === 'supermarket') poiLayers.supermarket.add(graphic);
        else if (poi.category === 'transit_station') poiLayers.transit_station.add(graphic);
        else if (poi.category === 'highway') poiLayers.highway.add(graphic);
      }
    });
    
    console.log("POI data loaded successfully.");
  } catch (e) {
    console.error("Failed to load POIs:", e);
  }
};

// 新增：处理开关切换逻辑
const handlePoiToggle = ({ type, isVisible }) => {
  if (poiLayers[type]) {
    poiLayers[type].visible = isVisible;
  }
};
const loadListings = async () => {
  try {
    const res = await axios.get(`${API_URL}/listings`);
    const listings = res.data;
    
    if (!listings || listings.length === 0) {
      console.warn("⚠️ warning: No listings data found.");
      return;
    }

    // 1. 预先计算图表所需的字段名 (例如 price_0, price_1...)
    if (listings.length > 0 && listings[0].price_history) {
      globalChartFields = listings[0].price_history.map((_, i) => `price_${i}`);
    }

    const graphics = listings.map((house, index) => {
      // 安全获取坐标
      const lng = house.location?.coordinates?.[0] || 0;
      const lat = house.location?.coordinates?.[1] || 0;
      
      // 处理单价
      let uPrice = 0;
      if (house.unit_price_per_sqm) {
        const cleanStr = String(house.unit_price_per_sqm).replace(/[$,]/g, '');
        uPrice = parseFloat(cleanStr);
      }
      if (isNaN(uPrice)) uPrice = 0;

      // 准备基础属性
      const attributes = {
        ObjectId: index + 1, // 使用数字 ID 以支持聚合
        address: house.address || 'Unknown',
        price: house.price,
        unitPrice: uPrice,
        bedrooms: house.bedrooms || '-',
        bathrooms: house.bathrooms || '-', // 补回 bathrooms
        type: house.property_type || 'Unknown', // 补回 type
        imageUrl: house.raw_data?.Property?.Photo?.[0]?.HighResPath || 'https://via.placeholder.com/300x200?text=No+Image',
        property_url: house.raw_data?.RelativeDetailsURL ? `https://www.realtor.ca${house.raw_data.RelativeDetailsURL}` : '#',
        lastUpdated: formatTime(house.last_updated) || 'Unknown'
      };

      const priceHistory = house.price_history || [];
      priceHistory.forEach((h, i) => {
        attributes[`price_${i}`] = h.price_value;
      });

      return new Graphic({
        geometry: { type: "point", longitude: lng, latitude: lat },
        attributes: attributes
      });
    });

    console.log(`Successfully loaded ${graphics.length} points`);

    housingLayer = new FeatureLayer({
      source: graphics,
      objectIdField: "ObjectId",
      fields: [
        { name: "ObjectId", type: "oid" }, 
        { name: "address", type: "string" },
        { name: "price", type: "string" },
        { name: "unitPrice", type: "double" },
        { name: "bedrooms", type: "string" },
        { name: "bathrooms", type: "string" },
        { name: "type", type: "string" },
        { name: "imageUrl", type: "string" },
        { name: "property_url", type: "string" },
        { name: "lastUpdated", type: "string" },
        ...globalChartFields.map(f => ({ name: f, type: "double" }))
      ],
      renderer: getPointRenderer(), 

      popupTemplate: getRichPopupTemplate(globalChartFields)
    });

    map.add(housingLayer);

  } catch (e) {
    console.error("Loading Failed:", e);
  }
};


const handleLayerToggle = (isAnalysisMode) => {
  if (!housingLayer) return;

  if (isAnalysisMode) {
    console.log("Exchange to analysise...");

    housingLayer.featureReduction = {
      type: "cluster",
      clusterRadius: "100px",
      fields: [
        {
          name: "avg_price_per_sqm",
          onStatisticField: "unitPrice",
          statisticType: "avg"
        },
        {
          name: "cluster_count",
          statisticType: "count"
        }
      ],
      labelingInfo: [{
        deconflictionStrategy: "none", 
        labelPlacement: "center-center",
        symbol: {
          type: "text",
          color: "white",
          font: { weight: "bold", family: "sans-serif", size: "11px" },
          haloColor: [0, 0, 0, 0.6], 
          haloSize: 1.5
        },
        labelExpressionInfo: {
          
          expression: "Text($feature.avg_price_per_sqm, '#,##0')" 
        }
      }],
      popupTemplate: {
        title: "Region Summary",
        content: `
          <div style="font-size:14px;">
            Include <b>{cluster_count}</b> propertys<br>
            Average Unit Price: <b style="color:#d93025">{avg_price_per_sqm}</b> $/m²
          </div>
        `,
        fieldInfos: [{ fieldName: "avg_price_per_sqm", format: { places: 0, digitSeparator: true } }]
      },
      renderer: getClusterRenderer(15000)
    };

    // housingLayer.renderer = getClusterRenderer(15000);
    housingLayer.labelingInfo = getClusterLabels();

  } else {

    housingLayer.featureReduction = null;
    housingLayer.renderer = getPointRenderer();
    housingLayer.popupTemplate = getRichPopupTemplate(globalChartFields);
    housingLayer.labelingInfo = [];
  }
};

const handleIntensityUpdate = (maxVal) => {
  if (housingLayer && housingLayer.featureReduction) {
    // housingLayer.featureReduction.renderer = getClusterRenderer(maxVal);
    console.log("Updating Max Value to:", maxVal);

    const newReduction = housingLayer.featureReduction.clone();
    const newRenderer = getClusterRenderer(maxVal); 
    newReduction.renderer = newRenderer;
    housingLayer.featureReduction = newReduction;
  }
};


const getPointRenderer = () => ({
  type: "simple",
  symbol: {
    type: "simple-marker",
    color: [226, 119, 40],
    size: 12,
    outline: { color: "white", width: 0.5 }
  }
});

const formatTime = (timeData) => {
  if (!timeData) return 'N/A'
  const date = timeData.$date ? new Date(timeData.$date) : new Date(timeData)
  return date.toLocaleString()
}
const getRichPopupTemplate = (chartFields) => ({
  title: "{address}",
  content: [
    {

      type: "text",
      text: `
        <div style="margin-bottom:10px;">
          <img src="{imageUrl}" style="width:100%; border-radius:4px; object-fit:cover; height:150px;" />
        </div>
        <div style="font-size: 14px; color: #555;">
          <b>Price:</b> <span style="color: #d93025; font-size: 16px;">{price}</span><br>
          <b>Unit Price:</b> {unitPrice} $/m²<br>
          <b>Bedrooms:</b> {bedrooms} <b>Bathrooms:</b> {bathrooms}<br>
          <b>Type:</b> {type}<br>
          <b>Last Updated:</b> {lastUpdated}<br>
        </div>
        <div style="margin-top: 10px;">
          <a href="{property_url}" target="_blank" 
             style="display: inline-block; padding: 8px 16px; background-color: #4285f4; color: white; text-decoration: none; border-radius: 4px; font-weight: bold;">
             Check on Realtor.ca
          </a>
        </div>
      `
    },
    {

      type: "media",
      mediaInfos: [{
        title: "Price History",
        type: "line-chart",
        caption: "History of listing price changes",
        value: {
          fields: chartFields, 
          normalizeField: null
        }
      }]
    }
  ]
});


const getClusterRenderer = (maxVal) => ({
  type: "simple",
  symbol: {
    type: "simple-marker",
    style: "circle",
    size: 20,
    color: [0, 0, 0, 0],
    outline: { color: "rgba(255, 255, 255, 0.8)", width: 1.5 }
  },
  visualVariables: [
    {
      type: "color",
      field: "avg_price_per_sqm",
      stops: [
        { value: 0, color: "rgba(200, 200, 200, 0.5)" },
        { value: maxVal*0.3, color: "rgba(68, 85, 136, 0.8)" },  
        { value: maxVal*0.6, color: "rgba(238, 187, 34, 0.8)" }, 
        { value: maxVal, color: "rgba(221, 68, 68, 0.9)" }  
      ]
    },
    {
      type: "size",
      field: "cluster_count",
      stops: [
        { value: 1, size: 24 },
        { value: 50, size: 60 },
        { value: 100, size: 80 }
      ]
    }
  ]
});

const getClusterLabels = () => [{
  deconflictionStrategy: "none",
  labelPlacement: "center-center",
  symbol: {
    type: "text",
    color: "white",
    font: { weight: "bold", family: "sans-serif", size: "10px" },
    haloColor: [0, 0, 0, 0.5],
    haloSize: 1
  },
  labelExpressionInfo: {
    expression: "Text($feature.avg_price_per_sqm, '#,###')" 
  }
}];
</script>

<style scoped>
.map-container, #viewDiv { width: 100%; height: 100%; margin: 0; padding: 0; }
</style>