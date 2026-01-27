import requests
import json
from pymongo import MongoClient

class RealtorSpider:
    def __init__(self, db_uri="mongodb://localhost:27017/"):
        self.client = MongoClient(db_uri)
        self.db = self.client.House_Analysis_Canada
        self.url = "https://api2.realtor.ca/Listing.svc/PropertySearch_Post"

    def get_latest_cookie(self):
        """从数据库读取前端更新的最新 Cookie"""
        config = self.db.config.find_one({"type": "realtor_config"})
        return config.get("cookie") if config else ""

    def fetch_data(self, region_coords, page=1):
        """根据传入的坐标抓取数据"""
        cookie = self.get_latest_cookie()
        if not cookie:
            print("❌ 错误: 数据库中未找到有效 Cookie，请在前端更新")
            return None

        headers = {
            "accept": "*/*",
            "accept-language": "en-CA,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,en-US;q=0.6,zh-TW;q=0.5",
            "cache-control": "no-cache",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://www.realtor.ca",
            "referer": "https://www.realtor.ca/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "cookie": cookie
            }
        # 将用户自定义区域坐标注入 payload
        payload = {
            "ZoomLevel": "18",
            "LatitudeMax": region_coords["lat_max"],
            "LongitudeMax": region_coords["lng_max"],
            "LatitudeMin": region_coords["lat_min"],
            "LongitudeMin": region_coords["lng_min"],
            "Sort": "6-D",
            "PropertyTypeGroupID": "1",
            "TransactionTypeId": "2",
            "PropertySearchTypeId": "0",
            "Currency": "CAD",
            "IncludeHiddenListings": "false",
            "RecordsPerPage": "12",
            "ApplicationId": "1",
            "CultureId": "1",
            "Version": "7.0",
            "CurrentPage": str(page)
        }

        try:
            response = requests.post(self.url, headers=headers, data=payload)
            if response.status_code == 200:
                
                total_pages = response.json().get("Paging", {}).get("TotalPages", 1)
                print(f"✅ 第 {page} 页数据抓取成功,总计 {total_pages} 页")
                return response.json(), page < total_pages
            elif response.status_code == 403:
                print("⚠️ 警告: Cookie 已失效或被封禁")
                # 这里可以触发通知逻辑，告知前端
                self.db.config.update_one({"type": "realtor_config"}, {"$set": {"status": "expired"}})
            return None, False
        except Exception as e:
            print(f"❌ 请求发生异常: {e}")
            return None, False