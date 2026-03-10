---
name: traffic-query
description: 出行交通查询助手，支持路况查询、高峰分析、高铁查询、美食推荐。触发词：路况、上班路况、高峰、拥堵、高铁、出行、附近美食、吃什么、去哪吃。Use when user asks about traffic conditions, commute status, train schedules, or nearby restaurants.
---

# 交通查询助手

基于高德地图API的出行助手，提供路况查询、高峰分析、高铁查询和美食推荐功能。

## 前置条件

1. 高德地图 Web 服务 API Key（免费申请：https://lbs.amap.com）
2. 配置好 `config.json`（首次使用需从模板复制并填写）

## 安装后设置

```bash
cd ~/.openclaw/workspace/skills/traffic-query
cp config.example.json config.json
# 编辑 config.json，填入你的高德 API Key 和常用地址
```

## 快速使用

### 1. 查询上班路况
```bash
python3 ~/.openclaw/workspace/skills/traffic-query/scripts/traffic.py route --origin "起点地址" --destination "终点地址"
```

### 2. 查询实时路况
```bash
python3 ~/.openclaw/workspace/skills/traffic-query/scripts/traffic.py traffic --road "道路名称"
```

### 3. 查询附近美食
```bash
python3 ~/.openclaw/workspace/skills/traffic-query/scripts/traffic.py poi --location "位置" --keywords "美食"
```

### 4. 查询高铁班次
```bash
python3 ~/.openclaw/workspace/skills/traffic-query/scripts/traffic.py train --from "深圳北" --to "广州南" --date "2026-03-10"
```

## 功能说明

| 功能 | 命令 | 说明 |
|------|------|------|
| 路线规划 | `route` | 驾车路线，包含实时路况、预计时间 |
| 实时路况 | `traffic` | 指定道路的拥堵情况 |
| POI搜索 | `poi` | 搜索附近餐饮、景点等 |
| 高铁查询 | `train` | 查询高铁/动车班次 |

## 配置说明

编辑 `config.json` 设置你的常用地址：

```json
{
  "home": { "name": "我的家", "city": "深圳", "full_address": "深圳XX小区" },
  "work": { "name": "公司", "city": "深圳", "full_address": "深圳XX产业园" }
}
```

## API 文档

详细 API 文档见：https://lbs.amap.com/api/webservice/summary
