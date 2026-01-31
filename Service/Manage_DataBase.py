from pymongo import MongoClient, UpdateOne
from datetime import datetime
import re

class Manage_DataBase:
    def __init__(self, db_uri="mongodb://localhost:27017/"):
        self.client = MongoClient(db_uri)
        self.db = self.client['House_Analysis_Canada']
        self.db.listings.create_index([("location", "2dsphere")])

    def process_and_save_listings(self, json_data):
        # 1. 连接 MongoDB
        collection = self.db.listings
        
        #     # 创建地理索引
        # collection.create_index([("location", "2dsphere")])

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
                today_midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                # 构造价格历史条目
                price_entry = {
                    "price": price_str,
                    "price_value": price_numeric,
                    "captured_at": today_midnight
                }
                
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
                    "$addToSet": {
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
            try:
                # ordered=False 可以让出错的操作不中断其他操作
                res = collection.bulk_write(operations, ordered=False)
                print(f"✅ 处理完成:")
                print(f"   - 匹配文档: {res.matched_count}")
                print(f"   - 新增文档: {res.upserted_count}")
                # 如果由于 $addToSet 发现数据已存在，modified_count 将不会增加
                print(f"   - 实际修改: {res.modified_count}")
                
            except Exception as e:
                print(f"❌ 批量写入发生错误: {e}")