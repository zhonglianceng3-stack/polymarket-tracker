/**
 * Polymarket 套利监控 - 前端逻辑
 */

// 状态
let notifyEnabled = false;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadData();
    setupNotifications();
    setInterval(loadData, 60000); // 每分钟刷新
});

// 加载数据
async function loadData() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        
        updateUI(data);
        updateConnectionStatus(true);
    } catch (error) {
        console.error('加载数据失败:', error);
        updateConnectionStatus(false);
    }
}

// 更新UI
function updateUI(data) {
    // 更新时间
    document.getElementById('last-update').textContent = 
        `更新时间: ${formatTime(data.musk.last_update)}`;
    
    // 马斯克盘口
    if (data.musk) {
        document.getElementById('musk-tweets').textContent = 
            data.musk.tweets || '--';
        document.getElementById('musk-prediction').textContent = 
            data.musk.prediction || '等待分析...';
        
        if (data.musk.prices) {
            renderPrices('musk-prices', data.musk.prices);
        }
    }
    
    // 天气盘口
    if (data.weather) {
        document.getElementById('weather-current').textContent = 
            data.weather.current_temp ? `${data.weather.current_temp}°C` : '--°C';
        document.getElementById('weather-forecast').textContent = 
            data.weather.forecast_high ? `${data.weather.forecast_high}°C` : '--°C';
        document.getElementById('weather-prediction').textContent = 
            data.weather.prediction || '等待分析...';
        
        if (data.weather.prices) {
            renderPrices('weather-prices', data.weather.prices);
        }
    }
    
    // 提醒
    if (data.alerts && data.alerts.length > 0) {
        renderAlerts(data.alerts);
    }
}

// 渲染价格
function renderPrices(containerId, prices) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    for (const [range, prob] of Object.entries(prices)) {
        const item = document.createElement('div');
        item.className = 'price-item';
        item.innerHTML = `
            <div class="range">${range}</div>
            <div class="prob">${prob}%</div>
        `;
        container.appendChild(item);
    }
}

// 渲染提醒
function renderAlerts(alerts) {
    const section = document.getElementById('alerts-section');
    const list = document.getElementById('alerts-list');
    
    if (alerts.length > 0) {
        section.classList.remove('hidden');
        list.innerHTML = '';
        
        alerts.forEach(alert => {
            const item = document.createElement('div');
            item.className = 'alert-item';
            item.innerHTML = `
                <div class="time">${formatTime(alert.time)}</div>
                <div class="message">${alert.message}</div>
            `;
            list.appendChild(item);
            
            // 浏览器通知
            if (notifyEnabled) {
                showNotification(alert.message);
            }
        });
    } else {
        section.classList.add('hidden');
    }
}

// 更新连接状态
function updateConnectionStatus(online) {
    const badge = document.getElementById('connection-status');
    badge.textContent = online ? '在线' : '离线';
    badge.className = `badge ${online ? 'online' : 'offline'}`;
}

// 格式化时间
function formatTime(isoString) {
    if (!isoString) return '--';
    const date = new Date(isoString);
    return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 通知设置
function setupNotifications() {
    const btn = document.getElementById('notify-btn');
    
    btn.addEventListener('click', async () => {
        if (!('Notification' in window)) {
            alert('浏览器不支持通知');
            return;
        }
        
        const permission = await Notification.requestPermission();
        
        if (permission === 'granted') {
            notifyEnabled = true;
            btn.textContent = '✅ 通知已开启';
            btn.disabled = true;
        }
    });
}

// 显示通知
function showNotification(message) {
    if (Notification.permission === 'granted') {
        new Notification('Polymarket 套利机会', {
            body: message,
            icon: '/static/icon.png'
        });
    }
}

// 刷新按钮
document.getElementById('refresh-btn').addEventListener('click', loadData);

// 清除提醒
document.getElementById('clear-alerts').addEventListener('click', async () => {
    await fetch('/api/alerts/clear', { method: 'POST' });
    loadData();
});