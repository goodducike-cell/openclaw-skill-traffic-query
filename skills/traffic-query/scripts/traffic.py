#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交通查询助手 - 基于高德地图API
功能：路线规划、实时路况、POI搜索、高铁查询
"""

import argparse
import json
import os
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, '..', 'config.json')

def _load_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ 配置文件不存在: {CONFIG_PATH}")
        print("请复制 config.example.json 为 config.json 并填入高德 API Key")
        exit(1)

_config = _load_config()
AMAP_KEY = os.environ.get('AMAP_KEY') or _config.get('amap_key', '')
if not AMAP_KEY or AMAP_KEY == 'YOUR_AMAP_API_KEY':
    print("❌ 请在 config.json 中配置 amap_key 或设置 AMAP_KEY 环境变量")
    exit(1)

AMAP_BASE_URL = "https://restapi.amap.com/v3"


def geocode(address, city=None):
    """地址转经纬度"""
    url = f"{AMAP_BASE_URL}/geocode/geo?key={AMAP_KEY}&address={urllib.parse.quote(address)}"
    if city:
        url += f"&city={urllib.parse.quote(city)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data['status'] == '1' and data['geocodes']:
                location = data['geocodes'][0]['location']
                return location.split(',')
            else:
                return None, None
    except Exception as e:
        print(f"❌ 地理编码失败: {e}")
        return None, None


def reverse_geocode(lng, lat):
    """经纬度转地址"""
    url = f"{AMAP_BASE_URL}/geocode/regeo?key={AMAP_KEY}&location={lng},{lat}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data['status'] == '1':
                return data['regeocode']['formatted_address']
            return None
    except Exception as e:
        print(f"❌ 逆地理编码失败: {e}")
        return None


def get_route(origin, destination, strategy=0):
    """
    驾车路线规划
    strategy: 0-速度优先, 1-费用优先, 2-距离优先, 4-躲避拥堵
    """
    # 先将地址转为经纬度
    origin_lng, origin_lat = geocode(origin)
    dest_lng, dest_lat = geocode(destination)
    
    if not origin_lng or not dest_lng:
        print("❌ 无法识别起点或终点地址")
        return None
    
    url = f"{AMAP_BASE_URL}/direction/driving?key={AMAP_KEY}"
    url += f"&origin={origin_lng},{origin_lat}"
    url += f"&destination={dest_lng},{dest_lat}"
    url += f"&strategy={strategy}"
    url += "&extensions=all"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if data['status'] != '1':
                print(f"❌ 路线规划失败: {data.get('info', '未知错误')}")
                return None
            
            return data
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None


def get_traffic_status(road_name, city=None):
    """查询道路实时路况"""
    # 使用POI搜索找到道路
    url = f"{AMAP_BASE_URL}/place/text?key={AMAP_KEY}"
    url += f"&keywords={urllib.parse.quote(road_name)}"
    url += "&types=190301"  # 道路附属设施
    if city:
        url += f"&city={urllib.parse.quote(city)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if data['status'] != '1' or not data['pois']:
                print(f"❌ 未找到道路: {road_name}")
                return None
            
            return data['pois']
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return None


def search_poi(location, keywords, radius=3000):
    """搜索附近POI"""
    # 先获取位置经纬度
    lng, lat = geocode(location)
    if not lng:
        print(f"❌ 无法识别位置: {location}")
        return None
    
    url = f"{AMAP_BASE_URL}/place/around?key={AMAP_KEY}"
    url += f"&location={lng},{lat}"
    url += f"&keywords={urllib.parse.quote(keywords)}"
    url += f"&radius={radius}"
    url += "&offset=20"
    url += "&extensions=all"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if data['status'] != '1':
                print(f"❌ POI搜索失败: {data.get('info', '未知错误')}")
                return None
            
            return data['pois']
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None


def search_train(from_station, to_station, date=None):
    """查询高铁/动车班次（通过12306网页爬取或第三方API）"""
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    # 使用携程API（公开接口）
    url = "https://train.qunar.com/qunar/checiInfo.htm"
    params = {
        'from_station': from_station,
        'to_station': to_station,
        'date': date
    }
    
    print(f"\n🚄 查询 {from_station} → {to_station} ({date})")
    print("─" * 50)
    print("💡 提示：高铁实时查询需要12306官方API，此处提供参考信息")
    print("   建议使用 12306 App 或 携程App 查看实时余票")
    print("─" * 50)
    
    # 返回常用高铁信息格式
    return {
        'from': from_station,
        'to': to_station,
        'date': date,
        'note': '请使用12306或携程App查询实时班次和余票'
    }


def format_route_result(data, origin_name, dest_name):
    """格式化路线规划结果"""
    if not data or 'route' not in data:
        return "❌ 无法获取路线信息"
    
    route = data['route']['paths'][0]
    
    result = []
    result.append(f"\n🚗 路线规划：{origin_name} → {dest_name}")
    result.append("═" * 50)
    
    # 基本信息
    distance = int(route['distance']) / 1000
    duration = int(route['duration']) / 60
    tolls = int(route.get('tolls', 0))
    traffic_lights = route.get('trafficLightsCount', 'N/A')
    
    result.append(f"📏 总距离：{distance:.1f} 公里")
    result.append(f"⏱️ 预计时间：{int(duration)} 分钟 ({duration/60:.1f} 小时)")
    result.append(f"💰 预估路费：¥{tolls}")
    result.append(f"🚦 红绿灯：{traffic_lights} 个")
    
    # 路况摘要
    if 'restriction' in route:
        result.append(f"⚠️ 限行提示：{route['restriction']}")
    
    # 详细路线
    result.append("\n📋 详细路线：")
    result.append("─" * 50)
    
    for i, step in enumerate(route['steps'][:10], 1):  # 最多显示10步
        instruction = step['instruction'].replace('<br>', ' ').strip()
        road = step.get('road', '')
        distance_step = int(step['distance']) / 1000
        
        if road:
            result.append(f"{i}. {instruction} ({distance_step:.1f}km)")
        else:
            result.append(f"{i}. {instruction}")
    
    if len(route['steps']) > 10:
        result.append(f"... 共 {len(route['steps'])} 个导航点")
    
    return '\n'.join(result)


def format_poi_result(pois, keywords):
    """格式化POI搜索结果"""
    if not pois:
        return f"❌ 未找到相关 {keywords}"
    
    result = []
    result.append(f"\n📍 附近{keywords}（共 {len(pois)} 家）")
    result.append("═" * 50)
    
    for i, poi in enumerate(pois[:15], 1):
        name = poi['name']
        address = poi.get('address', '地址不详')
        distance = int(poi.get('distance', 0))
        type_code = poi.get('typecode', '')
        
        # 评分（如果有）
        rating = poi.get('biz_ext', {}).get('rating', '')
        cost = poi.get('biz_ext', {}).get('cost', '')
        
        line = f"{i}. {name}"
        if rating:
            line += f" ⭐{rating}"
        if cost:
            line += f" 💰人均¥{cost}"
        line += f"\n   📍 {address}"
        if distance > 0:
            line += f" ({distance}米)"
        
        result.append(line)
    
    return '\n'.join(result)


def main():
    parser = argparse.ArgumentParser(description='交通查询助手')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 路线规划
    route_parser = subparsers.add_parser('route', help='路线规划')
    route_parser.add_argument('--origin', '-o', required=True, help='起点地址')
    route_parser.add_argument('--destination', '-d', required=True, help='终点地址')
    route_parser.add_argument('--strategy', '-s', type=int, default=4, 
                             help='策略：0-速度优先，1-费用优先，2-距离优先，4-躲避拥堵')
    
    # 实时路况
    traffic_parser = subparsers.add_parser('traffic', help='实时路况')
    traffic_parser.add_argument('--road', '-r', required=True, help='道路名称')
    traffic_parser.add_argument('--city', '-c', help='城市名称')
    
    # POI搜索
    poi_parser = subparsers.add_parser('poi', help='POI搜索')
    poi_parser.add_argument('--location', '-l', required=True, help='位置')
    poi_parser.add_argument('--keywords', '-k', required=True, help='关键词')
    poi_parser.add_argument('--radius', '-r', type=int, default=3000, help='搜索半径(米)')
    
    # 高铁查询
    train_parser = subparsers.add_parser('train', help='高铁查询')
    train_parser.add_argument('--from', '-f', required=True, dest='from_station', help='出发站')
    train_parser.add_argument('--to', '-t', required=True, dest='to_station', help='到达站')
    train_parser.add_argument('--date', '-d', help='日期 (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    if args.command == 'route':
        data = get_route(args.origin, args.destination, args.strategy)
        print(format_route_result(data, args.origin, args.destination))
    
    elif args.command == 'traffic':
        pois = get_traffic_status(args.road, args.city)
        if pois:
            print(f"\n🛣️ 道路查询：{args.road}")
            print("═" * 50)
            for poi in pois[:5]:
                print(f"📍 {poi['name']} - {poi.get('address', '地址不详')}")
    
    elif args.command == 'poi':
        pois = search_poi(args.location, args.keywords, args.radius)
        print(format_poi_result(pois, args.keywords))
    
    elif args.command == 'train':
        search_train(args.from_station, args.to_station, args.date)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
