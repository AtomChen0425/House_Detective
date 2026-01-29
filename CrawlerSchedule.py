from Crawler.Realtor_Spider import RealtorSpider
from Service.Manage_DataBase import Manage_DataBase 
from BackEnd.DataProcess import DataProcessor
import time
import os
import random
mongo_uri = os.getenv(
    "MONGO_URI",
    "mongodb://mongo:27017/" 
)
def run_daily_update():
    db_manager = Manage_DataBase(db_uri=mongo_uri)
    regions = db_manager.db.crawl_regions.find({"active": True})
    
    for region in regions:
        print(f"开始抓取区域: {region['name']}")
        collect_data_for_region(region)
        time.sleep(300+random.randint(0, 300))
def collect_data_for_region(region):
    spider = RealtorSpider(db_uri=mongo_uri)
    db_manager = Manage_DataBase(db_uri=mongo_uri)
    continue_fetching = True
    page = 1
    
    while continue_fetching:
        data, continue_fetching = spider.fetch_data(region["coords"], page=page)
        
        if data and data.get("Results"):
            db_manager.process_and_save_listings(data)
            print(f"✅ 区域 {region['name']} 第 {page} 页更新完成")
            page += 1
            time.sleep(10) 
            if page % 10 == 0:
                time.sleep(60+random.randint(0, 600))
        else:
            print(f"🛑 区域 {region['name']} 第 {page} 页抓取中断或无结果")
            break
if __name__ == "__main__":
    run_daily_update()
    processor = DataProcessor(db_uri=mongo_uri)
    processor.calculate_unit_price()