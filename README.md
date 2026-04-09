[![en](https://img.shields.io/badge/lang-en-red.svg)](README.md)
[![zh-cn](https://img.shields.io/badge/lang-zh--cn-blue.svg)](README.zh-CN.md)

# generate-linter-configuration-beta

beta edition of a linter configuration generate tool ,mainly use LLM . May need some help while using .



## How to use

1. 安装：在根目录下打开终端，使用指令安装

```python
pip install -e .
```

2. 配置大模型：配置大模型：本项目使用litellm库进行大模型的统一格式调用，因此在使用前请确保您已经将自己的key配置为环境变量且有充足的token资源。

3. 使用示例：

   ```python
   gen-linter-config -t checkstyle --input "函数参数不多于5个"
   gen-linter-config -t checkstyle --input rule.txt --out output.json
   gen-linter-config -t checkstyle --input "使用大括号包裹代码块" --format json
   gen-linter-config --tool Cppcheck --model dashscope/qwen3-max --input "禁止使用可能返回空指针的 malloc 函数而不进行检查。"
   # cppcheck不适用属性名系统所以实际上不会返回包含属性名的内容。
   ```
   
   如果不指定输出文件则直接输出在控制台中。

## 将key配置为系统级环境变量

Windows：通过系统属性设置。找到系统-属性，找到高级系统设置-环境变量，然后在上方的用户环境变量中新建一个变量名为OPENAI_API_KEY，值为密钥的值的用户变量。

Linux/macos：在shell配置文件中设置环境变量。打开终端，根据使用shell的不同执行指令：

```python
# Bash
nano ~/.bashrc
# Zsh
nano ~/.zshrc
# 其它的shell可能需要查阅相关文档确定具体指令。
```

在配置文件中添加：

```py
export OPENAI_API_KEY=[你的 OpenAI API 密钥]
```

然后保存并退出。让更改生效：

```python
# Bash
source ~/.bashrc
# Zsh
source ~/.zshrc
# 其它的shell可能需要查阅相关文档确定具体指令。
```

## 支持的工具清单

| Tool       | Y/N  |
| :--------- | ---- |
| Checkstyle | Y    |
| ESLint     | Y    |
| Biome      | Y    |
| ClangTidy  | Y    |
| CppCheck   | Y    |
| Flake8     | Y    |
| PMD        | Y    |
| Pylint     | Y    |
| Reek       | Y    |
| RuboCop    | Y    |
| Ruff       | Y    |

其中Checkstyle和ESLint支持较为完善的生成机制，其余工具则不支持，更多工具的配置生成还在开发中。
