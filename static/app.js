/**
 * Polymarket 套利监控 - 前端逻辑
 */

// 状态
let notifyEnabled = false;
let currentData = {};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadData();
    setupNotifications();
    setupTabs();
    setInterval(loadData, 60000); // 每分钟刷新
});

// 加载数据
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

// 更新UI
function updateUI(data) {
    // 更新时间
    document.getElementById('last-update').textContent = 
        `更新时间: ${formatTime(data.last_update)}`;
    
    // 更新馬斯克盘口
    if (data.musk) {
        updateMuskMarket('current', data.musk.current);
        updateMuskMarket('next', data.musk.next);
    }
    
    // 更新天气盘口
    if (data.weather) {
        updateWeatherMarket('shenzhen', 'today', data.weather.shenzhen?.today);
        updateWeatherMarket('shenzhen', 'tomorrow', data.weather.shenzhen?.tomorrow);
        updateWeatherMarket('beijing', 'today', data.weather.beijing?.today);
        updateWeatherMarket('shanghai', 'today', data.weather.shanghai?.today);
    }
    
    // 提醒
    if (data.alerts && data.alerts.length > 0) {
        renderAlerts(data.alerts);
    }
}

// 更新馬斯克盘口
function updateMuskMarket(period, marketData) {
    if (!marketData) return;
    
    const prefix = `musk-${period}`;
    
    const nameEl = document.getElementById(`${prefix}-name`);
    const tweetsEl = document.getElementById(`${prefix}-tweets`);
    const timeleftEl = document.getElementById(`${prefix}-timeleft`);
    const predictionEl = document.getElementById(`${prefix}-prediction`);
    const pricesEl = document.getElementById(`${prefix}-prices`);
    
    if (nameEl) nameEl.textContent = marketData.name || '--';
    if (tweetsEl) tweetsEl.textContent = marketData.tweets || '--';
    if (timeleftEl) timeleftEl.textContent = marketData.time_left || '--';
    if (predictionEl) predictionEl.textContent = marketData.prediction || '等待分析...';
    
    if (marketData.prices && pricesEl) {
        renderPrices(pricesEl, marketData.prices, marketData.highlight);
    }
}

// 更新天气盘口
function updateWeatherMarket(city, date, marketData) {
    if (!marketData) return;
    
    const prefix = `${city}-${date}`;
    
    const currentEl = document.getElementById(`${prefix}-current`);
    const forecastEl = document.getElementById(`${prefix}-forecast`);
    const predictionEl = document.getElementById(`${prefix}-prediction`);
    const pricesEl = document.getElementById(`${prefix}-prices`);
    
    if (currentEl) currentEl.textContent = marketData.current_temp ? `${marketData.current_temp}°C` : '--°C';
    if (forecastEl) forecastEl.textContent = marketData.forecast_high ? `${marketData.forecast_high}°C` : '--°C';
    if (predictionEl) predictionEl.textContent = marketData.prediction || '等待分析...';
    
    if (marketData.prices && pricesEl) {
        renderPrices(pricesEl, marketData.prices, marketData.highlight);
    }
}

// 渲染价格
function renderPrices(container, prices, highlight) {
    container.innerHTML = '';
    
    // 按概率排序
    const sorted = Object.entries(prices).sort((a, b) => parseFloat(b[1]) - parseFloat(a[1]));
    
    sorted.forEach(([range, prob]) => {
        const item = document.createElement('div');
        const probNum = parseFloat(prob);
        
        let className = 'price-item';
        if (highlight && range === highlight) {
            className += ' highlight';
        } else if (probNum < 5) {
            className += ' low';
        }
        
        item.className = className;
        item.innerHTML = `
            <div class="range">${range}</div>
            <div class="prob">${prob}%</div>
        `;
        container.appendChild(item);
    });
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

// 设置标签切换
function setupTabs() {
    // 馬斯克盘口标签
    document.querySelectorAll('.tab[data-market]').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab[data-market]').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            const market = tab.dataset.market;
            document.querySelectorAll('.market-panel').forEach(p => p.classList.remove('active'));
            document.getElementById(market)?.classList.add('active');
        });
    });
    
    // 城市标签
    document.querySelectorAll('.tab[data-city]').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab[data-city]').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            const city = tab.dataset.city;
            document.querySelectorAll('.weather-panel').forEach(p => {
                if (p.id.startsWith(city)) {
                    // 显示该城市的面板
                }
            });
        });
    });
    
    // 日期标签
    document.querySelectorAll('.date-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const parent = tab.closest('.weather-panel') || document;
            parent.querySelectorAll('.date-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            const date = tab.dataset.date;
            const activeCity = document.querySelector('.tab[data-city].active')?.dataset.city || 'shenzhen';
            
            document.querySelectorAll('.weather-panel').forEach(p => p.classList.remove('active'));
            document.getElementById(`${activeCity}-${date}`)?.classList.add('active');
        });
    });
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