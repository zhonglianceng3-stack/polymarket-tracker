#!/usr/bin/env python3
"""
Polymarket 本地监控服务 - 完整版
自动抓取实时数据并推送到网站
运行方式：python3 polymarket_monitor.py
"""

import requests
import json
import time
import re
from datetime import datetime
import threading

# 配置
WEB_APP_URL = "https://polymarket-tracker-production-dd79.up.railway.app"
XTRACKER_URL = "https://xtracker.polymarket.com/user/elonmusk"
POLYMARKET_URL = "https://polymarket.com/event/elon-musk-of-tweets-july-31-august-7"
TWITTER_URL = "https://nitter.net/elonmusk"  # 使用Nitter镜像

class PolymarketMonitor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.data = {
            "tweets": 0,
            "prices": {},
            "remaining": "",
            "temp_c": 0,
            "humidity": 0,
            "latest_tweets": [],
            "last_update": ""
        }
    
    def fetch_tweets_count(self):
        """获取推文数"""
        try:
            print("📊 获取推文数...")
            response = self.session.get(XTRACKER_URL, timeout=20)
            
            if response.status_code == 200:
                text = response.text
                
                # 查找推文数
                matches = re.findall(r'"(\d{2,4})".*?posts', text)
                
                if matches:
                    for match in reversed(matches):
                        num = int(match)
                        if 80 <= num <= 300:
                            self.data["tweets"] = num
                            print(f"  ✅ 推文数: {num}")
                            return num
                
                print("  ❌ 未找到推文数")
                return None
            else:
                print(f"  ❌ 请求失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            return None
    
    def fetch_prices(self):
        """获取价格分布"""
        try:
            print("📈 获取价格分布...")
            response = self.session.get(POLYMARKET_URL, timeout=20)
            
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
                            prices[range_val] = prob_match.group(1)
                
                if prices:
                    self.data["prices"] = prices
                    print(f"  ✅ 价格数据: {len(prices)}个区间")
                    return True
                
                print("  ❌ 未找到价格数据")
                return False
            else:
                print(f"  ❌ 请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            return False
    
    def fetch_weather(self):
        """获取天气数据"""
        try:
            print("🌡️ 获取天气数据...")
            response = self.session.get("https://wttr.in/Shenzhen?format=j1", timeout=10)
            
            if response.status_code == 200:
                weather = response.json()
                current = weather['current_condition'][0]
                
                self.data["temp_c"] = int(current['temp_C'])
                self.data["humidity"] = int(current['humidity'])
                
                print(f"  ✅ 温度: {self.data['temp_c']}°C, 湿度: {self.data['humidity']}%")
                return True
            else:
                print(f"  ❌ 请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            return False
    
    def fetch_latest_tweets(self):
        """获取最新推文"""
        try:
            print("🐦 获取最新推文...")
            
            # 尝试Nitter镜像
            mirrors = [
                "https://nitter.net",
                "https://nitter.poast.org",
                "https://nitter.privacydev.net"
            ]
            
            for mirror in mirrors:
                try:
                    url = f"{mirror}/elonmusk"
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        # 简单解析推文
                        tweets = re.findall(r'<div class="tweet-content.*?>(.*?)</div>', response.text, re.DOTALL)[:3]
                        
                        if tweets:
                            self.data["latest_tweets"] = [
                                {"text": re.sub(r'<.*?>', '', t)[:200], "time": "刚刚"}
                                for t in tweets
                            ]
                            print(f"  ✅ 最新推文: {len(self.data['latest_tweets'])}条")
                            return True
                except:
                    continue
            
            print("  ⚠️  无法获取推文列表")
            self.data["latest_tweets"] = []
            return False
                
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            self.data["latest_tweets"] = []
            return False
    
    def calculate_remaining(self):
        """计算剩余时间"""
        end_time = datetime(2026, 8, 8, 0, 0, 0)
        now = datetime.now()
        remaining = end_time - now
        
        if remaining.total_seconds() > 0:
            days = remaining.days
            hours = remaining.seconds // 3600
            self.data["remaining"] = f"约{days}天{hours}小时"
        else:
            self.data["remaining"] = "已结束"
    
    def update_web_app(self):
        """更新网站数据"""
        try:
            print("\n🌐 推送数据到网站...")
            
            url = f"{WEB_APP_URL}/api/manual-update"
            
            payload = {
                "tweets": self.data["tweets"],
                "prices": self.data["prices"],
                "temp_c": self.data["temp_c"],
                "humidity": self.data["humidity"],
                "remaining": self.data["remaining"],
                "latest_tweets": self.data["latest_tweets"],
                "prediction": f"当前{self.data['tweets']}条，日均{self.data['tweets']/5:.1f}条"
            }
            
            response = self.session.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 网站数据已更新: {result.get('message', '成功')}")
                return True
            else:
                print(f"❌ 更新失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 更新错误: {e}")
            return False
    
    def run_once(self):
        """运行一次"""
        print("=" * 60)
        print(f"🚀 Polymarket监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        self.fetch_tweets_count()
        self.fetch_prices()
        self.fetch_weather()
        self.fetch_latest_tweets()
        self.calculate_remaining()
        
        self.update_web_app()
        
        print("=" * 60)
        print(f"✅ 完成 - 下次更新: 5分钟后")
        print("=" * 60)
    
    def run_forever(self):
        """持续运行"""
        while True:
            self.run_once()
            time.sleep(300)  # 5分钟

if __name__ == '__main__':
    monitor = PolymarketMonitor()
    
    print("\n🎯 选择运行模式:")
    print("1. 运行一次")
    print("2. 持续监控（每5分钟更新）")
    
    choice = input("\n请选择 (1/2): ").strip()
    
    if choice == '2':
        print("\n📊 启动持续监控...")
        monitor.run_forever()
    else:
        monitor.run_once()