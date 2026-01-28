<template>
  <div id="viewDiv"></div>
</template>

<script setup>
import { onMounted } from 'vue';
import Map from '@arcgis/core/Map';
import MapView from '@arcgis/core/views/MapView';
import Graphic from '@arcgis/core/Graphic';
import GraphicsLayer from '@arcgis/core/layers/GraphicsLayer';
import axios from 'axios';


const API_URL = '/api';

onMounted(() => {
  const map = new Map({
    basemap: "streets-navigation-vector" 
  });

  const view = new MapView({
    container: "viewDiv",
    map: map,
    center: [-79.393, 43.646], 
    zoom: 14
  });

  const graphicsLayer = new GraphicsLayer();
  map.add(graphicsLayer);

  loadListings(graphicsLayer);
});

const loadListings = async (layer) => {
  try {
    const res = await axios.get(`${API_URL}/listings`);
    const listings = res.data;

    listings.forEach(house => {
      const coords = house.location.coordinates;
      
      // 准备图表数据
      const attributes = {
        ObjectId: house.mlsNumber, // 必须唯一
        address: house.address,
        price: house.price,
        bedrooms: house.bedrooms || '-',
        bathrooms: house.bathrooms || '-',
        type: house.property_type,
        // 尝试获取第一张图片，如果没有则用占位图
        imageUrl: house.raw_data?.Property?.Photo?.[0]?.HighResPath || 'https://via.placeholder.com/300x200?text=No+Image',
        property_url: house.raw_data?.RelativeDetailsURL? `https://www.realtor.ca${house.raw_data.RelativeDetailsURL}`: '#'
      };

      // 处理历史价格字段用于图表
      const priceHistory = house.price_history || [];
      priceHistory.forEach((h, index) => {
        attributes[`date_${index}`] = new Date(h.captured_at.$date || h.captured_at).toLocaleDateString();
        attributes[`price_${index}`] = h.price_value;
      });

      // 动态生成图表字段配置
      const chartFields = priceHistory.map((_, i) => `price_${i}`);

      const popupTemplate = {
        title: "{address}",
        content: [
          {
            // 显示图片和关键信息
            type: "text",
            text: `
              <div style="margin-bottom:10px;">
                <img src="{imageUrl}" style="width:100%; border-radius:4px; object-fit:cover; height:150px;" />
              </div>
              <div style="font-size: 14px; color: #555;">
                <b>Price:</b> <span style="color: #d93025; font-size: 16px;">{price}</span><br>
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
            // 价格趋势图
            type: "media",
            mediaInfos: [{
              title: "Price History",
              type: "line-chart",
              caption: "",
              value: {
                fields: chartFields,
                normalizeField: null
              }
            }]
          }
        ]
      };

      const point = {
        type: "point",
        longitude: coords[0],
        latitude: coords[1]
      };

      const simpleMarkerSymbol = {
        type: "simple-marker",
        color: [226, 119, 40],  // 橙色
        outline: { color: [255, 255, 255], width: 1 },
        size: "15px"
      };

      const graphic = new Graphic({
        geometry: point,
        symbol: simpleMarkerSymbol,
        attributes: attributes,
        popupTemplate: popupTemplate
      });

      layer.add(graphic);
    });
  } catch (e) {
    console.error("Load listings failed:", e);
  }
};
</script>

<style scoped>
#viewDiv {
  padding: 0;
  margin: 0;
  height: 100%;
  width: 100%;
}
</style>