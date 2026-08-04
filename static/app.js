/**
 * Polymarket 套利监控 - 前端逻辑（匹配版）
 */

let notifyEnabled = false;
let currentData = {};

document.addEventListener('DOMContentLoaded', () => {
    loadData();
    setInterval(loadData, 60000);  // 每分钟更新
    
    // 绑定按钮事件
    document.getElementById('refresh-btn')?.addEventListener('click', refreshData);
    document.getElementById('clear-alerts')?.addEventListener('click', clearAlerts);
});

async function loadData() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        currentData = data;
        
        updateUI(data);
        updateConnectionStatus(true);
    } catch (error) {
        console.error('加载数据失败:', error);
        updateConnectionStatus(false);
    }
}

function updateUI(data) {
    // 更新时间
    const updateTime = data.musk?.last_update || data.weather?.last_update || '--';
    document.getElementById('last-update').textContent = `更新时间: ${updateTime}`;
    
    // 更新马斯克数据（使用正确的元素ID）
    if (data.musk) {
        document.getElementById('musk-current-tweets').textContent = data.musk.tweets || '--';
        document.getElementById('musk-current-timeleft').textContent = data.musk.remaining || '--';
        document.getElementById('musk-current-prediction').textContent = data.musk.prediction || '等待分析...';
        
        // 更新概率分布
        renderPriceDistribution(data.musk.prices, 'musk-current-prices');
    }
    
    // 更新天气数据（使用正确的元素ID）
    if (data.weather) {
        document.getElementById('wu-temp-value').textContent = data.weather.current_temp || '--';
        document.getElementById('wu-humidity').textContent = `${data.weather.humidity || '--'}%`;
        document.getElementById('wu-update-time').textContent = data.weather.last_update || '--';
        
        // 更新天气预测
        const weatherPrediction = document.getElementById('weather-today-prediction');
        if (weatherPrediction) {
            weatherPrediction.textContent = data.weather.prediction || '等待分析...';
        }
        
        // 更新天气概率分布
        renderWeatherDistribution(data.weather.prices, 'weather-today-prices');
    }
    
    // 更新提醒
    if (data.alerts && data.alerts.length > 0) {
        renderAlerts(data.alerts);
        document.getElementById('alerts-section')?.classList.remove('hidden');
    }
}

function renderPriceDistribution(prices, containerId) {
    const container = document.getElementById(containerId);
    if (!container || !prices) return;
    
    container.innerHTML = '';
    
    const sorted = Object.entries(prices).sort((a, b) => {
        const aVal = parseInt(a[0].split('-')[0]) || parseInt(a[0]);
        const bVal = parseInt(b[0].split('-')[0]) || parseInt(b[0]);
        return aVal - bVal;
    });
    
    sorted.forEach(([range, prob]) => {
        const item = document.createElement('div');
        item.className = 'price-item';
        item.innerHTML = `
            <div class="price-range">${range}</div>
            <div class="price-prob">${prob}%</div>
        `;
        container.appendChild(item);
    });
}

function renderWeatherDistribution(prices, containerId) {
    const container = document.getElementById(containerId);
    if (!container || !prices) return;
    
    container.innerHTML = '';
    
    Object.entries(prices).forEach(([temp, prob]) => {
        const item = document.createElement('div');
        item.className = 'price-item';
        item.innerHTML = `
            <div class="price-range">${temp}</div>
            <div class="price-prob">${prob}%</div>
        `;
        container.appendChild(item);
    });
}

function renderAlerts(alerts) {
    const container = document.getElementById('alerts-list');
    if (!container) return;
    
    container.innerHTML = '';
    
    alerts.forEach(alert => {
        const item = document.createElement('div');
        item.className = 'alert-item';
        const time = alert.time || '';
        const message = alert.message || '';
        item.innerHTML = `
            <div class="alert-time">${time}</div>
            <div class="alert-message">${message}</div>
        `;
        container.appendChild(item);
    });
}

function updateConnectionStatus(online) {
    const statusElement = document.getElementById('connection-status');
    if (statusElement) {
        statusElement.textContent = online ? '在线' : '离线';
        statusElement.className = online ? 'badge online' : 'badge offline';
    }
}

// 手动刷新
async function refreshData() {
    try {
        const response = await fetch('/api/refresh', { method: 'POST' });
        const result = await response.json();
        
        if (result.status === 'success') {
            await loadData();
            alert('数据已刷新');
        } else {
            alert('刷新失败: ' + result.message);
        }
    } catch (error) {
        console.error('刷新失败:', error);
        alert('刷新失败');
    }
}

// 清除提醒
async function clearAlerts() {
    try {
        const response = await fetch('/api/alerts/clear', { method: 'POST' });
        const result = await response.json();
        
        if (result.status === 'success') {
            await loadData();
            document.getElementById('alerts-section')?.classList.add('hidden');
        }
    } catch (error) {
        console.error('清除失败:', error);
    }
}