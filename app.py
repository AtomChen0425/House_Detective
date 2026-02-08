from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from bson import json_util, ObjectId
from flask_cors import CORS
import json
import datetime
import os
from passlib.hash import pbkdf2_sha256
app = Flask(__name__, static_folder='frontend/dist', static_url_path='')
CORS(app, resources={r"/api/*": {"origins": "*"}})

mongo_uri = os.getenv("MONGO_URI", "mongodb://mongo:27017/") #"mongodb://192.168.2.24:27017/"
client = MongoClient(mongo_uri)
db = client.House_Analysis_Canada


def init_admin():
    if db.users.count_documents({"username": "admin"}) == 0:
        hashed_password = pbkdf2_sha256.hash("admin123") # 初始加密密码
        db.users.insert_one({
            "username": "admin",
            "password": hashed_password,
            "role": "admin",
            "created_at": datetime.datetime.now()
        })
        print("Admin user initialized.")

init_admin()

# --- 登录接口 ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = db.users.find_one({"username": username})
    

    if user and pbkdf2_sha256.verify(password, user['password']):
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "token": "admin-session-token", # 实际生产环境应使用 JWT
            "user": {"username": user['username'], "role": user['role']}
        })
    else:
        return jsonify({
            "status": "error", 
            "message": "username or password error"
        }), 401
        
@app.route('/api/config/update-password', methods=['POST'])
def update_password():
    data = request.json
    # 从请求体中提取 username
    username = data.get('username') 
    old_password = data.get('oldPassword')
    new_password = data.get('newPassword')

    if not username:
        return jsonify({"status": "error", "message": "Missing username"}), 400

    # 查找指定用户
    user = db.users.find_one({"username": username})
    
    if user and pbkdf2_sha256.verify(old_password, user['password']):
        # 加密并更新
        new_hashed = pbkdf2_sha256.hash(new_password)
        db.users.update_one(
            {"username": username}, 
            {"$set": {"password": new_hashed}}
        )
        return jsonify({"status": "success", "message": "Password updated successfully"})
    else:
        return jsonify({"status": "error", "message": "Old password is incorrect"}), 400
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
@app.route('/api/config/cookie', methods=['GET', 'POST', 'DELETE'])
def manage_cookie():
    if request.method == 'POST':
        data = request.json
        cookie_id = data.get("id")  # 如果前端传了 ID，就是修改
        cookie_str = data.get("cookie")
        
        update_data = {
            "cookie": cookie_str,
            "status": "active",
            "last_updated": datetime.datetime.now()
        }

        if cookie_id:
            # 修改
            db.config.update_one({"_id": ObjectId(cookie_id)}, {"$set": update_data})
            return jsonify({"status": "success", "message": "Cookie 已更新"})
        else:
            # 新增
            update_data["type"] = "realtor_config"
            db.config.insert_one(update_data)
            return jsonify({"status": "success", "message": "新 Cookie 已入池"})

    elif request.method == 'DELETE':
        cookie_id = request.args.get('id')
        count = db.config.count_documents({"type": "realtor_config"})
        if count <= 1:
            return jsonify({"status": "error", "message": "禁止删除：池中必须保留至少一个 Cookie"}), 403
        
        db.config.delete_one({"_id": ObjectId(cookie_id)})
        return jsonify({"status": "success", "message": "已成功删除"})

    else:
        configs = list(db.config.find({"type": "realtor_config"}))
        return json.loads(json_util.dumps(configs))
# --- 采集区域管理  ---

@app.route('/api/config/regions', methods=['GET', 'POST', 'DELETE'])
def manage_regions():
    """管理爬虫采集的区域"""
    if request.method == 'GET':
        regions = list(db.crawl_regions.find({}))
        return json.loads(json_util.dumps(regions))
    
    if request.method == 'POST':
        data = request.json
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