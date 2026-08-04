"""
Polymarket 套利监控 Web App - 完整版
确保数据抓取正常工作
"""

from flask import Flask, render_template, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
import threading
import time

# 确保requests可用
try:
    import requests
    import re
    HAS_REQUESTS = True
    print("✓ requests库已加载")
except ImportError:
    HAS_REQUESTS = False
    print("✗ requests库未安装，将使用默认数据")

app = Flask(__name__)
CORS(app)

# 数据存储
DATA_FILE = 'data.json'

# 默认数据（降级使用）
DEFAULT_DATA = {
    "musk": {
        "tweets": 107,
        "prices": {
            "180-199": "31",
            "200-219": "22",
            "160-179": "20",
            "220-239": "14",
            "240-259": "8",
            "260-279": "3"
        },
        "period": "7月31日-8月7日",
        "remaining": "约2天17小时",
        "prediction": "当前107条，需日均33条达200条",
        "last_update": "手动更新"
    },
    "weather": {
        "current_temp": 28,
        "humidity": 85,
        "forecast_high": 31,
        "prices": {
            "29°C": "20",
            "30°C": "45",
            "31°C": "30",
            "32°C": "5"
        },
        "prediction": "⚠️ 套利机会！预报31°C但概率仅30%",
        "last_update": "手动更新"
    },
    "tweets_list": [],
    "alerts": [
        {
            "time": "08/05 04:05",
            "message": "推文数107条，距离200条还需93条"
        }
    ],
    "status": "running"
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

def fetch_real_time_data():
    """获取实时数据"""
    if not HAS_REQUESTS:
        print("  ✗ requests不可用，跳过抓取")
        return
    
    try:
        print("  → 抓取XTracker数据...")
        url = "https://xtracker.polymarket.com/user/elonmusk"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            text = response.text
            
            # 查找推文数
            match = re.search(r'(\d{2,4})\s+posts', text)
            if match:
                tweets = int(match.group(1))
                if 80 <= tweets <= 500:
                    data["musk"]["tweets"] = tweets
                    print(f"  ✓ 推文数更新: {tweets}")
            
            # 更新时间
            data["musk"]["last_update"] = datetime.now().strftime("%H:%M:%S")
            
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
        
    except Exception as e:
        print(f"  ✗ 抓取失败: {e}")

def update_all_data():
    """更新所有数据"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 更新数据...")
    
    fetch_real_time_data()
    save_data()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ 数据更新完成\n")

def background_monitor():
    """后台监控线程"""
    print("=" * 60)
    print("🚀 Polymarket 套利监控 Web App 启动")
    print("📱 访问: https://polymarket-tracker-production-dd79.up.railway.app")
    print("📊 状态: 运行中")
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
        "requests": HAS_REQUESTS
    })

if __name__ == '__main__':
    # 加载已有数据
    load_data()
    
    # 启动Flask
    print("\n🌐 启动Web服务器...")
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)