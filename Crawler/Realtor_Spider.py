import requests
import json
import time
import random
from pymongo import MongoClient
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from fake_useragent import UserAgent  
class RealtorSpider:
    def __init__(self, db_uri="mongodb://localhost:27017/"):
        self.client = MongoClient(db_uri)
        self.db = self.client.House_Analysis_Canada
        self.url = "https://api2.realtor.ca/Listing.svc/PropertySearch_Post"
        
        # --- 初始化 UserAgent 生成器 ---
        self.ua = UserAgent(fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # --- 初始化 Session ---
        self.session = requests.Session()
        
        # 设置基础 Headers (注意：这里不再硬编码 User-Agent)
        self.session.headers.update({
            "accept": "*/*",
            "accept-language": "en-CA,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "cache-control": "no-cache",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://www.realtor.ca",
            "referer": "https://www.realtor.ca/",
        })

        # --- 配置重试策略 ---
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get_latest_cookie(self):
        """从数据库读取前端更新的最新 Cookie"""
        config = self.db.config.find_one({"type": "realtor_config"})
        return config.get("cookie") if config else ""

    def fetch_data(self, region_coords, page=1):
        """根据传入的坐标抓取数据"""
        
        cookie = self.get_latest_cookie()
        if not cookie:
            print("❌ 错误: 数据库中未找到有效 Cookie")
            return None, False

        # --- 关键修改：每次请求前随机更换 User-Agent ---
        # 这样服务器会认为是不同的设备在访问
        random_ua = self.ua.random
        
        # 更新 Session 的 Headers (Cookie 和 User-Agent 同时更新)
        self.session.headers.update({
            "cookie": cookie,
            "user-agent": random_ua
        })

        # 打印当前使用的 UA (调试用，稳定后可注释掉)
        # print(f"Current UA: {random_ua[:50]}...") 

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
            # 随机延时 (防封必备)
            time.sleep(random.uniform(1, 3)) 

            response = self.session.post(self.url, data=payload, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    total_pages = data.get("Paging", {}).get("TotalPages", 1)
                    print(f"✅ 第 {page} 页抓取成功 (Total: {total_pages})")
                    return data, page < total_pages
                except json.JSONDecodeError:
                    print(f"❌ JSON 解析失败")
                    return None, False

            elif response.status_code == 403:
                print("⚠️ 403 Forbidden: Cookie 失效或 IP 被封")
                self.db.config.update_one({"type": "realtor_config"}, {"$set": {"status": "expired"}})
                return None, False
            
            else:
                print(f"⚠️ 请求失败: {response.status_code}")
                return None, False

        except Exception as e:
            print(f"❌ 异常: {e}")
            return None, False