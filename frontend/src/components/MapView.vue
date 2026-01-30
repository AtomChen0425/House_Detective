<template>
  <div class="map-container">
    <div id="viewDiv"></div>
    <LayerControl 
      @toggle-mode="handleLayerToggle" 
      @update-intensity="handleIntensityUpdate"
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
import axios from 'axios';

const API_URL = '/api';

let map = null;
let view = null;
let housingLayer = null;
let globalChartFields = []; 

onMounted(() => {
  map = new Map({
    basemap: "streets-navigation-vector" 
  });

  view = new MapView({
    container: "viewDiv",
    map: map,
    center: [-79.393, 43.646], 
    zoom: 12
  });

  loadListings();
//   view.on("click", async (event) => {
//   const hit = await view.hitTest(event);
//   const g = hit.results[0]?.graphic;
//   if (!g) return;

//   console.log("avg_price_per_sqm:", g.attributes.avg_price_per_sqm);
//   console.log("attributes:", g.attributes);
// });
});

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
        property_url: house.raw_data?.RelativeDetailsURL ? `https://www.realtor.ca${house.raw_data.RelativeDetailsURL}` : '#'
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
          <b>Type:</b> {type}
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