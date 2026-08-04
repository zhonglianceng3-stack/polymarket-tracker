"""
Polymarket 套利监控 Web App - API版本
使用官方API获取准确数据
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
import os
from datetime import datetime, timezone, timedelta
import threading
import time

# 导入新的API模块
from monitors.scrapers import XTrackerAPI, PolymarketAPI, WundergroundScraper, WeatherMarketAPI

app = Flask(__name__)
CORS(app)

# 数据存储
DATA_FILE = 'data.json'
data = {
    "musk": {
        "tweets": 0,
        "prices": {},
        "period": "7月31日-8月7日",
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

# API实例
xtracker_api = XTrackerAPI()
polymarket_api = PolymarketAPI()
wu_scraper = WundergroundScraper()
weather_api = WeatherMarketAPI()

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

def update_musk_data():
    """更新马斯克数据"""
    print("[{}] 抓取马斯克盘口...".format(datetime.now().strftime("%H:%M:%S")))
    
    # 获取推文数
    tweets = xtracker_api.get_tweet_count()
    if tweets:
        data["musk"]["tweets"] = tweets
    
    # 获取价格数据
    prices, market_info = polymarket_api.get_market_prices(slug="elon-musk-of-tweets-july-31-august-7")
    if prices:
        data["musk"]["prices"] = prices
    
    data["musk"]["last_update"] = datetime.now().strftime("%H:%M:%S")
    
    # 计算剩余时间
    end_time = datetime(2026, 8, 7, 12, 0, 0)  # 美东时间8月7日12:00 PM
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
    
    # 获取WU实时温度
    temp_data = wu_scraper.fetch_shenzhen_temp()
    if temp_data:
        data["weather"]["temp_c"] = temp_data.get("temp_c")
        data["weather"]["humidity"] = temp_data.get("humidity")
        data["weather"]["last_update"] = temp_data.get("last_update")
    
    # 获取天气盘口价格
    print("[{}] 抓取天气盘口...".format(datetime.now().strftime("%H:%M:%S")))
    weather_prices = weather_api.fetch_weather_market()
    if weather_prices:
        data["weather"]["market_prices"] = weather_prices

def update_latest_tweets():
    """获取最新推文列表（暂时禁用，因为Nitter不稳定）"""
    print("[{}] 抓取最新推文...".format(datetime.now().strftime("%H:%M:%S")))
    # 暂时跳过推文列表抓取
    pass

def update_all_data():
    """更新所有数据"""
    update_musk_data()
    update_weather_data()
    update_latest_tweets()
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
        # 等待5分钟
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