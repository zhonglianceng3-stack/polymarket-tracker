"""
Polymarket 套利监控 Web App - 官方API版（稳定版）
使用Polymarket官方Gamma API + 多重数据源
"""

from flask import Flask, render_template, jsonify, request
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

# 默认数据（用于降级）
DEFAULT_DATA = {
    "musk": {
        "tweets": 113,
        "prices": {
            "180-199": "31",
            "200-219": "22",
            "160-179": "20",
            "220-239": "14",
            "240-259": "8"
        },
        "period": "7月31日-8月7日",
        "remaining": "约2天17小时",
        "prediction": "当前113条，日均22.6条",
        "last_update": ""
    },
    "weather": {
        "current_temp": 26,
        "humidity": 85,
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

def save_data():
    """保存数据"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✓ 数据已保存")
    except Exception as e:
        print(f"✗ 保存数据失败: {e}")

def fetch_polymarket_official():
    """使用Polymarket官方Gamma API获取数据（最稳定）"""
    try:
        print("  → 请求Polymarket官方API...")
        
        # Gamma API endpoint
        url = "https://gamma-api.polymarket.com/markets"
        params = {"slug": "elon-musk-of-tweets-july-31-august-7"}
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; PolymarketMonitor/1.0)',
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
                    print(f"  ✓ 价格数据: {len(prices)}个区间")
                
                # 从市场描述中提取推文数
                description = market.get('description', '')
                
                # 查找类似 "How many tweets will Elon Musk send" 和实际推文数
                # 尝试多种模式
                patterns = [
                    r'(\d{2,4})\s*tweets',
                    r'(\d{2,4})\s+posts',
                    r'tweets?:\s*(\d{2,4})'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        tweets = int(match.group(1))
                        if 80 <= tweets <= 300:
                            data["musk"]["tweets"] = tweets
                            print(f"  ✓ 推文数: {tweets}")
                            break
                
                # 更新时间
                data["musk"]["last_update"] = datetime.now().strftime("%H:%M:%S")
                
                return True
        else:
            print(f"  ✗ API请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ✗ Polymarket API错误: {e}")
        return False

def fetch_weather_api():
    """获取天气数据"""
    try:
        print("  → 请求天气API...")
        
        url = "https://wttr.in/Shenzhen?format=j1"
        headers = {'User-Agent': 'curl'}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            weather_data = response.json()
            current = weather_data.get('current_condition', [{}])[0]
            
            temp_c = int(current.get('temp_C', 0))
            humidity = int(current.get('humidity', 0))
            
            data["weather"]["current_temp"] = temp_c
            data["weather"]["humidity"] = humidity
            data["weather"]["last_update"] = datetime.now().strftime("%H:%M:%S")
            
            print(f"  ✓ 温度: {temp_c}°C, 湿度: {humidity}%")
            return True
        else:
            print(f"  ✗ 天气请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ✗ 天气API错误: {e}")
        return False

def fetch_xtracker_page():
    """尝试从XTracker页面抓取（备用）"""
    try:
        print("  → 尝试XTracker页面...")
        
        url = "https://xtracker.polymarket.com/user/elonmusk"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            text = response.text
            
            # 查找推文数
            matches = re.findall(r'"(\d{2,4})".*?posts', text)
            
            if matches:
                # 找最大的合理值
                for match in reversed(matches):
                    num = int(match)
                    if 80 <= num <= 300:
                        data["musk"]["tweets"] = num
                        print(f"  ✓ XTracker推文数: {num}")
                        return True
            
            print(f"  ✗ XTracker未找到推文数")
            return False
        else:
            print(f"  ✗ XTracker请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ✗ XTracker错误: {e}")
        return False

def update_all_data():
    """更新所有数据"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 更新数据...")
    
    # 方法1：Polymarket官方API（最稳定）
    success = fetch_polymarket_official()
    
    # 方法2：如果官方API没获取到推文数，尝试XTracker
    if not success or data["musk"].get("tweets", 0) == 0:
        fetch_xtracker_page()
    
    # 获取天气数据
    fetch_weather_api()
    
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
    
    # 更新时间
    data["musk"]["last_update"] = datetime.now().strftime("%H:%M:%S")
    
    # 生成预测
    tweets = data["musk"].get("tweets", 0)
    if tweets > 0:
        daily_avg = tweets / 5
        data["musk"]["prediction"] = f"当前{tweets}条，日均{daily_avg:.1f}条"
    
    # 保存数据
    save_data()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ 数据更新完成\n")

def background_monitor():
    """后台监控"""
    print("=" * 60)
    print("🚀 Polymarket 套利监控 Web App 启动")
    print("📱 访问: https://polymarket-tracker-production-dd79.up.railway.app")
    print("📊 数据源: Polymarket官方API + wttr.in")
    print("🔄 更新频率: 每5分钟")
    print("=" * 60)
    
    update_all_data()
    
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
        return jsonify({
            "status": "success",
            "message": "数据已刷新",
            "tweets": data["musk"].get("tweets", 0),
            "last_update": data["musk"].get("last_update", "")
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/manual-update', methods=['POST'])
def manual_update():
    """手动更新推文数（用于本地数据源）"""
    try:
        content = request.json
        tweets = content.get('tweets', 0)
        
        if tweets > 0:
            data["musk"]["tweets"] = tweets
            data["musk"]["last_update"] = datetime.now().strftime("%H:%M:%S")
            
            daily_avg = tweets / 5
            data["musk"]["prediction"] = f"当前{tweets}条，日均{daily_avg:.1f}条"
            
            save_data()
            
            return jsonify({
                "status": "success",
                "message": f"推文数已更新为{tweets}条"
            })
        else:
            return jsonify({"status": "error", "message": "无效的推文数"})
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/alerts/clear', methods=['POST'])
def clear_alerts():
    try:
        data["alerts"] = []
        save_data()
        return jsonify({"status": "success"})
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

if __name__ == '__main__':
    load_data()
    print("\n🌐 启动Web服务器...")
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)