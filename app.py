from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from bson import json_util, ObjectId
from flask_cors import CORS
import json
import datetime
import os

app = Flask(__name__, static_folder='frontend/dist', static_url_path='')
CORS(app, resources={r"/api/*": {"origins": "*"}})

mongo_uri = os.getenv("MONGO_URI", "mongodb://mongo:27017/") #"mongodb://192.168.2.24:27017/"
client = MongoClient(mongo_uri)
db = client.House_Analysis_Canada

# --- 路由 ---

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def catch_all(path):
    if path.startswith('api/'):
        return jsonify({"error": "Not Found"}), 404

    if os.path.exists(os.path.join(app.static_folder, path)):
         return app.send_static_file(path)

    return app.send_static_file('index.html')

@app.route('/api/listings', methods=['GET'])
def get_listings():
    """获取所有房源数据"""
    cursor = db.listings.find({}, {
        "mlsNumber": 1, "price": 1, "price_value": 1,
        "address": 1, "location": 1, "price_history": 1,
        "bedrooms": 1, "bathrooms": 1, "property_type": 1,
        "raw_data.Property.Photo": 1,"raw_data.RelativeDetailsURL":1,
        "unit_price_per_sqm": 1,
        "_id": 0
    })
    listings = list(cursor)
    return json.loads(json_util.dumps(listings))

# --- Cookie 管理 ---

@app.route('/api/config/cookie', methods=['GET', 'POST'])
def manage_cookie():
    """获取或更新 Cookie"""
    if request.method == 'POST':
        data = request.json
        new_cookie = data.get("cookie")
        if not new_cookie:
            return jsonify({"status": "error", "message": "Cookie 不能为空"}), 400
        
        db.config.update_one(
            {"type": "realtor_config"},
            {"$set": {
                "cookie": new_cookie, 
                "status": "active",
                "last_updated": datetime.datetime.now()
            }},
            upsert=True
        )
        return jsonify({"status": "success", "message": "Cookie 已更新"})
    
    else:
        config = db.config.find_one({"type": "realtor_config"}, {"_id": 0})
        return jsonify(config if config else {"status": "unknown"})

# --- 采集区域管理 (新增) ---

@app.route('/api/config/regions', methods=['GET', 'POST', 'DELETE'])
def manage_regions():
    """管理爬虫采集的区域"""
    if request.method == 'GET':
        regions = list(db.crawl_regions.find({}))
        return json.loads(json_util.dumps(regions))
    
    if request.method == 'POST':
        data = request.json
        # 简单验证
        if not all(k in data for k in ('name', 'lat_min', 'lat_max', 'lng_min', 'lng_max')):
            return jsonify({"error": "缺少必要坐标参数"}), 400
        
        region_doc = {
            "name": data['name'],
            "coords": {
                "lat_min": str(data['lat_min']),
                "lat_max": str(data['lat_max']),
                "lng_min": str(data['lng_min']),
                "lng_max": str(data['lng_max'])
            },
            "active": True,
            "created_at": datetime.datetime.now()
        }
        res = db.crawl_regions.insert_one(region_doc)
        return jsonify({"status": "success", "id": str(res.inserted_id)})

    if request.method == 'DELETE':
        region_id = request.args.get('id')
        if region_id:
            db.crawl_regions.delete_one({"_id": ObjectId(region_id)})
            return jsonify({"status": "deleted"})
        return jsonify({"error": "ID required"}), 400

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)