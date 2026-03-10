#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高铁查询助手 - 通过12306网页爬取
功能：查询高铁/动车班次、票价、时刻表
"""

import json
import urllib.request
import urllib.parse
import re
from datetime import datetime, timedelta

# 常用车站代码映射
STATION_CODES = {
    '深圳北': 'IOQ',
    '深圳': 'SZQ',
    '广州南': 'IZQ',
    '广州': 'GZQ',
    '北京南': 'VNP',
    '北京': 'BJP',
    '上海虹桥': 'AOH',
    '上海': 'SHH',
    '杭州东': 'HGH',
    '杭州': 'HZH',
    '南京南': 'NKH',
    '南京': 'NJH',
    '武汉': 'WHN',
    '成都东': 'ICW',
    '成都': 'CDW',
    '重庆北': 'CUW',
    '重庆': 'CQW',
    '西安北': 'EAY',
    '西安': 'XAY',
    '长沙南': 'CWQ',
    '长沙': 'CSQ',
    '郑州东': 'ZAF',
    '郑州': 'ZZF',
    '天津': 'TJP',
    '天津西': 'TXP',
    '合肥南': 'ENH',
    '合肥': 'HFH',
    '厦门北': 'XKS',
    '厦门': 'XMS',
    '福州': 'FZS',
    '福州南': 'FYS',
    '苏州': 'SZH',
    '无锡': 'WTH',
    '东莞': 'RTQ',
    '东莞东': 'DMA',
    '佛山': 'FOQ',
    '珠海': 'ZHQ',
    '中山': 'ZSQ',
    '惠州': 'HCQ',
    '汕头': 'OTQ',
}


def get_station_code(station_name):
    """获取车站代码"""
    return STATION_CODES.get(station_name)


def query_12306(from_station, to_station, date):
    """
    查询12306列车信息（模拟查询）
    由于12306需要验证码和登录，这里提供格式化输出
    """
    from_code = get_station_code(from_station)
    to_code = get_station_code(to_station)
    
    print(f"\n🚄 高铁查询")
    print("═" * 60)
    print(f"📍 路线：{from_station} → {to_station}")
    print(f"📅 日期：{date}")
    
    if not from_code or not to_code:
        print("⚠️ 站点代码未知，请使用以下方式查询：")
        print("─" * 60)
    else:
        print(f"🔖 站点代码：{from_code} → {to_code}")
        print("─" * 60)
    
    # 尝试访问12306 API
    try:
        url = f"https://kyfw.12306.cn/otn/leftTicket/queryA"
        url += f"?leftTicketDTO.train_date={date}"
        url += f"&leftTicketDTO.from_station={from_code}"
        url += f"&leftTicketDTO.to_station={to_code}"
        url += "&purpose_codes=ADULT"
        
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        req.add_header('Referer', 'https://kyfw.12306.cn/otn/leftTicket/init')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if data.get('status') and data.get('data', {}).get('result'):
                trains = data['data']['result']
                return parse_train_data(trains)
    
    except Exception as e:
        pass
    
    # 返回提示信息
    return None


def parse_train_data(trains):
    """解析列车数据"""
    result = []
    for train in trains[:20]:  # 最多显示20班
        info = train.split('|')
        if len(info) >= 35:
            train_data = {
                'train_no': info[3],
                'from_station': info[6],
                'to_station': info[7],
                'start_time': info[8],
                'arrive_time': info[9],
                'duration': info[10],
                'business_seat': info[32] or '无',
                'first_class': info[31] or '无',
                'second_class': info[30] or '无',
                'soft_sleeper': info[23] or '无',
                'hard_sleeper': info[28] or '无',
                'hard_seat': info[29] or '无',
            }
            result.append(train_data)
    return result


def format_train_result(trains, from_station, to_station):
    """格式化列车信息"""
    if not trains:
        result = []
        result.append("📱 实时查询建议：")
        result.append("─" * 60)
        result.append("1. 12306官网：https://kyfw.12306.cn")
        result.append("2. 12306 App（推荐）")
        result.append("3. 携程/去哪儿/飞猪 App")
        result.append("")
        result.append("💡 常见班次参考：")
        result.append("─" * 60)
        result.append(f"深圳北 → 广州南：每天约80+班次，车程约30分钟")
        result.append(f"深圳北 → 长沙南：每天约20+班次，车程约3小时")
        result.append(f"深圳北 → 厦门北：每天约15+班次，车程约3.5小时")
        result.append(f"深圳北 → 杭州东：每天约10+班次，车程约7小时")
        result.append(f"深圳北 → 上海虹桥：每天约15+班次，车程约8小时")
        result.append(f"深圳北 → 北京西：每天约10+班次，车程约8.5小时")
        return '\n'.join(result)
    
    result = []
    result.append(f"\n找到 {len(trains)} 班列车：")
    result.append("─" * 60)
    result.append(f"{'车次':<10} {'出发':<8} {'到达':<8} {'历时':<8} {'二等座':<8} {'一等座':<8}")
    result.append("─" * 60)
    
    for t in trains:
        line = f"{t['train_no']:<10} {t['start_time']:<8} {t['arrive_time']:<8} {t['duration']:<8} {t['second_class']:<8} {t['first_class']:<8}"
        result.append(line)
    
    return '\n'.join(result)


def search_train(from_station, to_station, date=None):
    """主查询函数"""
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    trains = query_12306(from_station, to_station, date)
    print(format_train_result(trains, from_station, to_station))
    
    return trains


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print("用法: python train.py <出发站> <到达站> [日期]")
        print("示例: python train.py 深圳北 广州南 2026-03-10")
        sys.exit(1)
    
    from_station = sys.argv[1]
    to_station = sys.argv[2]
    date = sys.argv[3] if len(sys.argv) > 3 else None
    
    search_train(from_station, to_station, date)
