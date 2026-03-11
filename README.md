# OpenClaw Skill: traffic-query

基于高德地图 Web API 的 OpenClaw 出行查询技能。

## 已实现能力

- 驾车路线规划：距离、预计用时、过路费、分段路况
- 指定道路实时路况：查询某条路当前拥堵情况
- POI 搜索：附近美食、景点、医院、咖啡店等

## 仓库结构

```text
.
├── SKILL.md
├── config.example.json
├── README.md
└── scripts/
    └── traffic_query.py
```

## 安装

### 方式 1：直接从 GitHub 安装

```bash
npx clawhub add https://github.com/Evan-ST/openclaw-skill-traffic-query --skill traffic-query -g
```

### 方式 2：本地打包后安装

```bash
python /opt/homebrew/lib/node_modules/openclaw/skills/skill-creator/scripts/package_skill.py . dist
```

生成：`dist/traffic-query.skill`

## 配置

```bash
cd ~/.openclaw/workspace/skills/traffic-query
cp config.example.json config.json
```

填写你的高德 Web 服务 Key：

```json
{
  "amap_key": "YOUR_AMAP_WEB_SERVICE_KEY",
  "aliases": {
    "home": {
      "name": "家",
      "city": "深圳",
      "full_address": "深圳市南山区科技园"
    },
    "work": {
      "name": "公司",
      "city": "深圳",
      "full_address": "深圳市南山区软件产业基地"
    }
  }
}
```

也支持用环境变量：

```bash
export TRAFFIC_QUERY_AMAP_KEY="你的Key"
```

## 手动测试

### 路线规划

```bash
python3 scripts/traffic_query.py route --from "深圳北站" --to "腾讯滨海大厦"
```

### 实时路况

```bash
python3 scripts/traffic_query.py traffic-road --road "深南大道" --city "深圳"
```

### POI 搜索

```bash
python3 scripts/traffic_query.py poi --keyword "咖啡" --city "深圳" --around "腾讯滨海大厦"
```

## 当前限制

- 当前版本未实现 12306 / 高铁查询
- 依赖高德地图 Web 服务 API Key

## License

MIT
