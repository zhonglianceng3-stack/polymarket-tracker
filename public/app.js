/**
 * Polymarket 套利监控 - 前端
 */

// 盘口结束时间：2026年8月8日00:00（北京时间）
const END_TIME = new Date('2026-08-08T00:00:00+08:00').getTime();

document.addEventListener('DOMContentLoaded', () => {
    loadData();
    
    // 每10秒更新数据
    setInterval(loadData, 10000);
    
    // 每秒更新倒计时
    setInterval(updateCountdown, 1000);
    updateCountdown();
});

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

async function loadData() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        
        // 更新连接状态
        const statusEl = document.getElementById('connection-status');
        if (statusEl) {
            statusEl.textContent = '在线';
            statusEl.className = 'badge online';
        }
        
        // 更新时间
        const updateTime = data.musk?.last_update || data.weather?.last_update || '--';
        document.getElementById('last-update').textContent = `更新时间: ${updateTime}`;
        
        // 温度
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
        
        // 推文
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
        
    } catch (error) {
        console.error('加载失败:', error);
        
        const statusEl = document.getElementById('connection-status');
        if (statusEl) {
            statusEl.textContent = '离线';
            statusEl.className = 'badge offline';
        }
    }
}