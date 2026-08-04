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
    return get_default_data()

def get_default_data():
    """默认数据结构"""
    return {
        "last_update": datetime.now().isoformat(),
        "musk": {
            "current": {
                "name": "7月31日-8月7日",
                "tweets": 96,
                "time_left": "约4天",
                "prices": {
                    "80-99": "<1",
                    "100-119": "<1",
                    "120-139": "1",
                    "140-159": "8",
                    "160-179": "20",
                    "180-199": "26",
                    "200-219": "21",
                    "220-239": "13",
                    "240-259": "6",
                    "260-279": "3",
                    "280-299": "1",
                    "300-319": "<1",
                    "320-339": "<1",
                    "340-359": "<1",
                    "360-379": "<1",
                    "380-399": "<1",
                    "400-419": "<1"
                },
                "highlight": "180-199",
                "prediction": "推文速度需26条/天达200条，建议关注160-199区间"
            },
            "next": {
                "name": "8月7日-8月14日",
                "tweets": 0,
                "time_left": "未开始",
                "prices": {
                    "100-119": "1",
                    "120-139": "3",
                    "140-159": "8",
                    "160-179": "15",
                    "180-199": "22",
                    "200-219": "20",
                    "220-239": "15",
                    "240-259": "8",
                    "260-279": "4",
                    "280-299": "2"
                },
                "highlight": "180-199",
                "prediction": "新盘口，等待数据"
            }
        },
        "weather": {
            "shenzhen": {
                "today": {
                    "current_temp": 28,
                    "forecast_high": 31,
                    "prices": {
                        "26°C": "1",
                        "27°C": "3",
                        "28°C": "10",
                        "29°C": "20",
                        "30°C": "35",
                        "31°C": "25",
                        "32°C": "5",
                        "33°C": "1"
                    },
                    "highlight": "30°C",
                    "prediction": "⚠️ 套利机会！预报31°C但30°C概率仅35%，建议买入30-31°C"
                },
                "tomorrow": {
                    "forecast_high": 32,
                    "prices": {
                        "27°C": "2",
                        "28°C": "5",
                        "29°C": "12",
                        "30°C": "25",
                        "31°C": "30",
                        "32°C": "18",
                        "33°C": "6",
                        "34°C": "2"
                    },
                    "highlight": "31°C",
                    "prediction": "预报32°C，31°C概率30%，可考虑买入"
                }
            },
            "beijing": {
                "today": {
                    "current_temp": 30,
                    "forecast_high": 34,
                    "prices": {
                        "30°C": "5",
                        "31°C": "10",
                        "32°C": "18",
                        "33°C": "30",
                        "34°C": "25",
                        "35°C": "10",
                        "36°C": "2"
                    },
                    "highlight": "33°C",
                    "prediction": "预报34°C，33-34°C概率较高"
                }
            },
            "shanghai": {
                "today": {
                    "current_temp": 29,
                    "forecast_high": 33,
                    "prices": {
                        "28°C": "3",
                        "29°C": "8",
                        "30°C": "15",
                        "31°C": "25",
                        "32°C": "30",
                        "33°C": "15",
                        "34°C": "4"
                    },
                    "highlight": "32°C",
                    "prediction": "预报33°C，32°C概率最高"
                }
            }
        },
        "alerts": [
            {
                "time": datetime.now().isoformat(),
                "message": "深圳天气盘口：预报31°C但30°C概率仅35%，存在套利机会"
            }
        ]
    }

def save_data(data):
    """保存数据"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 初始化数据
data = load_data()
save_data(data)

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
    """重置数据为新结构"""
    new_data = get_default_data()
    save_data(new_data)
    return jsonify({"status": "ok", "message": "数据已重置"})

def background_monitor():
    """后台监控线程"""
    while True:
        try:
            # TODO: 添加实际监控逻辑
            # 这里会在后续添加WU、Polymarket数据获取
            
            # 更新时间戳
            d = load_data()
            d['last_update'] = datetime.now().isoformat()
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