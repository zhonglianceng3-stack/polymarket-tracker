"""
Polymarket 套利监控 Web App - 最终修复版
直接从XTracker抓取实时推文数（修复版）
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
        "tweets": 113,
        "prices": {},
        "period": "7月31日-8月7日",
        "remaining": "",
        "prediction": "当前113条，日均22.6条",
        "last_update": ""
    },
    "weather": {
        "current_temp": 25,
        "humidity": 89,
        "forecast_high": 31,
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

def fetch_xtracker_tweets():
    """从XTracker抓取推文数（修复版）"""
    try:
        print("  → 抓取XTracker实时数据...")
        
        url = "https://xtracker.polymarket.com/user/elonmusk"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            text = response.text
            
            # 方法1：查找"July 31 - August 7"区间的推文数
            # 在XTracker中，格式是：
            # <heading>Elon Musk # tweets July 31 - August 7, 2026?</heading>
            # ... <generic>"113"</generic> <generic>posts</generic>
            
            # 查找July 31 - August 7区间的推文数
            # 使用更精确的正则
            pattern = r'July 31.*?August 7.*?"(\d+)".*?posts'
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            
            if match:
                tweets = int(match.group(1))
                if 80 <= tweets <= 300:
                    data["musk"]["tweets"] = tweets
                    print(f"  ✓ 推文数: {tweets}")
                    return True
            
            # 方法2：查找所有"数字 + posts"的组合
            # 然后找最大的合理值（应该是当前活跃盘口）
            posts_matches = re.findall(r'"(\d+)".*?posts', text, re.DOTALL)
            
            if posts_matches:
                # 找最大的合理值
                for posts in reversed(posts_matches):
                    num = int(posts)
                    if 80 <= num <= 300:  # 当前盘口应该在80-300之间
                        data["musk"]["tweets"] = num
                        print(f"  ✓ 推文数: {num}")
                        return True
            
            print(f"  ✗ 未找到有效推文数")
            return False
        else:
            print(f"  ✗ XTracker请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ✗ XTracker抓取错误: {e}")
        return False

def fetch_polymarket_prices():
    """从Polymarket抓取价格分布"""
    try:
        print("  → 抓取Polymarket价格数据...")
        
        url = "https://polymarket.com/event/elon-musk-of-tweets-july-31-august-7"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            text = response.text
            
            prices = {}
            ranges = re.findall(r'(\d{3}-\d{3})', text)
            ranges = sorted(set(ranges), key=lambda x: int(x.split('-')[0]))
            
            for range_val in ranges:
                pos = text.find(range_val)
                if pos != -1:
                    nearby = text[pos:pos+200]
                    prob_match = re.search(r'(\d+(?:\.\d+)?)\s*%', nearby)
                    if prob_match:
                        prob = prob_match.group(1)
                        prices[range_val] = prob
            
            if prices:
                data["musk"]["prices"] = prices
                print(f"  ✓ 价格数据: {len(prices)}个区间")
                return True
            
            print(f"  ✗ 未找到价格数据")
            return False
        else:
            print(f"  ✗ Polymarket请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ✗ Polymarket抓取错误: {e}")
        return False

def fetch_weather():
    """获取天气数据"""
    try:
        print("  → 抓取实时天气...")
        
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
        print(f"  ✗ 天气抓取错误: {e}")
        return False

def update_all_data():
    """更新所有数据"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 更新数据...")
    
    fetch_xtracker_tweets()
    fetch_polymarket_prices()
    fetch_weather()
    
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
    
    data["musk"]["last_update"] = datetime.now().strftime("%H:%M:%S")
    
    # 生成预测
    tweets = data["musk"].get("tweets", 0)
    if tweets > 0:
        daily_avg = tweets / 5
        data["musk"]["prediction"] = f"当前{tweets}条，日均{daily_avg:.1f}条"
    
    save_data()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ 数据更新完成\n")

def background_monitor():
    """后台监控"""
    print("=" * 60)
    print("🚀 Polymarket 套利监控 Web App 启动")
    print("📱 访问: https://polymarket-tracker-production-dd79.up.railway.app")
    print("📊 数据源: XTracker + Polymarket + wttr.in")
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
    try:
        return jsonify(data)
    except Exception as e:
        print(f"✗ API错误: {e}")
        return jsonify(DEFAULT_DATA)

@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    try:
        update_all_data()
        return jsonify({"status": "success", "message": "数据已刷新"})
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
        "tweets": data["musk"].get("tweets", 0)
    })

if __name__ == '__main__':
    load_data()
    print("\n🌐 启动Web服务器...")
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)