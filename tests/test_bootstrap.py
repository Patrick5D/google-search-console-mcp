"""
[INPUT]: 依赖 pathlib 检查项目根目录文件布局
[OUTPUT]: 对外提供 bootstrap 级元数据存在性测试
[POS]: tests 的启动骨架测试，先验证项目最小运行面是否被建立
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from pathlib import Path


def test_project_metadata_files_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (root / "pyproject.toml").exists()
    assert (root / ".gitignore").exists()
    assert (root / ".env.example").exists()
