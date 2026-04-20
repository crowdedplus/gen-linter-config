from importlib.metadata import version, PackageNotFoundError
try:
    __version__ = version("gen-linter-config")
except PackageNotFoundError:
    # 如果包未安装（如在开发环境中），可以提供一个默认值或留空
    __version__ = "0.0.0-dev"