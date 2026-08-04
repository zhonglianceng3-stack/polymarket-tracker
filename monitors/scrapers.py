"""
Polymarket 数据抓取模块
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
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        })
    
    def fetch_musk_market(self, url="https://polymarket.com/event/elon-musk-of-tweets-july-31-august-7"):
        """抓取马斯克推文盘口"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取推文数 - 查找 TWEET COUNT 区域
            tweets = 0
            tweet_elements = soup.find_all(string=re.compile(r'TWEET COUNT'))
            for elem in tweet_elements:
                parent = elem.parent
                if parent:
                    # 查找数字
                    numbers = parent.find_all(string=re.compile(r'\d+'))
                    for num in numbers:
                        try:
                            tweets = int(num.strip())
                            if tweets > 50:  # 合理的推文数
                                break
                        except:
                            pass
            
            # 提取价格分布
            prices = {}
            
            # 方法1: 查找按钮中的价格信息
            buttons = soup.find_all('button')
            for button in buttons:
                text = button.get_text()
                # 匹配模式如 "180-199" 和 "26%"
                range_match = re.search(r'(\d+-\d+)', text)
                prob_match = re.search(r'(\d+\.?\d*)%', text)
                
                if range_match and prob_match:
                    range_val = range_match.group(1)
                    prob_val = prob_match.group(1)
                    prices[range_val] = prob_match.group(1)
            
            # 方法2: 查找段落中的信息
            if not prices:
                paragraphs = soup.find_all('p')
                for p in paragraphs:
                    text = p.get_text()
                    range_match = re.search(r'(\d+-\d+)', text)
                    if range_match:
                        # 查找兄弟元素中的概率
                        parent = p.parent
                        if parent:
                            prob_text = parent.get_text()
                            prob_match = re.search(r'(\d+\.?\d*)%', prob_text)
                            if prob_match:
                                prices[range_match.group(1)] = prob_match.group(1)
            
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
            # 深圳天气盘口URL
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
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
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
            
            # 查找温度元素
            temp_elements = soup.find_all(class_=re.compile(r'temperature'))
            for elem in temp_elements:
                text = elem.get_text()
                match = re.search(r'(\d+)°F', text)
                if match:
                    temp_f = int(match.group(1))
                    break
            
            # 转换为摄氏度
            temp_c = None
            if temp_f:
                temp_c = round((temp_f - 32) * 5 / 9)
            
            return {
                "temp_f": temp_f,
                "temp_c": temp_c,
                "last_update": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"获取WU温度失败: {e}")
            return None

# 测试
if __name__ == "__main__":
    scraper = PolymarketScraper()
    data = scraper.fetch_musk_market()
    print("马斯克盘口数据:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    wu = WundergroundScraper()
    temp = wu.fetch_shenzhen_temp()
    print("\n深圳实时温度:")
    print(json.dumps(temp, indent=2, ensure_ascii=False))