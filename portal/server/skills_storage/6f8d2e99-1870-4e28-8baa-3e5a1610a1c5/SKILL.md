---
name: fire-opportunity-finder
description: |
  从Excel文件中筛选消防相关的商业机会（招标信息）。当用户提到以下场景时使用此skill：
  - 从招标数据中筛选消防相关项目
  - 查找消防设备、消防工程、灭火器、消防检测、消防培训等招标信息
  - 分析寻标宝、招标网等平台导出的Excel数据中的消防机会
  - 任何涉及"消防"+"招标/采购/商业机会/Excel"的组合查询
  即使用户没有明确说"消防招标"，只要涉及从Excel中筛选特定行业（消防）的招标信息，都应该使用此skill。
---

# 消防商业机会筛选器

从招标信息Excel文件中识别并筛选消防相关的商业机会。

## 使用方法

直接调用 `scripts/filter_fire_opportunities.py` 脚本：

```bash
python <skill_path>/scripts/filter_fire_opportunities.py <Excel文件路径>
```

## 脚本参数

| 参数 | 说明 |
|------|------|
| `file` | Excel文件路径（必填） |
| `--format`, `-f` | 输出格式：`markdown`(默认)、`json`、`csv` |
| `--output`, `-o` | 输出到文件（默认输出到stdout） |
| `--keywords`, `-k` | 添加额外关键词 |
| `--list-keywords` | 列出所有内置关键词 |

## 使用示例

**基本用法（输出Markdown）：**
```bash
python scripts/filter_fire_opportunities.py "c:\data\招标数据.xlsx"
```

**输出JSON格式：**
```bash
python scripts/filter_fire_opportunities.py "c:\data\招标数据.xlsx" -f json
```

**保存到文件：**
```bash
python scripts/filter_fire_opportunities.py "c:\data\招标数据.xlsx" -o result.md
```

**导出CSV：**
```bash
python scripts/filter_fire_opportunities.py "c:\data\招标数据.xlsx" -f csv -o 消防项目.csv
```

**添加自定义关键词：**
```bash
python scripts/filter_fire_opportunities.py "c:\data\招标数据.xlsx" -k 安全 应急
```

## 内置消防关键词

脚本内置30+个消防相关关键词，包括：

- **核心词**：消防、灭火、火灾、防火
- **设备类**：灭火器、消火栓、喷淋、烟感、温感、报警器、防火门、防火卷帘、消防泵、消防水箱、消防车、应急照明、疏散指示
- **服务类**：消防工程、消防设施、消防系统、消防改造、消防维保、消防检测、消防验收、消防培训、消防演练
- **管理类**：119、消防站、消防队、消防救援、消防监控

运行 `--list-keywords` 查看完整列表。

## 支持的Excel格式

- 寻标宝导出数据
- 其他招标平台导出数据
- 自动识别标题行（支持首行为标题或首行为数据）
- 自动识别"标题"、"项目名称"、"名称"等列名

## 输出示例

```markdown
## 消防相关商业机会筛选结果

**数据概览：**
- 原始数据总数：100 条
- 消防相关项目：5 条

**匹配的项目列表：**

### 1. 室内消防栓箱采购
- 标讯类型：招标｜招标公告
- 地区：广东省 湛江市 赤坎区
- 招采单位：湛江电力有限公司
- 投标截止：2026-04-01
- 联系人：0759-3165251（万云）
- 链接：[查看详情](https://...)
```
