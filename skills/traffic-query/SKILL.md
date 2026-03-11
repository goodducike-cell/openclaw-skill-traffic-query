---
name: traffic-query
description: 查询中国城市出行信息：驾车路线规划、道路实时路况、POI 搜索与附近美食/景点推荐，基于高德地图 Web API。用户提到路况、堵不堵、怎么去、附近有什么好吃的/景点、从 A 到 B 多久/多少钱时使用。高铁场景仅调用 train.py 作为参考查询，不要承诺实时余票准确性。
license: MIT
metadata: {"clawdbot":{"emoji":"🚗","requires":{"bins":["python3"]}}}
---

# Traffic Query

Use the bundled Python scripts instead of hand-writing HTTP requests.

## Setup

```bash
cd ~/.openclaw/workspace/skills/traffic-query
cp config.example.json config.json
```

Fill `config.json.amap_key`.

The traffic script reads the API key in this order:
1. `--api-key`
2. `TRAFFIC_QUERY_AMAP_KEY`
3. `config.json` → `amap_key`

## Commands

### Driving route

```bash
python3 ~/.openclaw/workspace/skills/traffic-query/scripts/traffic.py route --from "深圳北站" --to "腾讯滨海大厦"
```

### Road traffic

```bash
python3 ~/.openclaw/workspace/skills/traffic-query/scripts/traffic.py traffic-road --road "深南大道" --city "深圳"
```

### POI search

```bash
python3 ~/.openclaw/workspace/skills/traffic-query/scripts/traffic.py poi --keyword "咖啡" --city "深圳" --around "腾讯滨海大厦"
```

### Train reference query

```bash
python3 ~/.openclaw/workspace/skills/traffic-query/scripts/train.py 深圳北 广州南 2026-03-12
```

Use this only as a reference output. If the user needs accurate real-time ticket inventory, explicitly direct them to 12306.

## Output handling

- Return the conclusion first.
- Include ETA / distance / toll / congestion level when available.
- If geocoding fails, say which address failed.
- If the user says “家/公司”, prefer aliases from `config.json`.
