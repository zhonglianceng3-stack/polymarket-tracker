"""
增强版数据抓取模块 - API版本
使用XTracker API和Polymarket API获取准确数据
"""

import requests
import json
import re
from datetime import datetime, timezone, timedelta
import time

class XTrackerAPI:
    """XTracker API - 获取推文数据"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Origin': 'https://xtracker.polymarket.com',
            'Referer': 'https://xtracker.polymarket.com/'
        })
        # 已知的period_id映射
        self.period_ids = {
            'july-31-august-7': 'e5d7a6b5-c5e5-4b7e-9f3a-5d6e7f8a9b0c',  # 示例ID，需要真实ID
        }
    
    def get_tweet_count(self, period_name='july-31-august-7'):
        """
        获取推文数
        XTracker没有公开API，我们通过解析页面获取
        """
        try:
            print(f"  → 请求XTracker页面...")
            url = "https://xtracker.polymarket.com/user/elonmusk"
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                print(f"  ✗ XTracker请求失败: {response.status_code}")
                return None
            
            # 从HTML中提取推文数
            text = response.text
            
            # 查找 "Elon Musk # tweets July 31 - August 7, 2026?" 后面的推文数
            # 使用正则匹配
            patterns = [
                r'Elon Musk # tweets July 31 - August 7, 2026\?.*?(\d{2,4})\s+posts',
                r'July 31, 2026.*?Aug 7, 2026.*?(\d{2,4})\s+posts',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    tweets = int(match.group(1))
                    print(f"  ✓ 推文数: {tweets}")
                    return tweets
            
            # 如果正则失败，尝试从JavaScript数据中提取
            # 查找 __NEXT_DATA__ 或类似的JSON数据
            next_data_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', text, re.DOTALL)
            if next_data_match:
                try:
                    data = json.loads(next_data_match.group(1))
                    # 遍历找到对应的period
                    if 'props' in data and 'pageProps' in data['props']:
                        periods = data['props']['pageProps'].get('periods', [])
                        for period in periods:
                            if 'July 31' in period.get('name', '') and 'August 7' in period.get('name', ''):
                                tweets = period.get('postCount', 0)
                                print(f"  ✓ 推文数(从JSON): {tweets}")
                                return tweets
                except:
                    pass
            
            print(f"  ✗ 无法提取推文数")
            return None
            
        except Exception as e:
            print(f"  ✗ XTracker错误: {e}")
            return None

class PolymarketAPI:
    """Polymarket API - 获取价格数据"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Origin': 'https://polymarket.com',
            'Referer': 'https://polymarket.com/'
        })
        self.base_url = "https://clob.polymarket.com"
    
    def get_market_prices(self, condition_id=None, slug=None):
        """
        获取市场概率分布
        
        参数:
        - condition_id: 市场条件ID
        - slug: 市场slug（如 "elon-musk-of-tweets-july-31-august-7"）
        """
        try:
            print(f"  → 请求Polymarket API...")
            
            # 方法1: 通过slug查询
            if slug:
                # 首先获取市场信息
                markets_url = f"https://gamma-api.polymarket.com/markets?slug={slug}"
                response = self.session.get(markets_url, timeout=30)
                
                if response.status_code == 200:
                    markets = response.json()
                    if markets and len(markets) > 0:
                        # 获取市场数据
                        market = markets[0]
                        tokens = market.get('tokens', [])
                        
                        prices = {}
                        for token in tokens:
                            outcome = token.get('outcome', '')
                            price = token.get('price', 0)
                            # 转换为概率
                            prob = float(price) * 100 if price else 0
                            
                            # 提取数字区间（如 "180-199"）
                            range_match = re.search(r'(\d{3}-\d{3})', outcome)
                            if range_match:
                                range_val = range_match.group(1)
                                prices[range_val] = f"{prob:.0f}" if prob >= 1 else f"<1"
                        
                        print(f"  ✓ 价格数据: {len(prices)}个区间")
                        return prices, market
            
            # 方法2: 直接访问页面并解析
            url = f"https://polymarket.com/event/{slug}" if slug else "https://polymarket.com/event/elon-musk-of-tweets-july-31-august-7"
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                print(f"  ✗ Polymarket请求失败: {response.status_code}")
                return None, None
            
            text = response.text
            
            # 提取价格数据
            prices = {}
            
            # 查找所有价格区间和概率
            # 格式: "180-199" 和 "31%"
            range_pattern = r'(\d{3}-\d{3})'
            prob_pattern = r'(\d+(?:\.\d+)?)\s*%'
            
            # 查找所有区间
            ranges = re.findall(range_pattern, text)
            
            # 对于每个区间，查找其附近的概率
            for i, range_val in enumerate(ranges):
                # 在文本中查找该区间的位置
                pos = text.find(range_val)
                if pos != -1:
                    # 在该区间后面200个字符内查找概率
                    nearby_text = text[pos:pos+200]
                    
                    # 查找概率
                    prob_matches = re.findall(prob_pattern, nearby_text)
                    if prob_matches:
                        prob = prob_matches[0]
                        prices[range_val] = prob
            
            print(f"  ✓ 价格数据: {len(prices)}个区间")
            return prices, None
            
        except Exception as e:
            print(f"  ✗ Polymarket API错误: {e}")
            return None, None

