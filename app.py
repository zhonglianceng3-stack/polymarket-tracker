"""
Polymarket 套利监控 Web App - 简化版
直接使用XTracker页面获取准确数据
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests
import json
import re
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)
CORS(app)

# 数据存储
DATA_FILE = 'data.json'
data = {
    "musk": {
        "tweets": 0,
        "prices": {},
        "period": "7月31日-8月7日",
        "remaining": "",
        "last_update": ""
    },
    "weather": {
        "temp_c": None,
        "humidity": None,
        "market_prices": {},
        "last_update": ""
    },
    "tweets_list": [],
    "alerts": []
}

def load_data():
    """加载数据"""
    global data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            pass

def save_data():
    """保存数据"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存数据失败: {e}")

def fetch_xtracker_tweets():
    """从XTracker获取推文数"""
    try:
        print("  → 请求XTracker...")
        url = "https://xtracker.polymarket.com/user/elonmusk"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"  ✗ XTracker失败: {response.status_code}")
            return None
        
        text = response.text
        
        # 查找 "Elon Musk # tweets July 31 - August 7, 2026?" 对应的推文数
        # 从HTML中提取数字
        
        # 方法：查找特定period的posts数
        # 格式：Elon Musk # tweets July 31 - August 7, 2026? ... <number> posts
        
        # 使用正则查找
        pattern = r'Elon Musk # tweets July 31 - August 7, 2026\?.*?(\d{2,4})\s+posts'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        
        if match:
            tweets = int(match.group(1))
            print(f"  ✓ XTracker推文数: {tweets}")
            return tweets
        
        print("  ✗ 未找到推文数")
        return None
        
    except Exception as e:
        print(f"  ✗ XTracker错误: {e}")
        return None

def fetch_polymarket_prices():
    """从Polymarket获取价格分布"""
    try:
        print("  → 请求Polymarket...")
        url = "https://polymarket.com/event/elon-musk-of-tweets-july-31-august-7"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"  ✗ Polymarket失败: {response.status_code}")
            return None
        
        text = response.text
        
        # 提取价格数据
        prices = {}
        
        # 查找所有区间和概率
        # 格式: "180-199" 和 "31%"
        
        # 先找所有区间
        ranges = re.findall(r'(\d{3}-\d{3})', text)
        
        # 去重并排序
        ranges = sorted(set(ranges), key=lambda x: int(x.split('-')[0]))
        
        # 对每个区间，在其附近找概率
        for i, range_val in enumerate(ranges):
            # 在文本中找这个区间的位置
            pos = text.find(range_val)
            if pos != -1:
                # 在后面200字符内查找概率
                nearby = text[pos:pos+200]
                prob_match = re.search(r'(\d+(?:\.\d+)?)\s*%', nearby)
                if prob_match:
                    prob = prob_match.group(1)
                    prices[range_val] = prob
        
        print(f"  ✓ 价格数据: {len(prices)}个区间")
        return prices
        
    except Exception as e:
        print(f"  ✗ Polymarket错误: {e}")
        return None

def fetch_wu_temperature():
    """从Wunderground获取温度"""
    try:
        print("  → 请求WU...")
        url = "https://www.wunderground.com/weather/cn/shenzhen"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"  ✗ WU失败: {response.status_code}")
            return None
        
        text = response.text
        
        # 提取华氏度
        fahrenheit_match = re.search(r'(\d{2,3})\s*°F', text)
        
        temp_c = None
        humidity = None
        
        if fahrenheit_match:
            temp_f = int(fahrenheit_match.group(1))
            temp_c = round((temp_f - 32) * 5 / 9)
            print(f"  ✓ 温度: {temp_f}°F = {temp_c}°C")
        
        # 提取湿度
        humidity_match = re.search(r'Humidity[^\d]*(\d+)', text, re.IGNORECASE)
        if humidity_match:
            humidity = int(humidity_match.group(1))
            print(f"  ✓ 湿度: {humidity}%")
        
        return {
            "temp_c": temp_c,
            "humidity": humidity,
            "last_update": datetime.now().strftime("%H:%M:%S")
        }
        
    except Exception as e:
        print(f"  ✗ WU错误: {e}")
        return None

def update_musk_data():
    """更新马斯克数据"""
    print("[{}] 抓取马斯克盘口...".format(datetime.now().strftime("%H:%M:%S")))
    
    # 获取推文数（从XTracker）
    tweets = fetch_xtracker_tweets()
    if tweets:
        data["musk"]["tweets"] = tweets
    
    # 获取价格分布（从Polymarket）
    prices = fetch_polymarket_prices()
    if prices:
        data["musk"]["prices"] = prices
    
    data["musk"]["last_update"] = datetime.now().strftime("%H:%M:%S")
    
    # 计算剩余时间
    # 结束时间：美东时间8月7日12:00 PM = 北京时间8月8日00:00
    end_time = datetime(2026, 8, 8, 0, 0, 0)
    now = datetime.now()
    remaining = end_time - now
    
    if remaining.total_seconds() > 0:
        days = remaining.days
        hours = remaining.seconds // 3600
        data["musk"]["remaining"] = f"约{days}天{hours}小时"
    else:
        data["musk"]["remaining"] = "已结束"

def update_weather_data():
    """更新天气数据"""
    print("[{}] 抓取深圳温度...".format(datetime.now().strftime("%H:%M:%S")))
    
    temp_data = fetch_wu_temperature()
    if temp_data:
        data["weather"]["temp_c"] = temp_data.get("temp_c")
        data["weather"]["humidity"] = temp_data.get("humidity")
        data["weather"]["last_update"] = temp_data.get("last_update")

def update_all_data():
    """更新所有数据"""
    update_musk_data()
    update_weather_data()
    save_data()
    print("[{}] ✅ 数据更新完成".format(datetime.now().strftime("%H:%M:%S")))

def background_monitor():
    """后台监控线程"""
    print("🚀 后台监控启动")
    print("=" * 50)
    print("🚀 Polymarket 套利监控 Web App 启动")
    print("📱 访问: http://localhost:8080")
    print("📊 实时监控已启动")
    print("🐦 马斯克推文监控: 启用")
    print("🌡️ WU温度监控: 启用")
    print("=" * 50)
    
    # 首次更新
    update_all_data()
    
    while True:
        print("[{}] ⏳ 下次更新: 300秒后".format(datetime.now().strftime("%H:%M:%S")))
        time.sleep(300)
        update_all_data()

# 启动后台监控
monitor_thread = threading.Thread(target=background_monitor, daemon=True)
monitor_thread.start()

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """获取数据API"""
    return jsonify(data)

@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """手动刷新数据"""
    update_all_data()
    return jsonify({"status": "success", "message": "数据已刷新"})

@app.route('/api/alerts/clear', methods=['POST'])
def clear_alerts():
    """清除提醒"""
    data["alerts"] = []
    save_data()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    # 加载已有数据
    load_data()
    
    # 启动Flask
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)