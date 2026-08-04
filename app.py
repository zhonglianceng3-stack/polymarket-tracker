"""
Polymarket 套利监控 Web App - 直接抓取版本
直接从XTracker和Polymarket页面抓取实时数据
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

def fetch_xtracker_real():
    """直接从XTracker抓取实时推文数"""
    try:
        print("  → 抓取XTracker实时数据...")
        
        url = "https://xtracker.polymarket.com/user/elonmusk"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache'
        }
        
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            text = response.text
            
            # 查找 "Elon Musk # tweets July 31 - August 7, 2026?" 对应的推文数
            # 格式：先找这个标题，然后在其附近找推文数
            
            # 方法1：直接查找该period的推文数
            # 在HTML中，这个period的结构是：
            # <heading>Elon Musk # tweets July 31 - August 7, 2026?</heading>
            # ...<数字> posts
            
            # 使用正则直接匹配
            # 找到 July 31 - August 7 区间，然后找其后的数字+posts
            
            # 方法：查找所有包含 posts 的数字
            posts_matches = re.findall(r'(\d{2,4})\s+posts', text)
            
            if posts_matches:
                # 遍历所有匹配，找最大的合理值（应该是当前盘口的推文数）
                for posts in reversed(posts_matches):
                    num = int(posts)
                    if 80 <= num <= 300:  # 合理范围
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
    """从Polymarket页面抓取价格分布"""
    try:
        print("  → 抓取Polymarket价格数据...")
        
        url = "https://polymarket.com/event/elon-musk-of-tweets-july-31-august-7"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache'
        }
        
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            text = response.text
            
            # 提取价格数据
            prices = {}
            
            # 查找所有区间（如 180-199）
            ranges = re.findall(r'(\d{3}-\d{3})', text)
            ranges = sorted(set(ranges), key=lambda x: int(x.split('-')[0]))
            
            # 对每个区间，查找其附近的概率
            for range_val in ranges:
                # 在文本中查找该区间
                pos = text.find(range_val)
                if pos != -1:
                    # 在该区间后面200字符内查找概率
                    nearby = text[pos:pos+200]
                    prob_match = re.search(r'(\d+(?:\.\d+)?)\s*%', nearby)
                    if prob_match:
                        prob = prob_match.group(1)
                        prices[range_val] = prob
            
            if prices:
                data["musk"]["prices"] = prices
                print(f"  ✓ 价格数据: {len(prices)}个区间")
                return True
            else:
                print(f"  ✗ 未找到价格数据")
                return False
        else:
            print(f"  ✗ Polymarket请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ✗ Polymarket抓取错误: {e}")
        return False

def fetch_weather_real():
    """获取实时天气数据"""
    try:
        print("  → 抓取实时天气...")
        
        # 使用wttr.in
        url = "https://wttr.in/Shenzhen?format=j1"
        headers = {
            'User-Agent': 'curl'
        }
        
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
    
    # 获取XTracker实时推文数
    fetch_xtracker_real()
    
    # 获取Polymarket价格分布
    fetch_polymarket_prices()
    
    # 获取天气数据
    fetch_weather_real()
    
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
    
    # 生成预测建议
    tweets = data["musk"].get("tweets", 0)
    if tweets > 0:
        # 计算日均推文数（从7月31日到现在）
        start_time = datetime(2026, 7, 31, 0, 0, 0)
        days_passed = (now - start_time).days
        if days_passed > 0:
            daily_avg = tweets / days_passed
            prediction = f"当前{tweets}条，日均{daily_avg:.1f}条"
            data["musk"]["prediction"] = prediction
    
    # 保存数据
    save_data()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ 数据更新完成\n")

def background_monitor():
    """后台监控线程"""
    print("=" * 60)
    print("🚀 Polymarket 套利监控 Web App 启动")
    print("📱 访问: https://polymarket-tracker-production-dd79.up.railway.app")
    print("📊 数据源: XTracker + Polymarket + wttr.in")
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
        "tweets": data["musk"].get("tweets", 0)
    })

if __name__ == '__main__':
    # 加载已有数据
    load_data()
    
    # 启动Flask
    print("\n🌐 启动Web服务器...")
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)