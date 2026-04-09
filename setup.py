# setup.py
from setuptools import setup, find_packages

setup(
    name="gen-linter-config",
    version="1.0.0",
    description="GenerateLinterConfig - 代码检查规则生成工具",
    packages=find_packages(),
    py_modules=["generate_linter_config"],
    install_requires=[
        # 添加您的依赖项
    ],
    entry_points={
        'console_scripts': [
            'gen-linter-config=generate_linter_config:main',
        ],
    },
    python_requires='>=3.7',
)