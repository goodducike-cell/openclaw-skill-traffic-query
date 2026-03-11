#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
CONFIG_PATH = SKILL_DIR / "config.json"
CONFIG_EXAMPLE_PATH = SKILL_DIR / "config.example.json"
AMAP_BASE = "https://restapi.amap.com"


class TrafficQueryError(Exception):
    pass


def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if CONFIG_EXAMPLE_PATH.exists():
        return json.loads(CONFIG_EXAMPLE_PATH.read_text(encoding="utf-8"))
    return {}


def get_api_key(args, config):
    key = args.api_key or os.getenv("TRAFFIC_QUERY_AMAP_KEY") or config.get("amap_key")
    if not key or key == "YOUR_AMAP_WEB_SERVICE_KEY":
        raise TrafficQueryError(
            "Missing AMap API key. Set --api-key, TRAFFIC_QUERY_AMAP_KEY, or config.json.amap_key"
        )
    return key


def http_get_json(path, params):
    query = urllib.parse.urlencode(params)
    url = f"{AMAP_BASE}{path}?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "openclaw-traffic-query/1.1"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        data = resp.read().decode(charset)
    payload = json.loads(data)
    if str(payload.get("status")) != "1":
        raise TrafficQueryError(payload.get("info") or payload.get("infocode") or "AMap API error")
    return payload


def aliases(config):
    return config.get("aliases") or {}


def normalize_alias(name, config):
    raw = (name or "").strip()
    if not raw:
        return raw
    mapping = aliases(config)
    if raw in mapping:
        alias = mapping[raw]
        return alias.get("full_address") or alias.get("name") or raw
    for key, alias in mapping.items():
        alias_name = str(alias.get("name") or "").strip()
        if raw == alias_name:
            return alias.get("full_address") or raw
        if raw in {"家", "我家"} and key == "home":
            return alias.get("full_address") or raw
        if raw in {"公司", "单位", "上班地点"} and key == "work":
            return alias.get("full_address") or raw
    return raw


def poi_search(keyword, city, key, location=None, limit=5, city_limit=False):
    params = {
        "key": key,
        "keywords": keyword,
        "offset": max(limit, 5),
        "page": 1,
        "extensions": "all",
    }
    if city:
        params["city"] = city
        params["citylimit"] = "true" if city_limit else "false"
    if location:
        params["location"] = location
        params["sortrule"] = "distance"
    payload = http_get_json("/v5/place/text", params)
    return payload.get("pois") or []


