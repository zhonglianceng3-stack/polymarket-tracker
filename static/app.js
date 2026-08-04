/**
 * Polymarket 套利监控 - 前端（完整版 + 实时倒计时）
 */

// 盘口结束时间：2026年8月7日 24:00（北京时间）
const END_TIME = new Date('2026-08-08T00:00:00+08:00').getTime();

document.addEventListener('DOMContentLoaded', () => {
    loadData();
    
    // 每10秒更新数据（提高实时性）
    setInterval(loadData, 10000);
    
    // 每秒更新倒计时
    setInterval(updateCountdown, 1000);
    updateCountdown(); // 立即执行一次
});

async function loadData() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        updateUI(data);
        
        // 更新连接状态
        const statusEl = document.getElementById('connection-status');
        if (statusEl) {
            statusEl.textContent = '在线';
            statusEl.className = 'badge online';
        }
    } catch (error) {
        console.error('加载失败:', error);
        
        const statusEl = document.getElementById('connection-status');
        if (statusEl) {
            statusEl.textContent = '离线';
            statusEl.className = 'badge offline';
        }
    }
}

function updateCountdown() {
    const now = Date.now();
    const remaining = END_TIME - now;
    
    if (remaining <= 0) {
        document.getElementById('countdown-hours').textContent = '00';
        document.getElementById('countdown-minutes').textContent = '00';
        document.getElementById('countdown-seconds').textContent = '00';
        return;
    }
    
    const hours = Math.floor(remaining / (1000 * 60 * 60));
    const minutes = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((remaining % (1000 * 60)) / 1000);
    
    document.getElementById('countdown-hours').textContent = String(hours).padStart(2, '0');
    document.getElementById('countdown-minutes').textContent = String(minutes).padStart(2, '0');
    document.getElementById('countdown-seconds').textContent = String(seconds).padStart(2, '0');
}

function updateUI(data) {
    // 更新时间
    const updateTime = data.musk?.last_update || data.weather?.last_update || '--';
    setText('last-update', `更新时间: ${updateTime}`);
    
    // 更新马斯克数据
    if (data.musk) {
        setText('musk-current-tweets', data.musk.tweets || '--');
        setText('musk-current-timeleft', data.musk.remaining || '--');
        setText('musk-current-prediction', data.musk.prediction || '等待数据...');
        
        renderPrices('musk-current-prices', data.musk.prices);
    }
    
    // 更新天气数据
    if (data.weather) {
        setText('shenzhen-today-current', `${data.weather.current_temp || '--'}°C`);
        setText('shenzhen-today-humidity', `${data.weather.humidity || '--'}%`);
        setText('shenzhen-today-prediction', data.weather.prediction || '等待数据...');
        
        renderPrices('shenzhen-today-prices', data.weather.prices);
        
        // WU实时温度
        setText('wu-temp-value', data.weather.current_temp || '--');
        setText('wu-humidity', `${data.weather.humidity || '--'}%`);
        setText('wu-update-time', data.weather.last_update || '--');
    }
    
    // 更新最新推文
    const tweetsListEl = document.getElementById('latest-tweets-list');
    if (tweetsListEl) {
        if (data.tweets_list && data.tweets_list.length > 0) {
            tweetsListEl.innerHTML = data.tweets_list.map(t => `
                <div class="tweet-item">
                    <div class="tweet-time">${t.time || '刚刚'}</div>
                    <div class="tweet-text">${t.text || ''}</div>
                </div>
            `).join('');
        } else {
            tweetsListEl.innerHTML = '<div class="no-data">暂无最新推文数据</div>';
        }
    }
}

function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function renderPrices(elementId, prices) {
    const container = document.getElementById(elementId);
    if (!container || !prices) return;
    
    const entries = Object.entries(prices);
    
    // 排序
    entries.sort((a, b) => {
        const aVal = parseInt(a[0].split('-')[0]) || parseInt(a[0]);
        const bVal = parseInt(b[0].split('-')[0]) || parseInt(b[0]);
        return aVal - bVal;
    });
    
    // 渲染
    container.innerHTML = entries.map(([range, prob]) => `
        <div class="price-item">
            <div class="price-range">${range}</div>
            <div class="price-prob">${prob}%</div>
        </div>
    `).join('');
}

function switchTab(panelId) {
    // 切换面板
    document.querySelectorAll('.market-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    document.getElementById(panelId)?.classList.add('active');
    
    // 切换按钮
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');
}

async function refreshData() {
    const btn = event.target;
    btn.textContent = '刷新中...';
    btn.disabled = true;
    
    try {
        await loadData();
        btn.textContent = '🔄 刷新数据';
        btn.disabled = false;
    } catch (error) {
        console.error('刷新失败:', error);
        btn.textContent = '🔄 刷新数据';
        btn.disabled = false;
    }
}