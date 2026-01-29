import re
import math
from pymongo import MongoClient, UpdateOne
# from tqdm import tqdm

class DataProcessor:
    def __init__(self, db_uri="mongodb://localhost:27017/", db_name="House_Analysis_Canada", collection_name="listings"):
        self.client = MongoClient(db_uri)
        self.db = self.client[db_name]
        self.listings_collection = self.db[collection_name]
        self.SQFT_TO_SQM = 0.092903

    def _clean_number(self, value):
        """基础清洗：提取字符串中的第一个有效数字"""
        if isinstance(value, (int, float)):
            return float(value)
        if not value:
            return 0.0
        clean_str = re.sub(r'[^\d.]', '', str(value))
        try:
            return float(clean_str) if clean_str else 0.0
        except ValueError:
            return 0.0

    def _parse_range_max(self, range_str):
        """
        专门处理范围字符串，如 "700-1100", "1000+", "<700"
        返回其中的最大值
        """
        if not range_str:
            return 0.0
        numbers = re.findall(r"(\d+(?:\.\d+)?)", str(range_str).replace(',', ''))
        
        if not numbers:
            return 0.0
        
        max_val = max([float(n) for n in numbers])
        return max_val

    def _get_area_in_sqm(self, doc):
        """
        核心逻辑：根据不同路径提取面积并统一转为平方米
        """
        raw_data = doc.get('raw_data', {})
        building = raw_data.get('Building', {})
        size_interior = building.get('SizeInterior')
        if size_interior:
            area_sqm = self._clean_number(size_interior)
            if area_sqm > 0:
                return area_sqm, "exact_m2" 

        measurements = building.get('FloorAreaMeasurements', [])
        if isinstance(measurements, list) and len(measurements) > 0:
            area_range_str = measurements[0].get('Area')
            
            if area_range_str:
                max_sqft = self._parse_range_max(area_range_str)
                if max_sqft > 0:
                    area_sqm = round(max_sqft * self.SQFT_TO_SQM, 2)
                    return area_sqm, "converted_from_sqft_range"

        return 0.0, "missing"

    def calculate_unit_price(self, batch_size=1000):
        # query = {} # 建议全量跑一遍以清洗旧数据
        total_docs = self.listings_collection.count_documents({})
        cursor = self.listings_collection.find({})
        
        print(f"开始处理 {total_docs} 条数据 (统一转换为平方米)...")
        
        bulk_ops = []
        
        for doc in cursor:
            try:
                # 1. 获取价格 (优先取清洗好的，如果没有则取 raw)
                raw_price = doc.get('price') or doc.get('total_price')
                price = self._clean_number(raw_price)

                # 2. 获取统一面积 (m²)
                area_sqm, source_type = self._get_area_in_sqm(doc)
                
                updates = {
                    "area_sqm": area_sqm,        # 统一后的面积字段
                    "area_source": source_type   # 记录数据来源，方便排查
                }

                # 3. 计算单位价格 (元/平方米)
                if area_sqm > 0 and price > 0:
                    unit_price = round(price / area_sqm, 2)
                    updates["unit_price_per_sqm"] = unit_price
                else:
                    updates["unit_price_per_sqm"] = None

                bulk_ops.append(
                    UpdateOne({"_id": doc["_id"]}, {"$set": updates})
                )

                if len(bulk_ops) >= batch_size:
                    self.listings_collection.bulk_write(bulk_ops)
                    bulk_ops = []

            except Exception as e:
                # 打印错误但不中断循环
                # print(f"Error on {doc.get('_id')}: {e}")
                continue

        if bulk_ops:
            self.listings_collection.bulk_write(bulk_ops)

        print("\n处理完成！所有面积已统一为平方米。")

if __name__ == "__main__":
    processor = DataProcessor(db_uri="mongodb://192.168.2.24:27017/")
    processor.calculate_unit_price()
    
    # 验证一下 sqft 转换的数据
    sample = processor.listings_collection.find_one({"area_source": "converted_from_sqft_range"})
    if sample:
        print("\n[验证] 转换样本:")
        print(f"原始范围: {sample['raw_data']['Building']['FloorAreaMeasurements'][0]['Area']}")
        print(f"转换后: {sample['area_sqm']} m²")
        print(f"单价: {sample['unit_price_per_sqm']} /m²")