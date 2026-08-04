"""
增强版数据抓取模块 - 优化版
使用更稳定的方法抓取Polymarket和Wunderground数据
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time

class PolymarketScraper:
    """Polymarket 数据抓取"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        })
    
    def fetch_musk_market(self, url="https://polymarket.com/event/elon-musk-of-tweets-july-31-august-7"):
        """抓取马斯克推文盘口"""
        try:
            print(f"  → 请求: {url}")
            response = self.session.get(url, timeout=30)
            print(f"  → 状态码: {response.status_code}")
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 提取推文数 - 多种方法
            tweets = 0
            
            # 方法1: 查找包含数字的元素
            all_text = soup.get_text()
            
            # 查找"TWEET COUNT"后面的数字
            tweet_count_match = re.search(r'TWEET COUNT.*?(\d+)', all_text, re.DOTALL)
            if tweet_count_match:
                tweets = int(tweet_count_match.group(1))
                print(f"  → 方法1成功: 推文数={tweets}")
            
            # 方法2: 查找大数字（80-500之间）
            if tweets == 0:
                numbers = re.findall(r'\b(\d{2,3})\b', all_text)
                for num_str in numbers:
                    num = int(num_str)
                    if 80 <= num <= 500:
                        tweets = num
                        print(f"  → 方法2成功: 推文数={tweets}")
                        break
            
            # 提取价格分布
            prices = {}
            
            # 查找所有包含区间和概率的文本
            # 模式: "180-199" 和 "26%"
            text_content = soup.get_text()
            
            # 查找所有区间
            ranges = re.findall(r'(\d{3}-\d{3})', text_content)
            
            # 对于每个区间，查找附近概率
            for i, range_val in enumerate(ranges):
                # 查找该区间在文本中的位置
                pos = text_content.find(range_val)
                if pos != -1:
                    # 在该区间前后100个字符内查找概率
                    start = max(0, pos - 50)
                    end = min(len(text_content), pos + 100)
                    nearby_text = text_content[start:end]
                    
                    # 查找概率
                    prob_match = re.search(r'(\d+\.?\d*)\s*%', nearby_text)
                    if prob_match:
                        prob = prob_match.group(1)
                        # 只保留第一个匹配的概率
                        if range_val not in prices:
                            prices[range_val] = prob
            
            print(f"  → 价格数据: {len(prices)}个区间")
            
            return {
                "tweets": tweets,
                "prices": prices,
                "last_update": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"  ✗ 抓取失败: {e}")
            return None
    
    def fetch_weather_market(self, city="shenzhen"):
        """抓取天气盘口"""
        try:
            # 深圳天气盘口URL - 需要找到正确的URL
            url = f"https://polymarket.com/event/shenzhen-august-high-temperature"
            print(f"  → 请求天气盘口: {url}")
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 404:
                print(f"  ✗ 天气盘口URL不存在(404)")
                return None
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 提取温度概率
            prices = {}
            text_content = soup.get_text()
            
            # 查找温度档位（如 "30°C"）
            temps = re.findall(r'(\d+)°C', text_content)
            
            for temp in temps:
                # 查找该温度附近的概率
                pos = text_content.find(f"{temp}°C")
                if pos != -1:
                    start = max(0, pos - 30)
                    end = min(len(text_content), pos + 80)
                    nearby_text = text_content[start:end]
                    
                    prob_match = re.search(r'(\d+\.?\d*)\s*%', nearby_text)
                    if prob_match:
                        prob = prob_match.group(1)
                        prices[f"{temp}°C"] = prob
            
            print(f"  → 温度数据: {len(prices)}个档位")
            
            return {
                "prices": prices,
                "last_update": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"  ✗ 天气盘口抓取失败: {e}")
            return None

class WundergroundScraper:
    """Wunderground 数据抓取"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
            
            soup = BeautifulSoup(response.text, 'lxml')
            text_content = soup.get_text()
            
            # 提取温度（华氏度）
            temp_f = None
            temp_c = None
            humidity = None
            
            # 方法1: 查找 "°F"
            fahrenheit_matches = re.findall(r'(\d+)\s*°F', text_content)
            if fahrenheit_matches:
                # 取第一个合理的温度值
                for temp_str in fahrenheit_matches:
                    temp = int(temp_str)
                    if 60 <= temp <= 110:  # 合理的深圳温度范围（华氏度）
                        temp_f = temp
                        temp_c = round((temp_f - 32) * 5 / 9)
                        print(f"  → 温度: {temp_f}°F = {temp_c}°C")
                        break
            
            # 方法2: 如果没找到，查找摄氏度
            if not temp_c:
                celsius_matches = re.findall(r'(\d+)\s*°C', text_content)
                if celsius_matches:
                    for temp_str in celsius_matches:
                        temp = int(temp_str)
                        if 15 <= temp <= 45:  # 合理的深圳温度范围（摄氏度）
                            temp_c = temp
                            print(f"  → 温度: {temp_c}°C")
                            break
            
            # 提取湿度
            humidity_match = re.search(r'Humidity.*?(\d+)', text_content, re.DOTALL)
            if humidity_match:
                humidity = int(humidity_match.group(1))
                print(f"  → 湿度: {humidity}%")
            
            return {
                "temp_f": temp_f,
                "temp_c": temp_c,
                "humidity": humidity,
                "last_update": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"  ✗ WU抓取失败: {e}")
            return None

class TwitterScraper:
    """推特数据抓取"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def fetch_latest_tweets(self, username="elonmusk"):
        """获取最新推文"""
        try:
            # 使用Nitter镜像（更稳定）
            mirrors = [
                "https://nitter.net",
                "https://nitter.poast.org",
                "https://nitter.privacydev.net"
            ]
            
            for mirror in mirrors:
                try:
                    url = f"{mirror}/{username}"
                    print(f"  → 尝试Nitter镜像: {mirror}")
                    
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'lxml')
                        
                        tweets = []
                        # 查找推文内容
                        tweet_items = soup.find_all('div', class_='tweet-content', limit=3)
                        
                        for item in tweet_items:
                            tweet_text = item.get_text(strip=True)[:200]
                            
                            # 提取时间
                            time_elem = item.parent.find('span', class_='tweet-date')
                            tweet_time = time_elem.get_text(strip=True) if time_elem else '刚刚'
                            
                            tweets.append({
                                "text": tweet_text,
                                "time": tweet_time,
                                "link": f"https://x.com/{username}"
                            })
                        
                        if tweets:
                            print(f"  → 成功获取{len(tweets)}条推文")
                            return {
                                "tweets": tweets,
                                "last_update": datetime.now().isoformat()
                            }
                except:
                    continue
            
            print(f"  ✗ 所有Nitter镜像都失败")
            return None
            
        except Exception as e:
            print(f"  ✗ 推文抓取失败: {e}")
            return None

# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("数据抓取测试")
    print("=" * 60)
    
    pm = PolymarketScraper()
    print("\n1. 测试Polymarket马斯克盘口:")
    data = pm.fetch_musk_market()
    if data:
        print(f"  推文数: {data.get('tweets')}")
        print(f"  价格区间: {len(data.get('prices', {}))}")
    
    print("\n2. 测试Wunderground温度:")
    wu = WundergroundScraper()
    temp = wu.fetch_shenzhen_temp()
    if temp:
        print(f"  温度: {temp.get('temp_c')}°C")
        print(f"  湿度: {temp.get('humidity')}%")
    
    print("\n3. 测试推特抓取:")
    twitter = TwitterScraper()
    tweets = twitter.fetch_latest_tweets()
    if tweets:
        print(f"  推文数: {len(tweets.get('tweets', []))}")