def score_poi_match(query, poi):
    query = (query or "").strip().lower()
    name = str(poi.get("name") or "").strip().lower()
    address = str(poi.get("address") or "").strip().lower()
    adname = str(poi.get("adname") or "").strip().lower()
    type_name = str(poi.get("type") or "").strip().lower()
    score = 0
    if query == name:
        score += 100
    if query and query in name:
        score += 40
    if query and query in address:
        score += 20
    if query and query in adname:
        score += 10
    if any(k in type_name for k in ["商务住宅", "公司企业", "购物", "餐饮", "风景名胜", "医院", "学校"]):
        score += 5
    distance = poi.get("distance")
    try:
        if distance not in (None, ""):
            d = int(distance)
            score += max(0, 20 - min(d // 200, 20))
    except Exception:
        pass
    return score


def format_poi_candidate(poi):
    name = poi.get("name") or "未知"
    address = poi.get("address") or poi.get("adname") or ""
    city = poi.get("cityname") or ""
    adname = poi.get("adname") or ""
    line = name
    extras = [x for x in [city, adname, address] if x]
    if extras:
        line += " | " + " ".join(extras)
    return line


def resolve_place(query, city, key, config, prefer_poi=True):
    normalized = normalize_alias(query, config)
    if not normalized:
        raise TrafficQueryError("Empty place query")

    poi_candidates = []
    if prefer_poi:
        try:
            poi_candidates = poi_search(normalized, city, key, limit=8, city_limit=False)
        except Exception:
            poi_candidates = []

    scored = sorted(
        ((score_poi_match(normalized, poi), poi) for poi in poi_candidates),
        key=lambda x: x[0],
        reverse=True,
    )
    top_score = scored[0][0] if scored else -1
    top_pois = [poi for score, poi in scored if score == top_score and score >= 40][:3]

    if len(top_pois) > 1:
        raise TrafficQueryError(
            "地点不够精确，请从以下候选里选一个后重试：\n- "
            + "\n- ".join(format_poi_candidate(p) for p in top_pois)
        )

    if len(top_pois) == 1:
        poi = top_pois[0]
        location = poi.get("location")
        if not location:
            raise TrafficQueryError(f"POI missing location: {poi.get('name') or normalized}")
        return {
            "query": query,
            "resolved": normalized,
            "formatted_address": poi.get("name") or normalized,
            "location": location,
            "city": poi.get("cityname") or city,
            "match_type": "poi",
            "confidence": "high",
            "note": None,
        }

    payload = http_get_json(
        "/v3/geocode/geo",
        {"key": key, "address": normalized, **({"city": city} if city else {})},
    )
    geocodes = payload.get("geocodes") or []
    if not geocodes:
        raise TrafficQueryError(f"Place resolve failed: {normalized}")
    top = geocodes[0]
    location = top.get("location")
    if not location:
        raise TrafficQueryError(f"Missing location for: {normalized}")

    confidence = "high"
    note = None
    formatted = top.get("formatted_address") or normalized
    if normalized not in formatted and (top.get("district") or top.get("city") or top.get("province")):
        confidence = "approx"
        note = f"未精确命中“{query}”，当前只命中到“{formatted}”范围；结果为近似值，仅供参考。"

    return {
        "query": query,
        "resolved": normalized,
        "formatted_address": formatted,
        "location": location,
        "city": top.get("city") or city,
        "match_type": "geocode",
        "confidence": confidence,
        "note": note,
    }


def route_command(args, config):
    key = get_api_key(args, config)
    origin = resolve_place(args.origin, args.city, key, config)
    destination = resolve_place(args.destination, args.city, key, config)
    payload = http_get_json(
        "/v3/direction/driving",
        {
            "key": key,
            "origin": origin["location"],
            "destination": destination["location"],
            "extensions": "all",
            "strategy": args.strategy,
        },
    )
    route = payload.get("route") or {}
    paths = route.get("paths") or []
    if not paths:
        raise TrafficQueryError("No driving route returned")
    path = paths[0]
    duration_sec = int(float(path.get("duration") or 0))
    distance_m = int(float(path.get("distance") or 0))
    tolls = path.get("tolls") or "0"
    traffic_lights = path.get("traffic_lights") or path.get("trafficLightsCount") or "0"
    taxi_cost = route.get("taxi_cost") or ""
    print(f"路线: {origin['formatted_address']} -> {destination['formatted_address']}")
    print(f"距离: {distance_m / 1000:.1f} km")
    print(f"预计用时: {format_duration(duration_sec)}")
    print(f"过路费: ¥{tolls}")
    if taxi_cost:
        print(f"打车参考: ¥{taxi_cost}")
    print(f"红绿灯: {traffic_lights}")
    if origin.get("note"):
        print(f"提示: {origin['note']}")
    if destination.get("note"):
        print(f"提示: {destination['note']}")
    steps = path.get("steps") or []
    for idx, step in enumerate(steps[: args.steps], start=1):
        instruction = (step.get("instruction") or "").replace("<br>", " ").strip()
        road = (step.get("road") or "").strip()
        step_distance = step.get("distance") or "0"
        tmcs = step.get("tmcs") or []
        statuses = [t.get("status") for t in tmcs if t.get("status")]
        summary = summarize_statuses(statuses)
        line = f"{idx}. {instruction}"
        if road:
            line += f" | 道路: {road}"
        line += f" | {int(float(step_distance))}m"
        if summary:
            line += f" | 路况: {summary}"
        print(line)


def traffic_road_command(args, config):
    key = get_api_key(args, config)
    payload = http_get_json(
        "/v3/traffic/status/road",
        {"key": key, "name": args.road, **({"city": args.city} if args.city else {}), "extensions": "all"},
    )
    info = payload.get("trafficinfo") or {}
    print(f"道路: {info.get('description') or args.road}")
    if info.get("evaluation"):
        print(f"评估: {info['evaluation']}")
    if info.get("status"):
        print(f"状态: {info['status']}")
    if info.get("speed"):
        print(f"平均速度: {info['speed']} km/h")
    if info.get("direction"):
        print(f"方向: {info['direction']}")
    if info.get("angle"):
        print(f"角度: {info['angle']}")
    if info.get("description"):
        print(f"说明: {info['description']}")


def poi_command(args, config):
    key = get_api_key(args, config)
    location = None
    if args.around:
        center = resolve_place(args.around, args.city, key, config)
        location = center["location"]
        if center.get("note"):
            print(f"提示: {center['note']}")
    pois = poi_search(args.keyword, args.city, key, location=location, limit=args.limit, city_limit=args.city_limit)
    if not pois:
        raise TrafficQueryError("No POI results")
    for idx, poi in enumerate(pois[: args.limit], start=1):
        name = poi.get("name") or "未知"
        address = poi.get("address") or poi.get("adname") or ""
        distance = poi.get("distance")
        tel = ",".join(poi.get("tel") or []) if isinstance(poi.get("tel"), list) else (poi.get("tel") or "")
        biz = poi.get("business") or ""
        type_name = poi.get("type") or ""
        line = f"{idx}. {name}"
        if type_name:
            line += f" | {type_name}"
        if address:
            line += f" | {address}"
        if biz:
            line += f" | 商圈: {biz}"
        if distance not in (None, ""):
            line += f" | 距离: {distance}m"
        if tel:
            line += f" | 电话: {tel}"
        print(line)


def summarize_statuses(statuses):
    if not statuses:
        return ""
    order = ["未知", "畅通", "缓行", "拥堵", "严重拥堵"]
    unique = []
    for status in statuses:
        if status not in unique:
            unique.append(status)
    unique.sort(key=lambda s: order.index(s) if s in order else len(order))
    return "/".join(unique)


def format_duration(seconds):
    hours, rem = divmod(seconds, 3600)
    minutes, _ = divmod(rem, 60)
    parts = []
    if hours:
        parts.append(f"{hours}小时")
    if minutes or not parts:
        parts.append(f"{minutes}分钟")
    return "".join(parts)


def build_parser():
    parser = argparse.ArgumentParser(description="OpenClaw traffic-query skill helper")
    parser.add_argument("--api-key", help="AMap Web Service API key")
    sub = parser.add_subparsers(dest="command", required=True)

    route = sub.add_parser("route", help="Driving route with traffic")
    route.add_argument("--from", dest="origin", required=True, help="Origin address or alias")
    route.add_argument("--to", dest="destination", required=True, help="Destination address or alias")
    route.add_argument("--city", help="Optional city for geocoding")
    route.add_argument("--strategy", default="0", help="AMap driving strategy, default 0")
    route.add_argument("--steps", type=int, default=5, help="How many route steps to print")
    route.set_defaults(func=route_command)

    road = sub.add_parser("traffic-road", help="Road traffic status")
    road.add_argument("--road", required=True, help="Road name")
    road.add_argument("--city", help="City name")
    road.set_defaults(func=traffic_road_command)

    poi = sub.add_parser("poi", help="POI text search")
    poi.add_argument("--keyword", required=True, help="Keyword like 咖啡/景点/医院")
    poi.add_argument("--city", help="City name")
    poi.add_argument("--city-limit", action="store_true", help="Limit search to the city")
    poi.add_argument("--around", help="Address or alias used as search center")
    poi.add_argument("--limit", type=int, default=5, help="How many results to print")
    poi.set_defaults(func=poi_command)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    config = load_config()
    try:
        args.func(args, config)
    except TrafficQueryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
    except urllib.error.URLError as exc:
        print(f"ERROR: Network failure: {exc}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
