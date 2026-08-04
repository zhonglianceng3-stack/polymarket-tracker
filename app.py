#!/usr/bin/env python3
"""
Polymarket 套利监控 Web App - 完整版
支持实时数据更新、变化推送、实时信息板块
"""

from flask import Flask, render_template, jsonify
import json
import os
from datetime import datetime, timedelta
import threading
import time
import sys

# 添加monitors目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monitors.scrapers import PolymarketScraper, WundergroundScraper, TwitterScraper

app = Flask(__name__)

# 数据存储
DATA_FILE = "data.json"

# 初始化抓取器
pm_scraper = PolymarketScraper()
wu_scraper = WundergroundScraper()
twitter_scraper = TwitterScraper()

def load_data():
    """加载数据"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return get_default_data()

def save_data(data):
    """保存数据"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_default_data():
    """默认数据结构"""
    return {
        "last_update": datetime.now().isoformat(),
        "musk": {
            "current": {
                "name": "7月31日-8月7日",
                "tweets": 0,
                "time_left": "计算中...",
                "prices": {},
                "prediction": "等待数据..."
            },
            "next": {
                "name": "8月7日-8月14日",
                "tweets": 0,
                "time_left": "未开始",
                "prices": {},
                "prediction": "等待数据..."
            }
        },
        "weather": {
            "shenzhen": {
                "today": {
                    "current_temp": None,
                    "forecast_high": None,
                    "humidity": None,
                    "prices": {},
                    "prediction": "等待数据..."
                }
            }
        },
        "realtime": {
            "musk_tweets": [],
            "wu_temp": {
                "temp_c": None,
                "humidity": None,
                "update_time": None
            }
        },
        "alerts": []
    }

def calculate_time_left():
    """计算剩余时间"""
    end_time = datetime(2026, 8, 8, 1, 0, 0)
    now = datetime.now()
    
    if now >= end_time:
        return "已结束"
    
    delta = end_time - now
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    
    if days > 0:
        return f"约{days}天{hours}小时"
    elif hours > 0:
        return f"约{hours}小时{minutes}分钟"
    else:
        return f"约{minutes}分钟"

def generate_musk_prediction(tweets, prices):
    """生成马斯克盘口预测"""
    if not tweets or not prices:
        return "等待数据..."
    
    days_left = 4
    target_200 = 200 - tweets
    daily_needed = target_200 / days_left if days_left > 0 else 0
    
    max_prob = 0
    max_range = ""
    for range_val, prob_str in prices.items():
        try:
            prob = float(prob_str)
            if prob > max_prob:
                max_prob = prob
                max_range = range_val
        except:
            pass
    
    if daily_needed <= 20:
        return f"推文速度需{daily_needed:.0f}条/天，建议关注{max_range}区间"
    elif daily_needed <= 25:
        return f"推文速度需{daily_needed:.0f}条/天，建议关注{max_range}区间"
    else:
        return f"推文速度需{daily_needed:.0f}条/天，建议关注中低区间"

def generate_weather_prediction(current_temp, prices):
    """生成天气盘口预测"""
    if not prices:
        return "等待数据..."
    
    max_prob = 0
    max_temp = ""
    for temp, prob_str in prices.items():
        try:
            prob = float(prob_str)
            if prob > max_prob:
                max_prob = prob
                max_temp = temp
        except:
            pass
    
    if max_prob < 40 and current_temp:
        return f"⚠️ 套利机会！当前{current_temp}°C，{max_temp}概率仅{max_prob}%，建议关注"
    
    return f"市场预测{max_temp}，概率{max_prob}%"

def check_changes(old_data, new_data):
    """检测变化并生成提醒"""
    alerts = []
    
    # 检测马斯克推文变化
    old_tweets = old_data.get('musk', {}).get('current', {}).get('tweets', 0)
    new_tweets = new_data.get('musk', {}).get('current', {}).get('tweets', 0)
    
    if new_tweets > old_tweets and old_tweets > 0:
        diff = new_tweets - old_tweets
        alerts.append({
            "type": "musk_tweet",
            "time": datetime.now().isoformat(),
            "message": f"🐦 马斯克发推了！新增{diff}条推文，当前共{new_tweets}条"
        })
    
    # 检测温度变化
    old_temp = old_data.get('weather', {}).get('shenzhen', {}).get('today', {}).get('current_temp')
    new_temp = new_data.get('weather', {}).get('shenzhen', {}).get('today', {}).get('current_temp')
    
    if new_temp and old_temp and new_temp > old_temp:
        diff = new_temp - old_temp
        alerts.append({
            "type": "temp_rise",
            "time": datetime.now().isoformat(),
            "message": f"🌡️ 温度上涨{diff}°C！当前{new_temp}°C"
        })
    
    return alerts

