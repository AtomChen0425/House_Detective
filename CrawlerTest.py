# scheduler.py
from Crawler.Realtor_Spider import RealtorSpider
from Service.Manage_DataBase import Manage_DataBase 
import time
def run_daily_update():
    spider = RealtorSpider()
    # 1. 获取所有用户自定义的区域
    regions = spider.db.regions.find({"active": True})
    
    for region in regions:
        print(f"开始抓取区域: {region['name']}")
        # 2. 抓取数据
        data = spider.fetch_data(region["coords"])
        
        if data and data.get("Results"):
            # 3. 调用您已实现的存储逻辑进行保存
            db_manager = Manage_DataBase()
            db_manager.update_listings(data["Results"])
            print(f"✅ 区域 {region['name']} 更新完成")
        else:
            print(f"🛑 区域 {region['name']} 抓取失败，跳过")
def collect_data_for_region(region):
    spider = RealtorSpider(db_uri="mongodb://192.168.2.24:27017/")
    continue_fetching = True
    page = 1
    while continue_fetching:
        data, continue_fetching = spider.fetch_data(region["coords"], page=page)
        if data and data.get("Results"):
            db_manager = Manage_DataBase(db_uri="mongodb://192.168.2.24:27017/")
            db_manager.process_and_save_listings(data)
            print(f"✅ 区域 {region['name']} 更新完成")
            page += 1
        else:
            print(f"🛑 区域 {region['name']} 抓取失败，跳过")
        time.sleep(10)  # 避免请求过于频繁
if __name__ == "__main__":
    region={
        "name":"Toronto Downtown",
        "coords":{
        "lat_max": "43.65322",
        "lng_max": "-79.38794",
        "lat_min": "43.64513",
        "lng_min": "-79.3977"
        }
    }
    collect_data_for_region(region)
# 配合 Linux Crontab 或 Celery 定时执行