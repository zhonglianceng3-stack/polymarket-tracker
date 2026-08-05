# OpenClaw 定时健康检测任务
# 每5分钟检测Polymarket监控服务连通性

import subprocess
import requests
import json
import os
from datetime import datetime

# 配置
SERVICE_URL = os.environ.get('SERVICE_URL', 'https://polymarket-tracker-production-49d5.up.railway.app')
HEALTH_ENDPOINT = f"{SERVICE_URL}/health"
LOG_FILE = os.path.expanduser('~/.openclaw/workspace/memory/health-check.log')

def check_health():
    """检测服务健康状态"""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'healthy',
                'clients': data.get('clients', 0),
                'uptime': data.get('uptime', 0),
                'time': data.get('time', '')
            }
        else:
            return {
                'status': 'error',
                'code': response.status_code
            }
            
    except requests.exceptions.RequestException as e:
        return {
            'status': 'failed',
            'error': str(e)
        }

def restart_service():
    """重启Railway服务（需要Railway CLI）"""
    try:
        # 方法1: 使用Railway CLI重启
        result = subprocess.run(
            ['railway', 'restart'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
            
    except FileNotFoundError:
        return False, "Railway CLI未安装"
    except Exception as e:
        return False, str(e)

def log_message(message):
    """记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}\n"
    
    print(log_entry.strip())
    
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"写入日志失败: {e}")

def main():
    """主函数"""
    log_message(f"🔍 开始健康检测: {SERVICE_URL}")
    
    result = check_health()
    
    if result['status'] == 'healthy':
        log_message(f"✅ 服务正常 - 客户端数: {result['clients']}, 运行时间: {result['uptime']}秒")
        
    elif result['status'] == 'error':
        log_message(f"⚠️ 服务异常 - HTTP {result['code']}")
        
    elif result['status'] == 'failed':
        log_message(f"❌ 服务无法访问: {result['error']}")
        
        # 尝试重启服务
        log_message("🔄 尝试重启服务...")
        success, message = restart_service()
        
        if success:
            log_message(f"✅ 重启成功: {message}")
        else:
            log_message(f"❌ 重启失败: {message}")

if __name__ == '__main__':
    main()