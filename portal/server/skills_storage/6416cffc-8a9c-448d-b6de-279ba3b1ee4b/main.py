# Hello World 示例技能
# 一个简单的问候技能模板

def main(params):
    """技能入口函数"""
    user_input = params.get('input', '').strip()
    
    try:
        # 获取用户名称，如果没有输入则使用默认值
        name = user_input if user_input else '世界'
        
        # 生成问候消息
        greeting = f"你好，{name}！👋"
        
        # 添加一些额外信息
        message = f"{greeting}\n\n这是一个示例技能，你可以基于此模板开发自己的技能。\n\n你输入的内容是: {user_input if user_input else '(空)'}"
        
        return {
            "status": "success",
            "message": message,
            "data": {
                "input": user_input,
                "name": name,
                "greeting": greeting
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"执行失败: {str(e)}"
        }