#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
消防商机筛选器
搜索知识库或上传文件中的消防商机，输出Excel
"""

import sys
import json
import uuid
from pathlib import Path
from datetime import datetime

# 消防关键词
FIRE_KEYWORDS = [
    '消防', '灭火', '火灾', '防火', '灭火器', '消火栓', '喷淋',
    '烟感', '温感', '报警器', '防火门', '消防泵', '消防工程',
    '消防设施', '消防检测', '消防维保', '应急照明', '疏散'
]


def main(params=None):
    """
    搜索消防商机并输出Excel

    params:
        - file_path/file_paths: 上传的Excel文件（可选）
        - agent_id: Agent ID
        - keywords: 额外关键词
    """
    import pandas as pd

    params = params or {}

    # 获取文件路径
    file_path = params.get('file_path') or params.get('file')
    if not file_path:
        paths = params.get('file_paths') or params.get('files') or []
        if paths:
            file_path = paths[0] if isinstance(paths, list) else paths

    agent_id = params.get('agent_id')
    extra_keywords = params.get('keywords', [])

    # 合并关键词
    keywords = FIRE_KEYWORDS.copy()
    if extra_keywords:
        if isinstance(extra_keywords, str):
            keywords.append(extra_keywords)
        else:
            keywords.extend(extra_keywords)

    all_data = []
    source = ""

    # 1. 从上传文件读取
    if file_path and Path(file_path).exists():
        try:
            df = pd.read_excel(file_path)
            # 处理可能的标题行问题
            if 'Unnamed' in str(df.columns[0]):
                df.columns = df.iloc[0]
                df = df[1:].reset_index(drop=True)
            all_data = df.to_dict('records')
            source = "上传文件"
            print(f"[INFO] 从文件读取 {len(all_data)} 条数据", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] 读取文件失败: {e}", file=sys.stderr)

    # 2. 从知识库搜索
    if not all_data:
        try:
            # 先用 agent_id 搜索
            vector_data = search_knowledge_base(agent_id, keywords)
            # 如果没有结果，尝试搜索全部数据
            if not vector_data and agent_id:
                print(f"[INFO] agent_id={agent_id} 无数据，尝试搜索全部", file=sys.stderr)
                vector_data = search_knowledge_base(None, keywords)
            all_data = vector_data
            source = "知识库"
            print(f"[INFO] 从知识库获取 {len(all_data)} 条数据", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] 搜索知识库失败: {e}", file=sys.stderr)

    # 3. 筛选消防相关
    filtered = filter_fire_data(all_data, keywords)
    print(f"[INFO] 筛选出 {len(filtered)} 条消防相关商机", file=sys.stderr)

    # 4. 输出Excel
    if filtered:
        output_path, output_url = save_to_excel(filtered, source)
        print(f"找到 {len(filtered)} 条消防商机")
        return {
            "message": f"找到 {len(filtered)} 条消防商机，已导出Excel",
            "_output_file": {
                "path": output_path,
                "name": Path(output_path).name,
                "type": "excel",
                "url": output_url
            }
        }
    else:
        print("未找到消防相关商机，知识库中暂无数据")
        return {
            "message": "未找到消防相关商机，知识库中暂无数据",
            "_no_output_file": True
        }


def search_knowledge_base(agent_id, keywords):
    """从知识库搜索（直接 SQL 查询，关键词匹配）"""
    try:
        script_dir = Path(__file__).parent.parent.parent.parent
        sys.path.insert(0, str(script_dir))

        from config import get_settings
        import psycopg2

        settings = get_settings()
        conn = psycopg2.connect(settings.vector_db_url)

        try:
            with conn.cursor() as cur:
                # 构建关键词 LIKE 条件
                keyword_conditions = " OR ".join([
                    f"content ILIKE '%{kw}%'" for kw in keywords[:10]
                ])

                # 构建 agent_id 条件
                agent_condition = f"AND agent_id = '{agent_id}'" if agent_id else ""

                sql = f"""
                    SELECT content, metadata
                    FROM document_embeddings
                    WHERE ({keyword_conditions}) {agent_condition}
                    LIMIT 200
                """

                cur.execute(sql)
                rows = cur.fetchall()

                print(f"[INFO] SQL 查询返回 {len(rows)} 条记录", file=sys.stderr)

                # 转换格式
                data = []
                for row in rows:
                    content = row[0] or ''
                    metadata = row[1] or {}

                    item = {'原始内容': content}

                    # 尝试解析结构化字段
                    if '; ' in content:
                        for part in content.split('; '):
                            if ': ' in part:
                                k, v = part.split(': ', 1)
                                item[k.strip()] = v.strip()

                    data.append(item)

                return data

        finally:
            conn.close()

    except Exception as e:
        print(f"[ERROR] 知识库搜索异常: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return []


def filter_fire_data(data, keywords):
    """筛选消防相关数据"""
    if not data:
        return []

    filtered = []
    pattern = '|'.join(keywords)

    for item in data:
        text = json.dumps(item, ensure_ascii=False, default=str).lower()
        if any(kw.lower() in text for kw in keywords):
            filtered.append(item)

    return filtered


def save_to_excel(data, source):
    """保存到Excel，返回 (路径, URL)"""
    import pandas as pd

    # 获取输出目录
    script_dir = Path(__file__).parent.parent.parent.parent
    outputs_dir = script_dir / 'outputs'
    outputs_dir.mkdir(exist_ok=True)

    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"消防商机_{timestamp}.xlsx"
    output_path = outputs_dir / filename

    # 转换为DataFrame并保存
    df = pd.DataFrame(data)

    # 清理列名
    df.columns = [str(col).strip() for col in df.columns]

    # 保存
    df.to_excel(output_path, index=False, engine='openpyxl')
    print(f"[INFO] 已保存到 {output_path}", file=sys.stderr)

    # 生成 URL
    url = f"/outputs/{filename}"

    return str(output_path), url


if __name__ == '__main__':
    result = main({'agent_id': 'test'})
    print(json.dumps(result, ensure_ascii=False, indent=2))
