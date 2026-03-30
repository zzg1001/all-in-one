#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能通用配置模块

提供路径配置和文件解析功能，供所有技能的 main.py 使用。
后端在调用 main.py 时会自动注入 _config 配置。

使用方式:
    from skill_config import SkillConfig, setup_encoding, log

    # 设置编码（Windows 必须在最开始调用）
    setup_encoding()

    def main(params: dict = None):
        config = SkillConfig(params)

        # 获取路径
        outputs_dir = config.outputs_dir
        uploads_dir = config.uploads_dir

        # 解析文件路径（自动转换 /uploads/xxx 为完整路径）
        file_path = config.resolve_file_path("/uploads/xxx.xlsx")

        # 获取 Excel 文件
        excel_file = config.get_excel_file()
"""

import sys
from pathlib import Path


def setup_encoding():
    """设置 Windows 上的 UTF-8 编码，必须在脚本最开始调用"""
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def log(msg):
    """输出日志到 stderr，避免污染 JSON 输出"""
    print(msg, file=sys.stderr)


class SkillConfig:
    """技能配置类，处理路径配置和文件解析"""

    def __init__(self, params: dict = None):
        """
        初始化配置

        Args:
            params: 从后端传入的参数，包含 _config 字段（由后端自动注入）
        """
        params = params or {}
        self._config = params.get("_config", {})
        self._params = params

        # 如果没有传入配置，使用相对路径推导（兼容本地测试）
        self._script_dir = Path(__file__).parent
        self._server_dir = self._script_dir.parent  # skills_storage 的父目录

    @property
    def server_dir(self) -> Path:
        """服务器根目录"""
        if self._config.get("server_dir"):
            return Path(self._config["server_dir"])
        return self._server_dir

    @property
    def outputs_dir(self) -> Path:
        """输出目录"""
        if self._config.get("outputs_dir"):
            return Path(self._config["outputs_dir"])
        return self._server_dir / "outputs"

    @property
    def uploads_dir(self) -> Path:
        """上传目录"""
        if self._config.get("uploads_dir"):
            return Path(self._config["uploads_dir"])
        return self._server_dir / "uploads"

    @property
    def skills_storage_dir(self) -> Path:
        """技能存储目录"""
        if self._config.get("skills_storage_dir"):
            return Path(self._config["skills_storage_dir"])
        return self._server_dir / "skills_storage"

    @property
    def skill_folder(self) -> Path:
        """当前技能文件夹"""
        if self._config.get("skill_folder"):
            return Path(self._config["skill_folder"])
        return self._script_dir

    def ensure_dirs(self):
        """确保输出目录存在"""
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    def resolve_file_path(self, file_path: str) -> str:
        """
        将 URL 路径或相对路径转换为完整的文件系统路径

        Args:
            file_path: 文件路径，支持以下格式：
                - /uploads/xxx.xlsx (URL 格式)
                - /outputs/xxx.pdf (URL 格式)
                - 完整的文件系统路径

        Returns:
            完整的文件系统路径
        """
        if not file_path:
            return file_path

        # 如果已经是完整路径且文件存在，直接返回
        p = Path(file_path)
        if p.is_absolute() and p.exists():
            return file_path

        # 处理 /uploads/xxx 格式的路径
        if file_path.startswith('/uploads/') or file_path.startswith('\\uploads\\'):
            filename = file_path.replace('/uploads/', '').replace('\\uploads\\', '')
            full_path = self.uploads_dir / filename
            if full_path.exists():
                return str(full_path)

        # 处理 /outputs/xxx 格式的路径
        if file_path.startswith('/outputs/') or file_path.startswith('\\outputs\\'):
            filename = file_path.replace('/outputs/', '').replace('\\outputs\\', '')
            full_path = self.outputs_dir / filename
            if full_path.exists():
                return str(full_path)

        # 尝试在 uploads 目录查找
        uploads_path = self.uploads_dir / Path(file_path).name
        if uploads_path.exists():
            return str(uploads_path)

        # 返回原始路径
        return file_path

    def resolve_file_paths(self, file_paths: list) -> list:
        """批量解析文件路径"""
        return [self.resolve_file_path(fp) for fp in (file_paths or [])]

    def get_input_files(self) -> list:
        """获取输入文件列表（从 params 中提取并解析）"""
        file_paths = self._params.get("file_paths", [])
        file_path = self._params.get("file_path", "")

        if file_path and file_path not in file_paths:
            file_paths.append(file_path)

        return self.resolve_file_paths(file_paths)

    def get_excel_file(self) -> str:
        """获取第一个 Excel 文件路径，如果没有返回 None"""
        for fp in self.get_input_files():
            if fp.lower().endswith(('.xlsx', '.xls', '.csv')):
                return fp
        return None

    def get_context(self) -> str:
        """获取用户上下文/需求描述"""
        return self._params.get("context", "") or self._params.get("skillDescription", "")
