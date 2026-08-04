"""
Polymarket 套利监控 Web App - 官方API版本
使用Polymarket Gamma API和天气API获取准确数据
"""

from flask import Flask, render_template, jsonify
from flask_cors import CORS
import requests
import json
import os
from datetime import datetime
import threading
import time
import re

app = Flask(__name__)
CORS(app)

# 数据存储
DATA_FILE = 'data.json'

# 默认数据
DEFAULT_DATA = {
    "musk": {
        "tweets": 0,
        "prices": {},
        "period": "7月31日-8月7日",
        "remaining": "",
        "prediction": "等待数据...",
        "last_update": ""
    },
    "weather": {
        "current_temp": None,
        "humidity": None,
        "forecast_high": None,
        "prices": {},
        "prediction": "等待数据...",
        "last_update": ""
    },
    "tweets_list": [],
    "alerts": []
}

data = DEFAULT_DATA.copy()

def load_data():
    """加载数据"""
    global data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                if loaded.get("musk", {}).get("tweets", 0) > 0:
                    data = loaded
                    print("✓ 从缓存加载数据")
        except Exception as e:
            print(f"✗ 加载数据失败: {e}")
            data = DEFAULT_DATA.copy()

def save_data():
    """保存数据"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✓ 数据已保存")
    except Exception as e:
        print(f"✗ 保存数据失败: {e}")

def fetch_polymarket_market():
    """使用Polymarket Gamma API获取市场数据"""
    try:
        print("  → 请求Polymarket Gamma API...")
        
        # Gamma API endpoint
        url = "https://gamma-api.polymarket.com/markets"
        
        # 查询参数：搜索马斯克推文市场
        params = {
            "slug": "elon-musk-of-tweets-july-31-august-7"
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            markets = response.json()
            
            if markets and len(markets) > 0:
                market = markets[0]
                
                # 提取价格数据
                prices = {}
                tokens = market.get('tokens', [])
                
                for token in tokens:
                    outcome = token.get('outcome', '')
                    price = token.get('price', 0)
                    
                    # 提取区间
                    match = re.search(r'(\d{3}-\d{3})', outcome)
                    if match:
                        range_val = match.group(1)
                        prob = float(price) * 100 if price else 0
                        prices[range_val] = f"{prob:.0f}" if prob >= 1 else "<1"
                
                if prices:
                    data["musk"]["prices"] = prices
                    print(f"  ✓ 获取到{len(prices)}个价格区间")
                
                # 提取推文数（从市场描述中）
                description = market.get('description', '')
                
                # 查找类似 "107 posts" 的文本
                match = re.search(r'(\d{2,4})\s+posts', description, re.IGNORECASE)
                if match:
                    tweets = int(match.group(1))
                    data["musk"]["tweets"] = tweets
                    print(f"  ✓ 推文数: {tweets}")
                
                # 更新时间
                data["musk"]["last_update"] = datetime.now().strftime("%H:%M:%S")
                
                return True
        else:
            print(f"  ✗ API请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ✗ Polymarket API错误: {e}")
        return False

def fetch_weather_data():
    """获取天气数据"""
    try:
        print("  → 请求天气数据...")
        
        # 使用免费的天气API（wttr.in）
        url = "https://wttr.in/Shenzhen?format=j1"
        
        headers = {
            'User-Agent': 'curl'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            weather_data = response.json()
            
            # 提取当前温度
            current = weather_data.get('current_condition', [{}])[0]
            temp_c = int(current.get('temp_C', 0))
            humidity = int(current.get('humidity', 0))
            
            data["weather"]["current_temp"] = temp_c
            data["weather"]["humidity"] = humidity
            data["weather"]["last_update"] = datetime.now().strftime("%H:%M:%S")
            
            print(f"  ✓ 温度: {temp_c}°C, 湿度: {humidity}%")
            
            return True
        else:
            print(f"  ✗ 天气API失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ✗ 天气数据错误: {e}")
        return False

def update_all_data():
    """更新所有数据"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 更新数据...")
    
    # 获取Polymarket数据
    fetch_polymarket_market()
    
    # 获取天气数据
    fetch_weather_data()
    
    # 计算剩余时间
    end_time = datetime(2026, 8, 8, 0, 0, 0)
    now = datetime.now()
    remaining = end_time - now
    
    if remaining.total_seconds() > 0:
        days = remaining.days
        hours = remaining.seconds // 3600
        data["musk"]["remaining"] = f"约{days}天{hours}小时"
    else:
        data["musk"]["remaining"] = "已结束"
    
    # 生成预测建议
    tweets = data["musk"].get("tweets", 0)
    if tweets > 0:
        daily_rate = tweets / 5  # 假设已过5天
        prediction = f"当前{tweets}条，日均{daily_rate:.0f}条"
        data["musk"]["prediction"] = prediction
    
    # 保存数据
    save_data()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ 数据更新完成\n")

def background_monitor():
    """后台监控线程"""
    print("=" * 60)
    print("🚀 Polymarket 套利监控 Web App 启动")
    print("📱 访问: https://polymarket-tracker-production-dd79.up.railway.app")
    print("📊 数据源: Polymarket Gamma API + wttr.in")
    print("🔄 更新频率: 每5分钟")
    print("=" * 60)
    
    # 首次更新
    update_all_data()
    
    # 定时更新
    while True:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ 下次更新: 300秒后")
        time.sleep(300)
        update_all_data()

# 启动后台监控
try:
    monitor_thread = threading.Thread(target=background_monitor, daemon=True)
    monitor_thread.start()
    print("✓ 后台监控线程已启动")
except Exception as e:
    print(f"✗ 后台监控启动失败: {e}")

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """获取数据API"""
    try:
        return jsonify(data)
    except Exception as e:
        print(f"✗ API错误: {e}")
        return jsonify(DEFAULT_DATA)

@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """手动刷新数据"""
    try:
        update_all_data()
        return jsonify({"status": "success", "message": "数据已刷新"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/alerts/clear', methods=['POST'])
def clear_alerts():
    """清除提醒"""
    try:
        data["alerts"] = []
        save_data()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "time": datetime.now().isoformat(),
        "data_source": "official_api"
    })

if __name__ == '__main__':
    # 加载已有数据
    load_data()
    
    # 启动Flask
    print("\n🌐 启动Web服务器...")
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)