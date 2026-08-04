# Polymarket 套利监控 Web App

## 功能
- 实时监控马斯克推文盘口
- 实时监控天气盘口
- 预测套利机会并推送通知
- 手机/电脑浏览器访问

## 技术栈
- 后端：Python + Flask
- 前端：HTML/CSS/JS
- 推送：浏览器通知 API

## 部署
本地运行或部署到云平台

## 项目结构
```
polymarket-tracker/
├── app.py              # Flask 主应用
├── requirements.txt    # Python 依赖
├── templates/
│   └── index.html      # Web 界面
├── static/
│   ├── style.css       # 样式
│   └── app.js          # 前端逻辑
└── monitors/
    ├── musk.py         # 马斯克盘口监控
    └── weather.py      # 天气盘口监控
```