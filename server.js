const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 8080;

// 固定北京时区
process.env.TZ = 'Asia/Shanghai';

// 静态文件
app.use(express.static('public'));
app.use(express.json());

// 数据文件
const DATA_FILE = 'data.json';

// 读取数据
function loadData() {
    try {
        if (fs.existsSync(DATA_FILE)) {
            const data = fs.readFileSync(DATA_FILE, 'utf8');
            return JSON.parse(data);
        }
    } catch (error) {
        console.error('读取数据失败:', error);
    }
    
    // 默认数据
    return {
        musk: {
            tweets: 117,
            prices: {
                '180-199': '25',
                '200-219': '21',
                '160-179': '20',
                '220-239': '13',
                '140-159': '8'
            },
            remaining: '约2天14小时',
            prediction: '当前117条，日均23.4条',
            last_update: ''
        },
        weather: {
            current_temp: 27,
            humidity: 83,
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
        updateTime: new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })
    };
}

// 首页
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// API: 获取数据
app.get('/api/data', (req, res) => {
    const data = loadData();
    data.updateTime = new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' });
    res.json(data);
});

// API: 手动更新数据
app.post('/api/manual-update', (req, res) => {
    const { tweets, temp_c, humidity, remaining, prediction } = req.body;
    
    const data = loadData();
    
    if (tweets !== undefined) {
        data.musk.tweets = tweets;
        data.musk.remaining = remaining || data.musk.remaining;
        data.musk.prediction = prediction || data.musk.prediction;
        data.musk.last_update = new Date().toLocaleTimeString('zh-CN', { 
            timeZone: 'Asia/Shanghai',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
    
    if (temp_c !== undefined) {
        data.weather.current_temp = temp_c;
        data.weather.humidity = humidity || data.weather.humidity;
        data.weather.last_update = new Date().toLocaleTimeString('zh-CN', { 
            timeZone: 'Asia/Shanghai',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
    
    data.updateTime = new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' });
    
    // 保存数据
    try {
        fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
    } catch (error) {
        console.error('保存数据失败:', error);
    }
    
    res.json({ success: true, data });
});

// 健康检查
app.get('/health', (req, res) => {
    res.json({ 
        status: 'ok', 
        time: new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })
    });
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`Time: ${new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}`);
});