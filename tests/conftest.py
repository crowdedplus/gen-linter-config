import json
from pathlib import Path
import pytest

# 获取测试夹具根目录
FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture():
    """返回一个辅助函数，用于加载指定工具、用例类型的输入/期望输出。"""

    def _load(tool: str, case: str, kind: str):
        """
        :param tool: "checkstyle" 或 "eslint"
        :param case: 用例名（不含扩展名），如 "coding_format"
        :param kind: "input" 或 "expected"
        :return: 输入文本（str）或期望输出（dict）
        """
        if kind == "input":
            file_path = FIXTURE_DIR / tool / "input" / f"{case}.txt"
            return file_path.read_text(encoding="utf-8")
        elif kind == "expected":
            file_path = FIXTURE_DIR / tool / "expected" / f"{case}_out.json"
            return json.loads(file_path.read_text(encoding="utf-8"))
        else:
            raise ValueError("kind must be 'input' or 'expected'")

    return _load


@pytest.fixture
def default_model():
    """默认测试模型，可根据环境变量覆盖，避免频繁调用收费 API。"""
    import os
    return os.environ.get("TEST_MODEL", "deepseek/deepseek-chat")