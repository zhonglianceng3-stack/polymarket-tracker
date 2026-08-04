/**
 * Polymarket 套利监控 - 前端逻辑
 */

let notifyEnabled = false;
let currentData = {};

document.addEventListener('DOMContentLoaded', () => {
    loadData();
    setupNotifications();
    setupTabs();
    setInterval(loadData, 60000);
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
    document.getElementById('last-update').textContent = 
        `更新时间: ${formatTime(data.last_update)}`;
    
    // 更新实时信息板块
    updateRealtimeSection(data.realtime);
    
    // 更新馬斯克盘口
    if (data.musk) {
        updateMuskMarket('current', data.musk.current);
        updateMuskMarket('next', data.musk.next);
    }
    
    // 更新天气盘口
    if (data.weather) {
        updateWeatherMarket('shenzhen', 'today', data.weather.shenzhen?.today);
    }
    
    // 提醒
    if (data.alerts && data.alerts.length > 0) {
        renderAlerts(data.alerts);
    }
}

// 更新实时信息板块
function updateRealtimeSection(realtime) {
    if (!realtime) return;
    
    // 更新马斯克最新推文
    const tweetsEl = document.getElementById('musk-tweets-realtime');
    if (realtime.musk_tweets && realtime.musk_tweets.length > 0) {
        tweetsEl.innerHTML = '';
        realtime.musk_tweets.forEach(tweet => {
            const item = document.createElement('div');
            item.className = 'tweet-item';
            item.innerHTML = `
                <div class="time">${tweet.time || '刚刚'}</div>
                <div class="text">${tweet.text || '推文内容加载中...'}</div>
                <a href="${tweet.link || '#'}" class="link" target="_blank">查看原推 →</a>
            `;
            tweetsEl.appendChild(item);
        });
    } else {
        tweetsEl.innerHTML = '<div class="loading">暂无最新推文</div>';
    }
    
    // 更新WU实时温度
    const wuTemp = realtime.wu_temp;
    if (wuTemp) {
        const tempValue = document.getElementById('wu-temp-value');
        const humidity = document.getElementById('wu-humidity');
        const updateTime = document.getElementById('wu-update-time');
        
        if (wuTemp.temp_c) {
            tempValue.textContent = wuTemp.temp_c;
        }
        if (wuTemp.humidity) {
            humidity.textContent = wuTemp.humidity + '%';
        }
        if (wuTemp.update_time) {
            updateTime.textContent = wuTemp.update_time;
        }
    }
}

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

function updateWeatherMarket(city, date, marketData) {
    if (!marketData) return;
    
    const prefix = `${city}-${date}`;
    
    const currentEl = document.getElementById(`${prefix}-current`);
    const humidityEl = document.getElementById(`${prefix}-humidity`);
    const predictionEl = document.getElementById(`${prefix}-prediction`);
    const pricesEl = document.getElementById(`${prefix}-prices`);
    
    if (currentEl) currentEl.textContent = marketData.current_temp ? `${marketData.current_temp}°C` : '--°C';
    if (humidityEl) humidityEl.textContent = marketData.humidity ? `${marketData.humidity}%` : '--%';
    if (predictionEl) predictionEl.textContent = marketData.prediction || '等待分析...';
    
    if (marketData.prices && pricesEl) {
        renderPrices(pricesEl, marketData.prices, marketData.highlight);
    }
}

function renderPrices(container, prices, highlight) {
    container.innerHTML = '';
    
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
            
            if (notifyEnabled) {
                showNotification(alert.message);
            }
        });
    } else {
        section.classList.add('hidden');
    }
}

function setupTabs() {
    document.querySelectorAll('.tab[data-market]').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab[data-market]').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            const market = tab.dataset.market;
            document.querySelectorAll('.market-panel').forEach(p => p.classList.remove('active'));
            document.getElementById(market)?.classList.add('active');
        });
    });
    
    document.querySelectorAll('.tab[data-city]').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab[data-city]').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
        });
    });
    
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

function updateConnectionStatus(online) {
    const badge = document.getElementById('connection-status');
    badge.textContent = online ? '在线' : '离线';
    badge.className = `badge ${online ? 'online' : 'offline'}`;
}

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

function showNotification(message) {
    if (Notification.permission === 'granted') {
        new Notification('Polymarket 套利机会', {
            body: message,
            icon: '/static/icon.png'
        });
    }
}

// 刷新按钮
document.getElementById('refresh-btn').addEventListener('click', async () => {
    const btn = document.getElementById('refresh-btn');
    btn.textContent = '⏳ 刷新中...';
    btn.disabled = true;
    
    try {
        await fetch('/api/refresh', { method: 'POST' });
        await loadData();
        btn.textContent = '✅ 已刷新';
    } catch (e) {
        btn.textContent = '❌ 刷新失败';
    }
    
    setTimeout(() => {
        btn.textContent = '🔄 刷新数据';
        btn.disabled = false;
    }, 2000);
});

// 清除提醒
document.getElementById('clear-alerts').addEventListener('click', async () => {
    await fetch('/api/alerts/clear', { method: 'POST' });
    loadData();
});