# OpenClaw Skill: 交通查询助手

让 OpenClaw 具备出行交通查询能力，基于高德地图 API。

## 功能

| 功能 | 说明 |
|------|------|
| 路线规划 | 驾车路线 + 实时路况 + 预计用时 + 费用 |
| 实时路况 | 查询指定道路拥堵情况 |
| POI 搜索 | 搜索附近美食、景点等 |
| 高铁查询 | 查询高铁/动车班次（12306） |

## 安装

```bash
npx clawhub add https://github.com/Evan-ST/openclaw-skill-traffic-query --skill traffic-query -g
```

## 配置

安装后需要配置高德 API Key 和常用地址：

```bash
cd ~/.openclaw/workspace/skills/traffic-query
cp config.example.json config.json
```

编辑 `config.json`：

```json
{
  "amap_key": "你的高德API Key",
  "home": {
    "name": "我的家",
    "city": "深圳",
    "full_address": "深圳市XX小区"
  },
  "work": {
    "name": "公司",
    "city": "深圳",
    "full_address": "深圳市XX产业园"
  }
}
```

### 获取高德 API Key

1. 注册 [高德开放平台](https://lbs.amap.com) 账号
2. 创建应用 → 添加 Key → 选择 "Web服务"
3. 将 Key 填入 `config.json` 的 `amap_key` 字段

## 使用示例

在飞书/微信等渠道对 OpenClaw 说：

- "上班路况怎么样？"
- "深南大道现在堵不堵？"
- "附近有什么好吃的？"
- "深圳到广州的高铁"

## 前置条件

- OpenClaw 已安装并运行
- 高德地图 Web 服务 API Key（免费）
- Python 3.6+

## 许可

MIT
