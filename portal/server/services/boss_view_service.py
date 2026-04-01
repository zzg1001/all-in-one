"""
老板视角服务 - 聚合所有部门的File Manage数据
"""
from pathlib import Path
from typing import List, Dict, Any, Optional


# 部门Agent名称映射
DEPARTMENT_AGENTS = {
    "HR部门 Agent": "hr",
    "销售部门 Agent": "sales",
    "采购部门 Agent": "procurement",
    "行政部门 Agent": "admin",
    "财务部门 Agent": "finance",
}

# 老板视角Agent名称
BOSS_VIEW_AGENT_NAME = "老板视角"


def is_boss_view_agent(db, agent_id: str) -> bool:
    """判断是否是老板视角Agent"""
    from models.agent import Agent as AgentModel

    if not agent_id:
        return False
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent:
        return False
    return agent.name == BOSS_VIEW_AGENT_NAME


def get_department_agent_ids(db) -> Dict[str, str]:
    """获取所有部门Agent的ID映射

    Returns:
        Dict: {department_name: agent_id}
    """
    from models.agent import Agent as AgentModel

    result = {}
    for agent_name, dept_key in DEPARTMENT_AGENTS.items():
        agent = db.query(AgentModel).filter(AgentModel.name == agent_name).first()
        if agent:
            result[dept_key] = agent.id
    return result


def get_department_files(db, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """获取所有部门的File Manage文件列表

    Returns:
        Dict: {department_name: [file_info, ...]}
    """
    from models.data_note import DataNote

    dept_agent_ids = get_department_agent_ids(db)
    result = {}

    for dept_name, agent_id in dept_agent_ids.items():
        # 查询该部门agent的所有文件（非文件夹）
        files = db.query(DataNote).filter(
            DataNote.user_id == user_id,
            DataNote.agent_id == agent_id,
            DataNote.deleted_at.is_(None),
            DataNote.file_type != 'folder'
        ).all()

        result[dept_name] = [
            {
                "id": f.id,
                "name": f.name,
                "file_type": f.file_type,
                "file_url": f.file_url,
                "file_size": f.file_size,
                "description": f.description,
            }
            for f in files
        ]

    return result


async def read_file_content(file_url: str) -> Optional[str]:
    """读取文件内容（支持Excel、CSV、TXT）

    Args:
        file_url: 文件URL，如 /file-manage/xxx/yyy.xlsx

    Returns:
        文件内容的文本表示
    """
    from config import get_file_manage_dir, get_uploads_dir, get_outputs_dir

    if not file_url:
        return None

    try:
        # 解析路径
        if file_url.startswith('/file-manage/'):
            relative_path = file_url[len('/file-manage/'):]
            local_path = get_file_manage_dir() / relative_path
        elif file_url.startswith('/uploads/'):
            relative_path = file_url[len('/uploads/'):]
            local_path = get_uploads_dir() / relative_path
        elif file_url.startswith('/outputs/'):
            relative_path = file_url[len('/outputs/'):]
            local_path = get_outputs_dir() / relative_path
        else:
            return None

        if not local_path.exists():
            print(f"[BossView] 文件不存在: {local_path}")
            return None

        suffix = local_path.suffix.lower()

        # Excel 文件
        if suffix in ['.xlsx', '.xls']:
            import pandas as pd
            try:
                # 读取所有工作表
                excel_file = pd.ExcelFile(local_path)
                content_parts = []

                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    # 转换为Markdown表格
                    content_parts.append(f"### {sheet_name}\n")
                    content_parts.append(df.to_markdown(index=False))
                    content_parts.append("\n")

                return "\n".join(content_parts)
            except Exception as e:
                print(f"[BossView] 读取Excel失败: {e}")
                return None

        # CSV 文件
        elif suffix == '.csv':
            import pandas as pd
            try:
                df = pd.read_csv(local_path)
                return df.to_markdown(index=False)
            except Exception as e:
                print(f"[BossView] 读取CSV失败: {e}")
                return None

        # 文本文件
        elif suffix in ['.txt', '.md', '.json']:
            try:
                return local_path.read_text(encoding='utf-8')
            except:
                try:
                    return local_path.read_text(encoding='gbk')
                except Exception as e:
                    print(f"[BossView] 读取文本失败: {e}")
                    return None

        else:
            print(f"[BossView] 不支持的文件类型: {suffix}")
            return None

    except Exception as e:
        print(f"[BossView] 读取文件失败: {e}")
        return None


async def get_all_department_data(db, user_id: str, max_content_length: int = 50000) -> str:
    """获取所有部门的数据汇总

    Args:
        db: 数据库会话
        user_id: 用户ID
        max_content_length: 最大内容长度

    Returns:
        格式化的部门数据汇总文本
    """
    dept_files = get_department_files(db, user_id)

    content_parts = []
    total_length = 0

    dept_names_cn = {
        "hr": "人力资源部门",
        "sales": "销售部门",
        "procurement": "采购部门",
        "admin": "行政部门",
        "finance": "财务部门",
    }

    for dept_key, files in dept_files.items():
        dept_name = dept_names_cn.get(dept_key, dept_key)

        if not files:
            content_parts.append(f"\n## {dept_name}\n暂无数据文件\n")
            continue

        content_parts.append(f"\n## {dept_name}\n")

        for file_info in files:
            if total_length >= max_content_length:
                content_parts.append("\n[数据过多，已截断...]\n")
                break

            file_content = await read_file_content(file_info.get("file_url"))

            if file_content:
                # 截断单个文件内容
                if len(file_content) > 10000:
                    file_content = file_content[:10000] + "\n[文件内容过长，已截断...]"

                content_parts.append(f"\n### 文件: {file_info.get('name', '未知文件')}\n")
                content_parts.append(file_content)
                content_parts.append("\n")

                total_length += len(file_content)
            else:
                content_parts.append(f"\n### 文件: {file_info.get('name', '未知文件')}\n")
                content_parts.append(f"(文件类型: {file_info.get('file_type', '未知')}, 无法读取内容)\n")

    if not any(files for files in dept_files.values()):
        return ""

    return "".join(content_parts)


def build_boss_view_prompt(department_data: str, user_message: str) -> str:
    """构建老板视角的AI提示词

    Args:
        department_data: 各部门数据汇总
        user_message: 用户消息

    Returns:
        完整的提示词
    """
    if not department_data:
        return f"""## 用户问题
{user_message}

## 说明
当前没有各部门的数据文件。请告知用户需要先在各部门Agent的File Manage中上传相关数据文件，包括：
- HR部门 Agent: 人员数据、薪资数据、离职数据等
- 销售部门 Agent: 销售额、客户数据、区域数据等
- 采购部门 Agent: 采购额、供应商数据、成本数据等
- 行政部门 Agent: 费用数据、资产数据、预算数据等
- 财务部门 Agent: 收入、支出、利润、现金流等

上传数据后，可以生成综合的总裁仪表盘报告。"""

    return f"""## 各部门数据汇总

以下是从各部门Agent的File Manage中获取的数据：

{department_data}

---

## 用户问题
{user_message}

## 你的角色
你是企业的高层管理顾问，从老板/CEO视角分析企业整体经营状况。

## 回答要求
1. **综合分析各部门数据**，给出整体经营状况评估
2. **识别关键指标**：营收、利润、人力、采购、行政等核心KPI
3. **发现问题和风险**：哪些部门指标异常需要关注
4. **给出建议**：从管理决策角度提供建议

如果用户要求生成报告，请使用 executive-dashboard 技能生成综合PDF报告。"""