class WundergroundScraper:
    """Wunderground 数据抓取"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
    
    def fetch_shenzhen_temp(self):
        """获取深圳实时温度"""
        try:
            url = "https://www.wunderground.com/weather/cn/shenzhen"
            print(f"  → 请求WU: {url}")
            
            response = self.session.get(url, timeout=30)
            print(f"  → WU状态码: {response.status_code}")
            
            if response.status_code != 200:
                return None
            
            text = response.text
            
            # 提取温度（华氏度）
            temp_f = None
            temp_c = None
            humidity = None
            
            # 方法1: 查找°F和°C
            # WU通常显示: "85°F" 或 "29°C"
            
            # 查找华氏度
            fahrenheit_match = re.search(r'(\d{2,3})\s*°F', text)
            if fahrenheit_match:
                temp_f = int(fahrenheit_match.group(1))
                # 转换为摄氏度
                temp_c = round((temp_f - 32) * 5 / 9)
                print(f"  ✓ 温度: {temp_f}°F = {temp_c}°C")
            
            # 如果华氏度没找到，查找摄氏度
            if not temp_c:
                celsius_match = re.search(r'(\d{2})\s*°C', text)
                if celsius_match:
                    temp_c = int(celsius_match.group(1))
                    print(f"  ✓ 温度: {temp_c}°C")
            
            # 提取湿度
            humidity_match = re.search(r'Humidity[^\d]*(\d+)', text, re.IGNORECASE)
            if humidity_match:
                humidity = int(humidity_match.group(1))
                print(f"  ✓ 湿度: {humidity}%")
            
            return {
                "temp_f": temp_f,
                "temp_c": temp_c,
                "humidity": humidity,
                "last_update": datetime.now().strftime("%H:%M:%S")
            }
            
        except Exception as e:
            print(f"  ✗ WU抓取失败: {e}")
            return None

class WeatherMarketAPI:
    """天气盘口API"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
    
    def fetch_weather_market(self, city="shenzhen", date="august"):
        """获取天气盘口数据"""
        try:
            # 搜索天气盘口
            search_url = f"https://gamma-api.polymarket.com/markets?_s={city}+{date}+temperature"
            print(f"  → 搜索天气盘口: {search_url}")
            
            response = self.session.get(search_url, timeout=30)
            
            if response.status_code != 200:
                print(f"  ✗ 天气盘口搜索失败: {response.status_code}")
                return None
            
            markets = response.json()
            
            if not markets:
                print(f"  ✗ 未找到天气盘口")
                return None
            
            # 提取温度概率
            prices = {}
            for market in markets[:1]:  # 只取第一个匹配的
                tokens = market.get('tokens', [])
                for token in tokens:
                    outcome = token.get('outcome', '')
                    price = token.get('price', 0)
                    
                    # 提取温度
                    temp_match = re.search(r'(\d+)\s*°C', outcome)
                    if temp_match:
                        temp = temp_match.group(1)
                        prob = float(price) * 100 if price else 0
                        prices[f"{temp}°C"] = f"{prob:.0f}" if prob >= 1 else f"<1"
            
            print(f"  ✓ 天气数据: {len(prices)}个档位")
            return prices
            
        except Exception as e:
            print(f"  ✗ 天气盘口抓取失败: {e}")
            return None

# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("数据抓取测试 - API版本")
    print("=" * 60)
    
    # 测试XTracker
    print("\n1. 测试XTracker API:")
    xtracker = XTrackerAPI()
    tweets = xtracker.get_tweet_count()
    print(f"  推文数: {tweets}")
    
    # 测试Polymarket
    print("\n2. 测试Polymarket API:")
    pm = PolymarketAPI()
    prices, _ = pm.get_market_prices(slug="elon-musk-of-tweets-july-31-august-7")
    print(f"  价格数据: {prices}")
    
    # 测试WU
    print("\n3. 测试Wunderground:")
    wu = WundergroundScraper()
    temp = wu.fetch_shenzhen_temp()
    if temp:
        print(f"  温度: {temp.get('temp_c')}°C")
        print(f"  湿度: {temp.get('humidity')}%")
    
    # 测试天气盘口
    print("\n4. 测试天气盘口:")
    weather = WeatherMarketAPI()
    weather_prices = weather.fetch_weather_market()
    print(f"  天气数据: {weather_prices}")