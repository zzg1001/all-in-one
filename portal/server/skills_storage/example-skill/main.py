# 示例技能脚本
# 此脚本展示如何编写一个技能

# 可用的全局变量:
# - params: dict  用户传入的参数
# - SKILL_DIR: Path  技能文件夹路径
# - OUTPUTS_DIR: Path  输出目录
# - generate_unique_filename(prefix, ext): 生成唯一文件名
# - pd / pandas: pandas 库
# - Path: pathlib.Path

# 获取参数
name = params.get("name", "World")
action = params.get("action", "greet")

print(f"执行技能: action={action}, name={name}")

# 生成输出文件
filename = generate_unique_filename("example", "html")
filepath = OUTPUTS_DIR / filename

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>示例输出</title>
    <style>
        body {{ font-family: sans-serif; padding: 40px; background: #f5f5f5; }}
        .card {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto; }}
        h1 {{ color: #333; }}
        p {{ color: #666; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Hello, {name}!</h1>
        <p>Action: {action}</p>
        <p>This is an example output from the skill.</p>
    </div>
</body>
</html>
"""

filepath.write_text(html_content, encoding="utf-8")
print(f"已生成文件: {filename}")

# 设置 result 变量返回结果
# _output_file 是特殊字段，用于指定输出文件
result = {
    "message": f"Hello, {name}!",
    "action": action,
    "_output_file": {
        "name": filename,
        "type": "html",
        "url": f"/outputs/{filename}",
        "path": str(filepath)
    }
}
