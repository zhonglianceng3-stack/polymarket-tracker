/**
 * Polymarket 套利监控 - WebSocket版本前端
 * 
 * 特性：
 * - WebSocket实时接收数据（手机锁屏/切换标签也能正常接收）
 * - 自动重连机制（网络中断后自动恢复）
 * - 双重保障：WebSocket + HTTP轮询备用
 * - 强制不缓存
 */

// 盘口结束时间：2026年8月8日00:00（北京时间）
const END_TIME = new Date('2026-08-08T00:00:00+08:00').getTime();

// WebSocket配置
let ws = null;
let reconnectTimer = null;
let httpFallbackTimer = null;
let isWebSocketConnected = false;

// ============ DOM加载完成后初始化 ============

document.addEventListener('DOMContentLoaded', () => {
    console.log('[Init] 页面加载完成，启动WebSocket连接');
    
    // 启动WebSocket连接
    connectWebSocket();
    
    // 启动倒计时（每秒更新）
    setInterval(updateCountdown, 1000);
    updateCountdown();
    
    // 启动HTTP轮询作为备用方案
    startHttpFallback();
});

// ============ WebSocket连接管理 ============

function connectWebSocket() {
    // 构建WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}`;
    
    console.log('[WS] 连接到:', wsUrl);
    updateConnectionStatus('connecting', 'WebSocket: 连接中...');
    
    try {
        ws = new WebSocket(wsUrl);
        
        // 连接成功
        ws.onopen = () => {
            console.log('[WS] 连接成功');
            isWebSocketConnected = true;
            updateConnectionStatus('connected', 'WebSocket: 在线');
            clearReconnectTimer();
        };
        
        // 接收消息
        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                if (message.type === 'data') {
                    console.log('[WS] 收到数据更新');
                    handleDataUpdate(message.payload);
                }
            } catch (error) {
                console.error('[WS] 解析消息失败:', error);
            }
        };
        
        // 连接关闭
        ws.onclose = (event) => {
            console.log('[WS] 连接关闭:', event.code, event.reason);
            isWebSocketConnected = false;
            updateConnectionStatus('disconnected', 'WebSocket: 断开');
            scheduleReconnect();
        };
        
        // 连接错误
        ws.onerror = (error) => {
            console.error('[WS] 连接错误:', error);
            isWebSocketConnected = false;
            updateConnectionStatus('error', 'WebSocket: 错误');
        };
        
    } catch (error) {
        console.error('[WS] 创建连接失败:', error);
        scheduleReconnect();
    }
}

// 重连机制
function scheduleReconnect() {
    if (reconnectTimer) return;
    
    console.log('[WS] 5秒后重连...');
    updateConnectionStatus('reconnecting', 'WebSocket: 重连中...');
    
    reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        connectWebSocket();
    }, 5000);
}

function clearReconnectTimer() {
    if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
    }
}

// ============ HTTP轮询备用方案 ============

function startHttpFallback() {
    // 如果WebSocket断开，每10秒用HTTP拉取数据
    httpFallbackTimer = setInterval(() => {
        if (!isWebSocketConnected) {
            console.log('[HTTP] WebSocket断开，使用HTTP轮询');
            fetchData();
        }
    }, 10000);
    
    // 立即获取一次数据
    fetchData();
}

async function fetchData() {
    try {
        // 添加时间戳防止缓存
        const url = `/api/data?t=${Date.now()}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        handleDataUpdate(data);
        
    } catch (error) {
        console.error('[HTTP] 获取数据失败:', error);
        updateConnectionStatus('error', '网络错误');
    }
}

// 手动刷新
function manualRefresh() {
    console.log('[Manual] 用户手动刷新');
    fetchData();
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'refresh' }));
    }
}

// ============ 数据处理 ============

function handleDataUpdate(data) {
    console.log('[Data] 更新界面', data.updateTime);
    
    // 更新连接状态
    updateConnectionStatus('connected', isWebSocketConnected ? 'WebSocket: 在线' : 'HTTP: 在线');
    
    // 更新时间
    const updateTime = data.musk?.last_update || data.weather?.last_update || data.updateTime || '--';
    document.getElementById('last-update').textContent = `更新时间: ${updateTime}`;
    
    // 温度数据
    if (data.weather) {
        document.getElementById('temp').textContent = data.weather.current_temp || '--';
        document.getElementById('humidity').textContent = data.weather.humidity || '--';
        document.getElementById('weather-temp').textContent = `${data.weather.current_temp || '--'}°C`;
        document.getElementById('weather-prediction').textContent = data.weather.prediction || '--';
        
        // 天气概率分布
        if (data.weather.prices) {
            const weatherPrices = Object.entries(data.weather.prices)
                .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))
                .map(([temp, prob]) => `
                    <div class="price-item">
                        <div class="price-range">${temp}</div>
                        <div class="price-prob">${prob}%</div>
                    </div>
                `).join('');
            document.getElementById('weather-prices').innerHTML = weatherPrices;
        }
    }
    
    // 推文数据
    if (data.musk) {
        document.getElementById('tweets').textContent = data.musk.tweets || '--';
        document.getElementById('remaining').textContent = data.musk.remaining || '--';
        document.getElementById('prediction').textContent = data.musk.prediction || '--';
        
        // 推文概率分布
        if (data.musk.prices) {
            const muskPrices = Object.entries(data.musk.prices)
                .sort((a, b) => parseInt(a[0].split('-')[0]) - parseInt(b[0].split('-')[0]))
                .map(([range, prob]) => `
                    <div class="price-item">
                        <div class="price-range">${range}</div>
                        <div class="price-prob">${prob}%</div>
                    </div>
                `).join('');
            document.getElementById('musk-prices').innerHTML = muskPrices;
        }
    }
}

// ============ 状态更新 ============

function updateConnectionStatus(status, message) {
    const statusEl = document.getElementById('connection-status');
    const wsEl = document.getElementById('ws-status');
    
    if (statusEl) {
        statusEl.textContent = status === 'connected' ? '在线' : 
                               status === 'connecting' ? '连接中' : '离线';
        statusEl.className = `badge ${status === 'connected' ? 'online' : 'offline'}`;
    }
    
    if (wsEl) {
        wsEl.textContent = message;
        wsEl.className = `badge ${status === 'connected' ? 'online' : 'offline'}`;
    }
}

// ============ 倒计时 ============

function updateCountdown() {
    const now = Date.now();
    const remaining = END_TIME - now;
    
    if (remaining <= 0) {
        document.getElementById('hours').textContent = '00';
        document.getElementById('minutes').textContent = '00';
        document.getElementById('seconds').textContent = '00';
        return;
    }
    
    const hours = Math.floor(remaining / (1000 * 60 * 60));
    const minutes = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((remaining % (1000 * 60)) / 1000);
    
    document.getElementById('hours').textContent = String(hours).padStart(2, '0');
    document.getElementById('minutes').textContent = String(minutes).padStart(2, '0');
    document.getElementById('seconds').textContent = String(seconds).padStart(2, '0');
}

// ============ 页面可见性监听（处理手机锁屏/切换标签） ============

document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        console.log('[Visibility] 页面可见，检查连接状态');
        
        // 页面重新可见时，立即刷新数据
        if (isWebSocketConnected && ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'refresh' }));
        } else {
            fetchData();
        }
    } else {
        console.log('[Visibility] 页面不可见（后台/锁屏），WebSocket保持连接');
    }
});

// 页面卸载前关闭WebSocket
window.addEventListener('beforeunload', () => {
    if (ws) {
        ws.close();
    }
});

console.log('[App] WebSocket版本前端加载完成');