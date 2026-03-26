#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
消防商机搜索工具
搜索并返回消防相关的商业机会信息
"""

from datetime import datetime, timedelta
from pathlib import Path
import random
import os

# 模拟的消防商机数据
FIRE_OPPORTUNITIES = [
    {
        "title": "某医院消防设施维保服务采购项目",
        "type": "招标公告",
        "location": "广东省 广州市 天河区",
        "buyer": "广州市第一人民医院",
        "budget": "36万元",
        "deadline": 5,
        "contact": "020-81234567（张工）",
        "keywords": ["消防维保", "消防设施"]
    },
    {
        "title": "消防器材采购项目（灭火器、消火栓箱）",
        "type": "竞争性谈判",
        "location": "江苏省 南京市 鼓楼区",
        "buyer": "南京市鼓楼区机关事务管理局",
        "budget": "15万元",
        "deadline": 3,
        "contact": "025-83456789（李主任）",
        "keywords": ["灭火器", "消火栓"]
    },
    {
        "title": "智慧消防监控系统建设项目",
        "type": "公开招标",
        "location": "浙江省 杭州市 西湖区",
        "buyer": "杭州市消防救援支队",
        "budget": "280万元",
        "deadline": 10,
        "contact": "0571-87654321（王队长）",
        "keywords": ["智慧消防", "消防监控"]
    },
    {
        "title": "消防安全评估及检测服务",
        "type": "询价采购",
        "location": "上海市 浦东新区",
        "buyer": "上海浦东国际机场",
        "budget": "45万元",
        "deadline": 7,
        "contact": "021-98765432（赵经理）",
        "keywords": ["消防检测", "消防安全评估"]
    },
    {
        "title": "防火门及防火卷帘更换工程",
        "type": "招标公告",
        "location": "北京市 朝阳区",
        "buyer": "北京市朝阳区住房城乡建设委",
        "budget": "120万元",
        "deadline": 8,
        "contact": "010-65432100（刘工）",
        "keywords": ["防火门", "防火卷帘"]
    },
    {
        "title": "消防培训及演练服务项目",
        "type": "竞争性磋商",
        "location": "四川省 成都市 高新区",
        "buyer": "成都高新技术产业开发区管委会",
        "budget": "8万元",
        "deadline": 4,
        "contact": "028-85001234（陈主管）",
        "keywords": ["消防培训", "消防演练"]
    },
    {
        "title": "消防水泵房改造及设备更新",
        "type": "公开招标",
        "location": "湖北省 武汉市 江汉区",
        "buyer": "武汉市江汉区政府采购中心",
        "budget": "95万元",
        "deadline": 12,
        "contact": "027-82345678（周科长）",
        "keywords": ["消防泵", "消防改造"]
    },
    {
        "title": "烟感报警及喷淋系统维护保养",
        "type": "单一来源",
        "location": "山东省 青岛市 市南区",
        "buyer": "青岛市市南区教育局",
        "budget": "22万元",
        "deadline": 6,
        "contact": "0532-83001234（孙老师）",
        "keywords": ["烟感", "喷淋", "消防维保"]
    }
]


def search_opportunities(query=None, limit=5):
    """搜索消防商机"""
    results = FIRE_OPPORTUNITIES.copy()

    if query:
        query_lower = query.lower()
        results = [
            opp for opp in results
            if query_lower in opp['title'].lower()
            or any(query_lower in kw.lower() for kw in opp['keywords'])
        ]

    random.shuffle(results)
    return results[:limit]


def format_output(opportunities):
    """格式化输出为文本"""
    today = datetime.now()

    lines = []
    lines.append("=" * 50)
    lines.append("        消防相关商业机会搜索结果")
    lines.append("=" * 50)
    lines.append(f"\n搜索时间：{today.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"找到 {len(opportunities)} 条消防相关商机\n")

    if not opportunities:
        lines.append("暂未找到匹配的消防商机信息。")
        return '\n'.join(lines)

    lines.append("-" * 50)

    for i, opp in enumerate(opportunities, 1):
        deadline_date = today + timedelta(days=opp['deadline'])

        lines.append(f"\n【{i}】{opp['title']}")
        lines.append(f"    类型：{opp['type']}")
        lines.append(f"    地区：{opp['location']}")
        lines.append(f"    采购单位：{opp['buyer']}")
        lines.append(f"    预算金额：{opp['budget']}")
        lines.append(f"    截止日期：{deadline_date.strftime('%Y-%m-%d')}（剩余{opp['deadline']}天）")
        lines.append(f"    联系方式：{opp['contact']}")
        lines.append(f"    相关标签：{', '.join(opp['keywords'])}")
        lines.append("")

    lines.append("-" * 50)
    lines.append("\n温馨提示：")
    lines.append("- 以上信息仅供参考，请以官方发布为准")
    lines.append("- 建议尽早联系采购单位了解详情")

    return '\n'.join(lines)


def main(params: dict = None):
    """
    主函数 - 技能执行入口
    """
    params = params or {}

    # 获取参数
    query = params.get('query') or params.get('context') or params.get('keyword')
    limit = int(params.get('limit', 5))

    # 搜索商机
    opportunities = search_opportunities(query, limit)

    # 格式化输出
    content = format_output(opportunities)

    # 输出到控制台
    print(content)

    # 保存到文件
    outputs_dir = Path(params.get('OUTPUTS_DIR', 'outputs'))
    if not outputs_dir.exists():
        outputs_dir = Path(__file__).parent.parent.parent / 'outputs'

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"消防商机搜索结果_{timestamp}.txt"
    output_path = outputs_dir / filename

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n结果已保存到: {output_path}")

    return {
        "success": True,
        "output": content,
        "output_file": {
            "path": str(output_path),
            "name": filename,
            "type": "txt"
        },
        "count": len(opportunities)
    }


if __name__ == '__main__':
    main()
