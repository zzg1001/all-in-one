"""
初始化默认用户
"""
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import hash_password


DEFAULT_USERS = [
    # ========== 系统管理员 ==========
    {"username": "admin", "password": "admin123", "display_name": "系统管理员", "department": None, "role": "admin"},
    {"username": "superadmin", "password": "super123", "display_name": "超级管理员", "department": None, "role": "admin"},

    # ========== 老板/高管（可访问所有部门）==========
    {"username": "boss", "password": "boss123", "display_name": "张总", "department": None, "role": "boss"},
    {"username": "ceo", "password": "ceo123", "display_name": "王总经理", "department": None, "role": "boss"},

    # ========== HR 部门 ==========
    {"username": "hr_manager", "password": "hr123", "display_name": "李经理", "department": "HR", "role": "boss"},
    {"username": "hr_zhang", "password": "123456", "display_name": "张小红", "department": "HR", "role": "user"},
    {"username": "hr_wang", "password": "123456", "display_name": "王丽丽", "department": "HR", "role": "user"},
    {"username": "hr_liu", "password": "123456", "display_name": "刘招聘", "department": "HR", "role": "user"},

    # ========== 销售部门 ==========
    {"username": "sales_manager", "password": "sales123", "display_name": "陈经理", "department": "销售", "role": "boss"},
    {"username": "sales_zhao", "password": "123456", "display_name": "赵销售", "department": "销售", "role": "user"},
    {"username": "sales_qian", "password": "123456", "display_name": "钱大业", "department": "销售", "role": "user"},
    {"username": "sales_sun", "password": "123456", "display_name": "孙小明", "department": "销售", "role": "user"},
    {"username": "sales_li", "password": "123456", "display_name": "李销冠", "department": "销售", "role": "user"},

    # ========== 采购部门 ==========
    {"username": "purchase_manager", "password": "purchase123", "display_name": "吴经理", "department": "采购", "role": "boss"},
    {"username": "purchase_zhou", "password": "123456", "display_name": "周采购", "department": "采购", "role": "user"},
    {"username": "purchase_zheng", "password": "123456", "display_name": "郑供应", "department": "采购", "role": "user"},

    # ========== 行政部门 ==========
    {"username": "admin_manager", "password": "admin123", "display_name": "杨经理", "department": "行政", "role": "boss"},
    {"username": "admin_chen", "password": "123456", "display_name": "陈行政", "department": "行政", "role": "user"},
    {"username": "admin_huang", "password": "123456", "display_name": "黄前台", "department": "行政", "role": "user"},

    # ========== 财务部门 ==========
    {"username": "finance_manager", "password": "finance123", "display_name": "林经理", "department": "财务", "role": "boss"},
    {"username": "finance_xu", "password": "123456", "display_name": "徐会计", "department": "财务", "role": "user"},
    {"username": "finance_he", "password": "123456", "display_name": "何出纳", "department": "财务", "role": "user"},
    {"username": "finance_luo", "password": "123456", "display_name": "罗审计", "department": "财务", "role": "user"},
]


def init_default_users(db: Session):
    """
    初始化默认用户

    如果用户已存在则跳过
    """
    created_count = 0
    for user_data in DEFAULT_USERS:
        # 检查用户是否已存在
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        if existing:
            continue

        # 创建用户
        user = User(
            username=user_data["username"],
            password_hash=hash_password(user_data["password"]),
            display_name=user_data["display_name"],
            department=user_data["department"],
            role=user_data["role"],
            is_active=True
        )
        db.add(user)
        created_count += 1

    db.commit()
    print(f"Default users initialized. Created {created_count} new users.")
