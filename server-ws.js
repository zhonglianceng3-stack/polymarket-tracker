/**
 * Polymarket 套利监控 - WebSocket版本后端
 * 
 * 功能：
 * - WebSocket实时推送数据
 * - 健康检测接口 /health
 * - 防缓存响应头
 * - 自动保活机制
 */

const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');
const fs = require('fs');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

const PORT = process.env.PORT || 8080;

// 固定北京时区
process.env.TZ = 'Asia/Shanghai';

// ============ 中间件配置 ============

// 防缓存中间件 - 所有API响应添加防缓存头
app.use((req, res, next) => {
    // 强制不缓存所有响应
    res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate');
    res.setHeader('Pragma', 'no-cache');
    res.setHeader('Expires', '0');
    res.setHeader('Surrogate-Control', 'no-store');
    next();
});

// 静态文件（带缓存控制）
app.use(express.static('public', {
    etag: false,
    maxAge: 0,
    lastModified: false
}));

app.use(express.json());

// ============ 数据管理 ============

const DATA_FILE = 'data.json';
let currentData = loadData();
let lastUpdateTime = Date.now();

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

// 保存数据
function saveData(data) {
    try {
        fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
        currentData = data;
        lastUpdateTime = Date.now();
        return true;
    } catch (error) {
        console.error('保存数据失败:', error);
        return false;
    }
}

// ============ WebSocket连接管理 ============

const clients = new Set();

wss.on('connection', (ws) => {
    console.log(`[${new Date().toLocaleString('zh-CN')}] 新WebSocket连接，当前客户端数: ${wss.clients.size}`);
    clients.add(ws);
    
    // 立即发送当前数据
    ws.send(JSON.stringify({
        type: 'data',
        payload: currentData
    }));
    
    ws.on('close', () => {
        clients.delete(ws);
        console.log(`[${new Date().toLocaleString('zh-CN')}] WebSocket断开，剩余客户端数: ${wss.clients.size}`);
    });
    
    ws.on('error', (error) => {
        console.error('WebSocket错误:', error);
        clients.delete(ws);
    });
});

// 广播数据给所有客户端
function broadcastData(data) {
    const message = JSON.stringify({
        type: 'data',
        payload: data
    });
    
    let successCount = 0;
    wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
            try {
                client.send(message);
                successCount++;
            } catch (error) {
                console.error('发送失败:', error);
            }
        }
    });
    
    console.log(`[${new Date().toLocaleString('zh-CN')}] 广播数据给 ${successCount} 个客户端`);
}

// ============ HTTP路由 ============

// 首页 - 强制不缓存
app.get('/', (req, res) => {
    res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
    res.setHeader('Pragma', 'no-cache');
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// API: 获取数据 - 强制不缓存
app.get('/api/data', (req, res) => {
    const data = loadData();
    data.updateTime = new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' });
    
    // 强制防缓存
    res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
    res.setHeader('Pragma', 'no-cache');
    res.setHeader('Expires', '0');
    
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
    saveData(data);
    
    // WebSocket广播更新
    broadcastData(data);
    
    res.json({ success: true, data });
});

// 健康检查 - UptimeRobot保活接口
app.get('/health', (req, res) => {
    const uptime = Math.floor((Date.now() - lastUpdateTime) / 1000);
    const memory = process.memoryUsage();
    
    res.json({ 
        status: 'ok',
        uptime: uptime,
        clients: wss.clients.size,
        memory: {
            heapUsed: Math.round(memory.heapUsed / 1024 / 1024) + 'MB',
            heapTotal: Math.round(memory.heapTotal / 1024 / 1024) + 'MB'
        },
        time: new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' }),
        timezone: process.env.TZ || 'Asia/Shanghai'
    });
});

// 保活端点 - 供UptimeRobot调用
app.get('/keepalive', (req, res) => {
    res.json({ 
        status: 'alive',
        time: new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })
    });
});

// WebSocket状态接口
app.get('/ws-status', (req, res) => {
    res.json({
        connectedClients: wss.clients.size,
        lastUpdate: new Date(lastUpdateTime).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })
    });
});

// ============ 启动服务器 ============

server.listen(PORT, '0.0.0.0', () => {
    console.log('========================================');
    console.log('🚀 Polymarket 套利监控服务启动成功');
    console.log('========================================');
    console.log(`📡 HTTP端口: ${PORT}`);
    console.log(`🔌 WebSocket端口: ${PORT}`);
    console.log(`🕐 时间: ${new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}`);
    console.log(`🌏 时区: ${process.env.TZ || 'Asia/Shanghai'}`);
    console.log('========================================');
});

// 定期保活（每5分钟自我唤醒）
setInterval(() => {
    console.log(`[${new Date().toLocaleString('zh-CN')}] 保活心跳 - 客户端数: ${wss.clients.size}`);
}, 5 * 60 * 1000);