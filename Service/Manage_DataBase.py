from pymongo import MongoClient, UpdateOne
from datetime import datetime
import re

class Manage_DataBase:
    def __init__(self, db_uri="mongodb://localhost:27017/"):
        self.client = MongoClient(db_uri)
        self.db = self.client['House_Analysis_Canada']

    def process_and_save_listings(self, json_data):
        # 1. 连接 MongoDB
        collection = self.db.listings
        
            # 创建地理索引
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
                price_numeric = int(re.sub(r'[^\d]', '', price_str)) if price_str else 0
                
                # --- 坐标处理 ---
                lng = float(address_info.get("Longitude", 0))
                lat = float(address_info.get("Latitude", 0))
                
                # 当前时间快照
                now = datetime.now()

                # 构造价格历史条目
                price_entry = {
                    "price": price_str,
                    "price_value": price_numeric,
                    "captured_at": now
                }
                
                # --- 构造更新指令 ---
                # $set: 更新当前最新信息
                # $addToSet: 如果价格历史里没有这一条（基于价格和数值），则添加。
                # 或者直接用 $push 记录每一次爬取的时间点。
                update_doc = {
                    "$set": {
                        "price": price_str,           # 最新的价格显示
                        "price_value": price_numeric, # 最新价格数值
                        "address": address_info.get("AddressText"),
                        "location": {
                            "type": "Point",
                            "coordinates": [lng, lat]
                        },
                        "property_type": prop_info.get("Type"),
                        "bedrooms": item.get("Building", {}).get("Bedrooms"),
                        "bathrooms": item.get("Building", {}).get("BathroomTotal"),
                        "last_updated": now,
                        "raw_data": item 
                    },
                    "$push": {
                        "price_history": price_entry  # 将当前价格和时间压入历史数组
                    }
                }

                operations.append(
                    UpdateOne(
                        {"mlsNumber": mls_number}, 
                        update_doc, 
                        upsert=True
                    )
                )
            except Exception as e:
                print(f"⚠️ 解析房源 {mls_number} 时出错: {e}")

        # 2. 批量写入
        if operations:
            res = collection.bulk_write(operations)
            print(f"✅ 处理完成: 匹配 {res.matched_count} 条, 新增/更新 {res.upserted_count + res.modified_count} 条历史记录")