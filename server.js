const express = require('express');
const fetch = require('node-fetch');
const cors = require('cors');
const path = require('path');
const app = express();

// 固定北京时间时区（解决时间偏差）
process.env.TZ = 'Asia/Shanghai';

app.use(cors());
app.use(express.static('public'));

// 全局存储最新数据（缓存）
let cacheData = {
    musk: {
        tweets: 117,
        prices: {
            '180-199': '25',
            '200-219': '21',
            '160-179': '20',
            '220-239': '13',
            '140-159': '8'
        },
        remaining: '约17小时',
        prediction: '当前117条，日均23.4条',
        last_update: ''
    },
    weather: {
        current_temp: 26,
        humidity: 89,
        prices: {
            '30°C': '1',
            '31°C': '8',
            '32°C': '22',
            '33°C': '44',
            '34°C': '22',
            '35°C': '6',
            '36°C': '1'
        },
        prediction: '今日最高温预测：33°C概率最高(44%)',
        last_update: ''
    },
    updateTime: ''
};

// 数据源配置
const TARGET_APIS = {
    xtracker: 'https://xtracker.polymarket.com/user/elonmusk',
    weather: 'https://wttr.in/Shenzhen?format=j1'
};

// 抓取推文数据
async function fetchTweets() {
    try {
        console.log(`[${new Date().toLocaleTimeString()}] 抓取推文数据...`);
        
        const response = await fetch(TARGET_APIS.xtracker, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        });
        
        if (response.ok) {
            const text = await response.text();
            // 正则匹配推文数
            const matches = text.match(/"(\d{2,4})".*?posts/g);
            
            if (matches) {
                for (let i = matches.length - 1; i >= 0; i--) {
                    const num = parseInt(matches[i].match(/\d{2,4}/)[0]);
                    if (num >= 80 && num <= 300) {
                        cacheData.musk.tweets = num;
                        cacheData.musk.last_update = new Date().toLocaleTimeString();
                        console.log(`  ✓ 推文数: ${num}`);
                        return num;
                    }
                }
            }
            console.log('  ✗ 未找到推文数');
        } else {
            console.log(`  ✗ 请求失败: ${response.status}`);
        }
    } catch (error) {
        console.log('  ✗ 抓取失败:', error.message);
    }
}

// 抓取天气数据
async function fetchWeather() {
    try {
        console.log(`[${new Date().toLocaleTimeString()}] 抓取天气数据...`);
        
        const response = await fetch(TARGET_APIS.weather);
        
        if (response.ok) {
            const data = await response.json();
            const current = data.current_condition[0];
            
            cacheData.weather.current_temp = parseInt(current.temp_C);
            cacheData.weather.humidity = parseInt(current.humidity);
            cacheData.weather.last_update = new Date().toLocaleTimeString();
            
            console.log(`  ✓ 温度: ${current.temp_C}°C, 湿度: ${current.humidity}%`);
        } else {
            console.log(`  ✗ 请求失败: ${response.status}`);
        }
    } catch (error) {
        console.log('  ✗ 抓取失败:', error.message);
    }
}

// 计算剩余时间
function calculateRemaining() {
    const endTime = new Date('2026-08-08T00:00:00+08:00');
    const now = new Date();
    const remaining = endTime - now;
    
    if (remaining > 0) {
        const days = Math.floor(remaining / (1000 * 60 * 60 * 24));
        const hours = Math.floor((remaining % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        cacheData.musk.remaining = `约${days}天${hours}小时`;
    } else {
        cacheData.musk.remaining = '已结束';
    }
}

// 后台轮询任务（每3秒）
async function startPolling() {
    console.log('============================================================');
    console.log('🚀 Polymarket 后台轮询服务启动（每3秒）');
    console.log('⏰ 时区: Asia/Shanghai（北京时间）');
    console.log('============================================================');
    
    // 立即执行一次
    await fetchTweets();
    await fetchWeather();
    calculateRemaining();
    cacheData.updateTime = new Date().toLocaleString();
    
    // 循环轮询
    setInterval(async () => {
        await fetchTweets();
        await fetchWeather();
        calculateRemaining();
        cacheData.updateTime = new Date().toLocaleString();
    }, 3000);
}

// 前端页面
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// 对外接口，前端读取缓存数据
app.get('/api/latest', (req, res) => {
    res.json({
        updateTime: cacheData.updateTime,
        musk: cacheData.musk,
        weather: cacheData.weather
    });
});

// 兼容旧接口
app.get('/api/data', (req, res) => {
    res.json(cacheData);
});

// 健康检查
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        updateTime: cacheData.updateTime,
        tweets: cacheData.musk.tweets
    });
});

// 启动服务
const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
    console.log(`🌐 服务运行在端口: ${PORT}`);
    startPolling();
});