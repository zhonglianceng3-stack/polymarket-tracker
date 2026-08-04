/**
 * Polymarket 套利监控 - 前端逻辑（完整修复版）
 */

document.addEventListener('DOMContentLoaded', () => {
    loadData();
    setInterval(loadData, 60000);
});

async function loadData() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        
        updateUI(data);
    } catch (error) {
        console.error('加载数据失败:', error);
    }
}

function updateUI(data) {
    // 更新时间
    document.getElementById('last-update').textContent = `更新时间: ${data.musk?.last_update || '--'}`;
    
    // 更新马斯克数据
    if (data.musk) {
        document.getElementById('musk-current-tweets').textContent = data.musk.tweets || '--';
        document.getElementById('musk-current-timeleft').textContent = data.musk.remaining || '--';
        document.getElementById('musk-current-prediction').textContent = data.musk.prediction || '等待分析...';
        
        // 更新概率分布
        renderPrices('musk-current-prices', data.musk.prices);
    }
    
    // 更新天气数据
    if (data.weather) {
        document.getElementById('shenzhen-today-current').textContent = `${data.weather.current_temp || '--'}°C`;
        document.getElementById('shenzhen-today-humidity').textContent = `${data.weather.humidity || '--'}%`;
        document.getElementById('shenzhen-today-prediction').textContent = data.weather.prediction || '等待分析...';
        
        // 更新天气概率分布
        renderPrices('shenzhen-today-prices', data.weather.prices);
    }
    
    // 更新提醒
    if (data.alerts && data.alerts.length > 0) {
        const alertsList = document.getElementById('alerts-list');
        if (alertsList) {
            alertsList.innerHTML = data.alerts.map(alert => `
                <div class="alert-item">
                    <div class="alert-time">${alert.time || ''}</div>
                    <div class="alert-message">${alert.message}</div>
                </div>
            `).join('');
        }
    }
}

function renderPrices(elementId, prices) {
    const container = document.getElementById(elementId);
    if (!container || !prices) return;
    
    container.innerHTML = Object.entries(prices)
        .sort((a, b) => {
            const aVal = parseInt(a[0].split('-')[0]) || parseInt(a[0]);
            const bVal = parseInt(b[0].split('-')[0]) || parseInt(b[0]);
            return aVal - bVal;
        })
        .map(([range, prob]) => `
            <div class="price-item">
                <div class="price-range">${range}</div>
                <div class="price-prob">${prob}%</div>
            </div>
        `).join('');
}

async function refreshData() {
    try {
        const btn = document.querySelector('button[onclick="refreshData()"]');
        if (btn) btn.textContent = '刷新中...';
        
        const response = await fetch('/api/refresh', { method: 'POST' });
        const result = await response.json();
        
        if (result.status === 'success') {
            await loadData();
            alert('数据已刷新');
        } else {
            alert('刷新失败: ' + result.message);
        }
        
        if (btn) btn.textContent = '🔄 刷新数据';
    } catch (error) {
        console.error('刷新失败:', error);
        alert('刷新失败');
    }
}