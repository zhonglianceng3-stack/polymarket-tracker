/**
 * Polymarket 套利监控 - 前端（完整修复版）
 */

document.addEventListener('DOMContentLoaded', () => {
    loadData();
    setInterval(loadData, 30000); // 每30秒更新
});

async function loadData() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        updateUI(data);
    } catch (error) {
        console.error('加载失败:', error);
    }
}

function updateUI(data) {
    // 更新时间
    const updateTime = data.musk?.last_update || data.weather?.last_update || '--';
    const updateEl = document.getElementById('last-update');
    if (updateEl) updateEl.textContent = `更新时间: ${updateTime}`;
    
    // 更新马斯克数据
    if (data.musk) {
        // 推文数
        setText('musk-current-tweets', data.musk.tweets || '--');
        
        // 剩余时间
        setText('musk-current-timeleft', data.musk.remaining || '--');
        
        // 预测
        setText('musk-current-prediction', data.musk.prediction || '等待数据...');
        
        // 概率分布
        renderPrices('musk-current-prices', data.musk.prices);
    }
    
    // 更新天气数据
    if (data.weather) {
        // 温度（天气盘口）
        setText('shenzhen-today-current', `${data.weather.current_temp || '--'}°C`);
        
        // 湿度（天气盘口）
        setText('shenzhen-today-humidity', `${data.weather.humidity || '--'}%`);
        
        // 预测
        setText('shenzhen-today-prediction', data.weather.prediction || '等待数据...');
        
        // 天气概率分布
        renderPrices('shenzhen-today-prices', data.weather.prices);
        
        // WU实时温度（右上角卡片）
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

async function refreshData() {
    const btn = event.target;
    btn.textContent = '刷新中...';
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        updateUI(data);
        btn.textContent = '🔄 刷新数据';
        btn.disabled = false;
    } catch (error) {
        console.error('刷新失败:', error);
        btn.textContent = '🔄 刷新数据';
        btn.disabled = false;
    }
}