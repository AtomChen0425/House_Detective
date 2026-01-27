from pymongo import MongoClient, UpdateOne
from datetime import datetime
import re

def process_and_save_listings(json_data):
    # 1. 连接 MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client.House_Analysis_Canada
    collection = db.listings
    
    # 创建地理索引（如果不存在）
    collection.create_index([("location", "2dsphere")])

    results = json_data.get("Results", [])
    operations = []

    for item in results:
        try:
            mls_number = item.get("MlsNumber")
            prop_info = item.get("Property", {})
            address_info = prop_info.get("Address", {})
            
            # --- 价格处理 ---
            price_str = prop_info.get("Price", "0")
            # 提取数字，例如 "$490,000" -> 490000
            price_numeric = int(re.sub(r'[^\d]', '', price_str)) if price_str else 0
            
            # --- 坐标处理 (重要：MongoDB 顺序是 [经, 纬]) ---
            lng = float(address_info.get("Longitude", 0))
            lat = float(address_info.get("Latitude", 0))
            
            # --- 构造插入 MongoDB 的文档 ---
            doc = {
                "mlsNumber": mls_number,
                "price": price_str,
                "price_value": price_numeric,
                "address": address_info.get("AddressText"),
                "location": {
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                "property_type": prop_info.get("Type"),
                "bedrooms": item.get("Building", {}).get("Bedrooms"),
                "bathrooms": item.get("Building", {}).get("BathroomTotal"),
                "time_on_realtor": item.get("TimeOnRealtor"),
                "last_updated": datetime.now(),
                # 整个原始数据存入一个字段，防止以后需要新字段
                "raw_data": item 
            }

            # 使用 mlsNumber 进去去重更新
            operations.append(
                UpdateOne(
                    {"mlsNumber": mls_number}, 
                    {"$set": doc}, 
                    upsert=True
                )
            )
        except Exception as e:
            print(f"⚠️ 解析房源 {mls_number} 时出错: {e}")

    # 2. 批量写入
    if operations:
        res = collection.bulk_write(operations)
        print(f"✅ 写入完成: 匹配 {res.matched_count} 条, 新增 {res.upserted_count} 条")

# 测试调用
# data = json.loads(...) # 传入你拿到的 JSON
# process_and_save_listings(data)