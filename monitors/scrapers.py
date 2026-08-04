"""
增强版数据抓取模块
优化HTML解析，添加实时信息抓取
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
            'Connection': 'keep-alive'
        })
    
    def fetch_musk_market(self, url="https://polymarket.com/event/elon-musk-of-tweets-july-31-august-7"):
        """抓取马斯克推文盘口"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取推文数 - 多种方法尝试
            tweets = 0
            
            # 方法1: 查找包含TWEET COUNT的区域
            for elem in soup.find_all(string=re.compile(r'TWEET COUNT', re.I)):
                parent = elem.parent
                if parent:
                    # 查找数字
                    for child in parent.parent.find_all(string=True):
                        child_text = child.strip()
                        if child_text.isdigit() and int(child_text) > 50:
                            tweets = int(child_text)
                            break
            
            # 方法2: 查找大数字（推文数通常在80-500之间）
            if tweets == 0:
                for elem in soup.find_all(class_=re.compile(r'tweet|count|number', re.I)):
                    text = elem.get_text(strip=True)
                    match = re.search(r'(\d{2,3})', text)
                    if match:
                        num = int(match.group(1))
                        if 80 <= num <= 500:
                            tweets = num
                            break
            
            # 方法3: 查找JSON数据
            if tweets == 0:
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'tweetCount' in script.string:
                        match = re.search(r'tweetCount["\s:]+(\d+)', script.string)
                        if match:
                            tweets = int(match.group(1))
                            break
            
            # 提取价格分布
            prices = {}
            
            # 方法1: 查找所有价格按钮
            buttons = soup.find_all('button')
            for button in buttons:
                text = button.get_text()
                # 匹配区间和概率
                range_matches = re.findall(r'(\d{3}-\d{3})', text)
                prob_matches = re.findall(r'(\d+\.?\d*)%', text)
                
                for i, range_val in enumerate(range_matches):
                    if i < len(prob_matches):
                        prices[range_val] = prob_matches[i].replace('%', '')
            
            # 方法2: 查找段落
            if len(prices) < 5:
                paragraphs = soup.find_all('p')
                for p in paragraphs:
                    text = p.get_text()
                    range_match = re.search(r'(\d{3}-\d{3})', text)
                    if range_match:
                        range_val = range_match.group(1)
                        # 查找概率
                        parent = p.parent
                        if parent:
                            prob_text = parent.get_text()
                            prob_match = re.search(r'(\d+\.?\d*)%', prob_text)
                            if prob_match:
                                prices[range_val] = prob_match.group(1)
            
            return {
                "tweets": tweets,
                "prices": prices,
                "last_update": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"抓取马斯克盘口失败: {e}")
            return None
    
    def fetch_weather_market(self, city="shenzhen"):
        """抓取天气盘口"""
        try:
            url = f"https://polymarket.com/event/shenzhen-august-high-temperature"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取温度概率
            prices = {}
            
            # 查找温度档位
            elements = soup.find_all(string=re.compile(r'\d+°C'))
            for elem in elements:
                temp = elem.strip()
                parent = elem.parent.parent if elem.parent else None
                if parent:
                    prob_text = parent.get_text()
                    prob_match = re.search(r'(\d+\.?\d*)%', prob_text)
                    if prob_match:
                        prices[temp] = prob_match.group(1)
            
            return {
                "prices": prices,
                "last_update": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"抓取天气盘口失败: {e}")
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
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取当前温度（华氏度）
            temp_f = None
            temp_c = None
            humidity = None
            feels_like = None
            
            # 方法1: 查找temperature类
            temp_elems = soup.find_all(class_=re.compile(r'temperature|temp', re.I))
            for elem in temp_elems:
                text = elem.get_text()
                match = re.search(r'(\d+)°F', text)
                if match:
                    temp_f = int(match.group(1))
                    temp_c = round((temp_f - 32) * 5 / 9)
                    break
            
            # 方法2: 查找数字加°F
            if not temp_f:
                for elem in soup.find_all(string=re.compile(r'\d+°F')):
                    match = re.search(r'(\d+)°F', elem)
                    if match:
                        temp_f = int(match.group(1))
                        temp_c = round((temp_f - 32) * 5 / 9)
                        break
            
            # 提取湿度
            for elem in soup.find_all(string=re.compile(r'Humidity', re.I)):
                parent = elem.parent.parent if elem.parent else None
                if parent:
                    text = parent.get_text()
                    match = re.search(r'(\d+)%', text)
                    if match:
                        humidity = int(match.group(1))
                        break
            
            return {
                "temp_f": temp_f,
                "temp_c": temp_c,
                "humidity": humidity,
                "feels_like": feels_like,
                "last_update": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"获取WU温度失败: {e}")
            return None

class TwitterScraper:
    """推特数据抓取（模拟）"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def fetch_latest_tweets(self, username="elonmusk"):
        """获取最新推文（通过Nitter镜像）"""
        try:
            # 使用Nitter开源镜像
            url = f"https://nitter.net/{username}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            tweets = []
            tweet_items = soup.find_all('div', class_='tweet-content', limit=5)
            
            for item in tweet_items:
                tweet_text = item.get_text(strip=True)
                # 提取时间
                time_elem = item.parent.find('span', class_='tweet-date')
                tweet_time = time_elem.get_text(strip=True) if time_elem else ''
                
                tweets.append({
                    "text": tweet_text[:200],  # 限制长度
                    "time": tweet_time,
                    "link": f"https://x.com/{username}"
                })
            
            return {
                "tweets": tweets,
                "last_update": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"获取推文失败: {e}")
            return None

# 测试
if __name__ == "__main__":
    pm = PolymarketScraper()
    print("=== Polymarket 马斯克盘口 ===")
    data = pm.fetch_musk_market()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    wu = WundergroundScraper()
    print("\n=== Wunderground 深圳温度 ===")
    temp = wu.fetch_shenzhen_temp()
    print(json.dumps(temp, indent=2, ensure_ascii=False))