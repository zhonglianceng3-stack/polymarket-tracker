"""
Polymarket 套利监控 Web App - 完整版
支持本地监控脚本推送数据
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATA_FILE = 'data.json'

# 默认数据
data = {
    "musk": {
        "tweets": 115,
        "prices": {
            "180-199": "31",
            "200-219": "22",
            "160-179": "20",
            "220-239": "14",
            "240-259": "8"
        },
        "period": "7月31日-8月7日",
        "remaining": "约2天17小时",
        "prediction": "当前115条，日均23.0条",
        "last_update": ""
    },
    "weather": {
        "current_temp": 25,
        "humidity": 89,
        "forecast_high": 31,
        "prices": {
            "29°C": "20",
            "30°C": "45",
            "31°C": "30",
            "32°C": "5"
        },
        "prediction": "⚠️ 套利机会！预报31°C，但概率只有30%",
        "last_update": ""
    },
    "tweets_list": [],
    "alerts": []
}

def load_data():
    global data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                if loaded.get("musk", {}).get("tweets", 0) > 0:
                    data = loaded
        except:
            pass

def save_data():
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    return jsonify(data)

@app.route('/api/manual-update', methods=['POST'])
def manual_update():
    """接收本地监控脚本推送的数据"""
    try:
        content = request.json
        
        # 更新推文数
        if 'tweets' in content:
            data["musk"]["tweets"] = content["tweets"]
        
        # 更新价格
        if 'prices' in content:
            data["musk"]["prices"] = content["prices"]
        
        # 更新剩余时间
        if 'remaining' in content:
            data["musk"]["remaining"] = content["remaining"]
        
        # 更新预测
        if 'prediction' in content:
            data["musk"]["prediction"] = content["prediction"]
        
        # 更新天气
        if 'temp_c' in content:
            data["weather"]["current_temp"] = content["temp_c"]
        
        if 'humidity' in content:
            data["weather"]["humidity"] = content["humidity"]
        
        # 更新最新推文
        if 'latest_tweets' in content:
            data["tweets_list"] = content["latest_tweets"]
        
        # 更新时间
        now = datetime.now().strftime("%H:%M:%S")
        data["musk"]["last_update"] = now
        data["weather"]["last_update"] = now
        
        # 保存
        save_data()
        
        return jsonify({
            "status": "success",
            "message": f"数据已更新（推文数：{data['musk']['tweets']}，温度：{data['weather']['current_temp']}°C）",
            "tweets": data["musk"]["tweets"],
            "last_update": now
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "time": datetime.now().isoformat(),
        "tweets": data["musk"].get("tweets", 0),
        "last_update": data["musk"].get("last_update", "")
    })

# 加载数据
load_data()

if __name__ == '__main__':
    print("🌐 启动Web服务器...")
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)