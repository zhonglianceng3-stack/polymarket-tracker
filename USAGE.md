# 使用指南

## 启动方法

### 电脑启动
```bash
cd ~/.openclaw/workspace/polymarket-tracker
bash start.sh
```

或者：
```bash
cd ~/.openclaw/workspace/polymarket-tracker
pip3 install -r requirements.txt
python3 app.py
```

### 访问地址
- 电脑浏览器：http://localhost:5000
- 手机浏览器：http://你的电脑IP:5000

---

## 手机访问

### 1. 确保手机和电脑在同一WiFi

### 2. 查看电脑IP
```bash
# Mac/Linux
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig
```

### 3. 手机访问
打开手机浏览器，输入：`http://电脑IP:5000`

例如：`http://192.168.1.100:5000`

---

## 开启推送通知

1. 手机访问页面后，点击"🔔 开启通知"
2. 允许浏览器通知权限
3. 发现套利机会时会自动推送

---

## 功能说明

### 实时监控
- 马斯克推文盘口
- 深圳天气盘口
- 每分钟自动刷新

### 套利提醒
- 发现价格错配时自动推送
- 历史预测记录

---

## 后续开发

需要添加的功能：
1. 实际数据抓取（目前是示例数据）
2. 预测算法优化
3. 数据库存储
4. 用户设置页面