import requests
import json

# 1. API 地址
url = "https://api2.realtor.ca/Listing.svc/PropertySearch_Post"

# 2. 构造 Headers (完全照搬你的 curl)
headers = {
    "accept": "*/*",
    "accept-language": "en-CA,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,en-US;q=0.6,zh-TW;q=0.5",
    "cache-control": "no-cache",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://www.realtor.ca",
    "referer": "https://www.realtor.ca/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # 注意：这里直接把你的 Cookie 字符串放进去
    # 这些 Cookie 是有时效性的，如果失效了需要重新从浏览器复制
    "cookie": "visid_incap_2269415=ZfeO0GlaSYSdYucfCumHtN8iVGkAAAAAQUIPAAAAAABP/5OC1UtZQyqoT5Fxg4sz; visid_incap_3157676=fsFdUPQeSqS54sOiRPanmt8iVGkAAAAAQUIPAAAAAACutQmcfCvrE2XJx2guY4Ux; _gcl_au=1.1.1854660065.1767121636; _cc_id=2b06e6b55fd4b3a13f5e5dfb5ed1929; _sharedid=72a24d10-506c-403d-b1d4-cd0449107330; _sharedid_cst=zix7LPQsHA%3D%3D; visid_incap_3057435=zU/Vzrd6R42Pj0S/Gkwxh+IiVGkAAAAAQUIPAAAAAACluwHhY8CvIBym26Q6jC5H; gig_bootstrap_3_mrQiIl6ov44s2X3j6NGWVZ9SDDtplqV7WgdcyEpGYnYxl7ygDWPQHqQqtpSiUfko=gigya-pr_ver4; reese84=3:8nuV3MsY20Mjt82kSGn5SQ==:jItceaoDo2DJWHxRXP6PB8rfVNGB9xTdXhxIStFkl7H+Py30AgXSH6SjjEhG1MmZk3YsIkklJLWlr6qvPFvrT2zEZIil+ZALkNT2eQr9deagJ5mxPV4mWTmONOyGVZqCyHfUVBPli/vpTGPJD8dncyL7F1fI4IXf3RCmbaZ6x/gXd6Y1TvNT86BGHq21pAOXN84knl87w+XRkHULizYfaHum3yKCY4i6zQIzFkNLs9PaS412yTxZiaD05q9BlUn0nQ/tEYAMjHfJ5l4p1WxYn2wr5nWg4DM/7I9aJGHrIsPoH0OaFGNQDyblNpUiHJtkaLcS+F8nOSbUJWTsnJ1wSG4eGAE6MXfTfAwQ5o28G4CenLZcNIVZ83N7C4EtQpIWCZLOzx1Xfp71fY9ha18bLVF46QnpcTOjssLqq4jXXDYLzB4kjD0XznxBj2DVirKj8FrX6/Bkb+LcuEapvz7AQg==:Yxe5v2DPALFJWYlvr7fOyDULj4M6thpL3cQCWRwo+A0=; panoramaId_expiry=1770058836858; panoramaId=0eda70b59b55633610ae28fa32fd16d53938bff4a72de626a4d99e9df26a5059;"
}

# 3. 构造 Body 数据 (Form Data)
payload = {
    "ZoomLevel": "14",
    "LatitudeMax": "43.65322",
    "LongitudeMax": "-79.38794",
    "LatitudeMin": "43.64513",
    "LongitudeMin": "-79.3977",
    "Sort": "6-D",
    "PropertyTypeGroupID": "1",
    "PropertySearchTypeId": "0",
    "Currency": "CAD",
    "IncludeHiddenListings": "true",
    "RecordsPerPage": "12",
    "ApplicationId": "1",
    "CultureId": "1",
    "Version": "7.0",
    "CurrentPage": "1"
}

try:
    # 发送请求
    response = requests.post(url, headers=headers, data=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功! 抓取到 {len(data.get('Results', []))} 套房源")
        print(json.dumps(data, indent=2, ensure_ascii=False),file=open("realtor_data.json","w",encoding="utf-8"))
        # 打印第一套房看看
        if data.get('Results'):
            first = data['Results'][0]
            print(f"🏠 地址: {first.get('Property', {}).get('Address', {}).get('AddressText')}")
            print(f"💰 价格: {first.get('Property', {}).get('Price')}")
    else:
        print(f"❌ 失败: 状态码 {response.status_code}")
        print(response.text[:200])

except Exception as e:
    print(f"❌ 发生错误: {e}")