# Polymarket 套利监控 - WebSocket版本部署指南

## 📋 版本说明

**WebSocket版本 v2.0** - 彻底解决前端不更新问题

### ✅ 核心改进

1. **WebSocket实时推送**
   - 后端抓取数据后主动推送到前端
   - 手机锁屏/切换标签也能正常接收
   - 无需轮询，零延迟

2. **自动重连机制**
   - 网络中断后自动重连
   - 双重保障：WebSocket + HTTP备用

3. **防缓存策略**
   - 所有API添加防缓存响应头
   - HTML添加no-cache meta标签
   - 强制浏览器每次读取最新数据

4. **健康检测**
   - `/health` 接口监控服务状态
   - UptimeRobot保活配置
   - 自动检测并重启异常服务

---

## 🚀 快速部署（5分钟完成）

### 步骤1：上传文件到GitHub

**访问**：https://github.com/zhonglianceng3-stack/polymarket-tracker/upload/main

**拖拽上传以下文件**：
- `server-ws.js` → 重命名为 `server.js`
- `public/index.html`
- `public/app.js`
- `public/style.css`
- `package.json`
- `railway.toml`

**提交信息**：`WebSocket版本 - 修复前端不更新问题`

---

### 步骤2：Railway自动部署

Railway会自动检测到更新并重新部署。

**等待时间**：约2-3分钟

---

### 步骤3：设置环境变量

**Railway Dashboard** → **Variables** → 添加：

```
TZ=Asia/Shanghai
```

---

### 步骤4：验证部署

**访问**：https://polymarket-tracker-production-49d5.up.railway.app/

**检查项**：
- ✅ 页面显示"WebSocket: 在线"
- ✅ 数据实时更新
- ✅ 倒计时正常运行

---

## 🔍 UptimeRobot保活配置

### 配置参数

**Monitor Type**: HTTP(s)
**Friendly Name**: Polymarket Tracker
**URL**: https://polymarket-tracker-production-49d5.up.railway.app/health
**Monitoring Interval**: 5 minutes

**作用**：
- 每5分钟访问一次，防止Railway服务休眠
- 自动检测服务异常
- 发送告警邮件

---

## 📊 本地测试

### 启动服务

```bash
cd ~/.openclaw/workspace/polymarket-tracker
npm install
node server-ws.js
```

### 访问地址

- **前端页面**: http://localhost:8080/
- **API接口**: http://localhost:8080/api/data
- **健康检查**: http://localhost:8080/health
- **WebSocket状态**: http://localhost:8080/ws-status

---

## 🔧 故障排查

### 问题1：WebSocket连接失败

**现象**：显示"WebSocket: 断开"

**解决方案**：
1. 检查浏览器是否支持WebSocket
2. 检查防火墙设置
3. 查看Railway日志

---

### 问题2：数据不更新

**现象**：页面显示旧数据

**解决方案**：
1. 强制刷新页面（Ctrl+Shift+R）
2. 清除浏览器缓存
3. 检查WebSocket连接状态

---

### 问题3：手机锁屏后停止更新

**现象**：解锁后显示旧数据

**解决方案**：
- WebSocket版本已自动处理此问题
- 页面可见时会自动刷新数据

---

## 📁 文件结构

```
polymarket-tracker/
├── server-ws.js           # WebSocket后端（主文件）
├── server.js              # HTTP后端（旧版本）
├── package.json           # Node.js依赖
├── railway.toml           # Railway配置
├── health-monitor.py      # 健康监控脚本
└── public/
    ├── index.html         # 前端页面
    ├── app.js             # 前端逻辑（WebSocket）
    └── style.css          # 样式文件
```

---

## 🎯 关键特性

### WebSocket优势

1. **实时推送**：后端有新数据立即推送
2. **省流量**：无需频繁轮询
3. **稳定可靠**：网络中断自动重连
4. **跨平台**：手机/电脑都能用

### 防缓存策略

```javascript
// 后端响应头
Cache-Control: no-store, no-cache, must-revalidate
Pragma: no-cache
Expires: 0

// 前端meta标签
<meta http-equiv="Cache-Control" content="no-cache">
```

---

## 📞 技术支持

**GitHub仓库**: https://github.com/zhonglianceng3-stack/polymarket-tracker

**问题反馈**: 在GitHub Issues提交

---

**部署完成时间**: 2026年8月5日 12:00 北京时间