def update_data():
    """更新数据"""
    global data
    
    old_data = load_data()
    new_data = get_default_data()
    
    try:
        # 1. 抓取马斯克盘口
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 抓取马斯克盘口...")
        musk_data = pm_scraper.fetch_musk_market()
        
        if musk_data:
            new_data['musk']['current']['tweets'] = musk_data.get('tweets', 0)
            new_data['musk']['current']['prices'] = musk_data.get('prices', {})
            new_data['musk']['current']['time_left'] = calculate_time_left()
            new_data['musk']['current']['prediction'] = generate_musk_prediction(
                musk_data.get('tweets', 0),
                musk_data.get('prices', {})
            )
        
        # 2. 抓取深圳温度
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 抓取深圳温度...")
        temp_data = wu_scraper.fetch_shenzhen_temp()
        
        if temp_data:
            new_data['weather']['shenzhen']['today']['current_temp'] = temp_data.get('temp_c')
            new_data['weather']['shenzhen']['today']['humidity'] = temp_data.get('humidity')
            
            # 更新实时温度板块
            new_data['realtime']['wu_temp'] = {
                "temp_c": temp_data.get('temp_c'),
                "humidity": temp_data.get('humidity'),
                "update_time": datetime.now().strftime('%H:%M:%S')
            }
        
        # 3. 抓取天气盘口
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 抓取天气盘口...")
        weather_data = pm_scraper.fetch_weather_market()
        
        if weather_data:
            new_data['weather']['shenzhen']['today']['prices'] = weather_data.get('prices', {})
            new_data['weather']['shenzhen']['today']['prediction'] = generate_weather_prediction(
                new_data['weather']['shenzhen']['today'].get('current_temp'),
                weather_data.get('prices', {})
            )
        
        # 4. 抓取马斯克最新推文（实时信息板块）
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 抓取最新推文...")
        tweets_data = twitter_scraper.fetch_latest_tweets()
        
        if tweets_data:
            new_data['realtime']['musk_tweets'] = tweets_data.get('tweets', [])
        
        # 检测变化
        alerts = check_changes(old_data, new_data)
        new_data['alerts'] = alerts + old_data.get('alerts', [])[:10]
        
        new_data['last_update'] = datetime.now().isoformat()
        
        # 保存数据
        save_data(new_data)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 数据更新完成")
        
        if alerts:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔔 发现{len(alerts)}条新提醒")
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 更新失败: {e}")

def get_update_interval():
    """动态计算更新间隔（A+B组合）"""
    now = datetime.now()
    end_time = datetime(2026, 8, 8, 1, 0, 0)
    time_left = end_time - now
    
    # 关键时段（最后24小时）：每1分钟
    if time_left < timedelta(hours=24):
        return 60
    
    # 发推高峰时段（北京时间06:00-12:00）：每1分钟
    if 6 <= now.hour <= 12:
        return 60
    
    # 其他时段：每5分钟
    return 300

def background_monitor():
    """后台监控线程"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 后台监控启动")
    
    # 首次更新
    update_data()
    
    while True:
        try:
            interval = get_update_interval()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ 下次更新: {interval}秒后")
            
            time.sleep(interval)
            update_data()
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 监控错误: {e}")
            time.sleep(60)

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

@app.route('/api/reset', methods=['POST'])
def reset_data():
    """重置数据"""
    new_data = get_default_data()
    save_data(new_data)
    return jsonify({"status": "ok", "message": "数据已重置"})

@app.route('/api/refresh', methods=['POST'])
def manual_refresh():
    """手动刷新"""
    update_data()
    return jsonify({"status": "ok", "message": "数据已刷新"})

# 启动后台线程
monitor_thread = threading.Thread(target=background_monitor, daemon=True)
monitor_thread.start()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    print("=" * 50)
    print("🚀 Polymarket 套利监控 Web App 启动")
    print(f"📱 访问: http://localhost:{port}")
    print("📊 实时监控已启动")
    print("🐦 马斯克推文监控: 启用")
    print("🌡️ WU温度监控: 启用")
    print("=" * 50)
    app.run(debug=False, host='0.0.0.0', port=port)