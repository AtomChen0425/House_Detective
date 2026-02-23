import requests
from pymongo import MongoClient, UpdateOne, GEOSPHERE

class POISpider:
    def __init__(self, db_uri="mongodb://localhost:27017/"):
        self.client = MongoClient(db_uri)
        self.db = self.client.House_Analysis_Canada
        # 创建专门的 POI 集合
        self.collection = self.db.toronto_pois
        self.overpass_url = "http://overpass-api.de/api/interpreter"
        
        # 初始化数据库：为位置字段创建 2dsphere 索引，方便后续空间查询
        self.collection.create_index([("location", GEOSPHERE)])

    def fetch_and_store_pois(self):
        # 使用 out geom 获取完整几何图形（线段数据）
        overpass_query = """
        [out:json][timeout:90];
        area["name"="Toronto"]["boundary"="administrative"]->.searchArea;
        (
          node["shop"="supermarket"](area.searchArea);
          node["public_transport"="station"](area.searchArea);
          way["highway"="motorway"](area.searchArea);
        );
        out geom tags;
        """
        
        print("🌍 正在向 Overpass API 获取多伦多 POI 及道路数据 (可能需要几十秒)...")
        response = requests.post(self.overpass_url, data={'data': overpass_query})
        
        if response.status_code == 200:
            data = response.json()
            elements = data.get('elements', [])
            print(f"✅ 数据获取成功！共找到 {len(elements)} 个原始要素。正在处理入库...")
            
            operations = []
            
            for el in elements:
                osm_id = el.get('id')
                el_type = el.get('type')
                tags = el.get('tags', {})
                name = tags.get('name', 'N/A')
                
                # 确定 POI 类别
                category = "unknown"
                if tags.get('shop') == 'supermarket':
                    category = "supermarket"
                elif tags.get('public_transport') == 'station':
                    category = "transit_station"
                elif tags.get('highway') == 'motorway':
                    category = "highway"
                
                # 构建 MongoDB 兼容的 GeoJSON 数据结构
                location = None
                
                if el_type == 'node':
                    # 点状数据 (Point) - 注意 MongoDB 要求 [longitude, latitude]
                    lon = el.get('lon')
                    lat = el.get('lat')
                    if lon and lat:
                        location = {
                            "type": "Point",
                            "coordinates": [lon, lat]
                        }
                        
                elif el_type == 'way':
                    # 线状数据 (LineString) - 提取完整道路轨迹
                    geometry = el.get('geometry', [])
                    coordinates = []
                    for point in geometry:
                        lon = point.get('lon')
                        lat = point.get('lat')
                        if lon and lat:
                            coordinates.append([lon, lat])
                    
                    if len(coordinates) >= 2:
                        location = {
                            "type": "LineString",
                            "coordinates": coordinates
                        }

                if location:
                    # 构建文档
                    poi_document = {
                        "osm_id": osm_id,
                        "type": el_type,
                        "category": category,
                        "name": name,
                        "tags": tags,
                        "location": location
                    }
                    
                    # 使用 UpdateOne 进行 Upsert，避免重复抓取时产生冗余数据
                    operations.append(
                        UpdateOne(
                            {"osm_id": osm_id}, 
                            {"$set": poi_document}, 
                            upsert=True
                        )
                    )
            
            # 批量写入数据库
            if operations:
                result = self.collection.bulk_write(operations)
                print(f"📦 数据处理完毕！")
                print(f"   - 新插入: {result.upserted_count} 条")
                print(f"   - 更新/已存在: {result.matched_count} 条")
            else:
                print("⚠️ 没有解析到有效的位置数据。")
                
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")

if __name__ == "__main__":
    spider = POISpider(db_uri="mongodb://192.168.2.24:27017/")
    spider.fetch_and_store_pois()