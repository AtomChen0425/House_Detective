from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from bson import json_util
from flask_cors import CORS
import json
import datetime
app = Flask(__name__)
CORS(app)
# 数据库连接
client = MongoClient("mongodb://192.168.2.24:27017/")
db = client.House_Analysis_Canada

@app.route('/')
def index():
    """返回前端主页面"""
    return render_template('index.html')

@app.route('/api/listings', methods=['GET'])
def get_listings():
    """获取所有房源及价格历史"""
    # 提取地图和图表所需的字段
    cursor = db.listings.find({}, {
        "mlsNumber": 1, 
        "price": 1, 
        "price_value": 1,
        "address": 1, 
        "location": 1, 
        "price_history": 1,
        "bedrooms": 1,
        "bathrooms": 1,
        "_id": 0
    })
    listings = list(cursor)
    # 使用 json_util 处理 MongoDB 的日期格式
    return json.loads(json_util.dumps(listings))

@app.route('/api/config/cookie', methods=['POST'])
def update_cookie():
    """接收前端传来的新 Cookie 并存入数据库"""
    data = request.json
    new_cookie = data.get("cookie")
    
    if not new_cookie:
        return jsonify({"status": "error", "message": "Cookie 不能为空"}), 400
    
    db.config.update_one(
        {"type": "realtor_config"},
        {"$set": {
            "cookie": new_cookie, 
            "status": "active",
            "last_updated": datetime.now()
        }},
        upsert=True
    )
    return jsonify({"status": "success", "message": "Cookie 已更新"})

if __name__ == '__main__':
    # 树莓派部署建议 host='0.0.0.0'
    app.run(debug=True, host='0.0.0.0', port=5000)