#!/usr/bin/env python3
"""
Polymarket 套利监控 Web App
"""

from flask import Flask, render_template, jsonify
import json
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)

# 数据存储
DATA_FILE = "data.json"

def load_data():
    """加载数据"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "musk": {
            "tweets": 0,
            "prices": {},
            "last_update": None,
            "prediction": None
        },
        "weather": {
            "current_temp": 0,
            "forecast_high": 0,
            "prices": {},
            "last_update": None,
            "prediction": None
        },
        "alerts": []
    }

def save_data(data):
    """保存数据"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 初始化数据
data = load_data()

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """获取数据API"""
    return jsonify(load_data())

@app.route('/api/alerts/clear', methods=['POST'])
def clear_alerts():
    """清除提醒"""
    d = load_data()
    d['alerts'] = []
    save_data(d)
    return jsonify({"status": "ok"})

def background_monitor():
    """后台监控线程"""
    while True:
        try:
            # TODO: 添加实际监控逻辑
            # 这里会在后续添加WU、Polymarket数据获取
            
            # 更新时间戳
            d = load_data()
            d['musk']['last_update'] = datetime.now().isoformat()
            d['weather']['last_update'] = datetime.now().isoformat()
            save_data(d)
            
        except Exception as e:
            print(f"监控错误: {e}")
        
        time.sleep(60)  # 每分钟检查一次

# 启动后台线程
monitor_thread = threading.Thread(target=background_monitor, daemon=True)
monitor_thread.start()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    print("🚀 Polymarket 套利监控 Web App 启动")
    print(f"📱 访问: http://localhost:{port}")
    app.run(debug=False, host='0.0.0.0', port=port)